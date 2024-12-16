"""
Hook for extracting values from paths.
"""
import os
import re
import sgtk
from tank_vendor import six

HookBaseClass = sgtk.get_hook_baseclass()

class PathInfo(HookBaseClass):
    """
    Methods for extracting information from path structures.
    """
    
    def get_file_path_components(self, path):
        """
        Extracts the components of the given path.

        :param path: The path to extract components from
        :returns: Dictionary of path components
        """
        # break down the path into its components
        path_info = {
            "path": path,
            "filename": os.path.basename(path),
            "extension": os.path.splitext(path)[1][1:],
            "folder": os.path.dirname(path),
        }

        return path_info

    def get_version_number(self, path):
        """
        Extract a version number from the supplied path.

        :param path: The path to extract the version number from
        :returns: An integer representing the version number in the supplied path
        """
        # default implementation uses a regular expression to find
        # the version number
        version_number = 1
        
        # default regex pattern would match something like "v1", "v001", "v0001"
        version_pattern = re.compile(r"v(\d+)", re.IGNORECASE)
        
        # split the path into components
        path_info = self.get_file_path_components(path)
        
        # search the filename for the version pattern
        filename = path_info["filename"]
        result = re.search(version_pattern, filename)
        
        if result:
            version_number = int(result.group(1))
            
        return version_number

    def get_template_fields(self, path, template):
        """
        Extract field values from a path using the given template.
        
        :param path: The path to extract fields from
        :param template: The template to use for extraction
        :returns: Dictionary of field names and their values
        """
        fields = {}
        
        try:
            fields = template.get_fields(path)
        except sgtk.TankError:
            pass
            
        return fields
