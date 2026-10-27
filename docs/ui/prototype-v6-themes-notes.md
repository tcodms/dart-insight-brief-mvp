# UI 프로토타입 v6 — 반투명 Light / Dark

작성일: 2026-10-27

- [Light](prototype-v6-light-violet.png)
- [Dark](prototype-v6-dark-violet.png)

## 디자인 방향

- 사용자가 선호한 블랙 버전의 구조를 기반으로 밝고 어두운 두 테마를 구성했다.
- 반투명 화이트와 반투명 차콜 패널, 공통 탐색과 여섯 화면으로 대응한다.
- 포인트 후보 세 가지(형광 보라·노랑·핑크) 중 이번 이미지에는 보라를 적용했다. 최종 색상 승인을 의미하지 않는다.
- 탭·선택 표시·핵심 행동·원문 하이라이트에 보라를 제한해서 사용했다.
- 픽셀 단순 반전이 아닌, 각 모드에서 읽기 쉬운 배경·본문·테두리·강조 색을 설계하는 방향이다.
- 테마 전환 스위치는 UI 예시이며 실제 구현 전이다.
- 내장 ImageGen으로 각각 생성했다. 두 이미지의 세부 문구·간격 차이는 실제 공통 컴포넌트 구현에서 통일한다.
- 모든 기업·자료·문구는 예시다. 디자인 검토 이미지이며 실제 기능·품질 검증 결과가 아니다.

## Light 생성 프롬프트

```text
Use case: ui-mockup / coordinated theme variants.
Create a new DART Insight prototype board by restyling the attached references. Image 1 (black six-screen board) is the authoritative LAYOUT AND CONTENT reference. Image 2 (milky white six-screen board) is a FROSTED MATERIAL reference only. Preserve the restrained black reference's layout, same app structure, labels and six screens; do not add new features or dashboards. Produce the requested THEME as one complete portrait 2:3 overview, 2 columns x 3 rows, all six desktop screens. The companion theme has IDENTICAL geometry, controls, typography, hierarchy and content: they are one product with a Light/Dark toggle, not two different designs.

DESIGN SYSTEM:
Sophisticated translucent document workspace. Fine low-contrast borders, restrained corner radius, almost flat polished folder silhouettes, minimal noise, no glossy plastic or theatrical glow. Neutral bases only; ONE accent hue FLUORESCENT VIOLET, approximately #B292FF. Accent is rare (under 5% of surface): selected navigation left marker, short active-tab underline, small active source marker, one key action per screen and highlighted PDF passage. No yellow, pink, green, red, sky-blue or rainbow accents. Avoid large purple panels and purple atmospheric blobs. Neon means crisp fresh violet, not luminous cyberpunk glow. Text in neutral grays with strong readable contrast. Use colors adapted for readable text in each mode, rather than mechanically inverting the rendered pixels. Bright accent background uses near-black legible text; subtle accent source marks use neutral readable labels. State/status labels remain neutral, words and tiny monochrome symbols distinguish them.
Add small sun/moon theme toggle in shared header, clearly selected requested mode. Very subtle frosted blur behind sidebar, toolbar and a dialog only; all actual labels and document text SHARP, content panels more opaque for reading.
No scores, rankings, hiring probabilities or fabricated metrics. Use A기업/B기업/C기업 demo facts. No web automatic collection. No stock photos, background ornaments, mascots, sparkle icons, big gradients or colored browser traffic lights. PDF page in each theme should be a readable corresponding document-viewing surface.

SIX SCREENS:
01 소개·로그인: "기업을 이해하고, 나의 경험을 연결하세요", Google로 시작하기, 분석 시작하기, brief feature summaries.
02 내 분석 대시보드: persistent narrow sidebar 홈/내 분석/내 자료/기업 비교; company folders A/B/C, analysis result list, right document properties. All folders neutral (gray or white) except a fine violet selection edge on A기업. No multicolor folders.
03 기업 브리프·원문 근거: same sidebar; left brief sections 주요 사업과 투자 방향/중장기 전략/조직 및 인재; right PDF at 42쪽, relevant quote highlighted very subtly violet. Source action matches highlight.
04 내 자료 관리: CV/JD tabs, uploaded filename/version table, selected file metadata; small deletion dialog "CV를 삭제할까요?", 기업 브리프는 유지됩니다, 취소/삭제. No red; delete is neutral button, reserved violet primary can stay on upload.
05 개인화 기여 분석: company/role/CV/JD inputs, 기여 분석하기, structured "기업의 활동 → 내 경험 → 가능한 기여", direct/indirect/evidence missing neutral labels, prep gaps and evidence links.
06 기업·직무 비교: three company+role columns; rows 주요 사업/직무 요건/연결되는 경험/가능한 기여/준비할 점/근거; CV v2/v1 differences; C기업 "JD 미등록 · 판단 불가" in neutral; input difference notice neutral; no winner or fit percentages.
Top title DART Insight, compact subtitle identifying current theme. Screen captions in concise Korean. Footer "예시 데이터 · 디자인 검토용". High quality crisp Korean UI text; prioritize large headings and short body copy over dense tiny prose.

REQUESTED THEME: LIGHT. Subtitle "Light · 반투명 화이트 + 형광 보라". Pale neutral-gray background #ECEDEE, translucent white shell rgba(255,255,255,.78), white reading panes .94, pearl-white sidebar .65. Charcoal typography #292A2E, gray secondary text. White folder silhouettes and white or light-gray controls; small violet accent consistent as above. Thin white reflective edge and very soft neutral shadow suggest frosted glass. No black-filled surfaces or giant black buttons. User wants inverse companion of black reference; LIGHT is neutral white, not a purple-tinted or sky-blue page. Make all six layouts match the black reference closely.
```

## Dark 생성 프롬프트

```text
Use case: ui-mockup / coordinated theme variants.
Create a new DART Insight prototype board by restyling the attached references. Image 1 (black six-screen board) is the authoritative LAYOUT AND CONTENT reference. Image 2 (milky white six-screen board) is a FROSTED MATERIAL reference only. Preserve the restrained black reference's layout, same app structure, labels and six screens; do not add new features or dashboards. Produce the requested THEME as one complete portrait 2:3 overview, 2 columns x 3 rows, all six desktop screens. The companion theme has IDENTICAL geometry, controls, typography, hierarchy and content: they are one product with a Light/Dark toggle, not two different designs.

DESIGN SYSTEM:
Sophisticated translucent document workspace. Fine low-contrast borders, restrained corner radius, almost flat polished folder silhouettes, minimal noise, no glossy plastic or theatrical glow. Neutral bases only; ONE accent hue FLUORESCENT VIOLET, approximately #B292FF. Accent is rare (under 5% of surface): selected navigation left marker, short active-tab underline, small active source marker, one key action per screen and highlighted PDF passage. No yellow, pink, green, red, sky-blue or rainbow accents. Avoid large purple panels and purple atmospheric blobs. Neon means crisp fresh violet, not luminous cyberpunk glow. Text in neutral grays with strong readable contrast. Use colors adapted for readable text in each mode, rather than mechanically inverting the rendered pixels. Bright accent background uses near-black legible text; subtle accent source marks use neutral readable labels. State/status labels remain neutral, words and tiny monochrome symbols distinguish them.
Add small sun/moon theme toggle in shared header, clearly selected requested mode. Very subtle frosted blur behind sidebar, toolbar and a dialog only; all actual labels and document text SHARP, content panels more opaque for reading.
No scores, rankings, hiring probabilities or fabricated metrics. Use A기업/B기업/C기업 demo facts. No web automatic collection. No stock photos, background ornaments, mascots, sparkle icons, big gradients or colored browser traffic lights. PDF page in each theme should be a readable corresponding document-viewing surface.

SIX SCREENS:
01 소개·로그인: "기업을 이해하고, 나의 경험을 연결하세요", Google로 시작하기, 분석 시작하기, brief feature summaries.
02 내 분석 대시보드: persistent narrow sidebar 홈/내 분석/내 자료/기업 비교; company folders A/B/C, analysis result list, right document properties. All folders neutral (gray or white) except a fine violet selection edge on A기업. No multicolor folders.
03 기업 브리프·원문 근거: same sidebar; left brief sections 주요 사업과 투자 방향/중장기 전략/조직 및 인재; right PDF at 42쪽, relevant quote highlighted very subtly violet. Source action matches highlight.
04 내 자료 관리: CV/JD tabs, uploaded filename/version table, selected file metadata; small deletion dialog "CV를 삭제할까요?", 기업 브리프는 유지됩니다, 취소/삭제. No red; delete is neutral button, reserved violet primary can stay on upload.
05 개인화 기여 분석: company/role/CV/JD inputs, 기여 분석하기, structured "기업의 활동 → 내 경험 → 가능한 기여", direct/indirect/evidence missing neutral labels, prep gaps and evidence links.
06 기업·직무 비교: three company+role columns; rows 주요 사업/직무 요건/연결되는 경험/가능한 기여/준비할 점/근거; CV v2/v1 differences; C기업 "JD 미등록 · 판단 불가" in neutral; input difference notice neutral; no winner or fit percentages.
Top title DART Insight, compact subtitle identifying current theme. Screen captions in concise Korean. Footer "예시 데이터 · 디자인 검토용". High quality crisp Korean UI text; prioritize large headings and short body copy over dense tiny prose.

REQUESTED THEME: DARK. Subtitle "Dark · 반투명 블랙 + 형광 보라". Neutral charcoal-black background #111214, translucent charcoal shell rgba(25,26,29,.82), near-black reading panes, charcoal sidebar .7. Off-white typography #EEEEEC, soft gray secondary text. Gray folder silhouettes, charcoal control backgrounds, soft gray rim. Keep a few tiny violet accent markers and violet key action button, not large purple fill. No white cards or colored backgrounds. Frosted layer depth is dark-on-dark with diffuse neutral light, not opaque flat black and not neon cyberpunk. Make all six layouts match original black reference closely.
```
