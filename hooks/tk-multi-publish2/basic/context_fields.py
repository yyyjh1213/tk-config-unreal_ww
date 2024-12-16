"""
Hook for managing context fields.
"""
import sgtk
import datetime

HookBaseClass = sgtk.get_hook_baseclass()

class ContextFields(HookBaseClass):
    """
    Methods for managing context fields.
    """
    
    def get_context_fields(self, context, template=None):
        """
        Get fields from context and validate required fields.
        
        :param context: The context to extract fields from
        :param template: Optional template to validate fields against
        :returns: Dictionary of fields or None if validation fails
        """
        if not context:
            self.logger.error("No context provided")
            return None
            
        self.logger.debug("Getting fields from context: %s" % context)
        
        fields = {}
        
        # Get fields from entity
        if context.entity:
            self.logger.debug("Entity fields: %s" % context.entity)
            
            # Get asset code
            asset_code = context.entity.get("code")
            if not asset_code:
                self.logger.error("Required field 'code' is missing from entity")
                return None
            fields["Asset"] = asset_code
            
            # Get asset type
            asset_type = context.entity.get("sg_asset_type")
            if not asset_type:
                self.logger.error("Required field 'sg_asset_type' is missing from entity")
                return None
            fields["sg_asset_type"] = asset_type
        else:
            self.logger.error("Context has no entity")
            return None
            
        # Get fields from step
        if context.step:
            self.logger.debug("Step fields: %s" % context.step)
            step_name = context.step.get("short_name")
            if not step_name:
                self.logger.error("Required field 'short_name' is missing from step")
                return None
            fields["Step"] = step_name
        else:
            self.logger.error("Context has no step")
            return None
            
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
            except sgtk.TankError as e:
                self.logger.error("Failed to apply fields to template: %s" % e)
                return None
                
        return fields
        
    def validate_required_fields(self, context):
        """
        Validate that context has all required fields.
        
        :param context: The context to validate
        :returns: True if valid, False otherwise
        """
        if not context:
            self.logger.error("No context provided")
            return False
            
        # Validate entity
        if not context.entity:
            self.logger.error("Context has no entity")
            return False
            
        required_entity_fields = ["sg_asset_type", "code"]
        for field in required_entity_fields:
            if not context.entity.get(field):
                self.logger.error("Required entity field '%s' is missing" % field)
                return False
                
        # Validate step
        if not context.step:
            self.logger.error("Context has no step")
            return False
            
        if not context.step.get("short_name"):
            self.logger.error("Required step field 'short_name' is missing")
            return False
            
        return True
        
    def get_entity_fields(self, entity):
        """
        Extract fields from an entity.
        
        :param entity: The entity to extract fields from
        :returns: Dictionary of field names and their values
        """
        fields = {}
        
        if not entity:
            return fields
            
        # extract standard fields
        fields["Asset"] = entity.get("code", "default")
        fields["sg_asset_type"] = entity.get("sg_asset_type", "Asset")
        
        return fields
        
    def get_step_fields(self, step):
        """
        Extract fields from a pipeline step.
        
        :param step: The pipeline step to extract fields from
        :returns: Dictionary of field names and their values
        """
        fields = {}
        
        if not step:
            return fields
            
        # extract standard fields
        fields["Step"] = step.get("short_name", "publish")
        
        return fields
