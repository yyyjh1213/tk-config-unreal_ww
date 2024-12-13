import unreal
import os
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel, QApplication, QFormLayout
from PySide6.QtCore import Qt

dialog = None

class FolderCreatorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("폴더 템플릿 생성")
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # 설명 라벨
        label = QLabel("Episode, Sequence, Shot을 입력하세요.")
        layout.addWidget(label)

        # 입력 폼
        form_layout = QFormLayout()
        self.episode_input = QLineEdit()
        self.sequence_input = QLineEdit()
        self.shot_input = QLineEdit()

        # 탭 이동 가능 설정
        self.episode_input.setFocusPolicy(Qt.StrongFocus)
        self.sequence_input.setFocusPolicy(Qt.StrongFocus)
        self.shot_input.setFocusPolicy(Qt.StrongFocus)

        # 폼 레이아웃 추가
        form_layout.addRow("Episode:", self.episode_input)
        form_layout.addRow("Sequence:", self.sequence_input)
        form_layout.addRow("Shot:", self.shot_input)
        layout.addLayout(form_layout)

        # 생성 버튼
        create_button = QPushButton("폴더 생성")
        create_button.clicked.connect(self.create_folders)
        layout.addWidget(create_button)

        self.setLayout(layout)

    def create_folders(self):
        episode = self.episode_input.text().strip()
        sequence = self.sequence_input.text().strip()
        shot = self.shot_input.text().strip()

        if not (episode and sequence and shot):
            unreal.log_warning("모든 필드를 입력해주세요.")
            return

        try:
            # 기본 프로젝트 경로
            project_path = os.path.dirname(unreal.Paths.get_project_file_path())
            cinematics_path = os.path.join(project_path, "Content/Cinematics/LevelSequence")
            target_path = os.path.join(cinematics_path, episode, sequence, shot)

            # 경로를 슬래시(`/`)로 통일
            target_path = os.path.normpath(target_path).replace("\\", "/")

            # 메인 경로 생성
            if not os.path.exists(target_path):
                os.makedirs(target_path)
                unreal.log(f"폴더 생성됨: {target_path}")

            # 서브 폴더 생성
            subfolders = [
                f"{episode}_{sequence}_{shot}_char",
                f"{episode}_{sequence}_{shot}_env",
                f"{episode}_{sequence}_{shot}_fx",
                f"{episode}_{sequence}_{shot}_prop",
                f"{episode}_{sequence}_{shot}_cam",
                f"{episode}_{sequence}_{shot}_lgt",
            ]

            for subfolder in subfolders:
                subfolder_path = os.path.normpath(os.path.join(target_path, subfolder)).replace("\\", "/")
                if not os.path.exists(subfolder_path):
                    os.makedirs(subfolder_path)
                    unreal.log(f"폴더 생성됨: {subfolder_path}")

            unreal.log("모든 폴더가 성공적으로 생성되었습니다.")
            self.close()

        except Exception as e:
            unreal.log_error(f"폴더 생성 중 오류 발생: {str(e)}")

def main():
    global dialog  # 전역 변수로 관리
    app = QApplication.instance()
    if not app:
        app = QApplication([])

    if dialog is None:  # dialog가 없을 때만 생성
        dialog = FolderCreatorDialog()
    dialog.show()


if __name__ == "__main__":
    main()