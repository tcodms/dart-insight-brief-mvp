# UI 프로토타입 v5 — 화이트 투명도와 아주 연한 하늘색

작성일: 2026-10-27

이미지: [전체 시안](prototype-v5-white-sky.png)

- v4의 6개 화면 구성을 유지했다.
- 블랙 채움 버튼과 다색 파스텔을 제거하고, 화이트 패널의 투명도 차이로 통일했다.
- 선택 영역·원문 하이라이트에만 매우 연한 하늘색을 사용한다.
- 텍스트는 가독성을 위해 짙은 회색, 버튼은 화이트와 얇은 테두리로 표현했다.
- 비교 안내에 남은 베이지를 추가로 화이트 보정했다.
- 내장 ImageGen으로 생성한 디자인 검토용 이미지이며 실제 알파 투명 배경 파일이나 구현 완료 화면이 아니다. 원문·문구·상태는 예시다.

## 생성 프롬프트

```text
Edit the attached DART Insight six-screen prototype image. Preserve all screen layouts, exact service functions, Korean labels, six-screen 2x3 portrait board, company folders, split document viewer, CV/JD management, contribution and comparison. THIS IS A STRICT MATERIAL/PALETTE REFINEMENT, not new layout.
User correction: the frosted WHITE version must NOT contain black buttons or multiple pastel colors. Unify the entire product through WHITE layers with varying transparency. Use only ONE EXTREMELY PALE SKY-BLUE accent sparingly.

MANDATORY PALETTE:
- Only neutral WHITE #FFFFFF at different apparent opacity for surfaces: background milk white/neutral cool gray-white; sidebar white about 55-65%; main shell white about 70%; inner content white 80-90%; buttons white 95-100%.
- The only chromatic color permitted is barely visible ice/sky blue #ECF7FC (very faint, almost white). Use as selected nav backing and highlighted source passage. Do not use any saturated blue text. Icons and text in neutral gray.
- Absolutely REMOVE ALL BLACK FILLED BUTTONS: "분석 시작하기", "+ 새 기업 분석", "+ 파일 업로드", "기여 분석하기", dialog "삭제" all become high-opacity frosted WHITE pill/rounded rectangle buttons with charcoal-gray labels and fine cool-gray outline. Differentiate primary from secondary through opacity, border and typography, NOT black fill and NOT blue fill.
- Remove lavender/purple from panels, folders, evidence chips, selected nav, header tint and background. Remove beige/butter/yellow/peach from folders and comparison notice. Remove any pink and mint. No multicolor G logo; use neutral gray monochrome G.
- Three company folders all WHITE TRANSLUCENT GLASS. Same neutral palette, different layering/selected outline at most. Not one blue, one purple, one beige.
- Evidence chips translucent white with gray text; only active evidence gets the barely-there sky blue fill. PDF selected quote same extremely pale sky blue. Table, modal, uploader and all statuses unified milky white/gray.
- Background is clean neutral pale gray-white with diffuse WHITE shapes behind the frosted UI. No lavender sky, pink blobs, colorful iridescence or excessive glow.
- Light fine border, feather-soft neutral shadow, restrained glass layering with subtle white rim. No bevels or overly puffy neumorphic plastic.
- Headings and readable text remain dark neutral gray #3A3D40 (not harsh pure black), secondary #73777B. White-only palette refers to SURFACES, do not make text white-on-white or blur text.
- Active reading text stays SHARP. Blur only shapes behind glass, not labels, table content or source text. Keep original document page mostly opaque white for legibility.

Six screenshots: 01 소개·로그인, 02 내 분석 대시보드, 03 기업 브리프·원문 근거, 04 내 자료 관리, 05 개인화 기여 분석, 06 기업·직무 비교. Top DART Insight title in dark gray. Footer "예시 데이터 · 디자인 검토용". Preserve no scores, no rankings, CV differences and JD missing note.
The desired feel is a feather-light, milky-white translucent document workspace, almost monochrome WHITE, with an occasional whisper of very pale SKY BLUE. Entire board and all six screens must reflect this, especially previously black CTA buttons and previously purple highlights. Produce one clean complete portrait overview image, crisp as possible.
```

## 최종 보정 프롬프트

```text
Localized color correction only. Preserve the attached DART Insight six-screen frosted white prototype image exactly: all layouts, labels, white translucent buttons and panels, very pale sky-blue highlights, text contrast and 2x3 portrait composition. In the bottom-right screen 06 기업·직무 비교, the horizontal informational strip beneath company selection reading 서로 다른 CV가 포함되어 있습니다 is still warm beige/peach. Change this ONE STRIP background to neutral translucent WHITE (same frosted white as surrounding controls) with a thin pale cool-gray border and gray text/icon. Remove its beige/cream/yellow/pink tint entirely. Do not introduce any new accent colors, change any content, blur active text or alter other screens. All surfaces must be neutral white transparency layers; the only color anywhere besides neutral gray is the existing extremely pale sky blue. Keep the rest unchanged.
```
