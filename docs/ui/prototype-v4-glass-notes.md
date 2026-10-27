# UI 프로토타입 v4 — 반투명 화이트

작성일: 2026-10-27

이미지: [반투명 화이트 전체 시안](prototype-v4-glass.png)

## 변경 범위

- 기존 여섯 화면과 서비스 흐름을 유지했다.
- 사용자 첨부 레퍼런스의 반투명 화이트·프로스트 글라스 질감을 적용했다.
- 사이드바·툴바·팝업에는 유리 겹침, 배경에는 부드러운 블러를 사용했다.
- 블랙 주요 버튼과 은은한 파스텔 폴더를 유지하고 문서·비교표 본문은 선명하게 표현했다.
- 내장 ImageGen으로 생성한 디자인 검토용 이미지이며, 실제 투명 배경 PNG나 동작하는 웹 UI는 아니다.
- 전체 화면과 색상·텍스트 대비를 시각 확인했다. 실제 구현에서는 대비·블러 성능·문구를 화면별로 검증한다.

## 최종 생성 프롬프트

```text
Use case: ui-mockup / style-transfer.
Edit image 1, the approved DART Insight white six-screen prototype board, using image 2 solely as visual material and atmosphere reference. Preserve six screen functions and consistent app layout, Korean content and two-column three-row board. Make a new WHITE TRANSLUCENT FROSTED-GLASS variant, clearly distinct from the opaque-white v2 and the black variant. This is a self-contained opaque PNG of glass UI, NOT a transparent-background cutout.

VISUAL DIRECTION:
Reference 2's milky translucent white navigation panel floating above a subdued gray workspace, thin glass edges, layered light surfaces and a muted lavender-gray environment. The key is translucent material and backdrop diffusion. Frosted white sidebar and top toolbar should reveal SOFT blurred shapes behind them; modal and selected panels feel layered over the workspace. Pearl-white panels with 70-88% opacity appearance, restrained backdrop blur, subtle 1px translucent white rim, minimal shadows. Very soft pale lavender/pearl gray background with extremely subtle warm ivory diffusion; no rainbow or colorful blobs. Primary controls charcoal or near-black with white text as previously preferred. Secondary controls frosted white with charcoal type. Main headings black/charcoal, body text medium-dark gray, metadata gray. Very muted powder-blue/lavender/ivory glass folders. No green/red pills, no bright blue accent, no AI sparkle icon, neon, dramatic gradients, metallic shine or thick 3D plastic. Do not copy the unrelated company's logo, watermark, management metrics, calendar or customer brands from reference 2.

IMPORTANT READABILITY:
Apply blur to BACKGROUNDS UNDER GLASS, never to active text, comparison cells, selected document passage, navigation labels or primary headings. Do not copy reference 2's intentional out-of-focus text. The UI is a usable document-analysis workspace with crisp Korean text, not a blurred mood image. Document PDF page stays mostly opaque pearl-white for legibility; its viewer frame and toolbar may be translucent. Comparison table cells mostly white/very light glass, thin gray row dividers. Avoid excessively low contrast. Black primary buttons give clear anchors.

BOARD:
Portrait 2:3 overview with six desktop screenshots arranged 2 columns x 3 rows. Soft neutral gray board backdrop and clean top title "DART Insight", subtitle "취업 기업분석 서비스 · 전체 UI 프로토타입". Rounded screen edges, frosted browser chrome with neutral gray dots, consistent spaces. The six artboards remain readable and distinct.
01 소개·로그인: headline "기업을 이해하고, 나의 경험을 연결하세요", Google login, black "분석 시작하기", quiet preview/evidence glass overlay and three feature summaries. Sidebar not required on public page but retain source if layout needed.
02 내 분석 대시보드: frosted left navigation, saved company folders A기업/B기업/C기업, recent-result list, translucent right file properties panel. Dashboard folders have subtle milky lavender/powder-blue/ivory glass fills and tab silhouettes. Search only saved personal records, not web collection.
03 기업 브리프·원문 근거: analysis left and real report page right. Pearl page, charcoal text, very faint lavender selected passage connected to "근거 · 42쪽". Central white reading surfaces anchored within frosted shell.
04 내 자료 관리: CV/JD tabs, uploaded file/version table and properties, translucent deletion confirmation panel "CV를 삭제할까요?" showing "기업 브리프는 유지됩니다". Black "삭제", outlined "취소", no red.
05 개인화 기여 분석: company/role/CV/optional JD inputs, black action; "기업의 활동 → 내 경험 → 가능한 기여", qualitative linkage and prep gaps, tiny evidence links. No score or ranking.
06 기업·직무 비교: max three company+role columns and common rows 주요 사업/직무 요건/연결되는 경험/가능한 기여/준비할 점/근거. Show CV version differences with a quiet pale-gray notice; missing JD reads "JD 미등록 · 판단 불가" in gray, no alarm. Crisp legible text within mostly-white table.
Shared navigation "홈", "내 분석", "내 자료", "기업 비교"; bottom profile "채은". Footer "예시 데이터 · 디자인 검토용". No real personal email addresses, fake testimonials or numerical fit percentages.

Make material layering visibly frosted and translucent, not merely white cards with shadows. Keep content sharp and services unchanged. A polished, restrained premium frosted white desktop application prototype, one complete image.
```
