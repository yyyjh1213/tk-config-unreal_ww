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

        return True

    def publish(self, settings, item):
        publisher = self.parent
        path = _session_path()

        # Get the path in a normalized state. No trailing separator, separators are
        # appropriate for current os, no double separators, etc.
        path = sgtk.util.ShotgunPath.normalize(path)

        # Ensure the session is saved
        _save_session(path)

        # Get the publish path
        publish_path = self._get_publish_path(settings, item)
        
        # Ensure the publish folder exists
        publish_folder = os.path.dirname(publish_path)
        self.parent.ensure_folder_exists(publish_folder)
        
        # Export the FBX
        self._maya_export_fbx(publish_path)

        # Register the publish
        self._register_publish(settings, item, publish_path)

        return True

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

    if path is not None:
        path = six.ensure_str(path)

    return path
