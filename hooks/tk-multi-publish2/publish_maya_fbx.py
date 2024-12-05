"""
Maya FBX 퍼블리시 플러그인입니다.
"""

import os
import maya.cmds as cmds
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()

class MayaFBXPublishPlugin(HookBaseClass):
    """
    Maya FBX 내보내기를 위한 퍼블리시 플러그인입니다.
    """
    
    @property
    def name(self):
        """플러그인 이름을 반환합니다."""
        return "Maya FBX Publisher"

    @property
    def description(self):
        """플러그인 설명을 반환합니다."""
        return "Maya 씬을 FBX 형식으로 내보내고 ShotGrid에 등록합니다."

    @property
    def settings(self):
        """플러그인 설정을 정의합니다."""
        return {
            "Template": {
                "type": "template",
                "default": None,
                "description": "퍼블리시 대상의 템플릿 경로입니다."
            },
            "Export Options": {
                "type": "dict",
                "default": {
                    "Version": "FBX202000",
                    "Up Axis": "Z",
                    "Scale Factor": 1.0,
                    "Convert Units": True,
                    "Convert Textures": True,
                    "Convert NURBS": True
                },
                "description": "FBX 내보내기 옵션입니다."
            }
        }

    def accept(self, settings, item):
        """
        이 플러그인이 주어진 항목을 처리할 수 있는지 확인합니다.
        """
        if not item.type == "maya.fbx":
            return False, "Maya FBX 항목이 아닙니다."
            
        return True, ""

    def validate(self, settings, item):
        """
        항목의 유효성을 검사합니다.
        """
        path = self._get_publish_path(settings, item)
        
        # 경로가 유효한지 확인
        if not path:
            return False, "퍼블리시 경로를 찾을 수 없습니다."
            
        return True, ""

    def publish(self, settings, item):
        """
        항목을 퍼블리시합니다.
        """
        publisher = self.parent
        path = self._get_publish_path(settings, item)
        
        # 퍼블리시 폴더 생성
        publish_folder = os.path.dirname(path)
        self.parent.ensure_folder_exists(publish_folder)
        
        # FBX 내보내기
        try:
            self._export_fbx(path, settings["Export Options"])
        except Exception as e:
            self.logger.error("FBX 내보내기 실패: %s" % e)
            return False
        
        # ShotGrid에 등록
        self._register_publish(settings, item, path)
        
        return True

    def _export_fbx(self, path, options):
        """
        Maya 씬을 FBX로 내보냅니다.
        """
        # FBX 내보내기 옵션 설정
        cmds.FBXResetExport()
        cmds.FBXExportFileVersion(v=options["Version"])
        cmds.FBXExportUpAxis(axis=options["Up Axis"])
        cmds.FBXExportScaleFactor(options["Scale Factor"])
        
        if options["Convert Units"]:
            cmds.FBXExportConvertUnitString("cm")
        
        if options["Convert Textures"]:
            cmds.FBXExportEmbeddedTextures(True)
        
        if options["Convert NURBS"]:
            cmds.FBXExportSmoothingGroups(True)
            cmds.FBXExportHardEdges(True)
            cmds.FBXExportTangents(True)
        
        # FBX 파일 내보내기
        cmds.FBXExport(f=path)

    def _get_publish_path(self, settings, item):
        """
        퍼블리시 경로를 생성합니다.
        """
        publisher = self.parent
        
        # 템플릿 가져오기
        template_name = settings["Template"].value
        template = publisher.get_template_by_name(template_name)
        
        if template:
            return template.apply_fields(item.properties)
        
        return None

    def _register_publish(self, settings, item, path):
        """
        퍼블리시를 ShotGrid에 등록합니다.
        """
        publisher = self.parent
        
        publish_data = {
            "tk": publisher.sgtk,
            "context": item.context,
            "comment": item.description,
            "path": path,
            "name": item.name,
            "version_number": item.properties.get("version_number", 1),
            "thumbnail_path": item.get_thumbnail_as_path(),
            "published_file_type": "FBX File"
        }
        
        # ShotGrid에 등록
        publisher.register_publish(**publish_data)
