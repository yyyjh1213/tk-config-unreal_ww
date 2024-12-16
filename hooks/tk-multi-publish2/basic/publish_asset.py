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
        Returns a boolean to indicate validity.
        """
        publisher = self.parent
        engine = publisher.engine

        # Enhanced context validation
        context = self.parent.context
        if not context:
            self.logger.error("No context found!")
            return False
            
        if not context.entity:
            self.logger.error("No entity found in context!")
            return False
            
        if not context.step:
            self.logger.error("No step found in context!")
            return False

        # Detailed context logging
        self.logger.debug("=== Context Details ===")
        self.logger.debug(f"Context: {context}")
        self.logger.debug(f"Context Entity: {context.entity}")
        self.logger.debug(f"Context Step: {context.step}")
        self.logger.debug(f"Context Task: {context.task}")
        self.logger.debug(f"Context User: {context.user}")
        self.logger.debug(f"Context Project: {context.project}")
        
        # Validate entity fields
        if context.entity:
            self.logger.debug("=== Entity Fields ===")
            for field in ['type', 'id', 'name', 'code', 'sg_asset_type']:
                value = context.entity.get(field)
                self.logger.debug(f"Entity {field}: {value}")
        else:
            self.logger.error("Entity not found in context")
            return False

        # Validate step fields
        if context.step:
            self.logger.debug("=== Step Fields ===")
            for field in ['type', 'id', 'name', 'code']:
                value = context.step.get(field)
                self.logger.debug(f"Step {field}: {value}")
        else:
            self.logger.error("Step not found in context")
            return False

        # Get template and validate
        publish_template_name = settings["Publish Template"].value
        publish_template = publisher.get_template_by_name(publish_template_name)
        
        if not publish_template:
            self.logger.error(f"Could not find template '{publish_template_name}'")
            return False

        self.logger.debug(f"Template Name: {publish_template_name}")
        self.logger.debug(f"Template: {publish_template}")
        self.logger.debug(f"Template Keys: {publish_template.keys}")
        
        try:
            # Basic required fields
            fields = {
                "name": os.path.splitext(os.path.basename(item.properties.get("unreal_asset_path", "")))[0],
                "version": 1
            }
            
            # Get entity fields safely
            if context.entity:
                if hasattr(context.entity, "code"):
                    fields["Asset"] = context.entity.code
                else:
                    fields["Asset"] = context.entity.get("code", "")
                    
            # Get step fields safely
            if context.step:
                if hasattr(context.step, "name"):
                    fields["Step"] = context.step.name
                else:
                    fields["Step"] = context.step.get("name", "")
            
            # Log all available fields
            self.logger.debug("=== Available Template Fields ===")
            for key in publish_template.keys:
                self.logger.debug(f"Template requires: {key}")
                
            self.logger.debug("=== Current Field Values ===")
            for key, value in fields.items():
                self.logger.debug(f"{key}: {value}")
            
            # Validate required fields
            missing_fields = []
            for key in publish_template.keys:
                if key not in fields or not fields[key]:
                    missing_fields.append(key)
                    
            if missing_fields:
                self.logger.error(f"Missing required fields for template: {missing_fields}")
                self.logger.error(f"Current fields: {fields}")
                return False

            # Try to create publish path
            publish_path = publish_template.apply_fields(fields)
            self.logger.debug(f"Generated publish path: {publish_path}")
            
            item.properties["path"] = publish_path
            item.properties["publish_path"] = publish_path
            
            return True

        except Exception as e:
            self.logger.error(f"Error resolving template: {str(e)}")
            self.logger.error(f"Current fields: {fields}")
            return False

    def publish(self, settings, item):
        """
        Executes the publish logic for the given item and settings.
        """
        publisher = self.parent

        # Get the path in a normalized state. No trailing separator, separators are
        # appropriate for current os, no double separators, etc.
        path = tank.util.ShotgunPath.normalize(path)

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
