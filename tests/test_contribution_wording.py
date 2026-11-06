from pipeline.contribution_wording import polish_contribution_report


def test_agent_response_parser_applies_wording_after_json_decoding():
    import json
    from pipeline.contribution_service import _report_text
    raw = '# 보고서\n\n## 핵심 요약\n- **가장 강한 연결:** JD의 시험 업무와 가장 가깝게 연결됩니다.【†3】'
    shown = _report_text(json.dumps(raw, ensure_ascii=False))
    assert '**활용할 경험:** 직무기술서의 시험 업무와 관련성이 가장 높습니다.' in shown
    assert '【†3】' not in shown


def test_summary_labels_and_stock_phrases_change_without_rewriting_facts():
    raw = '''# 녹십자 취업용 개인 경험 연결

## 핵심 요약

- **가장 강한 연결:** 실습 경험은 JD의 시험 업무와 가장 가깝게 연결됩니다.
- **준비할 부분:** QMS·Veeva·LIMS와 GMP 제조소 경험은 CV에 미경험으로 명시되어 있어 보완 준비가 필요합니다.
- **회사 맥락:** 오창공장 가동률 68%를 확인했고 [B01-E071] 원문 45쪽을 참고합니다.

## 근거 확인

- **CV:** hands_on_skills[7] · 원본 PDF 1쪽
- **기업 fact:** B01-E071 · 68% · 원문 45쪽
'''
    cleaned = polish_contribution_report(raw)
    assert '- **활용할 경험:** 실습 경험은 직무기술서의 시험 업무와 관련성이 가장 높습니다.' in cleaned
    assert '- **보완할 점:** QMS·Veeva·LIMS와 GMP 제조소 경험은 이력서에 미경험으로 명시되어 있어 추가 준비가 필요합니다.' in cleaned
    assert '- **지원 방향:** 오창공장 가동률 68%를 확인했고 [B01-E071] 원문 45쪽을 참고합니다.' in cleaned
    assert cleaned.split('## 근거 확인')[1] == raw.split('## 근거 확인')[1]
    assert polish_contribution_report(cleaned) == cleaned


def test_code_quotes_links_and_negations_are_not_rewritten():
    raw = '''## 핵심 요약
- **준비할 부분:** GMP 경험 없음. Python은 학습만 확인되며 실무 충족으로 단정하지 않습니다. `CV에` "JD의" [참고](https://example.test/CV에)

```
- **회사 맥락:** JD의 원문 문구
```

## 자기소개서·면접 활용
- **가장 강한 연결:** CV에 있던 원문입니다.
'''
    cleaned = polish_contribution_report(raw)
    assert 'GMP 경험 없음. Python은 학습만 확인되며 실무 충족으로 단정하지 않습니다.' in cleaned
    assert '`CV에` "JD의" [참고](https://example.test/CV에)' in cleaned
    assert '```\n- **회사 맥락:** JD의 원문 문구\n```' in cleaned
    assert cleaned.split('## 자기소개서·면접 활용')[1] == raw.split('## 자기소개서·면접 활용')[1]
    assert polish_contribution_report('원문에 핵심 요약이 없습니다.') == '원문에 핵심 요약이 없습니다.'
