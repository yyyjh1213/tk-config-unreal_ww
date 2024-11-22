import unreal
import json
import os
from pathlib import Path
import re

class UnrealAssetManager:

    def __init__(self, config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.prefix_patterns = self.config['prefix_patterns']
        self.path_rules = self.config['path_rules']
        
        print(f"self.prefix_patterns : {self.prefix_patterns}")
        print(f"self.path_rules : {self.path_rules}")
        # LogPython: self.prefix_patterns : {'Static Mesh': 'SM', 'Skeletal Mesh': 'SK', 'Material': 'M', 'Material Instance': 'MI', 'Texture': 'T', 'Blueprint': 'BP', 'Animation': 'A', 'Sound': 'S', 'Particle System': 'PS', 'Widget Blueprint': 'WBP'}
        # LogPython: self.path_rules : {'Static Mesh': '/Game/Assets/SM', 'Skeletal Mesh': '/Game/Assets/SK', 'Material': '/Game/Assets/M', 'Material Instance': '/Game/Assets/MI', 'Texture': '/Game/Assets/Textures', 'Blueprint': '/Game/Assets/Blueprints', 'Animation': '/Game/Assets/Animations', 'Sound': '/Game/Assets/Sounds', 'Particle System': '/Game/Assets/FX', 'Widget Blueprint': '/Game/Assets/UI'}


# 에셋 타입을 추출하고, 타입에 맞는 prefix, 경로 찾기
    def get_asset_type(self, asset_path):
        """asset path를 받아서 asset type 리턴"""

        asset_data = unreal.EditorAssetLibrary.find_asset_data(asset_path)
        if not asset_data.is_valid():
            return None
        # <Struct 'AssetData' (0x0000050599816EA0) {
        # package_name: "/Game/Assets/master_Materials",
        # package_path: "/Game/Assets",
        # asset_name: "master_Materials",
        # asset_class_path: {package_name: "/Script/Engine", asset_name: "Material"}}>

        # asset_data에서 class 추출 
        asset_class = asset_data.asset_class_path
        # LogPython: <Struct 'TopLevelAssetPath' (0x000005059A42797C) {package_name: "/Script/Engine", asset_name: "StaticMesh"}>
        asset_type = asset_class.asset_name
        # StaticMesh, Material 등

        return asset_type

    def get_correct_prefix(self, asset_type):
        """
        asset type에 따라 config에 지정해둔 prefix 설정
        정보 없으면 prefix 없게
        """
        return self.prefix_patterns.get(asset_type, '')

    def get_correct_path(self, asset_type, sub_category=None):
        """
        asset type에 따라 새로운 path 설정
        정보 없으면 /Game/Assets에 넣기
        """
        base_path = self.path_rules.get(asset_type, '/Game/Assets')
    
        if sub_category:
            return f"{base_path}/{sub_category}"
        return base_path



    def validate_asset_name(self, asset_name, asset_type):
        """
        prefix_AssetName 형식으로 최종 이름을 리턴
        """

        # naming convention에 맞게 이름 수정
        prefix = self.get_correct_prefix(asset_type)
        name_without_prefix = re.sub(r'^[A-Z]{2}_', '', asset_name) # prefix가 있을 경우 제거

        # prefix 적용한 새로운 이름
        if prefix:
            correct_name = f"{prefix}_{name_without_prefix}"
        else:
            correct_name = name_without_prefix

        # PascalCase로 변환
        name_parts = correct_name.split('_')
        if len(name_parts) > 1:
            name_parts[1:] = [part.capitalize() for part in name_parts[1:]]
        
        # name_parts를 _로 연결해서 리턴
        full_name = '_'.join(name_parts)
        print(f"---------- full_name : {full_name}")
        return full_name

    def rename_and_move_asset(self, old_path, new_name=None, sub_category=None):
        """규약에 맞게 Rename, 경로 이동"""

        try:
            # 경로에서 .uasset 확장자 제거
            print(f"---------- old_path1 = {old_path}")
            old_path = old_path.replace('.uasset', '')
            print(f"---------- old_path2 = {old_path}")

            # Get asset type
            asset_type = self.get_asset_type(old_path)
            if not asset_type:
                print(f"에셋을 찾을 수 없거나 유효하지 않습니다: {old_path}")
                return False

            # Get current asset name
            current_name = old_path.split('/')[-1]
            print(f"---------- current_name = {current_name}")

            # Determine new name
            if new_name:
                final_name = self.validate_asset_name(new_name, asset_type)
            else:
                final_name = self.validate_asset_name(current_name, asset_type)



            # Get correct path
            new_base_path = self.get_correct_path(asset_type, sub_category)
            new_full_path = f"{new_base_path}/{final_name}"
            
            # Remove any duplicate slashes
            new_full_path = re.sub(r'\/+', '/', new_full_path)
            
            # Check if asset already exists at destination
            if unreal.EditorAssetLibrary.does_asset_exist(new_full_path):
                print(f"대상 경로에 이미 에셋이 존재합니다: {new_full_path}")
                return False
                
            # Move and rename asset
            success = unreal.EditorAssetLibrary.rename_asset(old_path, new_full_path)
            
            if success:
                print(f"에셋 이동 & rename 성공: {old_path} -> {new_full_path}")
            else:
                print(f"에셋 이동 & rename 실패: {old_path} -> {new_full_path}")

            return success

        except Exception as e:
            print(f"오류 발생: {e}")
            return False

    def batch_process_assets(self, directory_path):
        """
        directory_path에 있는 모든 에셋에 대해 rename_and_move_asset() 함수 실행"""

        assets = unreal.EditorAssetLibrary.list_assets(directory_path, recursive=True)
        # ["/Game/Assets/master_Materials.master_Materials",
        # "/Game/Assets/meat.meat",
        # "/Game/Assets/Rib.Rib",
        # "/Game/Assets/SM_Meat.SM_Meat"]
        # 여기서 왜 에셋이름.에셋이름 이렇게 2번 나오지?

        for asset_path in assets:
            print(asset_path) # /Game/Assets/master_Materials.master_Materials
            package_path = asset_path.split('.', 1)[0]  # "/Game/Assets/master_Materials"
            asset_name = asset_path.split('.', 1)[1]    # "master_Materials"
            self.rename_and_move_asset(package_path)


def run():
    # 설정 파일 경로
    config_path = "C:/Users/admin/Desktop/git_hyoeun/tk-config-unreal_ww/env/includes/unreal/settings/asset_config.json"

    # 에셋 매니저 초기화
    asset_manager = UnrealAssetManager(config_path)

    # 디렉토리 일괄 처리
    directory_path = "/Game/Assets"
    asset_manager.batch_process_assets(directory_path)

    # 단일 에셋을 지정해서 처리
    # asset_manager.rename_and_move_asset(
    #    "/Game/Assets/SM/meat"
    # )


if __name__ == "__main__":
    run()