# Agent 연결

현재 `.env`의 기존 Upstage Agent를 FastAPI에 연결했다. Agent 프롬프트나 기존 루트의 파이프라인 코드는 변경하지 않는다.

## 실행 흐름

1. 로그인한 사용자가 사업보고서를 등록하고 **기업 분석 시작**을 누른다.
2. `POST /api/jobs`는 입력 문서 종류·소유권과 Agent 설정을 검사하고 작업을 저장한다.
3. 단일 로컬 작업 스레드가 LangGraph의 `prepare → invoke_agents → persist_result`를 실행한다.
4. 별도 Python 프로세스가 기존 기업 파이프라인을 호출한다. 기존 3개 추출 Agent의 병렬 처리와 검증·병합·최종 브리프 흐름을 유지한다.
5. 기업 fact, 브리프 JSON·Markdown, 원문 근거를 사용자별 SQLite에 저장한다. 임시 산출물은 실행별 폴더로 격리하고 완료·실패 후 정리한다. 전역 `latest_*`를 사용자 결과로 읽지 않는다.
6. 완성된 브리프와 CV·JD·지원 직무를 선택하면 기존 기여 파이프라인을 실행한다. 사용자 입력 직무는 기업 사실·JD 원문과 구분한 서비스 문맥으로 전달한다.

등록만으로 외부 요청을 보내지 않는다. 분석 시작 시 선택한 PDF와 추출 결과를 Upstage에 전달한다. 기여 분석은 현재 CV와 JD가 모두 필요하다. JD 없는 분석은 팀원과 별도 합의가 필요하다.

## API

| API | 기능 |
|---|---|
| `GET /api/analysis/capabilities` | 기업·기여 Agent 설정 여부, JD 필수 여부 |
| `POST /api/jobs` | `jobType=brief`, `reportDocumentId` 또는 `jobType=personal`, `briefId`, `cvDocumentId`, `jdDocumentId`, `targetRole` |
| `GET /api/jobs` | 본인 작업의 상태·진행 단계·완료 결과 ID |
| `GET /api/jobs/{id}` | 본인 작업 하나 조회 |
| `GET /api/analyses` | 저장된 기업·기여 분석 목록 |
| `GET /api/analyses/brief/{id}` | 기업 fact·브리프·원문 근거 |
| `GET /api/analyses/personal/{id}` | 기여 Markdown·CV/JD 추출 결과 |
| `GET /api/analyses/{kind}/{id}/download` | Markdown 다운로드 |
| `GET /api/documents/{id}/preview` | 권한 확인 후 원본 PDF 표시 |

변경 요청에는 기존 세션·Origin·CSRF 검사가 동일하게 적용된다. 서버 파일 경로나 외부 Agent 작업 ID는 브라우저에 반환하지 않는다.

## 현재 실행 한계

- 개발용 단일 프로세스 큐다. 서버는 `--workers` 없이 실행한다. 다중 서버·외부 작업 큐는 아직 지원하지 않는다.
- 한 사용자당 진행 작업 1개, 전체 대기·진행 작업 최대 20개다. 같은 입력으로 중복 클릭하면 기존 진행 작업을 반환한다.
- 새로고침·화면 이동 후에도 서버 작업은 계속된다. 화면은 진행 중일 때 약 2.5초 간격으로 상태를 조회한다. SSE는 아직 없다.
- 서버 재시작으로 실행 중이던 작업은 실패 처리한다. 자동 재실행·자동 과금 재시도를 하지 않는다. 대기 작업은 이어서 실행한다. 외부 제공자의 실행 취소는 지원하지 않는다.
- 분석이 진행 중인 입력 문서는 삭제를 막는다. 완료 후 문서 삭제 시 연결된 결과·작업도 FK 규칙에 따라 제거한다.
- 기여 Agent 출력은 Markdown이다. 실제 보고서를 2~3개 나란히 읽을 수 있고 CV 차이를 안내한다. 구조화된 항목별 비교·점수·순위를 만들어내지 않는다.
- LangGraph의 기본 호출 흐름을 연결한 단계이며 체크포인트 재개·단계별 회귀·ChromaDB·Docker는 별도 작업이다.

## 검증

API 테스트는 외부 호출을 대체한 임시 DB에서 입력 소유권·중복 작업·결과 및 근거 저장·실패·재시작 처리를 확인한다. 기존 파이프라인 테스트도 실행한다.

실제 연결 확인에는 개인정보가 없는 합성 CV·JD·기업 fact를 사용했다. CV와 JD가 각각 JSON 22개 필드를 반환했고, 기여 Agent까지 완료되어 Markdown 보고서가 반환됐다. 이 확인을 실제 사업보고서 전체 파이프라인의 실문서 검증으로 간주하지 않는다. 실제 사용자 문서는 사용자가 화면에서 선택해 실행한다.
