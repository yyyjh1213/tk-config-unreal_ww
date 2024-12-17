# Progress Report - 2024.12.17

## 주요 오류 사항

### 1. Publish 메뉴 미표시 문제
- **현상**: Unreal Engine의 ShotGrid 메뉴에서 Publish 항목이 지속적으로 보이지 않는 문제 발생
- **원인 분석**: 
  - 메뉴 등록 과정에서 설정 파일의 구조적 문제 의심
  - engine_locations.yml 파일의 경로 설정 문제 가능성
  - publish2 앱의 초기화 과정에서 오류 발생 가능성
- **해결 시도**:
  - display_name 설정 추가
  - 앱 설정 파일 재검토
  - 로그 분석을 통한 원인 파악 중
- **현재 상태**: 
  - 문제 지속 중
  - 추가 조사 및 해결 방안 모색 필요

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
- Unreal Engine 재시작 후에도 "Publish..." 메뉴 항목이 나타나지 않는 문제 지속
- 설정 파일은 정상적으로 수정되었으나 메뉴 등록 실패
- 추가 디버깅 및 설정 검토 필요

### 2.6 테스트해봐야 하는 것들
- engine_locations.yml 파일 설정 확인
- 로그 파일에서 메뉴 등록 관련 오류 메시지 분석
- 다른 ShotGrid 메뉴 항목들과의 설정 비교
- Unreal Engine과 ShotGrid 통합 설정 전반 검토

## 3. FBX Export 템플릿 경로 수정

### 3.1 원본 코드
```yaml
# core/templates.yml
maya_shot_fbx:
    definition: '@shot_root/pub/maya/fbx/{name}/v{version}/{Shot}_{name}_v{version}.fbx'
    root_name: primary

maya_asset_publish_fbx:
    definition: '@asset_root/pub/maya/fbx/{name}.{Step}.v{version}.fbx'
    root_name: primary

# env/includes/unreal/templates.yml
unreal.maya_asset_fbx_publish:
    definition: '@asset_root/pub/fbx/{name}.v{version}.fbx'
```

### 3.2 수정된 코드
```yaml
# core/templates.yml
# maya_shot_fbx와 maya_asset_publish_fbx 템플릿 주석 처리

# env/includes/unreal/templates.yml
unreal.maya_asset_fbx_publish:
    definition: '@asset_root/pub/maya/fbx/{name}.{Step}.v{version}.fbx'
```

### 3.3 변경 사항 설명
- 기존의 `maya_shot_fbx`와 `maya_asset_publish_fbx` 템플릿을 주석 처리하여 비활성화
- `unreal.maya_asset_fbx_publish` 템플릿으로 통합하여 FBX 파일 경로 구조 단순화
- 새로운 경로 구조에 `{Step}` 정보를 포함하여 작업 단계 구분 가능
- 버전 관리를 위한 `v{version}` 요소 유지

### 3.4 기대 효과
- FBX 파일 경로 구조 통일로 관리 효율성 향상
- 작업 단계(`{Step}`)를 파일명에 포함하여 에셋의 제작 단계 명확히 구분
- 버전 관리 기능 유지로 작업 이력 추적 가능

### 3.5 후속 작업
- 새로운 템플릿 구조에 따른 FBX Export 기능 테스트
- 기존 FBX 파일들의 새로운 경로 구조로의 마이그레이션 계획 수립
- Unreal Engine에서 FBX Import 시 경로 인식 테스트

## 4. Maya Asset FBX Publish 경로 구조 변경

### 4.1 원본 코드
```yaml
# templates.yml
unreal.maya_asset_fbx_publish:
    definition: '@asset_root/pub/fbx/{name}.v{version}.fbx'
```

### 4.2 수정된 코드
```yaml
# templates.yml
unreal.maya_asset_fbx_publish:
    definition: '@asset_root/pub/maya/fbx/{name}.v{version}.fbx'
```

### 4.3 변경 사항 설명
- Maya에서 생성된 FBX 파일들을 위한 전용 하위 디렉토리 생성
- 기존: pub/fbx/ → 변경: pub/maya/fbx/
- 에셋 타입별로 구분된 구조로 변경하여 파일 관리 용이성 향상

### 4.4 테스트 필요 사항
- 새로운 경로에서의 FBX Publish 기능 정상 작동 확인
- Unreal Engine에서 새 경로의 FBX 파일 임포트 테스트
- 기존 FBX 파일들의 새 경로 구조로의 마이그레이션 계획 수립
