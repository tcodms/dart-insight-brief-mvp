from backend.app.personal_evidence import candidate_evidence


def test_candidate_references_keep_document_identity_and_skip_unverified_pages():
    extracts = {'cv': {'hands_on_skills': ['무균 조작', '희석'], 'source_page_references': [
        'hands_on_skills[1] | 원본 PDF 1쪽 | 무균 조작',
        'hands_on_skills[2] | 원본 일부: 희석',
        'hands_on_skills[3] | 원본 PDF 1쪽 | 없는 항목',
    ]}, 'jd': {'key_responsibilities': ['시험', '관리'], 'source_page_references': [
        'key_responsibilities[1] | 원본 PDF 1쪽 | 시험',
        'key_responsibilities[2] | 원본 PDF 3쪽 | 관리',
    ]}}
    docs = {'cv': {'id': 'cv-document', 'original_name': '이력서.pdf', 'pages': 1},
            'jd': {'id': 'jd-document', 'original_name': '직무.pdf', 'pages': 1}}
    result = candidate_evidence(extracts, docs)
    assert [item['id'] for item in result] == ['CV-hands_on_skills-1', 'JD-key_responsibilities-1']
    assert result[0]['documentId'] == 'cv-document'
    assert result[1]['documentId'] == 'jd-document'
    assert result[0]['fieldRef'] == 'hands_on_skills[1]'
    assert result[0]['sourceKind'] == 'cv'
    assert candidate_evidence(extracts, {}) == []


def test_conflicting_duplicate_reference_does_not_choose_a_page():
    extracts = {'cv': {'summary': '소개', 'source_page_references': [
        'summary | 원본 PDF 1쪽 | 소개', 'summary | 원본 PDF 2쪽 | 소개',
    ]}}
    assert candidate_evidence(extracts, {'cv': {'id': 'cv', 'original_name': 'CV.pdf', 'pages': 2}}) == []
