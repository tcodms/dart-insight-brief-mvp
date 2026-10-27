# UI 프로토타입 v2 — 화이트·블랙·파스텔

작성일: 2026-10-27

이미지: [전체 프로토타입 v2](prototype-v2.png)

## 변경 범위

- v1의 6개 화면과 주요 기능을 유지한다.
- 전체 화이트 바탕, 블랙 주요 버튼, 차콜 텍스트를 사용한다.
- 폴더는 라벤더·파우더 블루·버터 계열 파스텔로 구분한다.
- 원문 하이라이트와 선택 영역에만 은은한 포인트 색을 사용한다.
- 상태·삭제·JD 미등록의 초록·빨강 포인트를 중립 색으로 바꾼다.
- 사용자 첨부 Floe 워크스페이스와 Exams 화면은 스타일 참고이며 해당 서비스의 기능·브랜드는 가져오지 않는다.
- 실제 구현이 아닌 디자인 검토용 이미지이며 작은 본문·예시 데이터·출력 형식은 구현 시 확정한다.

생성 방식: 내장 ImageGen. v1을 편집하고, 남은 빨강 상태 표시 한 곳을 추가 보정했다. 최종 이미지에서 여섯 화면과 블랙 버튼·파스텔 폴더·중립 상태 표시를 시각 확인했다.

## 스타일 변경 프롬프트

```text
Use case: ui-mockup / style-transfer edit.
Edit the FIRST attached image, the DART Insight 6-screen full-service prototype board. Preserve the approved functional content, Korean language, six named screens, two-column three-row overview layout, shared navigation, split analysis/PDF evidence view, folder dashboard, CV/JD management with deletion confirmation, contribution explanation and comparison table. The SECOND and THIRD images are style references ONLY. Do not import their workflow/calendar/education content or brand names.

USER REQUEST: all-white overall UI, black primary buttons, restrained pastel accents. The current bright blue buttons, green success pills, red delete buttons and orange warning strips make it look generic and AI-generated. Replace that visual language comprehensively with a quieter, intentional designer-made document workspace inspired by the attached Floe and Exams references.

STYLE:
- Pure white main surfaces (#FFFFFF), very light warm gray separators (#EAE9E6), charcoal and near-black typography (#171717).
- All primary CTA buttons solid near-black with white lettering. Secondary buttons white with a thin neutral border and charcoal text.
- DART Insight logo/wordmark is BLACK, not blue.
- Minimal one-stroke charcoal icons. No shiny icons, blue icon tiles, gradients, glows or chunky emoji motifs.
- Supporting color ONLY in low-saturation pastel containers: pale lavender (#EDE9F7), pale powder blue (#E7F0F7), soft butter (#FAF1D8), very light peach (#F8EBDD). White remains dominant, roughly 85% of UI. Use color thoughtfully on folder fills, selected workspace background and evidence highlight, not on every small element.
- Dashboard: THREE folder-shaped cards A기업, B기업, C기업 with soft lavender, powder blue and butter fills reminiscent of Floe screenshot; thin subtle outline and black company labels, not vibrant solid blue folders. Quiet flat folders, no 3D render.
- Shared sidebar: off-white or barely lavender-tinted neutral background. Selected item is a soft pastel block or white raised pill, black label/icon. Bottom profile neutral.
- PDF evidence highlight is pale lavender or pale butter, with charcoal type and a small black source marker.
- All status labels such as 분석 완료, 분석 중, 직접 연결, 간접 연결, 자료 부족 use gray text or neutral outlined pills. NO green checkmark circles, NO red failure pills, NO red delete button, NO orange warning strip, NO bright blue tabs or links. Distinguish states by words and icons, not red/green meaning.
- Delete confirmation uses a black "삭제" button and white outlined "취소", clear concise destructive action copy, not red.
- The differing-CV note in comparison is a very subtle butter-tinted informational strip with a black info icon, not an alarm.
- Tabs use charcoal text with a thin black underline. Evidence links can use black underlined text or pale lavender pills with black text.
- Browser chrome, if retained, has tiny NEUTRAL gray circles instead of red/yellow/green dots.
- Remove ambient blue glow and heavy soft shadows. Shadows very small, border based, professional not glossy.
- Comfortable white space, good typographic hierarchy with moderate rather than overly bold headings, consistent margins. Crisp Korean sans-serif. Avoid repetitive nested floating cards where a quiet divider/list suffices.
- Presentation board background is light warm neutral gray, title black, section labels black with tiny neutral numerals.

SCREEN CONTENT TO RETAIN:
01 소개·로그인: headline "기업을 이해하고, 나의 경험을 연결하세요", Google login and black 분석 시작하기.
02 내 분석 대시보드: saved company folders, recent results list, right selected-document panel.
03 기업 브리프·원문 근거: summary/strategy/organization left; original PDF with linked passage highlight right.
04 내 자료 관리: CV and JD tabs, file/version table, document properties, clear delete dialog.
05 개인화 기여 분석: choose company/role/CV/JD, black action; "기업의 활동 → 내 경험 → 가능한 기여"; qualitative relation words, source links, preparation gaps.
06 기업·직무 비교: max three company+role columns, rows 주요 사업 / 직무 요건 / 연결되는 경험 / 가능한 기여 / 준비할 점 / 근거; CV v2/v1 metadata and quiet input-difference note; C기업 JD 미등록 · 판단 불가.
No scores, rankings, testimonials, fabricated performance claims, web collection/search feature or technical implementation labels. All data is illustrative.
Bottom note "예시 데이터 · 디자인 검토용".
This must be a complete, coherent recolored and carefully restyled v2 prototype, NOT merely placing the original blue prototype inside a white border. Recolor every one of the six screens. Maintain legible Korean text and the same useful service information. Make the image as large and sharp as possible, portrait 2:3 overall.
```

## 최종 국소 보정 프롬프트

```text
Make ONE tiny precise color correction to this prototype image. Preserve EVERYTHING else: exact six screenshots, board composition, white backgrounds, black buttons, pastel folder colors, typography, all Korean labels and content. Do not redesign or change layout.
In the BOTTOM RIGHT screenshot "06 기업·직무 비교", in the THIRD company C기업 column, the row "직무 요건" has a pink/red chip reading "JD 미등록 · 판단 불가". Change ONLY that chip to very pale neutral warm gray #F3F2EF background and DARK GRAY #62615D text. Remove any red/pink outline or red text there. The text still reads "JD 미등록 · 판단 불가". All status indicators across the board should be neutral gray, not red or green. Keep the Google brand icon as it is. Do not add red or green UI indicators anywhere. This is a localized color edit, all other parts must remain unchanged.
```
