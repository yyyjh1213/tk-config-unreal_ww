import unreal

def post_import_asset(asset):
    # 어셋 처리 (예: 경로 변경, 이름 재지정 등)
    print("@"*20)
    unreal.log("@"*20)
    if isinstance(asset, unreal.StaticMesh):
        new_path = "/Game/MyStaticMeshes/"
        asset_name = "CustomStaticMeshName"
        unreal.EditorAssetLibrary.rename_asset(asset.get_path_name(), f"{new_path}{asset_name}")
        print(f"Asset renamed and path set: {new_path}{asset_name}")
    print("@"*20)
    unreal.log("@"*20)

# 연결
unreal.EditorAssetLibrary.on_asset_imported().add_callable(post_import_asset)
