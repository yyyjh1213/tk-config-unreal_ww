import os
import shutil
import sgtk


def get_ue_template():
    # 임의로 로컬의 어느 경로로 지정 (이후 퍼포스 서버에서 다운로드 받는 방법으로 대체)
    template_path = "C:/Westworld_Pipeline/Templates/TP_West"
    return template_path

def get_engine_dir():
    print("엔진과 템플릿 경로 찾기")
    # engine_dir = unreal.SystemLibrary.get_engine_directory()

    # 현재 엔진 인스턴스 가져오기
    engine = sgtk.platform.current_engine()
    
    if engine:
        # 엔진의 설치 경로 가져오기
        engine_path = engine.disk_location
        print(engine_path)




    ##########################################################
    # print(f"Engine Directory : {engine_dir}")

    # template_dir = engine_dir + "/Template"
    # print(f"Engine Template Directory : {template_dir}")
    # return template_dir


def get_app_info():
    # 현재 컨텍스트 가져오기
    current_context = sgtk.platform.current_bundle().context
    
    # 현재 엔진 가져오기
    engine = sgtk.platform.current_engine()
    
    if engine:
        print(f"현재 엔진: {engine.name}")
        print(f"엔진 경로: {engine.disk_location}")
        
        # 모든 등록된 앱 정보 출력
        print("\n등록된 앱들:")
        for app_instance_name, app in engine.apps.items():
            print(f"\n앱 인스턴스: {app_instance_name}")
            print(f"앱 경로: {app.disk_location}")
            print(f"앱 설정: {app.configuration}")
            
            # 앱의 환경 설정 가져오기
            env = app.get_setting("env")
            if env:
                print(f"환경 설정: {env}")


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
    get_app_info()