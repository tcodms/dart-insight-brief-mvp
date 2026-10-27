# UI 프로토타입 v3 — 올블랙

작성일: 2026-10-27

이미지: [전체 다크 프로토타입](prototype-v3-dark.png)

## 변경 내용

- v2의 여섯 화면·공통 흐름을 유지한 다크 테마 시안.
- 사용자 첨부 다크 폴더 워크스페이스·대시보드의 스타일을 참고했다.
- 블랙·차콜 배경과 회색 폴더, 밝은 회색 주요 버튼을 사용한다.
- 상태·선택·근거는 색상 대신 명도·테두리·문구로 구분한다.
- 원문 뷰어도 다크 보기의 예시이며, 실제 PDF 표시 방식과 접근성은 구현 단계에서 검증한다.
- 작은 본문·예시 데이터·다운로드 표시를 구현 사양으로 확정한 것은 아니다.
- 내장 ImageGen으로 생성했고 전체 여섯 화면과 다크 팔레트를 시각 확인했다. 코드 실행 테스트 대상이 아닌 디자인 이미지다.

## 최종 생성 프롬프트

```text
Use case: ui-mockup / style-transfer edit.
Edit image 1, the DART Insight six-screen prototype board. Images 2 and 3 are DARK VISUAL STYLE REFERENCES only. Preserve all six application screens, Korean product content, two-column three-row overview, screen labels 01 through 06, shared navigation, same service features. Create a sophisticated ALL-BLACK / CHARCOAL MONOCHROME version inspired by the dark knowledge-base folder workspace and warm-black document dashboard in the references.

Palette: board backdrop #101010, screen surfaces #151515, content background #101010, sidebar #1A1A1A, elevated areas #202020, borders #303030, primary text #ECEBE7, secondary text #A4A39F. Mostly neutral blacks, subtle warm charcoal. No colored accents at all in app controls. No pastel lavender, blue, green, red, orange, purple. Google logo may use a MONOCHROME G to keep the board monochrome.
Buttons: primary CTA soft ivory/light gray #E7E5DF with near-black text, secondary buttons dark with fine gray outline and off-white text. Crisp modest radius, no glowing borders, no gradient buttons. DART Insight wordmark off-white. Selected nav #303030 with white lettering; inactive nav gray with slim light-gray outline icons. Dark document-research workspace, tactile gray folder silhouettes as in reference 2. Distinguish hierarchy through gray VALUE and typography rather than color.
Folder cards: A기업, B기업, C기업 are actual dark gray folder shapes with slight neutral edge highlights and small paper tabs, no vivid color or shiny 3D. Keep dashboard folder hierarchy and right selected-file metadata panel.
Original PDF viewer: the viewer frame and DOCUMENT PAGE are dark charcoal in this DARK VIEW prototype, white/gray readable document text, gray table lines. Source passage highlight medium gray #414141 with bright ivory letters and a slim white marker, no purple. Do not invert Korean letters into illegibility.
Status labels "분석 완료", "분석 중", "직접 연결", "간접 연결", "자료 부족" use neutral gray pills and tiny monochrome symbols. No red/green semantic status. Delete confirmation is charcoal with ivory primary "삭제" and outline "취소". Comparison note for different CVs is slightly lighter gray with an ivory information symbol. C기업 missing JD is neutral gray text "JD 미등록 · 판단 불가", no red.
All app areas, modals, tables, uploader boxes, dropdowns, browser bars, headers and board background must be DARK. Do not leave white page rectangles. The only large light areas are small primary buttons. No decorative stock imagery, purple gradients, colorful score charts, glossy AI-sparkle icons or neon. Borrow references' disciplined dense typography, restrained thin borders, dark-on-dark depth, generous breathing room. Sufficient text contrast: it must be readable, not washed out low-contrast gray.

Preserve screen roles:
01 소개·로그인 — headline "기업을 이해하고, 나의 경험을 연결하세요", intro, Google login and 분석 시작하기 CTA.
02 내 분석 대시보드 — A/B/C company folders, recent results list, selected-file information.
03 기업 브리프·원문 근거 — analysis on left, report page with related highlighted passage on right.
04 내 자료 관리 — CV/JD tabs, file/version list, selected material, deletion impact dialog.
05 개인화 기여 분석 — company/role/CV/JD controls; 기업의 활동 → 내 경험 → 가능한 기여; evidence and preparation gaps.
06 기업·직무 비교 — up to 3 company+role columns, shared comparison rows, CV version differences, optional-JD missing state, evidence links.
No numeric match scores, company rankings or hiring predictions. Use illustrative company data. No automatic document collection. Keep the service logic unchanged.
Top title "DART Insight", subtitle "취업 기업분석 서비스 · 전체 UI 프로토타입". Footer "예시 데이터 · 디자인 검토용". Top-level labels and captions also off-white or gray on black.
Final is one complete high-quality portrait 2:3 prototype board with six desktop mockups. Preserve composition and content while comprehensively restyling into all-black, quiet premium monochrome. Render Korean typography as legibly as possible.
```
