# Progress Report - 2024-12-16

## Maya Publish Menu Issues Resolution

### Issues Addressed

1. **Undefined Reference Error**
   - **Issue**: `settings.tk-multi-publish2.maya.asset_step.unreal` 참조를 찾을 수 없음
   - **Resolution**: 
     - `tk-maya.yml`의 publish 설정을 올바른 참조로 수정
     - `unreal/settings/tk-multi-publish2.yml`에 Maya asset step unreal 설정 추가

2. **Legacy Breakdown Location Error**
   - **Issue**: `settings.tk-multi-breakdown.location` 참조를 찾을 수 없음
   - **Resolution**:
     - `tk-maya.yml`의 breakdown 설정을 `@apps.tk-multi-breakdown.location`으로 수정
     - 올바른 app_locations.yml 참조 사용

3. **Turntable Publish Error**
   - **Issue**: Unreal Engine 버전 불일치로 인한 임시 디렉토리 접근 오류
   - **Resolution**:
     - `C:\Temp` 디렉토리 생성
     - Unreal Engine 버전을 5.0에서 5.3으로 업데이트
     - Turntable publish 템플릿 경로 수정:
       ```yaml
       unreal.maya_turntable_publish:
           definition: '@asset_root/review/{name}.{Step}.turntable_v{version}.mov'
       ```

4. **FBX Export Path Issue**
   - **Issue**: FBX 파일이 원하는 경로에 저장되지 않음
   - **Resolution**:
     - FBX publish 템플릿 경로 수정:
       ```yaml
       unreal.maya_asset_fbx_publish:
           definition: '@asset_root/pub/unreal/fbx/{name}.{Step}.v{version}.fbx'
       ```

### Modified Files

1. `env/includes/settings/tk-maya.yml`
   - Publish 설정 참조 수정
   - Legacy Breakdown 설정 추가 및 수정

2. `env/includes/unreal/settings/tk-multi-publish2.yml`
   - Maya asset step unreal 설정 추가
   - Unreal Engine 버전 업데이트

3. `env/includes/unreal/templates.yml`
   - Turntable publish 템플릿 경로 수정
   - FBX publish 템플릿 경로 수정

### Next Steps

1. **Testing Required**:
   - Maya에서 새 버전으로 파일 저장 후 publish 테스트
   - FBX export 경로 확인
   - Turntable 렌더링 테스트

2. **Documentation**:
   - 수정된 설정들에 대한 문서화
   - 사용자 가이드 업데이트

3. **Monitoring**:
   - 수정된 설정들이 정상적으로 작동하는지 모니터링
   - 추가 오류 발생 시 즉시 대응
