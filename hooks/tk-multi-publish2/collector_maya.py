"""
Maya 전용 Collector 플러그인입니다.
기본 Collector를 상속받아 Maya 특화 기능을 추가합니다.

수정 이력:
- 2024.01: 초기 버전 작성
- 2024.02: maya_collector.py와 통합
"""

import os
import maya.cmds as cmds
import sgtk
from . import collector

HookBaseClass = sgtk.get_hook_baseclass()

class MayaUnrealSessionCollector(collector.BasicCollectorPlugin, HookBaseClass):
    """
    Maya 전용 Collector 플러그인입니다.
    Maya 씬에서 FBX 내보내기 대상을 수집합니다.
    """

    @property
    def settings(self):
        """Collector 설정을 정의합니다."""
        return {
            "Work Template": {
                "type": "template",
                "default": None,
                "description": "Template path for the current work file."
            },
            "Export Types": {
                "type": "list",
                "values": {
                    "Meshes": True,
                    "Skeletons": True,
                    "Animations": True
                },
                "default": ["Meshes"],
                "description": "Types of content to collect for export."
            }
        }

    def process_current_session(self, settings, parent_item):
        """
        현재 Maya 세션을 처리하고 수집 항목을 생성합니다.
        
        :param dict settings: Collector 설정
        :param parent_item: 부모 항목
        """
        # Get the current Maya scene path
        scene_path = cmds.file(query=True, sn=True)
        if not scene_path:
            self.logger.warning("Current Maya scene is not saved.")
            return

        # Create the main session item
        session_item = parent_item.create_item(
            "maya.session",
            "Maya Session",
            "Maya Scene"
        )
        session_item.properties["path"] = scene_path

        # Create the FBX export item
        fbx_item = session_item.create_item(
            "maya.fbx.unreal",
            "Unreal FBX Export",
            "FBX Export for Unreal"
        )

        # Set the FBX output path
        fbx_path = scene_path.replace(".ma", ".fbx").replace(".mb", ".fbx")
        fbx_item.properties["path"] = fbx_path
        fbx_item.set_icon_from_path(":/icons/alembic.png")
        fbx_item.description = "FBX file optimized for Unreal Engine export."

        # Collect additional items based on settings
        self._collect_meshes(session_item, settings)
        self._collect_skeletons(session_item, settings)
        self._collect_animations(session_item, settings)

        return session_item

    def _collect_meshes(self, parent_item, settings):
        """메시 오브젝트를 수집합니다."""
        if not settings.get("Export Types", {}).get("Meshes", True):
            return

        meshes = cmds.ls(type="mesh", long=True) or []
        
        for mesh in meshes:
            # 메시의 transform 노드 가져오기
            transform = cmds.listRelatives(mesh, parent=True, fullPath=True)[0]
            
            mesh_item = parent_item.create_item(
                "maya.fbx.mesh",
                "Mesh",
                transform
            )
            
            mesh_item.properties["path"] = transform
            mesh_item.properties["type"] = "mesh"
            
            self.logger.info("Collected mesh: %s" % transform)

    def _collect_skeletons(self, parent_item, settings):
        """스켈레톤을 수집합니다."""
        if not settings.get("Export Types", {}).get("Skeletons", True):
            return

        joints = cmds.ls(type="joint", long=True) or []
        
        for joint in joints:
            # 루트 조인트만 수집
            if not cmds.listRelatives(joint, parent=True, type="joint"):
                skeleton_item = parent_item.create_item(
                    "maya.fbx.skeleton",
                    "Skeleton",
                    joint
                )
                
                skeleton_item.properties["path"] = joint
                skeleton_item.properties["type"] = "skeleton"
                
                self.logger.info("Collected skeleton: %s" % joint)

    def _collect_animations(self, parent_item, settings):
        """애니메이션을 수집합니다."""
        if not settings.get("Export Types", {}).get("Animations", True):
            return

        # 타임라인에 애니메이션이 있는지 확인
        start_time = cmds.playbackOptions(q=True, min=True)
        end_time = cmds.playbackOptions(q=True, max=True)
        
        if start_time != end_time:
            anim_item = parent_item.create_item(
                "maya.fbx.animation",
                "Animation",
                "Scene Animation"
            )
            
            anim_item.properties["start_frame"] = start_time
            anim_item.properties["end_frame"] = end_time
            anim_item.properties["type"] = "animation"
            
            self.logger.info("Collected animation: %s - %s" % (start_time, end_time))
