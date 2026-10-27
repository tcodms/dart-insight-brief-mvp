# DART Insight UI 프로토타입 v1

작성일: 2026-10-27

이미지: [전체 프로토타입](prototype-v1.png)

## 검토 목적

React + TypeScript + Vite로 개발할 화면의 전체 흐름을 검토하는 이미지 시안이다. 실제 구현·동작 확인 결과가 아니다. 생성 방식은 내장 ImageGen이다. 기능 범위와 실제 저장·다운로드 형식은 개발 계획을 기준으로 확정한다.

## 레퍼런스 적용

- 전체prototype예시1.jpeg: 세로형 전체 구성을 한눈에 보는 보드 형식. 다중 화면을 읽기 쉽도록 2열·3행으로 배치했다.
- 전체프로토타입예시2.jpeg: 섹션 제목과 화면별 구분.
- 대시보드&파일관리화면예시_폴더구조.jpeg: 좌측 탐색·기업별 폴더·우측 상세 정보.
- 대시보드&파일관리화면예시.jpeg: 차분한 워크스페이스 탐색과 목록 표현.
- 원본문서근거표시예시1.jpeg / 원본문서근거표시예시2.jpeg: 분석 내용과 원문 문서의 좌우 분할.
- 원본문서하이라이트예시.jpeg / 원본문서하이라이트예시2.jpeg: 선택한 근거와 원문 하이라이트 연결.

8개를 모두 시각적으로 검토했고, 도구의 참조 이미지 5개 제한에 따라 대표 이미지 5개를 직접 첨부했다. 나머지 특징은 프롬프트에 반영했다.

## 화면 구성

1. 소개·Google 로그인: 핵심 가치와 분석 시작.
2. 내 분석 대시보드: 기업 폴더, 분석 이력, 선택한 분석의 상세 정보.
3. 기업 브리프·원문 근거: 요약·전략·조직 정보와 원본 PDF 하이라이트.
4. 내 자료 관리: CV·JD 목록·버전·연결 결과 및 삭제 영향 안내.
5. 개인화 기여 분석: 기업 활동 → 경험 → 기여, 연결 이유·준비할 점·근거.
6. 기업·직무 비교: 최대 3개 대상의 공통 항목 비교, CV 차이와 JD 미등록 표시.

## 이미지 검토 메모

- 밝은 회색·화이트와 블루 포인트, 공통 사이드바를 사용했다.
- 종합점수·기업 순위 대신 경험 연결과 기여·부족한 점을 보여준다.
- 모든 기업·문서·개인정보·본문 수치는 예시이며 실제 분석 결과가 아니다.
- 전체 보드여서 작은 본문은 화면별 상세 설계에서 교정해야 한다. 문구·아이콘·표 정합성을 실제 구현 사양으로 그대로 사용하지 않는다.
- 이미지에 보이는 PDF 다운로드 등은 확정된 지원 형식이라는 뜻이 아니다. 기본 Markdown·JSON 및 추가 PDF 여부는 개발 계획과 후속 결정에 따른다.
- 이 시안은 사용자의 디자인 승인이나 실제 웹 UI 완성을 의미하지 않는다.

## 최종 생성 프롬프트

```text
Use case: ui-mockup.
Create ONE high-resolution portrait UX prototype overview board for a Korean web application named "DART Insight". This is a NEW design guided by eight reference images, not an edit of their content. Asset is a polished low-to-medium fidelity full-service prototype image for discussing a React + TypeScript + Vite frontend, not code. Readability and consistency are essential.

REFERENCE ROLES:
1 전체prototype예시1.jpeg: the key deliverable reference. Use its long vertically organized whole-prototype presentation, generous pale-gray outer margin, centered clean white canvas, deliberate section hierarchy. Do not reuse veterinary content or Russian copy.
2 전체프로토타입예시2.jpeg: section labels and clean overview composition, but no unnecessary annotation clutter.
3 대시보드&파일관리화면예시_폴더구조.jpeg: persistent narrow sidebar, project folder cards, selected blue folder, right properties panel.
4 대시보드&파일관리화면예시.jpeg: restrained workspace navigation, tidy table/list options, whitespace. Not a task management product.
5 원본문서근거표시예시1.jpeg and 6 원본문서근거표시예시2.jpeg: analysis on the left and a realistic document page preview on the right.
7 원본문서하이라이트예시.jpeg and 8 원본문서하이라이트예시2.jpeg: pale indigo text selection in the original document with a linked evidence explanation.

COMPOSITION:
Portrait image, as large and sharp as possible, approximately 2048 x 3840. A professional Figma-style prototype presentation board. Title at top "DART Insight" and subtitle "취업 기업분석 서비스 · 전체 UI 프로토타입". SIX clearly separated landscape desktop screen artboards, arranged in TWO COLUMNS and THREE ROWS on one long light-gray board. Each artboard is a complete actual webpage UI screenshot, not an illustration and not a floating vague card. Consistent UI scale and aligned artboard sizes, generous gutters, slim browser-like top bars, rounded corners subtle. Labels above each screen: "01 소개·로그인", "02 내 분석 대시보드", "03 기업 브리프·원문 근거", "04 내 자료 관리", "05 개인화 기여 분석", "06 기업·직무 비교". Distinct app views, not six copies of one dashboard. Flow reads top-left to bottom-right. Minimal small flow arrows in gutters only if space permits.
Use short legible correct Korean labels and real readable example text instead of tiny nonsense. Headings are bold, metadata light gray, crisp sans typography. Soft white and cool-gray surfaces, charcoal text, indigo/blue primary actions, subtle lavender highlight, restrained rounded shapes. No decorative photos, 3D objects, gradient backgrounds, ratings, fabricated user reviews or fake performance claims.

PRODUCT:
A private signed-in career document analysis workspace. Users upload annual report PDFs, CVs and optional job description PDFs. No web search or automatic collection. Company briefs can exist without a CV. Google login. Saved results belong to the signed-in user. Dashboard project folders represent company reports. Company+role is a comparison target; max 3. CV versions can differ but need a visible input-difference note. No numeric match scores, percentages, rankings, stars or predicted hiring chance.
Show illustrative companies A기업, B기업, C기업, generic demo report text, not unsupported real company factual claims. Profile "채은". Short prototype note at bottom "예시 데이터 · 디자인 검토용".

SCREEN DETAILS:
01 Public landing page: top DART Insight logo, nav "서비스 소개", "분석 예시", button "Google로 시작하기". Large left headline "기업을 이해하고, 나의 경험을 연결하세요". Small supporting line "사업보고서부터 지원동기와 면접 준비까지". CTA "분석 시작하기". Right side compact product-preview showing a report with evidence highlights. Below three concise feature blocks "기업 브리프", "경험 연결", "기업·직무 비교". Clean aspirational software landing, no invented statistics.
02 Signed-in dashboard: left shared sidebar DART Insight; nav "내 분석", "내 자료", "기업 비교", bottom profile 채은. Top breadcrumb "내 작업 공간 / 내 분석". Headline "내 분석", primary "+ 새 기업 분석". Search INPUT placeholder "저장된 기업·직무 찾기" searches personal saved records ONLY. Three large folder cards "A기업", "B기업", "C기업", report year "2025 사업보고서", simple status "분석 완료" or "분석 중". A기업 folder selected in soft blue. Below compact recent analyses list with company, role, CV version, status. Thin right information panel "선택한 분석", document names, report period. No collaborators, quotas, calendar, kanban project tasks.
03 Enterprise brief/evidence screen: same sidebar, breadcrumb "내 분석 / A기업". Heading "A기업 기업 브리프", tab bar "핵심 요약", "사업·전략", "재무·조직", "원문 근거"; download action. Central-left analysis panel has small title "주요 사업과 투자 방향", short example statement "데이터 기반 업무 개선을 추진하고 있습니다." source chip "근거 E014 · 42쪽", another strategy/organization summary. On right a large original PDF document viewer occupying ~45% screen width with toolbar "사업보고서.pdf  |  42 / 180", page containing table and paragraph; one relevant passage highlighted lavender. The evidence chip is selected and matching document passage highlighted. Evidence details "원문 인용" visible. Professional readable PDF, not a generic blank rectangle.
04 Materials screen: shared sidebar with "내 자료" selected. Headline "내 자료 관리", tabs "CV", "직무기술서", primary "+ 파일 업로드". Table rows "개발자 CV_v2.pdf", "개발자 CV_v1.pdf", "A기업_데이터직무.pdf"; columns "자료명", "종류", "버전", "연결된 분석", action ellipsis. Include a compact upload area "PDF 파일을 업로드하세요". Right detail panel displays selected CV, version "v2", related personal analyses. Small deletion confirmation panel or dialog with heading "CV를 삭제할까요?", body "연결된 개인화 결과도 함께 삭제됩니다.", actions "취소", "삭제". Company brief preserved note "기업 브리프는 유지됩니다." No overwhelming modal covering whole screen.
05 Personal contribution analysis: shared sidebar. Header "내 경험 연결", controls "기업 A기업", "지원 직무 데이터 분석", "CV 개발자 CV v2", "JD A기업 데이터직무", button "기여 분석하기". Result tabs "기여 포인트", "준비할 점", "근거". One prominent structured chain: "기업의 활동" -> "내 경험" -> "가능한 기여". Text examples "데이터 처리 업무", "데이터 자동화 프로젝트", "반복 처리 과정 자동화". Labels "직접 연결", "간접 연결", "자료 부족" as qualitative interpretations, never numerical. Evidence links "기업 E014", "CV 2쪽", "JD 1쪽". Lower "추가로 준비할 점" with short skill-evidence note. Small live progress stepper if needed without contradicting completed result, no technical API identifiers.
06 Comparison screen: wide content with shared sidebar, headline "기업·직무 비교", selected company+role tags "A기업 · 데이터 분석", "B기업 · 백엔드", "C기업 · 직무 미지정", "최대 3개". The main comparison table is the hero: three company columns, labeled row headers "주요 사업", "직무 요건", "연결되는 경험", "가능한 기여", "준비할 점", "근거". Each column short meaningful sample text. At column top show CV v2 for A/B, CV v1 for C. Notice strip "서로 다른 CV가 포함되어 있습니다". C JD row "JD 미등록 · 판단 불가", not low match. Link buttons for original evidence, export button "비교 결과 다운로드". No winner, sort by suitability or ratings.

The output should look like a cohesive plausible web app designed from these references and our specific functional requirements. Use board labels and concise Korean labels over long body copy. All six screens must be clearly present and useful for reviewing the full service.
Directly attached references are representative images 1,3,4,6,8 from the analysis above. The other references were visually inspected and their useful traits described in the prompt.
```
