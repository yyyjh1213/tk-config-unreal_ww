import sgtk

HookBaseClass = sgtk.get_hook_baseclass()

class PostLoadHook(HookBaseClass):
    def post_load(self, context, file_path, publish_type, sequence=None):
        """
        Your custom post-load logic here
        """
        # 예시: 로드된 파일 경로 출력
        self.logger.debug("Loading completed: %s" % file_path)
        self.logger.debug("20"*200)
        
        # 여기에 원하는 커스텀 코드 작성
        
        return True