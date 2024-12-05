# import os
# import shutil
# import unreal


# def get_ue_template():
#     # 임의로 로컬의 어느 경로로 지정 (이후 퍼포스 서버에서 다운로드 받는 방법으로 대체)
#     template_path = "C:/Westworld_Pipeline/Templates/TP_West"
#     return template_path

# def get_engine_dir():
#     print("엔진과 템플릿 경로 찾기")
#     engine_dir = unreal.SystemLibrary.get_engine_directory()
#     print(f"Engine Directory : {engine_dir}")

#     template_dir = engine_dir + "/Template"
#     print(f"Engine Template Directory : {template_dir}")

#     return template_dir

# def move(src_dir, dst_dir):
#     print("다운받은 템플릿을 엔진 템플릿 위치로 이동시킵니다.")
#     try:
#         # 목적지 디렉토리가 존재하면 삭제
#         if os.path.exists(dst_dir):
#             shutil.rmtree(dst_dir)
        
#         # 디렉토리 이동
#         shutil.move(src_dir, dst_dir)
#         print(f"성공적으로 이동됨: {src_dir} -> {dst_dir}")
        
#     except Exception as e:
#         print(f"에러 발생: {str(e)}")


# # Execute
# def run():
#     # download_latest_ue_template()
#     print("D"*20, "get_unreal_template 모듈 실행")
#     src_directory = get_ue_template()
#     dst_directory = get_engine_dir()
#     move(src_directory, dst_directory)




###################### 다른 방법
import psutil
import os

def find_running_unreal_process():
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # UE 프로세스 찾기
            if 'UE' in proc.info['name'] or 'UnrealEditor' in proc.info['name']:
                cmdline = proc.info['cmdline']
                if cmdline:
                    # 커맨드 라인에서 엔진 경로 찾기
                    for arg in cmdline:
                        if 'UE_' in arg and 'Engine' in arg:
                            return os.path.dirname(os.path.dirname(arg))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return None

def get_engine_directory():
    try:
        # 먼저 언리얼 API 시도
        import unreal
        return unreal.SystemLibrary.get_engine_directory()
    except ImportError:
        # API를 사용할 수 없는 경우 프로세스 검색
        return find_running_unreal_process()

engine_dir = get_engine_directory()
if engine_dir:
    print(f"Unreal Engine Directory: {engine_dir}")
else:
    print("Could not find Unreal Engine directory")