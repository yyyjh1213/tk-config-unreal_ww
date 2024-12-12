import tank
import os
import sys
import maya.cmds as cmds
import maya.mel as mel

HookBaseClass = tank.get_hook_baseclass()

class MayaAssetPublishPlugin(HookBaseClass):
    """
    Plugin for publishing a Maya asset.
    """

    @property
    def description(self):
        return """Publishes the Maya asset to Shotgun. A <b>Publish</b> entry will be
        created in Shotgun which will include a reference to the exported asset's current
        path on disk. Other users will be able to access the published file via
        the <b>Loader</b> app so long as they have access to
        the file's location on disk."""

    @property
    def settings(self):
        base_settings = super(MayaAssetPublishPlugin, self).settings or {}
        publish_template_setting = {
            "Publish Template": {
                "type": "template",
                "default": None,
                "description": "Template path for published work files. Should"
                               "correspond to a template defined in "
                               "templates.yml.",
            },
            "Publish Folder": {
                "type": "string",
                "default": None,
                "description": "Optional folder to use as a root for publishes"
            },
        }
        base_settings.update(publish_template_setting)
        return base_settings

    @property
    def item_filters(self):
        return ["maya.session"]

    def accept(self, settings, item):
        if item.type == "maya.session":
            if not cmds.ls(type="mesh"):
                self.logger.warn("No meshes found in the scene")
                return {"accepted": False}
            return {"accepted": True}
        return {"accepted": False}

    def validate(self, settings, item):
        """
        Validates the given item to check that it is ok to publish.
        """
        publisher = self.parent
        path = _session_path()
        
        if not path:
            error_msg = "The Maya session has not been saved."
            self.logger.error(error_msg)
            raise Exception(error_msg)

        if not os.path.exists(path):
            error_msg = "The Maya session file '%s' does not exist." % path
            self.logger.error(error_msg)
            raise Exception(error_msg)

        # Get the publish path
        publish_path = self._get_publish_path(settings, item)
        
        # If the publish path exists, increment the version number
        if os.path.exists(publish_path):
            self.logger.info("A file already exists in the publish path. Looking for the next available version number.")
            publish_path = self._get_next_version_path(publish_path)
            
        # Store the publish path on the item properties
        item.properties["publish_path"] = publish_path

        return True

    def publish(self, settings, item):
        publisher = self.parent
        path = _session_path()

        # Get the path in a normalized state. No trailing separator, separators are
        # appropriate for current os, no double separators, etc.
        path = os.path.normpath(path)

        # Ensure the session is saved
        _save_session(path)

        # Get the publish path
        publish_path = item.properties.get("publish_path")
        
        # Ensure the publish folder exists
        publish_folder = os.path.dirname(publish_path)
        self.parent.ensure_folder_exists(publish_folder)
        
        # Export the FBX
        self._maya_export_fbx(publish_path)

        # Register the publish
        self._register_publish(settings, item, publish_path)

        return True

    def _get_publish_path(self, settings, item):
        """
        Get the path where the plugin will publish the asset.
        """
        # Get the path in a normalized state
        path = _session_path()
        path = os.path.normpath(path)

        # Get settings values - need to get the actual value from the PluginSetting object
        publish_template = settings.get("Publish Template")
        publish_template = publish_template.value if hasattr(publish_template, "value") else publish_template
        
        publish_folder = settings.get("Publish Folder")
        publish_folder = publish_folder.value if hasattr(publish_folder, "value") else publish_folder

        if publish_template:
            publisher = self.parent
            fields = {}
            
            # Get fields from the current session path
            work_template = publisher.sgtk.template_from_path(path)
            if work_template:
                fields = work_template.get_fields(path)
            
            # Apply fields to publish template
            publish_template = publisher.sgtk.templates.get(publish_template)
            if not publish_template:
                raise Exception("Publish template '%s' not found!" % publish_template)
            
            return publish_template.apply_fields(fields)
        
        elif publish_folder:
            # Use publish folder with the same filename
            filename = os.path.basename(path)
            basename, ext = os.path.splitext(filename)
            publish_path = os.path.join(publish_folder, basename + ".fbx")
            return publish_path
        
        else:
            # Use the same path but change extension to .fbx
            basename, ext = os.path.splitext(path)
            publish_path = basename + ".fbx"
            return publish_path

    def _get_next_version_path(self, path):
        """
        Given a file path, return a new path with a version number incremented.
        """
        directory = os.path.dirname(path)
        filename = os.path.basename(path)
        basename, ext = os.path.splitext(filename)
        
        # Check if the basename ends with a version number
        import re
        version_pattern = re.compile(r"_v(\d+)$")
        match = version_pattern.search(basename)
        
        if match:
            # Get current version number and increment it
            current_version = int(match.group(1))
            new_version = current_version + 1
            # Replace the version number in the basename
            new_basename = version_pattern.sub("_v%03d" % new_version, basename)
        else:
            # No version number found, add v001
            new_basename = "%s_v001" % basename
            
        return os.path.join(directory, new_basename + ext)

    def _register_publish(self, settings, item, publish_path):
        """
        Register the publish with Shotgun
        """
        publisher = self.parent
        
        # Get the publish info
        publish_version = publisher.util.get_version_number(publish_path)
        publish_name = publisher.util.get_publish_name(publish_path)
        
        # Populate the version data to register
        version_data = {
            "project": publisher.context.project,
            "code": publish_name,
            "description": item.description,
            "entity": publisher.context.entity,
            "sg_task": publisher.context.task,
            "created_by": publisher.context.user,
            "user": publisher.context.user,
            "sg_status_list": "rev",
            "sg_path_to_frames": publish_path
        }
        
        # Create the version in Shotgun
        try:
            version = publisher.shotgun.create("Version", version_data)
            self.logger.info("Created version in Shotgun: %s" % version)
        except Exception as e:
            self.logger.error("Failed to create version in Shotgun: %s" % e)
            raise

        # Register the file with Shotgun
        publish_data = {
            "tk": publisher.sgtk,
            "context": publisher.context,
            "comment": item.description,
            "path": publish_path,
            "name": publish_name,
            "version_number": publish_version,
            "published_file_type": "FBX File"
        }
        
        try:
            publisher.util.register_publish(**publish_data)
            self.logger.info("Published file registered in Shotgun: %s" % publish_path)
        except Exception as e:
            self.logger.error("Failed to register publish in Shotgun: %s" % e)
            raise

    def _maya_export_fbx(self, publish_path):
        """FBX 내보내기 최적화 설정"""
        # Select all meshes
        all_meshes = cmds.ls(type="mesh", long=True)
        if not all_meshes:
            raise Exception("No meshes found in the scene")
        
        # Get the transform nodes of the meshes
        transform_nodes = [cmds.listRelatives(mesh, parent=True, fullPath=True)[0] for mesh in all_meshes]
        
        # Select the transform nodes
        cmds.select(transform_nodes, replace=True)
        
        # FBX export settings
        mel.eval('FBXExportSmoothingGroups -v true')
        mel.eval('FBXExportHardEdges -v false')
        mel.eval('FBXExportTangents -v false')
        mel.eval('FBXExportSmoothMesh -v true')
        mel.eval('FBXExportInstances -v false')
        mel.eval('FBXExportReferencedAssetsContent -v false')
        mel.eval('FBXExportAnimationOnly -v false')
        mel.eval('FBXExportBakeComplexAnimation -v false')
        
        # Save the FBX
        mel.eval('FBXExport -f "%s" -s' % publish_path.replace("\\", "/"))

def _session_path():
    """
    Return the path to the current session
    :return:
    """
    path = cmds.file(query=True, sn=True)

    if isinstance(path, bytes):
        path = path.decode('utf-8')
    elif path is None:
        path = ''

    return path

def _save_session(path):
    """
    Save the current session
    """
    cmds.file(save=True, force=True)
