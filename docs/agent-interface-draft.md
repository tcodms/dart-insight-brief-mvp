# Agent 연동 접점 초안

2026-10-28 · 연동 전 조사에서 작성한 초안. 현재 실행 API는 [Agent 연결 안내](agent-integration.md)에 구현 상태를 기록한다. 구조화 출력·JD 선택 입력은 여전히 팀원과 합의가 필요하다.

## 현재 호출 형식

| 기존 함수 | 입력 | 반환 |
|---|---|---|
| `service.run_company_brief_pipeline` | 사업보고서 PDF 경로, 진행 콜백 | 기업 fact(`merged_company_data`), 브리프 JSON·Markdown, 산출물 경로 등 |
| `candidate_document_service.run_candidate_document_analysis` | CV/JD PDF 경로 중 하나 이상, 진행 콜백 | `cv`, `jd` 추출 JSON, 실행 폴더와 산출물 경로 |
| `contribution_service.run_contribution_pipeline` | CV PDF 경로, JD PDF 경로, 기업 fact JSON 경로, 진행 콜백 | `report` Markdown, 실행 폴더와 산출물 경로 |

현재 기여 파이프라인은 CV와 JD를 모두 요구한다. 서비스 기획의 **JD 없이 기업 활동과 경험만 연결**하는 흐름은 아직 지원하지 않으므로 팀원과 처리 방식을 확인해야 한다.

## 서비스 어댑터 제안

- 브리프 요청: `report_document_id`.
- 개인화 요청: `brief_id`, `cv_document_id`, 선택적 `jd_document_id`, `target_role`.
- 서버는 모든 입력의 소유자와 문서 종류를 검사하고, DB 식별자를 내부 파일 경로로 변환한다. 클라이언트가 서버 경로나 Agent ID를 직접 지정하지 않는다.
- 실행마다 `analysis_jobs.id`를 발급하고 상태·진행 단계를 기록한다. 실행별 산출물을 사용하며 전역 `latest_*` 파일을 사용자 결과 조회에 사용하지 않는다.
- 원본 결과를 보관하면서 UI용 결과를 별도로 정규화한다. DB에는 `schema_version`을 함께 저장하고, 내부 경로·외부 작업 토큰은 브라우저에 반환하지 않는다.

## 팀원 확인이 필요한 항목

1. JD가 없는 경우 기여 Agent를 호출할 수 있는지, 별도 프롬프트/설정이 필요한지.
2. 현재 기여 결과는 Markdown이다. 비교 화면에 필요한 `연결 경험·판단·이유·가능한 기여·준비할 점`을 구조화된 JSON으로 추가할 수 있는지. 합의 전 Markdown을 임의 분해해 비교 사실로 취급하지 않는다.
3. 각 결과에 기업 fact ID와 CV/JD 원문 쪽수·인용을 어떤 형식으로 돌려줄지. 쪽수는 원본 PDF 기준 1부터 시작하며 근거가 없으면 누락을 명시한다.
4. 진행·실패·시간 초과의 반환 방식과 재시도 정책. 연결 판단은 `직접 연결 / 간접 연결 / 자료 부족`을 제안하며 점수·순위는 생성하지 않는다.

확정 전까지 새 문서 등록은 외부 Agent를 실행하지 않는다. 기존 팀원 Agent 코드도 이번 인증·저장 작업에서 변경하지 않았다.
