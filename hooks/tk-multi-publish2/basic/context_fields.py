"""
Hook for managing context fields with improved error handling and field validation.
"""
import sgtk
import datetime

HookBaseClass = sgtk.get_hook_baseclass()

class ContextFields(HookBaseClass):
    """
    Enhanced methods for managing context fields.
    """
    
    def get_context_fields(self, context, template=None):
        """
        Get fields from context and validate required fields with improved error handling.
        
        :param context: The context to extract fields from
        :param template: Optional template to validate fields against
        :returns: Dictionary of fields or None if validation fails
        """
        self.logger.debug("Input context: %s" % context)
        self.logger.debug("Input template: %s" % template)
        
        if not context:
            self.logger.error("No context provided")
            return None
            
        try:
            # Initialize with default fields
            default_fields = {
                "version": 1,
                "Step": "publish",
                "sg_asset_type": "Asset"
            }
            
            fields = default_fields.copy()
            
            # Add date fields
            current_time = datetime.datetime.now()
            fields.update({
                "YYYY": current_time.year,
                "MM": current_time.month,
                "DD": current_time.day
            })
            
            # Get fields from entity
            if context.entity:
                self.logger.debug("Entity fields: %s" % context.entity)
                
                # Get asset code and name
                asset_code = context.entity.get("code")
                if not asset_code:
                    self.logger.error("Required field 'code' is missing from entity")
                    return None
                    
                fields["Asset"] = asset_code
                fields["name"] = context.entity.get("name", asset_code)
                
                # Get asset type
                asset_type = context.entity.get("sg_asset_type")
                if asset_type:  # Override default only if exists
                    fields["sg_asset_type"] = asset_type
            else:
                self.logger.error("Context has no entity")
                return None
                
            # Get fields from step
            if context.step:
                self.logger.debug("Step fields: %s" % context.step)
                step_name = context.step.get("short_name")
                if step_name:  # Override default only if exists
                    fields["Step"] = step_name
            
            # Get version
            version = context.get_shotgun_version()
            if version is not None:
                fields["version"] = version
            
            self.logger.debug("Generated fields: %s" % fields)
            
            # Validate against template if provided
            if template:
                missing_keys = template.missing_keys(fields)
                if missing_keys:
                    self.logger.error("Missing required fields for template: %s" % missing_keys)
                    return None
                    
                try:
                    template.apply_fields(fields)
                except sgtk.TankError as e:
                    self.logger.error("Failed to apply fields to template: %s" % e)
                    return None
            
            # Final validation of required fields
            required_fields = ["name", "version", "sg_asset_type", "Step", "Asset"]
            missing_fields = [field for field in required_fields if field not in fields]
            if missing_fields:
                self.logger.error("Missing required fields: %s" % missing_fields)
                return None
            
            self.logger.debug("Successfully generated fields: %s" % fields)
            return fields
            
        except Exception as e:
            self.logger.error("Error getting context fields: %s" % e)
            return None
    
    def validate_required_fields(self, context):
        """
        Validate that context has all required fields.
        
        :param context: The context to validate
        :returns: True if valid, False otherwise
        """
        if not context:
            self.logger.error("No context provided")
            return False
        
        try:
            # Validate entity
            if not context.entity:
                self.logger.error("Context has no entity")
                return False
            
            required_entity_fields = ["sg_asset_type", "code", "name"]
            for field in required_entity_fields:
                if not context.entity.get(field):
                    self.logger.warning("Required entity field '%s' is missing" % field)
            
            # Validate step
            if not context.step:
                self.logger.warning("Context has no step, will use default")
            elif not context.step.get("short_name"):
                self.logger.warning("Required step field 'short_name' is missing, will use default")
            
            return True
            
        except Exception as e:
            self.logger.error("Error validating required fields: %s" % e)
            return False
    
    def get_entity_fields(self, entity):
        """
        Extract fields from an entity with improved field handling.
        
        :param entity: The entity to extract fields from
        :returns: Dictionary of field names and their values
        """
        fields = {}
        
        if not entity:
            return fields
        
        try:
            # Extract standard fields with better fallbacks
            fields["Asset"] = entity.get("code", "default")
            fields["name"] = entity.get("name", entity.get("code", "default"))
            fields["sg_asset_type"] = entity.get("sg_asset_type", "Asset")
            
            # Add any custom fields here if needed
            
            return fields
            
        except Exception as e:
            self.logger.error("Error getting entity fields: %s" % e)
            return {}
    
    def get_step_fields(self, step):
        """
        Extract fields from a pipeline step with improved error handling.
        
        :param step: The pipeline step to extract fields from
        :returns: Dictionary of field names and their values
        """
        fields = {}
        
        if not step:
            return fields
        
        try:
            # Extract standard fields with default
            fields["Step"] = step.get("short_name", "publish")
            
            # Add any custom step fields here if needed
            
            return fields
            
        except Exception as e:
            self.logger.error("Error getting step fields: %s" % e)
            return {}