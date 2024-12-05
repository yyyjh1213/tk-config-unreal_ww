"""
Maya 파일을 Unreal Engine용 FBX로 내보내기 위한 기본 훅입니다.
이 훅은 FBX 내보내기의 핵심 기능을 제공하며, 다른 퍼블리시 훅의 기반이 됩니다.

주요 기능:
1. Maya 씬을 Unreal Engine에 최적화된 FBX 형식으로 내보내기
2. 텍스처 자동 변환 및 최적화
3. FBX 내보내기 설정 관리 (버전, 스케일, 선택 객체 등)

수정 이력:
- 2024.01: 코드 구조 개선 및 주석 추가
- 기본 FBX 내보내기 기능을 별도 클래스로 분리하여 재사용성 향상
"""
import os
import maya.cmds as cmds
import maya.mel as mel
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()

class MayaFBXUnrealExportPlugin(HookBaseClass):
    """
    Unreal Engine에 최적화된 Maya FBX 파일 내보내기를 위한 기본 플러그인입니다.
    이 클래스는 FBX 내보내기의 핵심 기능을 제공하며, 다른 퍼블리시 플러그인에서 상속하여 사용할 수 있습니다.
    
    주요 설정:
    - Export Selection: 선택된 객체만 내보내기
    - FBX Version: FBX 파일 버전 설정
    - Convert Textures: 프로시저럴 텍스처를 파일 텍스처로 변환
    - Scale Factor: 내보내기 시 적용할 스케일 값
    """

    @property
    def name(self):
        """플러그인의 이름을 반환합니다."""
        return "Maya FBX Unreal Export"

    @property
    def description(self):
        """플러그인의 설명을 반환합니다."""
        return "Export Maya scene as FBX file optimized for Unreal Engine."

    @property
    def settings(self):
        """
        FBX 내보내기에 필요한 기본 설정을 정의합니다.
        이 설정들은 상속받는 클래스에서 확장하여 사용할 수 있습니다.
        """
        return {
            "Export Selection": {
                "type": "bool",
                "default": True,
                "description": "Export only selected objects if enabled.",
            },
            "FBX Version": {
                "type": "str",
                "default": "FBX202000",
                "description": "FBX file version to export.",
            },
            "Convert Textures": {
                "type": "bool",
                "default": True,
                "description": "Convert procedural textures to file textures.",
            },
            "Scale Factor": {
                "type": "float",
                "default": 1.0,
                "description": "Scale factor to apply during export.",
            },
            "Up Axis": {
                "type": "str",
                "default": "z",
                "description": "Up axis for the exported FBX file (y or z).",
            }
        }

    def validate(self, settings, item):
        """
        씬을 내보내기 전에 검증합니다.
        """
        if settings.get("Export Selection", True) and not cmds.ls(selection=True):
            self.logger.warning("Nothing selected for export.")
            return False

        # Check for unsupported texture nodes
        if settings.get("Convert Textures", True):
            unsupported = self._find_unsupported_textures()
            if unsupported:
                self.logger.warning(f"Found unsupported textures: {unsupported}")
                return False

        return True

    def export_fbx(self, settings, item):
        """
        Maya 씬을 FBX 형식으로 내보냅니다.
        """
        try:
            # Clean up node names first
            self._clean_node_names()
            
            # Convert NURBS to polygons
            self._convert_nurbs_to_polygons()
            
            # Convert textures if needed
            if settings.get("Convert Textures", True):
                self._convert_procedural_textures()

            # Get export path
            path = item.properties["path"]
            
            # Prepare FBX export options
            mel.eval('FBXResetExport')
            
            # Set FBX export settings
            mel.eval('FBXExportFileVersion -v "{}"'.format(settings.get("FBX Version", "FBX202000")))
            mel.eval('FBXExportUpAxis -v "{}"'.format(settings.get("Up Axis", "z")))
            mel.eval('FBXExportScaleFactor -v {}'.format(settings.get("Scale Factor", 1.0)))
            mel.eval('FBXExportShapes -v true')
            mel.eval('FBXExportSmoothingGroups -v true')
            mel.eval('FBXExportSkins -v true')
            mel.eval('FBXExportConstraints -v false')
            mel.eval('FBXExportLights -v false')
            mel.eval('FBXExportCameras -v false')
            mel.eval('FBXExportBakeComplexAnimation -v false')
            mel.eval('FBXExportEmbeddedTextures -v true')
            mel.eval('FBXExportTriangulate -v true')
            
            # Export selected or all
            if settings.get("Export Selection", True):
                mel.eval('FBXExport -f "{}" -s'.format(path.replace("\\", "/")))
            else:
                mel.eval('FBXExport -f "{}"'.format(path.replace("\\", "/")))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export FBX: {str(e)}")
            return False

    def _find_unsupported_textures(self):
        """
        지원되지 않는 텍스처 노드를 찾습니다.
        """
        unsupported_types = ['checker', 'ramp']
        unsupported = []
        
        for node_type in unsupported_types:
            nodes = cmds.ls(type=node_type) or []
            unsupported.extend(nodes)
            
        return unsupported

    def _convert_procedural_textures(self):
        """
        프로시저럴 텍스처를 파일 텍스처로 변환합니다.
        """
        # Get all materials in the scene
        materials = cmds.ls(mat=True)
        
        for material in materials:
            # Get all textures connected to the material
            textures = cmds.listConnections(material, type='checker') or []
            
            for texture in textures:
                try:
                    # Get the texture's output connections
                    connections = cmds.listConnections(texture, plugs=True, connections=True, destination=True) or []
                    
                    if connections:
                        # Get the checker pattern colors
                        color1 = cmds.getAttr(f'{texture}.color1')[0]
                        color2 = cmds.getAttr(f'{texture}.color2')[0]
                        
                        # Create a new ramp node instead
                        ramp_node = cmds.shadingNode('ramp', asTexture=True)
                        place2d = cmds.shadingNode('place2dTexture', asUtility=True)
                        
                        # Set up the ramp to look like a checker
                        cmds.setAttr(f'{ramp_node}.type', 3)  # Checker type
                        cmds.setAttr(f'{ramp_node}.interpolation', 0)  # No interpolation
                        
                        # Set colors
                        cmds.setAttr(f'{ramp_node}.colorEntryList[0].color', *color1)
                        cmds.setAttr(f'{ramp_node}.colorEntryList[1].color', *color2)
                        
                        # Connect place2dTexture to ramp node
                        cmds.connectAttr(f'{place2d}.outUV', f'{ramp_node}.uv')
                        cmds.connectAttr(f'{place2d}.outUvFilterSize', f'{ramp_node}.uvFilterSize')
                        
                        # Connect to original destinations
                        for i in range(0, len(connections), 2):
                            src = connections[i]
                            dst = connections[i+1]
                            cmds.connectAttr(f'{ramp_node}.outColor', dst, force=True)
                        
                        # Delete the original checker node
                        cmds.delete(texture)
                        
                        self.logger.info(f"Converted checker {texture} to ramp texture")
                        
                except Exception as e:
                    self.logger.warning(f"Failed to convert texture {texture}: {str(e)}")
                    continue

    def _convert_nurbs_to_polygons(self):
        """
        NURBS 표면을 폴리곤으로 변환합니다.
        """
        # Get all NURBS surfaces in the scene or selection
        nurbs_surfaces = cmds.ls(selection=True, type=['nurbsSurface', 'revolvedSurface', 'nurbsBooleanSurface']) if cmds.ls(selection=True) else cmds.ls(type=['nurbsSurface', 'revolvedSurface', 'nurbsBooleanSurface'])
        
        if not nurbs_surfaces:
            return
            
        self.logger.info("Converting NURBS surfaces to polygons...")
        
        for surface in nurbs_surfaces:
            try:
                # Get the transform node
                transform = cmds.listRelatives(surface, parent=True)[0]
                
                # Convert NURBS to polygons
                poly = cmds.nurbsToPoly(transform, 
                    format=3,  # NURBS to polygons
                    polygonType=1,  # Triangle
                    constructionHistory=False,
                    name=transform + "_poly")[0]
                
                # Copy materials from NURBS to polygon
                shading_groups = cmds.listConnections(surface, type='shadingEngine')
                if shading_groups:
                    cmds.sets(poly, edit=True, forceElement=shading_groups[0])
                
                # Delete the original NURBS surface
                cmds.delete(transform)
                
                self.logger.info(f"Converted {surface} to polygon mesh")
                
            except Exception as e:
                self.logger.warning(f"Failed to convert {surface} to polygon: {str(e)}")
                continue

    def _clean_node_names(self):
        """
        노드 이름을 정리합니다.
        """
        # Get all transforms in the scene or selection
        nodes = cmds.ls(selection=True, long=True) if cmds.ls(selection=True) else cmds.ls(long=True)
        
        for node in nodes:
            try:
                # Skip if it's a long path
                if '|' not in node:
                    continue
                    
                # Get the short name
                short_name = node.split('|')[-1]
                
                # Skip if no namespace
                if ':' not in short_name:
                    continue
                    
                # Get namespace and base name
                namespace, base_name = short_name.split(':', 1)
                
                # Remove numbers from the end of the name
                clean_name = ''.join(c for c in base_name if not c.isdigit())
                
                # Create a unique name
                unique_name = namespace + ':' + clean_name
                
                # Rename the node if it's different
                if unique_name != short_name:
                    cmds.rename(node, unique_name)
                    
            except Exception as e:
                self.logger.warning(f"Failed to clean name for {node}: {str(e)}")
                continue
