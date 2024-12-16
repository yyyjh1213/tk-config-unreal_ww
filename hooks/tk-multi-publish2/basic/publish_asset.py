# Copyright (c) 2017 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import tank
import os
import sys
import datetime
from . import path_info
from . import context_fields

# Local storage path field for known Oses.
_OS_LOCAL_STORAGE_PATH_FIELD = {
    "darwin": "mac_path",
    "win32": "windows_path",
    "linux": "linux_path",
    "linux2": "linux_path",
}[sys.platform]

HookBaseClass = tank.get_hook_baseclass()

# Import unreal module only when in Unreal environment
try:
    import unreal
    UNREAL_AVAILABLE = True
except ImportError:
    UNREAL_AVAILABLE = False

class UnrealAssetPublishPlugin(HookBaseClass):
    """
    Plugin for publishing an Unreal asset.
    """

    def __init__(self, *args, **kwargs):
        super(UnrealAssetPublishPlugin, self).__init__(*args, **kwargs)
        self._path_info = self.load_framework("tk-framework-shotgunutils").import_module("path_info")
        self._context_fields = self.load_framework("tk-framework-shotgunutils").import_module("context_fields")

    @property
    def description(self):
        return """Publishes the asset to Shotgun. A <b>Publish</b> entry will be
        created in Shotgun which will include a reference to the exported asset's current
        path on disk. Other users will be able to access the published file via
        the <b>Loader</b> app so long as they have access to
        the file's location on disk."""

    @property
    def settings(self):
        base_settings = super(UnrealAssetPublishPlugin, self).settings or {}
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
            "Additional Fields": {
                "type": "dict",
                "default": {},
                "description": "Additional fields to include in the publish template"
            }
        }
        base_settings.update(publish_template_setting)
        return base_settings

    @property
    def item_filters(self):
        return ["unreal.asset.StaticMesh"]

    def accept(self, settings, item):
        """
        Method called by the publisher to determine if an item is of any interest to this plugin.
        Only items matching the filters defined via the item_filters property will be presented to this method.

        A publish task will be generated for each item accepted here.

        :param settings: Dictionary of Settings. The keys are strings, matching the keys returned in the settings property.
                       The values are `Setting` instances.
        :param item: Item to process

        :returns: dictionary with the following keys:
            - accepted (bool): True if the plugin should accept the item, False otherwise
            - enabled (bool): If True, the plugin will be enabled in the UI, otherwise it will be disabled.
                            Only applies to accepted tasks.
            - visible (bool): If True, the plugin will be visible in the UI, otherwise it will be hidden.
                            Only applies to accepted tasks.
            - checked (bool): If True, the plugin will be checked in the UI, otherwise it will be unchecked.
                            Only applies to accepted tasks.
        """
        if UNREAL_AVAILABLE and item.properties.get("unreal_asset_path"):
            return {"accepted": True}
        return {"accepted": False}

    def validate(self, settings, item):
        """
        Validates the given item to check that it is ok to publish.
        """
        publisher = self.parent
        
        # Get the path in a normalized state
        path = tank.util.ShotgunPath.normalize(item.properties.get("path"))

        # Get the publish template from the settings
        publish_template = publisher.get_template_by_name(settings.get("Publish Template").value)
        if not publish_template:
            self.logger.debug("No publish template set for item")
            return False

        # Initialize field gatherers
        path_info_hook = self.parent.get_hook_instance("path_info_hook")
        context_fields_hook = self.parent.get_hook_instance("context_fields_hook")

        # Get context and fields
        context = item.context or publisher.context
        fields = context_fields_hook.get_context_fields(context, publish_template)

        # Get template fields from path
        if path:
            template_fields = path_info_hook.get_template_fields(path, publish_template)
            fields.update(template_fields)

        # Get version from path
        if path:
            version = path_info_hook.get_version_number(path)
            fields["version"] = version

        # Add fields from entity and step
        if context.entity:
            entity_fields = context_fields_hook.get_entity_fields(context.entity)
            fields.update(entity_fields)

        if context.step:
            step_fields = context_fields_hook.get_step_fields(context.step)
            fields.update(step_fields)

        # Add/override with any fields from item properties
        fields.update({
            "name": item.properties.get("name", "default"),
            "version": item.properties.get("version_number", fields.get("version", 1)),
        })

        # Add date fields
        current_time = datetime.datetime.now()
        fields.update({
            "YYYY": current_time.year,
            "MM": current_time.month,
            "DD": current_time.day
        })

        # Validate required fields
        try:
            missing_keys = publish_template.missing_keys(fields)
            if missing_keys:
                raise tank.TankError("Missing required fields: %s" % missing_keys)
        except tank.TankError as e:
            self.logger.error("Field validation failed: %s" % e)
            self.logger.error("Context: %s" % context)
            self.logger.error("Fields: %s" % fields)
            self.logger.error("Template keys: %s" % publish_template.keys)
            return False

        try:
            publish_path = publish_template.apply_fields(fields)
            item.properties["publish_path"] = publish_path
            self.logger.debug("Publishing to path: %s" % publish_path)
        except tank.TankError as e:
            self.logger.error("Failed to resolve publish path: %s" % e)
            return False

        return True

    def publish(self, settings, item):
        """
        Executes the publish logic for the given item and settings.
        """
        publisher = self.parent

        # Get the publish path
        publish_path = item.properties["publish_path"]
        
        # Ensure the publish folder exists
        publish_folder = os.path.dirname(publish_path)
        self.parent.ensure_folder_exists(publish_folder)

        # Get the asset path and name
        asset_path = item.properties["unreal_asset_path"]
        asset_name = os.path.splitext(os.path.basename(publish_path))[0]

        # Export the asset to FBX
        _unreal_export_asset_to_fbx(publish_folder, asset_path, asset_name)

        # Register the publish
        self._register_publish(settings, item, publish_path)

        return True

def _unreal_export_asset_to_fbx(destination_path, asset_path, asset_name):
    """
    Export an asset to FBX from Unreal

    :param destination_path: The path where the exported FBX will be placed
    :param asset_path: The Unreal asset to export to FBX
    :param asset_name: The asset name to use for the FBX filename
    """
    task = _generate_fbx_export_task(destination_path, asset_path, asset_name)
    exported = unreal.Exporter.run_asset_export_task(task)
    if not exported:
        raise Exception("FBX 내보내기에 실패했습니다.")

def _generate_fbx_export_task(destination_path, asset_path, asset_name):
    """
    Create and configure an Unreal AssetExportTask

    :param destination_path: The path where the exported FBX will be placed
    :param asset_path: The Unreal asset to export to FBX
    :param asset_name: The FBX filename to export to
    :return the configured AssetExportTask
    """
    # Create the export task
    export_task = unreal.AssetExportTask()
    
    # Configure the task
    export_task.object = unreal.load_asset(asset_path)
    export_task.filename = os.path.join(destination_path, asset_name + ".fbx")
    export_task.selected = False
    export_task.replace_identical = True
    export_task.prompt = False
    export_task.automated = True
    
    return export_task
