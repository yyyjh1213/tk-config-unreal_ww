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
import re

# Local storage path field for known OSes
_OS_LOCAL_STORAGE_PATH_FIELD = {
    "darwin": "mac_path",
    "win32": "windows_path",
    "linux": "linux_path",
    "linux2": "linux_path",
}[sys.platform]

HookBaseClass = tank.get_hook_baseclass()

try:
    import unreal
    UNREAL_AVAILABLE = True
except ImportError:
    UNREAL_AVAILABLE = False

class UnrealAssetPublishPlugin(HookBaseClass):
    """
    Plugin for publishing an Unreal asset with integrated context field handling.
    """

    def __init__(self, *args, **kwargs):
        super(UnrealAssetPublishPlugin, self).__init__(*args, **kwargs)
        self._path_info = self.load_framework("tk-framework-shotgunutils").import_module("path_info")

    @property
    def description(self):
        return """Publishes the asset to Shotgun. A <b>Publish</b> entry will be
        created in Shotgun which will include a reference to the exported asset's current
        path on disk."""

    @property
    def settings(self):
        base_settings = super(UnrealAssetPublishPlugin, self).settings or {}
        publish_settings = {
            "Publish Template": {
                "type": "template",
                "default": None,
                "description": "Template path for published work files."
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
        base_settings.update(publish_settings)
        return base_settings

    @property
    def item_filters(self):
        return ["unreal.asset.StaticMesh"]

    def get_context_fields(self, context, template=None):
        """
        Get fields from context with improved error handling and validation.
        
        :param context: The context to extract fields from
        :param template: Optional template to validate fields against
        :returns: Dictionary of fields or None if validation fails
        """
        self.logger.debug("Getting context fields from: %s" % context)
        
        if not context:
            self.logger.error("No context provided")
            return None
            
        try:
            # Initialize with default fields
            fields = {
                "version": 1,
                "Step": "publish",
                "sg_asset_type": "Asset"
            }
            
            # Get entity fields
            if context.entity:
                self.logger.debug("Processing entity fields: %s" % context.entity)
                
                # Get asset code and name
                asset_code = context.entity.get("code")
                if not asset_code:
                    self.logger.error("Required field 'code' missing from entity")
                    return None
                    
                fields["Asset"] = asset_code
                fields["name"] = context.entity.get("name", asset_code)
                
                # Get asset type
                asset_type = context.entity.get("sg_asset_type")
                if asset_type:
                    fields["sg_asset_type"] = asset_type
            else:
                self.logger.error("Context has no entity")
                return None
            
            # Get step fields
            if context.step:
                self.logger.debug("Processing step fields: %s" % context.step)
                step_name = context.step.get("short_name")
                if step_name:
                    fields["Step"] = step_name
            
            # Add date fields
            current_time = datetime.datetime.now()
            fields.update({
                "YYYY": current_time.year,
                "MM": current_time.month,
                "DD": current_time.day
            })
            
            self.logger.debug("Generated fields: %s" % fields)
            
            # Validate against template if provided
            if template:
                missing_keys = template.missing_keys(fields)
                if missing_keys:
                    self.logger.error("Missing required fields for template: %s" % missing_keys)
                    return None
                    
                try:
                    template.apply_fields(fields)
                except tank.TankError as e:
                    self.logger.error("Failed to apply fields to template: %s" % e)
                    return None
            
            return fields
            
        except Exception as e:
            self.logger.error("Error getting context fields: %s" % e)
            return None

    def accept(self, settings, item):
        if UNREAL_AVAILABLE and item.properties.get("unreal_asset_path"):
            return {"accepted": True}
        return {"accepted": False}

    def validate(self, settings, item):
        """
        Validates the given item with integrated context field handling.
        """
        publisher = self.parent
        
        # Get publish template
        publish_template_name = settings.get("Publish Template").value
        publish_template = publisher.get_template_by_name(publish_template_name)
        if not publish_template:
            self.logger.error("No publish template found: %s" % publish_template_name)
            return False
            
        # Get context
        context = item.context or publisher.context
        if not context:
            self.logger.error("No context found for item")
            return False
            
        # Get context fields
        fields = self.get_context_fields(context, publish_template)
        if not fields:
            self.logger.error("Failed to get context fields")
            return False
        
        # Update version from path if available
        path = item.properties.get("path")
        if path:
            version_match = re.search(r"\.?v(\d+)", path, re.IGNORECASE)
            if version_match:
                fields["version"] = int(version_match.group(1))
        
        # Update name from item properties
        fields["name"] = item.properties.get("asset_name", fields.get("name", "unknown"))
        
        try:
            # Generate publish path
            publish_path = publish_template.apply_fields(fields)
            item.properties["publish_path"] = publish_path
            item.properties["fields"] = fields
            self.logger.debug("Publish path: %s" % publish_path)
            return True
        except Exception as e:
            self.logger.error("Error creating publish path: %s" % e)
            return False

    def publish(self, settings, item):
        """
        Executes the publish logic with integrated context handling.
        """
        try:
            publisher = self.parent
            publish_path = item.properties["publish_path"]
            
            # Ensure publish folder exists
            publish_folder = os.path.dirname(publish_path)
            self.parent.ensure_folder_exists(publish_folder)
            
            # Get asset info
            asset_path = item.properties["unreal_asset_path"]
            asset_name = os.path.splitext(os.path.basename(publish_path))[0]
            
            # Export to FBX
            _unreal_export_asset_to_fbx(publish_folder, asset_path, asset_name)
            
            # Register publish
            self._register_publish(settings, item, publish_path)
            
            return True
        except Exception as e:
            self.logger.error("Error during publish: %s" % e)
            return False

def _unreal_export_asset_to_fbx(destination_path, asset_path, asset_name):
    """Export an asset to FBX from Unreal"""
    task = _generate_fbx_export_task(destination_path, asset_path, asset_name)
    exported = unreal.Exporter.run_asset_export_task(task)
    if not exported:
        raise Exception("FBX export failed")

def _generate_fbx_export_task(destination_path, asset_path, asset_name):
    """Generate FBX export task configuration"""
    export_task = unreal.AssetExportTask()
    export_task.object = unreal.load_asset(asset_path)
    export_task.filename = os.path.join(destination_path, asset_name + ".fbx")
    export_task.selected = False
    export_task.replace_identical = True
    export_task.prompt = False
    export_task.automated = True
    return export_task