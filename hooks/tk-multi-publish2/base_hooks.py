"""
ShotGrid 파이프라인의 기본 Hook 클래스들을 정의합니다.
이 모듈은 모든 DCC 툴에서 공통으로 사용되는 기본 기능을 제공합니다.

수정 이력:
- 2024.01: 초기 버전 작성
"""

import os
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()

class BaseShotGridHook(HookBaseClass):
    """
    모든 ShotGrid Hook의 기본 클래스입니다.
    로깅, 설정 관리, 오류 처리 등의 공통 기능을 제공합니다.
    """

    @property
    def logger(self):
        """로거 인스턴스를 반환합니다."""
        return sgtk.platform.get_logger(__name__)

    def get_plugin_name(self):
        """플러그인 이름을 반환합니다."""
        return self.__class__.__name__

    def get_settings(self):
        """플러그인 설정을 반환합니다."""
        return {}

    def validate_settings(self, settings):
        """
        설정의 유효성을 검사합니다.
        
        :param dict settings: 검사할 설정
        :raises: ValueError 유효하지 않은 설정이 있는 경우
        """
        pass

    def init_settings(self, settings):
        """
        설정을 초기화합니다.
        
        :param dict settings: 초기화할 설정
        :return: 초기화된 설정
        """
        return settings

class BasePublishPlugin(BaseShotGridHook):
    """
    모든 Publish 플러그인의 기본 클래스입니다.
    """

    @property
    def name(self):
        """플러그인 이름을 반환합니다."""
        return "Base Publish Plugin"

    @property
    def description(self):
        """플러그인 설명을 반환합니다."""
        return "기본 퍼블리시 플러그인입니다."

    @property
    def settings(self):
        """플러그인 설정을 정의합니다."""
        return {
            "Template": {
                "type": "template",
                "default": None,
                "description": "퍼블리시 대상의 템플릿 경로입니다."
            }
        }

    def accept(self, settings, item):
        """
        이 플러그인이 주어진 항목을 처리할 수 있는지 확인합니다.
        
        :param dict settings: 플러그인 설정
        :param item: 처리할 항목
        :return: (bool, str) 처리 가능 여부와 설명
        """
        return True, ""

    def validate(self, settings, item):
        """
        항목의 유효성을 검사합니다.
        
        :param dict settings: 플러그인 설정
        :param item: 검사할 항목
        :return: (bool, str) 유효성 검사 결과와 설명
        """
        return True, ""

    def publish(self, settings, item):
        """
        항목을 퍼블리시합니다.
        
        :param dict settings: 플러그인 설정
        :param item: 퍼블리시할 항목
        """
        pass

    def finalize(self, settings, item):
        """
        퍼블리시 후 정리 작업을 수행합니다.
        
        :param dict settings: 플러그인 설정
        :param item: 처리된 항목
        """
        pass

class BaseCollectorPlugin(BaseShotGridHook):
    """
    모든 Collector 플러그인의 기본 클래스입니다.
    """

    @property
    def name(self):
        """플러그인 이름을 반환합니다."""
        return "Base Collector Plugin"

    @property
    def description(self):
        """플러그인 설명을 반환합니다."""
        return "기본 수집 플러그인입니다."

    @property
    def settings(self):
        """플러그인 설정을 정의합니다."""
        return {
            "Work Template": {
                "type": "template",
                "default": None,
                "description": "작업 파일의 템플릿 경로입니다."
            }
        }

    def process_current_session(self, settings, parent_item):
        """
        현재 세션을 처리하고 수집 항목을 생성합니다.
        
        :param dict settings: 플러그인 설정
        :param parent_item: 부모 항목
        :return: 생성된 세션 항목
        """
        pass

    def process_file(self, settings, parent_item, path):
        """
        파일을 처리하고 수집 항목을 생성합니다.
        
        :param dict settings: 플러그인 설정
        :param parent_item: 부모 항목
        :param path: 처리할 파일 경로
        :return: 생성된 파일 항목
        """
        pass
