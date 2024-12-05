"""
Maya 전용 Collector 플러그인입니다.
기본 Collector를 상속받아 Maya 특화 기능을 추가합니다.

수정 이력:
- 2024.01: 초기 버전 작성
"""

import os
import maya.cmds as cmds
import sgtk
from . import collector

class MayaCollectorPlugin(collector.BasicCollectorPlugin):
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
        # 부모 클래스의 process_current_session 호출
        session_item = super(MayaCollectorPlugin, self).process_current_session(settings, parent_item)
        
        if not session_item:
            return
            
        # Maya 씬에서 내보내기 가능한 항목 수집
        self._collect_meshes(session_item, settings)
        self._collect_skeletons(session_item, settings)
        self._collect_animations(session_item, settings)
        
        return session_item

    def _collect_meshes(self, parent_item, settings):
        """메시 오브젝트를 수집합니다."""
        if not settings["Export Types"].get("Meshes", True):
            return

        meshes = cmds.ls(type="mesh", long=True) or []
        
        for mesh in meshes:
            # 메시의 transform 노드 가져오기
            transform = cmds.listRelatives(mesh, parent=True, fullPath=True)[0]
            
            mesh_item = parent_item.create_item(
                "maya.fbx.unreal",
                "Mesh",
                transform
            )
            
            mesh_item.properties["path"] = transform
            mesh_item.properties["type"] = "mesh"
            
            self.logger.info("Collected mesh: %s" % transform)

    def _collect_skeletons(self, parent_item, settings):
        """스켈레톤을 수집합니다."""
        if not settings["Export Types"].get("Skeletons", True):
            return

        joints = cmds.ls(type="joint", long=True) or []
        
        for joint in joints:
            # 루트 조인트만 수집
            if not cmds.listRelatives(joint, parent=True, type="joint"):
                skeleton_item = parent_item.create_item(
                    "maya.fbx.unreal",
                    "Skeleton",
                    joint
                )
                
                skeleton_item.properties["path"] = joint
                skeleton_item.properties["type"] = "skeleton"
                
                self.logger.info("Collected skeleton: %s" % joint)

    def _collect_animations(self, parent_item, settings):
        """애니메이션을 수집합니다."""
        if not settings["Export Types"].get("Animations", True):
            return

        # 타임라인에 키프레임이 있는 경우만 수집
        if cmds.keyframe(query=True, keyframeCount=True):
            anim_item = parent_item.create_item(
                "maya.fbx.unreal",
                "Animation",
                "Scene Animation"
            )
            
            anim_item.properties["type"] = "animation"
            anim_item.properties["start_frame"] = cmds.playbackOptions(query=True, minTime=True)
            anim_item.properties["end_frame"] = cmds.playbackOptions(query=True, maxTime=True)
            
            self.logger.info("Collected animation: %s" % anim_item.name)
