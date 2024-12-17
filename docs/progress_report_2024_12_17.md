# Progress Report - 2024.12.17

## 1. Git 커밋 히스토리 정리

### 1.1 작업 내용
- 의미 없는 "." 커밋들을 의미 있는 커밋으로 통합
- 관련된 변경사항들을 논리적으로 그룹화
- 커밋 메시지에 상세한 설명 추가

### 1.2 주요 커밋 정리 결과
1. "Publish 플러그인 경로 및 구조 정리"
   - Publish 플러그인 경로 구조화
   - 플러그인 구성 및 설정 최적화
   - 파일 구조 및 참조 경로 정리

2. "템플릿 구조 개선 및 Publish 설정 최적화"
   - 파일 저장 경로 구조 개선
   - 템플릿 구조 및 확장자 관리 개선
   - Publish 설정 및 구조 최적화

3. "파일 저장 및 퍼블리싱 기능 개선"
   - 파일 저장 시 Scene 대신 Asset 이름 사용
   - Publish 메뉴 추가 및 구조화
   - 파일 저장 및 버전 관리 기능 개선

## 2. Maya 파일 저장 시 이름 자동화 개선

### 2.1 원본 코드
```yaml
# templates.yml
maya_shot_work:
    definition: '@shot_root/dev/maya/{name}.v{version}.{maya_extension}'
    root_name: primary

maya_asset_work:
    definition: '@asset_root/dev/maya/{name}.{Step}.v{version}.{maya_extension}'
    root_name: primary
```

### 2.2 수정된 코드
```yaml
# templates.yml
maya_shot_work:
    definition: '@shot_root/dev/maya/{Shot}_{Step}.v{version}.{maya_extension}'
    root_name: primary

maya_asset_work:
    definition: '@asset_root/dev/maya/{Asset}_{Step}.v{version}.{maya_extension}'
    root_name: primary
```

### 2.3 오류의 원인과 코드 수정 방향
- Maya에서 파일 저장 시 사용자가 이름을 지정하지 않으면 기본값으로 'scene'이 사용되는 문제 발생
- 수동 입력 대신 현재 작업 중인 Shot이나 Asset의 정보를 자동으로 사용하도록 템플릿 수정
- Shot의 경우 `{Shot}_{Step}`, Asset의 경우 `{Asset}_{Step}` 형식으로 통일

### 2.4 예측 결과
- Shot 작업 시: "SH010_Animation.v001.ma"와 같은 형식으로 저장
- Asset 작업 시: "Chair_Modeling.v001.ma"와 같은 형식으로 저장
- 사용자의 수동 입력 없이 자동으로 의미 있는 파일명 생성

### 2.5 실제 결과
- 템플릿 수정 후 Maya 재시작 필요
- 파일명이 자동으로 생성되어 'scene' 기본값 문제 해결
- Shot/Asset 정보가 파일명에 자동으로 반영됨

### 2.6 테스트해봐야 하는 것들
- 다양한 Shot/Asset 조합에서 파일명 생성 테스트
- 버전 관리 시스템과의 호환성 확인
- 기존 파일들의 마이그레이션 계획 수립

## 3. Unreal Engine ShotGrid 메뉴 Publish 항목 추가

### 3.1 발견된 오류
- 컨텍스트 필드 참조 방식 오류 발견
- `context.entity.sg_asset_type`와 같은 직접 참조 방식이 동작하지 않음
- `context.step.short_name` 대신 `context.step.name` 사용 필요

### 3.2 수정된 코드
```yaml
# tk-multi-publish2.yml
settings.tk-multi-publish2.unreal.asset_step:
  publish_plugins:
  - name: Export and Publish to ShotGrid
    settings:
        Additional Fields:
            sg_asset_type: "{context.entity['sg_asset_type']}"  # 딕셔너리 접근 방식으로 수정
            Asset: "{context.entity['code']}"
            Step: "{context.step['name']}"  # short_name에서 name으로 변경
```

### 3.3 오류의 원인과 수정 방향
- 컨텍스트 객체의 속성 접근 방식이 잘못 설정됨
- 직접 속성 접근(dot notation) 대신 딕셔너리 접근 방식(`['key']`)으로 수정 필요
- `short_name` 대신 `name` 필드 사용으로 변경

### 3.4 수정 사항 설명
1. 컨텍스트 필드 접근 방식 변경
   - `context.entity.sg_asset_type` → `context.entity['sg_asset_type']`
   - `context.entity.code` → `context.entity['code']`
   - `context.step.short_name` → `context.step['name']`

2. collector 설정 수정
   - engine 참조 경로 정상화
   - 불필요한 중복 코드 제거

### 3.5 다음 단계
- 수정된 컨텍스트 필드 접근 방식 테스트
- 다양한 에셋 타입에서 필드값 정상 출력 확인
- 에러 로그 모니터링
- 필요시 추가 필드 접근 방식 수정
