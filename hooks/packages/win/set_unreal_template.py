import os
import shutil


def get_ue_template():
    # 임의로 로컬의 어느 경로로 지정 (이후 퍼포스 서버에서 다운로드 받는 방법으로 대체)
    template_path = "C:/Westworld_Pipeline/Templates/TP_West"
    return template_path

def get_engine_dir():
    print("엔진과 템플릿 경로 찾기")
    # engine_dir = unreal.SystemLibrary.get_engine_directory()
    launcher_config_path = os.path.expandvars("%PROGRAMDATA%/Epic/UnrealEngineLauncher/LauncherInstalled.dat")
    
    if os.path.exists(launcher_config_path):
        with open(launcher_config_path, 'r') as f:
            config = json.load(f)
            for install in config.get('InstallationList', []):
                if 'AppName' in install and install['AppName'].startswith('UE_'):
                    print(f"설치 경로: {install.get('InstallLocation', '')}")

    # print(f"Engine Directory : {engine_dir}")

    # template_dir = engine_dir + "/Template"
    # print(f"Engine Template Directory : {template_dir}")
    # return template_dir

def move(src_dir, dst_dir):
    print("다운받은 템플릿을 엔진 템플릿 위치로 이동시킵니다.")
    try:
        # 목적지 디렉토리가 존재하면 삭제
        if os.path.exists(dst_dir):
            shutil.rmtree(dst_dir)
        
        # 디렉토리 이동
        shutil.move(src_dir, dst_dir)
        print(f"성공적으로 이동됨: {src_dir} -> {dst_dir}")
        
    except Exception as e:
        print(f"에러 발생: {str(e)}")


# Execute
def run():
    # download_latest_ue_template()
    print("D"*20, "get_unreal_template 모듈 실행")
    src_directory = get_ue_template()
    dst_directory = get_engine_dir()
    move(src_directory, dst_directory)