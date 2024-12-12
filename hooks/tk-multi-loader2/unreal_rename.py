import unreal
from collections import defaultdict

def get_new_name_and_path(asset_class, original_path):
    """
    에셋의 클래스에 따른 Prefix, 경로 규칙을 정의합니다.
    원본 경로에서 에셋의 클래스에 따라 Prefix가 적용된 새로운 경로를 반환합니다.
    Return 새로운 이름, 새로운 경로
    """
    base_name = original_path.split('/')[-1]

    class_rules = {
        'StaticMesh': {
            'prefix': 'SM_',
            'path': '/Game/Assets/SM/',
        },
        'SkeletalMesh': {
            'prefix': 'SK_',
            'path': '/Game/Assets/SK/',
        },
        'Skeleton': {
            'prefix': 'S_',
            'path': '/Game/Assets/S/',
        },
        'PhysicsAsset': {
            'prefix': 'PHY_',
            'path': '/Game/Assets/PHY/',
        },
        'Material': {
            'prefix': 'M_',
            'path': '/Game/Assets/M/',
        },
        'MaterialInstance': {
            'prefix': 'MI_',
            'path': '/Game/Assets/M/MI/',
        },
        'Texture2D': {
            'prefix': 'T_',
            'path': '/Game/Assets/T/',
        },
        'Blueprint': {
            'prefix': 'BP_',
            'path': '/Game/Assets/BP/',
        },
        'AnimSequence': {
            'prefix': 'AS_',
            'path': '/Game/Assets/AS/',
        },
        'AnimBlueprint': {
            'prefix': 'ABP_',
            'path': '/Game/Assets/AS/ABP/',
        },
        'ParticleSystem': {
            'prefix': 'NS_',
            'path': '/Game/Assets/NS/',
        }
    }

    if asset_class in class_rules:
        rule = class_rules[asset_class]
        # 기존 접두사 제거 후 새 접두사 추가
        for prefix in class_rules.values():
            if base_name.startswith(prefix['prefix']):
                base_name = base_name[len(prefix['prefix']):]
                break
        new_name = rule['prefix'] + base_name
        new_path = rule['path'] + new_name
        return new_name, new_path

    return base_name, original_path

def list_and_reorganize_assets():
    """
    콘텐츠 브라우저의 모든 애셋을 클래스에 따라 이름을 변경하고 경로를 재지정합니다.
    """
    editor_lib = unreal.EditorAssetLibrary()
    assets_by_class = defaultdict(list)

    # Contents(Game) 경로 하위에 있는 모든 에셋 가져오기
    all_assets = editor_lib.list_assets("/Game/", recursive=True, include_folder=False)

    for asset_path in all_assets:
        try:
            asset = editor_lib.load_asset(asset_path) # UE의 오브젝트 시스템(메모리)에 로드
            if asset:
                asset_class = asset.get_class().get_name() # 에셋의 클래스 이름 추출
                _, new_path = get_new_name_and_path(asset_class, asset_path) # 클래스에 따라 분류한 새로운 이름과 경로
                # print(f"asset_path : {asset_path}") # /Game/Assets/SM_cat_tower_lkd.SM_cat_tower_lkd
                # print(f"new_path : {new_path}") # /Game/Assets/SM/SM_cat_tower_lkd.SM_cat_tower_lkd

                # 경로가 변경된 경우에만 이동
                if not new_path == asset_path:

                    # 새 경로의 폴더가 없다면 생성
                    new_folder_path = '/'.join(new_path.split('/')[:-1])
                    if not editor_lib.does_directory_exist(new_folder_path):
                        editor_lib.make_directory(new_folder_path)

                    asset_path = sanitize_asset_path(asset_path) # /Game/Assets/cat_tower
                    new_path = sanitize_asset_path(new_path) # /Game/Assets/SM/SM_cat_tower

                    # 애셋 이동 및 이름 변경
                    success = editor_lib.rename_asset(asset_path, new_path)
                    if success:
                        print(f"이동 완료: {asset_path} -> {new_path}")
                    else:
                        print(f"이동 실패: {asset_path}")

                assets_by_class[asset_class].append(new_path)
        except Exception as e:
            print(f"에러: {asset_path} 처리 실패 - {str(e)}")
    
    # 결과 출력
    print("\n=== 재구성된 클래스별 애셋 목록 ===\n")
    for asset_class, assets in sorted(assets_by_class.items()):
        print("-" * 50)
        print(f"\n[{asset_class}] - 총 {len(assets)}개")
        for asset_path in sorted(assets):
            print(f"  {asset_path}")


def sanitize_asset_path(path):
    """
    'PackageName.ObjectName' 형식의 ObjectPath에서,
    '.' 이전의 PackageName 부분만 반환합니다.
    """
    return path.split(".")[0]  # '.' 이후 제거


if __name__ == "__main__":
    with unreal.ScopedEditorTransaction("Reorganize Assets by Class") as transaction:
        list_and_reorganize_assets()