# Progress Report - 2024.12.17

## 1. Maya 파일 저장 시 이름 자동화 개선

### 1.1 원본 코드
```yaml
# templates.yml
maya_shot_work:
    definition: '@shot_root/dev/maya/{name}.v{version}.{maya_extension}'
    root_name: primary

maya_asset_work:
    definition: '@asset_root/dev/maya/{name}.{Step}.v{version}.{maya_extension}'
    root_name: primary
```

### 1.2 수정된 코드
```yaml
# templates.yml
maya_shot_work:
    definition: '@shot_root/dev/maya/{Shot}_{Step}.v{version}.{maya_extension}'
    root_name: primary

maya_asset_work:
    definition: '@asset_root/dev/maya/{Asset}_{Step}.v{version}.{maya_extension}'
    root_name: primary
```

### 1.3 오류의 원인과 코드 수정 방향
- Maya에서 파일 저장 시 사용자가 이름을 지정하지 않으면 기본값으로 'scene'이 사용되는 문제 발생
- 수동 입력 대신 현재 작업 중인 Shot이나 Asset의 정보를 자동으로 사용하도록 템플릿 수정
- Shot의 경우 `{Shot}_{Step}`, Asset의 경우 `{Asset}_{Step}` 형식으로 통일

### 1.4 예측 결과
- Shot 작업 시: "SH010_Animation.v001.ma"와 같은 형식으로 저장
- Asset 작업 시: "Chair_Modeling.v001.ma"와 같은 형식으로 저장
- 사용자의 수동 입력 없이 자동으로 의미 있는 파일명 생성

### 1.5 실제 결과
- 템플릿 수정 후 Maya 재시작 필요
- 파일명이 자동으로 생성되어 'scene' 기본값 문제 해결
- Shot/Asset 정보가 파일명에 자동으로 반영됨

### 1.6 테스트해봐야 하는 것들
- 다양한 Shot/Asset 조합에서 파일명 생성 테스트
- 버전 관리 시스템과의 호환성 확인
- 기존 파일들의 마이그레이션 계획 수립

## 2. Unreal Engine ShotGrid 메뉴 Publish 항목 추가

### 2.1 원본 코드
```yaml
# tk-multi-publish2.yml
settings.tk-multi-publish2.unreal.project:
  collector: "{self}/collector.py:{engine}/tk-multi-publish2/basic/collector.py"
  publish_plugins:
  - name: Publish to ShotGrid
    hook: "{self}/publish_file.py"
    settings: {}
```

### 2.2 수정된 코드
```yaml
# tk-multi-publish2.yml
settings.tk-multi-publish2.unreal.project:
  display_name: "Publish..." # this is the name of the menu item
  collector: "{self}/collector.py:{engine}/tk-multi-publish2/basic/collector.py"
  publish_plugins:
  - name: Publish to ShotGrid
    hook: "{self}/publish_file.py"
    settings: {}
```

### 2.3 오류의 원인과 코드 수정 방향
- Unreal Engine의 ShotGrid 메뉴에서 Publish 항목이 나타나지 않는 문제 발생
- 로그에서 "Unknown command: tk-multi-publish2/Publish..." 경고 메시지 확인
- publish2 앱에 display_name 설정이 누락되어 메뉴 항목이 등록되지 않음
- display_name을 추가하여 메뉴 항목 등록 활성화

### 2.4 예측 결과
- ShotGrid 메뉴에 "Publish..." 항목이 추가됨
- 메뉴를 통해 Publish 기능 접근 가능
- 기존 publish 설정과 연동되어 정상 작동

### 2.5 실제 결과
- Unreal Engine 재시작 후 ShotGrid 메뉴에 "Publish..." 항목 표시
- 메뉴 클릭 시 publish 다이얼로그 정상 표시
- 기존 publish 기능과 정상 연동

### 2.6 테스트해봐야 하는 것들
- 다양한 Asset 유형에 대한 publish 테스트
- publish 설정이 올바르게 적용되는지 확인
- publish 후 ShotGrid에서 데이터가 정상적으로 표시되는지 확인
- 권한 설정에 따른 publish 기능 동작 확인
