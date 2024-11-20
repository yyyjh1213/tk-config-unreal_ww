import sgtk
import unreal

HookBaseClass = sgtk.get_hook_baseclass()

class PostLoadHook(HookBaseClass):
    def post_load(self, context, file_path, publish_type, sequence=None):
        """
        Your custom post-load logic here
        """
        # 예시: 로드된 파일 경로 출력
        self.logger.debug("Loading completed: %s" % file_path)
        self.logger.debug("==========\n"*20)
        self.parent.log_debug("dddddddddd"*20)
        print("==========\n"*20)
        unreal.log("----------\n"*20)
        

        # 여기에 원하는 커스텀 코드 작성
        return True