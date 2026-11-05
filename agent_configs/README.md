# Studio Agent 설정

현재 사용하는 설정은 `latest/`에 역할별 파일 하나씩 보관한다. 수정하면 해당 파일을 갱신하고 변경 이력은 Git으로 관리한다.

| 파일 번호 | 역할 |
|---|---|
| 01 | 사업·전략 FACT 추출 |
| 02 | 재무·경영 FACT 추출 |
| 03 | 인력·조직·ESG FACT 추출 |
| 04 | 취업용 기업 브리프 |
| 05 | CV 추출 |
| 06 | JD 추출 |
| 07 | 기여 보고서 |

기업 브리프 설정은 저장소 루트에서 `python -m scripts.build_company_brief_agent_v4`로 재생성한다.
생성기는 현재 04 설정의 파이프라인·모델 설정을 유지하고 프롬프트와 출력 스키마를 갱신한다.
Studio에 가져온 뒤 발급된 Agent ID와 Config ID는 로컬 `.env`에 입력한다.

브리프 입력과 검증 방법은 [브리프 Agent 안내](../docs/brief-agent.md)를 참고한다.
