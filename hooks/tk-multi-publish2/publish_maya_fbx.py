"""
Maya FBX 파일을 Unreal Engine으로 퍼블리시하기 위한 훅입니다.

작동 원리:
1. Maya 씬을 FBX 형식으로 내보내기
2. Shotgrid에 에셋 정보 등록
3. Unreal Engine에서 사용할 수 있도록 최적화된 형태로 저장

수정 이력:
- 2024.01: 코드 구조 개선 및 주석 추가
- MayaFBXUnrealExportPlugin을 상속받아 퍼블리시 기능 특화
"""
import os
import sgtk
from . import maya_fbx_unreal_export

# 기본 hook 클래스 대신 MayaFBXUnrealExportPlugin을 상속받아 사용
HookBaseClass = maya_fbx_unreal_export.MayaFBXUnrealExportPlugin

class MayaFBXPublishPlugin(HookBaseClass):
    """
    Maya FBX 파일을 Shotgrid와 Unreal Engine에 퍼블리시하기 위한 플러그인입니다.
    MayaFBXUnrealExportPlugin의 FBX 내보내기 기능을 확장하여 Shotgrid 퍼블리시 기능을 추가합니다.
    
    주요 기능:
    - Maya 씬을 Unreal Engine 호환 FBX로 내보내기 (상속)
    - Shotgrid에 에셋 등록 및 메타데이터 업데이트 (확장)
    - 퍼블리시 템플릿에 따른 파일 저장 경로 관리 (확장)
    """

    @property
    def name(self):
        """플러그인의 이름을 반환합니다."""
        return "Publish Maya FBX to Unreal"

    @property
    def description(self):
        """플러그인의 설명을 반환합니다."""
        return "Publish the Maya scene as an FBX file optimized for Unreal Engine and register it in ShotGrid."

    @property
    def settings(self):
        """
        플러그인의 설정을 정의합니다.
        부모 클래스의 FBX 내보내기 설정을 상속받고, 퍼블리시 관련 설정을 추가합니다.
        """
        # 부모 클래스(MayaFBXUnrealExportPlugin)의 설정을 가져옴
        fbx_settings = super(MayaFBXPublishPlugin, self).settings

        # 퍼블리시 관련 설정 추가
        publish_settings = {
            "Publish Template": {
                "type": "template",
                "default": None,
                "description": "Template path for published files. Should correspond to a template defined in templates.yml.",
            }
        }

        # 두 설정을 병합
        fbx_settings.update(publish_settings)
        return fbx_settings

    def accept(self, settings, item):
        """
        이 플러그인이 처리할 수 있는 아이템인지 확인합니다.
        maya.fbx.unreal 타입의 아이템만 처리합니다.
        """
        return item.type == "maya.fbx.unreal"

    def validate(self, settings, item):
        """
        퍼블리시 전에 아이템이 유효한지 검증합니다.
        
        검증 항목:
        1. 필수 설정이 모두 제공되었는지 확인
        2. 템플릿 경로가 올바른지 확인
        3. FBX 내보내기에 필요한 조건이 충족되었는지 확인
        """
        path = item.properties.get("path", "")
        
        if not path:
            self.logger.error("No path found for item")
            return False
            
        # Create exporter instance for validation
        exporter = maya_fbx_unreal_export.MayaFBXUnrealExportPlugin(self.parent)
        if not exporter.validate(settings, item):
            return False
            
        return True

    def publish(self, settings, item):
        """
        Executes the publish logic for the given item and settings.
        """
        publisher = self.parent
        
        # Get the path in a normalized state
        path = item.properties["path"]
        path = sgtk.util.ShotgunPath.normalize(path)
        
        # Ensure the publish folder exists
        publish_folder = os.path.dirname(path)
        self.parent.ensure_folder_exists(publish_folder)
        
        # Export the FBX file using our exporter
        exporter = maya_fbx_unreal_export.MayaFBXUnrealExportPlugin(self.parent)
        if not exporter.export_fbx(settings, item):
            self.logger.error("Failed to export FBX file")
            return False
        
        # Register the published file
        self._register_publish(settings, item, path)
        
        return True

    def _register_publish(self, settings, item, path):
        """
        Register the published file with Shotgun.
        """
        publisher = self.parent
        
        # Get the publish info
        publish_version = publisher.util.get_version_number(path)
        publish_name = publisher.util.get_publish_name(path)
        
        # Create the publish
        publish_data = {
            "tk": publisher.sgtk,
            "context": item.context,
            "comment": item.description,
            "path": path,
            "name": publish_name,
            "version_number": publish_version,
            "published_file_type": "FBX File",
        }
        
        # Register the publish using the base class implementation
        super(MayaFBXPublishPlugin, self)._register_publish(settings, item, path)
