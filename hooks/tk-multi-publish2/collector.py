# This file is based on templates provided and copyrighted by Autodesk, Inc.
# This file has been modified by Epic Games, Inc. and is subject to the license
# file included in this repository.

import glob
import os
import sys
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()


class BasicCollectorPlugin(HookBaseClass):
    """
    기본 Collector 플러그인입니다.
    모든 DCC 툴별 collector의 기본 클래스로 사용됩니다.
    
    주요 기능:
    - 기본 파일 수집
    - 공통 메타데이터 처리
    - 기본 필터링
    """
    
    @property
    def common_file_extensions(self):
        """지원하는 파일 확장자 목록을 반환합니다."""
        return [".ma", ".mb", ".fbx", ".abc", ".uasset", ".umap"]

    def process_current_session(self, settings, parent_item):
        """
        현재 세션을 처리하고 수집 항목을 생성합니다.

        :param dict settings: Collector 설정
        :param parent_item: 부모 항목
        """
        engine = self.parent.engine
        if not engine:
            self.logger.debug("Current engine is not available.")
            return

        # 현재 세션 정보 수집
        session_item = parent_item.create_item(
            "session",
            "Current Session",
            "Current DCC Session"
        )
        
        # 현재 작업 파일 경로 가져오기
        path = engine.app.get_current_path()
        
        if path:
            session_item.properties["path"] = path
            session_item.properties["file_extension"] = os.path.splitext(path)[1]
            
        self.logger.info("Collected current session: %s" % session_item.name)
        
        return session_item

    def _collect_file(self, path, parent_item, type_display, type_spec=None):
        """
        파일을 수집하고 항목을 생성합니다.

        :param path: 파일 경로
        :param parent_item: 부모 항목
        :param type_display: 표시용 타입 이름
        :param type_spec: 내부 사용 타입 지정자
        :return: 생성된 항목
        """
        if not os.path.exists(path):
            self.logger.warning("File not found: %s" % path)
            return None

        file_item = parent_item.create_item(
            type_spec or "file",
            type_display,
            os.path.basename(path)
        )

        file_item.properties["path"] = path
        file_item.properties["file_extension"] = os.path.splitext(path)[1]

        self.logger.info("Collected file: %s" % file_item.name)
        
        return file_item

class UnrealCollectorPlugin(BasicCollectorPlugin):
    """
    Collector that operates on the current Unreal Editor session. Should
    inherit from the basic collector hook.
    """
    
    def process_current_session(self, settings, parent_item):
        """
        Analyzes the current session open in Unreal and parents a subtree of
        items under the parent_item passed in.

        :param dict settings: Configured settings for this collector
        :param parent_item: Root item instance

        """
        # create an item representing the current Unreal session
        item = self.collect_current_unreal_session(settings, parent_item)
        if not item:
            return

        # look at the render folder to find rendered images on disk
        self.collect_rendered_images(item)

        # look at the scene geometry to find meshes to publish
        self.collect_meshes(item)

    def collect_current_unreal_session(self, settings, parent_item):
        """
        Creates an item that represents the current Unreal session.

        :param dict settings: Configured settings for this collector
        :param parent_item: Parent Item instance

        :returns: Item of type unreal.session
        """
        
        publisher = self.parent

        # get the path to the current file
        path = unreal.Paths.get_project_file_path()

        # ensure the file path is normalized and append the filename
        path = sgtk.util.ShotgunPath.normalize(path)

        # display name for the item
        display_name = "Current Unreal Session"

        # create the session item for the publish hierarchy
        session_item = parent_item.create_item(
            "unreal.session",
            "Unreal Session",
            display_name
        )

        # get the icon path to display for this item
        icon_path = os.path.join(
            self.disk_location,
            "icons",
            "unreal.png"
        )

        # set the icon for the item
        session_item.set_icon_from_path(icon_path)

        # if a work template is configured, add it to the item properties so
        # that it can be used by attached publish plugins
        work_template_setting = settings.get("Work Template")
        if work_template_setting:

            work_template = publisher.get_template_by_name(work_template_setting)

            # store the template on the item for use by publish plugins. we
            # can't evaluate the fields here because there's no guarantee the
            # current session path won't change once the item has been created.
            # the attached publish plugins will need to resolve the fields at
            # execution time.
            session_item.properties["work_template"] = work_template
            self.logger.debug("Work template defined for Unreal collection.")

        self.logger.info("Collected current Unreal scene")

        return session_item

    def collect_rendered_images(self, parent_item):
        """
        Creates items for any rendered images that can be found.

        :param parent_item: Parent Item instance
        :returns: Nothing
        """
        
        # iterate over all the known render paths
        render_paths = []

        # look for rendered images. currently just looks for rendered images
        # in a "images" subfolder of the project root
        render_path = os.path.join(unreal.Paths.get_project_saved_dir(), "images")
        if os.path.exists(render_path):
            render_paths.append(render_path)

        if not render_paths:
            self.logger.debug(
                "No valid render paths found. Skipping rendered image collection.")
            return

        # look for movie files in the render paths
        for render_path in render_paths:

            # create the item for the publish
            item = parent_item.create_item(
                "unreal.movie",
                "Rendered Movie",
                "Rendered Movie"
            )

            # get the icon path to display for this item
            icon_path = os.path.join(
                self.disk_location,
                "icons",
                "unreal.png"
            )

            # set the icon for the item
            item.set_icon_from_path(icon_path)

            # store the render path for each item
            item.properties["path"] = render_path

            # add the layer used to render
            item.properties["sequence_name"] = "Image Sequence"

            # if no specific frame spec, assume it is an image sequence
            # with a frame spec
            item.properties["is_sequence"] = True

            # display the rendered images in the publish item UI
            self.logger.info(
                "Collected rendered movie for Unreal. Path: %s" % (render_path,))

    def collect_meshes(self, parent_item):
        """
        Creates items for each mesh.

        :param parent_item: Parent Item instance
        :returns: Nothing
        """
        
        # get a handle on the unreal editor subsystem
        editor_subsystem = unreal.UnrealEditorSubsystem()

        # get all selected assets
        selected_assets = editor_subsystem.get_selected_assets()

        if not selected_assets:
            self.logger.debug("No assets selected. Skipping mesh collection.")
            return

        # iterate over all the selected assets
        for asset in selected_assets:
            # get the path to the asset
            asset_path = asset.get_path_name()

            # get the asset name
            asset_name = asset.get_name()

            # get the asset class
            asset_class = asset.get_class()

            # get the asset class name
            asset_class_name = asset_class.get_name()

            # create an item for the asset
            item = parent_item.create_item(
                "unreal.asset.%s" % asset_class_name,
                "Unreal Asset",
                asset_name
            )

            # get the icon path to display for this item
            icon_path = os.path.join(
                self.disk_location,
                "icons",
                "unreal.png"
            )

            # set the icon for the item
            item.set_icon_from_path(icon_path)

            # store the asset path and name for each item
            item.properties["asset_path"] = asset_path
            item.properties["asset_name"] = asset_name

            # display the asset in the publish item UI
            self.logger.info(
                "Collected asset for Unreal. Path: %s" % (asset_path,))
