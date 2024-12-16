# This file is based on templates provided and copyrighted by Autodesk, Inc.
# This file has been modified by Epic Games, Inc. and is subject to the license
# file included in this repository.

import sgtk
import sys
from tank_vendor import six

import copy
import datetime
import os
import pprint
import subprocess
import tempfile

import maya.cmds as cmds
import maya.mel as mel

# Local storage path field for known Oses.
_OS_LOCAL_STORAGE_PATH_FIELD = {
    "darwin": "mac_path",
    "win32": "windows_path",
    "linux": "linux_path",
    "linux2": "linux_path",
}[sys.platform]

HookBaseClass = sgtk.get_hook_baseclass()


class MayaMoviePublishPlugin(HookBaseClass):
    """
    Plugin for publishing a Maya scene as a rendered movie file using Unreal Engine.
    """

    @property
    def description(self):
        return """
        Publish a Maya scene as a rendered movie file using Unreal Engine. A review
        version will be generated for Flow Production Tracking.
        """

    @property
    def settings(self):
        """
        Dictionary defining the settings that this plugin expects to receive
        through the settings parameter in the accept, validate, publish and
        finalize methods.
        """
        return {
            "Publish Template": {
                "type": "template",
                "default": None,
                "description": "Template path for published work files. Should"
                "correspond to a template defined in "
                "templates.yml.",
            }
        }

    @property
    def item_filters(self):
        """
        List of item types that this plugin is interested in.
        Only items matching entries in this list will be presented to the
        accept() method. Strings can contain glob patterns such as *, for example
        ["maya.*", "file.maya"]
        """
        return ["maya.session"]

    def accept(self, settings, item):
        """
        Method called by the publisher to determine if an item is of any
        interest to this plugin. Only items matching the filters defined via the
        item_filters property will be presented to this method.
        """
        publisher = self.parent
        template_name = settings["Publish Template"].value

        # ensure a work file template is available on the parent item
        work_template = item.parent.properties.get("work_template")
        if not work_template:
            self.logger.debug(
                "A work template is required for the session item in order to "
                "publish a movie. Not accepting the item."
            )
            return {"accepted": False}

        # ensure the publish template is available
        publish_template = publisher.get_template_by_name(template_name)
        if not publish_template:
            self.logger.debug(
                "A valid publish template could not be determined for the "
                "session item. Not accepting the item."
            )
            return {"accepted": False}

        # we've validated the work and publish templates. add them to the item properties
        # for use in subsequent methods
        item.properties["work_template"] = work_template
        item.properties["publish_template"] = publish_template

        # check that the FBX export hook is available
        if not self._fbx_hook_available():
            self.logger.debug(
                "FBX export hook is not available. Not accepting the item."
            )
            return {"accepted": False}

        # because a publish template is configured, we know we can publish movie
        # files. We can check the validity of the item here if we want.
        return {"accepted": True}

    def validate(self, settings, item):
        """
        Validates the given item to check that it is ok to publish.
        """
        path = _session_path()

        # ---- ensure the session has been saved

        if not path:
            # the session still requires saving. provide a save button.
            # validation fails.
            error_msg = "The Maya session has not been saved."
            self.logger.error(error_msg)
            raise Exception(error_msg)

        # get the normalized path
        path = sgtk.util.ShotgunPath.normalize(path)

        # check that there is still geometry in the scene:
        if not cmds.ls(geometry=True, noIntermediate=True):
            error_msg = (
                "Validation failed because there is no geometry in the scene "
                "to be exported. You can uncheck this plugin or create "
                "geometry to export to render a movie."
            )
            self.logger.error(error_msg)
            raise Exception(error_msg)

        return True

    def publish(self, settings, item):
        """
        Executes the publish logic for the given item and settings.
        """
        publisher = self.parent

        # get the path in a normalized state. no trailing separator, separators
        # are appropriate for current os, no double separators, etc.
        path = sgtk.util.ShotgunPath.normalize(_session_path())

        # ensure the session is saved
        _save_session(path)

        # get the path to create the movie
        publish_path = self.get_publish_path(settings, item)

        # export selected geometry as FBX
        fbx_path = self._export_fbx(item)

        # import FBX into Unreal and create level sequence
        self._create_unreal_sequence(fbx_path, publish_path)

        # clean up temporary files
        os.remove(fbx_path)

        # register the publish
        self._register_publish(settings, item, publish_path)

        return True

    def get_publish_path(self, settings, item):
        """
        Get a publish path for the supplied settings and item.
        """
        publisher = self.parent

        # get the path in a normalized state. no trailing separator, separators
        # are appropriate for current os, no double separators, etc.
        path = sgtk.util.ShotgunPath.normalize(_session_path())

        # ensure the session is saved
        _save_session(path)

        # get the publish path components
        path_info = publisher.util.get_file_path_components(path)
        filename = path_info["filename"]

        if not filename:
            raise Exception("Could not determine filename for publishing.")

        # get the publish template from the item properties
        publish_template = item.properties["publish_template"]

        # get fields from the template
        fields = {}
        work_template = item.properties["work_template"]
        if work_template:
            fields = work_template.get_fields(path)
            fields["extension"] = publish_template.defaults.get(
                "extension", "mov"
            )

        # create the publish path by applying the fields to the template
        publish_path = publish_template.apply_fields(fields)

        return publish_path

    def _fbx_hook_available(self):
        """
        Check if the FBX export hook is available.
        """
        engine = sgtk.platform.current_engine()
        if not engine:
            return False

        app = engine.apps.get("tk-multi-fbxexport")
        if not app:
            return False

        return True

    def _export_fbx(self, item):
        """
        Export selected geometry as FBX.
        """
        # get a temporary path for the FBX export
        temp_dir = tempfile.gettempdir()
        fbx_path = os.path.join(temp_dir, "temp_export.fbx")

        # select all geometry
        cmds.select(cmds.ls(geometry=True, noIntermediate=True), replace=True)

        # get the FBX export hook
        engine = sgtk.platform.current_engine()
        app = engine.apps.get("tk-multi-fbxexport")
        hook = app.execute_hook_method("fbx_hook", "export_fbx",
                                     fbx_path=fbx_path,
                                     items_to_export=None)

        return fbx_path

    def _create_unreal_sequence(self, fbx_path, publish_path):
        """
        Import FBX into Unreal and create a level sequence for rendering.
        """
        # This method would contain the logic to:
        # 1. Import the FBX into Unreal
        # 2. Create a level sequence
        # 3. Set up the camera and animation
        # 4. Render the sequence using Movie Render Queue
        pass

    def _register_publish(self, settings, item, publish_path):
        """
        Register the publish in Flow Production Tracking.
        """
        publisher = self.parent

        # get the publish info
        publish_version = publisher.util.get_version_number(publish_path)
        publish_name = publisher.util.get_publish_name(publish_path)

        # arguments for publish registration
        self.logger.info("Registering publish...")
        publish_data = {
            "tk": publisher.sgtk,
            "context": item.context,
            "comment": item.description,
            "path": publish_path,
            "name": publish_name,
            "version_number": publish_version,
            "thumbnail_path": item.get_thumbnail_as_path(),
            "published_file_type": "Movie",
            "dependency_paths": [],
        }

        # log the publish data for debugging
        self.logger.debug(
            "Populated Publish data...",
            extra={
                "action_show_more_info": {
                    "label": "Publish Data",
                    "tooltip": "Show the complete Publish data dictionary",
                    "text": "<pre>%s</pre>" % (pprint.pformat(publish_data),),
                }
            },
        )

        # create the publish and stash it in the item properties for other
        # plugins to use
        item.properties["sg_publish_data"] = sgtk.util.register_publish(
            **publish_data
        )
        self.logger.info("Publish registered!")


def _session_path():
    """
    Return the path to the current session.
    """
    path = cmds.file(query=True, sn=True)

    if path:
        path = six.ensure_str(path)

    return path


def _save_session(path):
    """
    Save the current session to the supplied path.
    """
    # Maya can choose the wrong file type so we should set it here
    # explicitly based on the extension
    maya_file_type = None
    if path.lower().endswith(".ma"):
        maya_file_type = "mayaAscii"
    elif path.lower().endswith(".mb"):
        maya_file_type = "mayaBinary"

    cmds.file(save=True, force=True, type=maya_file_type)
