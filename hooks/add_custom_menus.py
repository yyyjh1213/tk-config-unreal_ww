import unreal

def add_content_browser_menu():
    try:
        # 메뉴 시스템 초기화
        tool_menus = unreal.ToolMenus.get()
        
        # 콘텐츠 브라우저 빈 공간의 컨텍스트 메뉴 찾기
        menu_name = "ContentBrowser.FolderContextMenu"
        menu = tool_menus.find_menu(menu_name)
        
        if not menu:
            unreal.log_warning(f"Menu not found: {menu_name}")
            return
            
        unreal.log(f"Found menu: {menu_name}")
        
        # 새로운 섹션 추가
        section_name = "MyCustomSection"
        menu.add_section(
            section_name,
            unreal.Text("My Custom Actions")
        )

        # 메뉴 항목 추가
        entry = unreal.ToolMenuEntry(
            name="MyCustomAction",
            type=unreal.MultiBlockType.MENU_ENTRY
        )
        
        # 메뉴 항목 설정
        entry.set_label(unreal.Text("Make Folder Structure"))
        
        # 실행할 Python 명령 설정
        command_string = """
import unreal
unreal.log("********** 커스텀 액션을 실행합니다~")

win_dir = os.path.abspath(os.path.dirname(__file__))
if win_dir not in sys.path:
    sys.path.append(win_dir)

import create_shot_directory
create_shot_directory.main()
"""
        entry.set_string_command(
            unreal.ToolMenuStringCommandType.PYTHON,
            "PythonCommand",
            command_string
        )
        
        # 메뉴에 항목 추가
        menu.add_menu_entry(section_name, entry)
        unreal.log("Added menu entry")
        
        # 메뉴 변경사항 적용
        tool_menus.refresh_all_widgets()
        unreal.log("Refreshed all widgets")
        
    except Exception as e:
        unreal.log_error(f"Error adding menu: {str(e)}")

# 메뉴 추가 실행
# add_content_browser_menu()


unreal.log("="*20)
unreal.log("add custom menu 스크립트 실행")
unreal.log("="*20)