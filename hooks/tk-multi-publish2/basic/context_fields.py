"""
Hook for managing context fields.
"""
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()

class ContextFields(HookBaseClass):
    """
    Methods for managing context fields.
    """
    
    def get_context_fields(self, context, template):
        """
        Extract fields from the context for the given template.
        
        :param context: The context to extract fields from
        :param template: The template to extract fields for
        :returns: Dictionary of field names and their values
        """
        fields = {}
        
        try:
            fields = context.as_template_fields(template)
        except Exception as e:
            self.logger.debug("Unable to get context fields: %s" % e)
            
        return fields
        
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
