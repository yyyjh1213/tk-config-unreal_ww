# import unreal
print("커스텀 메뉴를 만드는 모듈 임포트 완료!")

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
        
        # 섹션 추가
        section_name = "MyCustomSection"
        menu.add_section(
            section_name,
            unreal.Text("My Custom Actions")
        )
        
        # 상위 메뉴 생성
        parent_entry = unreal.ToolMenuEntry(
            name="MyCustomSubmenu",
            type=unreal.MultiBlockType.MENU_ENTRY
        )
        parent_entry.set_label(unreal.Text("My Tools"))
        
        # 서브메뉴를 위한 메뉴 생성
        submenu = unreal.ToolMenu("MyToolsSubmenu", "MyToolsSubmenu", True)
        tool_menus.register_menu("MyToolsSubmenu", "My Tools Submenu", None)
        
        # 서브메뉴에 항목 추가
        submenu.add_menu_entry(
            "SubSection",
            unreal.ToolMenuEntry(
                name="MakeFolderStructure",
                type=unreal.MultiBlockType.MENU_ENTRY
            ).set_label(unreal.Text("Make Folder Structure"))
        )
        
        submenu.add_menu_entry(
            "SubSection",
            unreal.ToolMenuEntry(
                name="AnotherAction",
                type=unreal.MultiBlockType.MENU_ENTRY
            ).set_label(unreal.Text("Another"))
        )
        
        # 상위 메뉴와 서브메뉴 연결
        parent_entry.sub_menu_data = submenu
        
        # 메인 메뉴에 상위 메뉴 추가
        menu.add_menu_entry(section_name, parent_entry)
        
        # 메뉴 변경사항 적용
        tool_menus.refresh_all_widgets()
        unreal.log("Refreshed all widgets")
        
    except Exception as e:
        unreal.log_error(f"Error adding menu: {str(e)}")


def run():
    print("R"*20, "작동 테스트")


# 메뉴 추가 실행
# add_content_browser_menu()
run()