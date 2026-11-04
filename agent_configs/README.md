# Studio Agent 설정

Studio에 가져올 최신 설정은 `latest/`에 모은다. Agent를 수정하거나 새 버전을 전달받으면 해당 Agent의 JSON을 이 폴더에서 갱신하고, 파일명이 바뀌면 이전 복사본을 빼서 역할별로 최신 파일 하나만 유지한다.

1~3번은 전달받은 FACT 추출 Agent다. 4번 기업 브리프 Agent는 저장소 루트에서 `python build_company_brief_agent_v4.py`로 재생성하면 `latest/`에 저장된다.

`brief_v4/`, `validated_v3/`, `revised/`, `mvp_final/` 및 루트의 기존 JSON은 이전 버전 비교에 사용한다.
