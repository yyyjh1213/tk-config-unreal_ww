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

import unreal

# Local storage path field for known Oses.
_OS_LOCAL_STORAGE_PATH_FIELD = {
    "darwin": "mac_path",
    "win32": "windows_path",
    "linux": "linux_path",
    "linux2": "linux_path",
}[sys.platform]

HookBaseClass = sgtk.get_hook_baseclass()


class UnrealMoviePublishPlugin(HookBaseClass):
    """
    Plugin for publishing an Unreal sequence as a rendered movie file.
    """

    @property
    def description(self):
        return """
        Publish an Unreal sequence as a rendered movie file. A review version
        will be generated for Flow Production Tracking.
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
        return ["unreal.session"]

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

        # because a publish template is configured, we know we can publish movie
        # files. We can check the validity of the item here if we want.
        return {"accepted": True}

    def validate(self, settings, item):
        """
        Validates the given item to check that it is ok to publish.
        """
        # Get the path to the current project
        project = unreal.EditorLevelLibrary.get_editor_world()
        if not project:
            error_msg = "No active Unreal project found."
            self.logger.error(error_msg)
            raise Exception(error_msg)

        return True

    def publish(self, settings, item):
        """
        Executes the publish logic for the given item and settings.
        """
        publisher = self.parent

        # get the path to create the movie
        publish_path = self.get_publish_path(settings, item)

        # render the sequence using Movie Render Queue
        self._render_sequence(publish_path)

        # register the publish
        self._register_publish(settings, item, publish_path)

        return True

    def get_publish_path(self, settings, item):
        """
        Get a publish path for the supplied settings and item.
        """
        publisher = self.parent

        # get the publish template from the item properties
        publish_template = item.properties["publish_template"]

        # get the current level name
        level = unreal.EditorLevelLibrary.get_editor_world().get_name()

        # get fields from the template
        fields = {
            "name": level,
            "version": 1,  # You might want to implement proper versioning
            "extension": publish_template.defaults.get("extension", "mov")
        }

        # create the publish path by applying the fields to the template
        publish_path = publish_template.apply_fields(fields)

        return publish_path

    def _render_sequence(self, output_path):
        """
        Render the current sequence using Movie Render Queue.
        """
        # Get the Movie Render Queue subsystem
        mrq = unreal.MovieRenderQueueSubsystem.get_movie_render_queue()
        if not mrq:
            raise Exception("Failed to get Movie Render Queue subsystem")

        # Create render settings
        settings = unreal.AutomatedLevelSequenceCapture()
        settings.settings.output_file = output_path
        settings.settings.output_format = unreal.MoviePipelineOutputFormat.MP4
        settings.settings.resolution.x = 1920
        settings.settings.resolution.y = 1080
        settings.settings.frame_rate = 30.0

        # Add job to queue
        job = mrq.add_job(settings)
        if not job:
            raise Exception("Failed to add render job to queue")

        # Start rendering
        mrq.render_queue_jobs()

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
