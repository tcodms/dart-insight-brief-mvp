"""Conservative presentation rules for the contribution report's summary only."""

import re

LABELS = {'가장 강한 연결': '활용할 경험', '준비할 부분': '보완할 점', '회사 맥락': '지원 방향'}
PHRASES = (
    ('JD의', '직무기술서의'),
    ('CV에', '이력서에'),
    ('가장 가깝게 연결됩니다.', '관련성이 가장 높습니다.'),
    ('보완 준비가 필요합니다.', '추가 준비가 필요합니다.'),
    ('해당 사업장 맥락에서', '해당 사업장에서'),
    ('배우고 적용하고자 연결할 수 있습니다.', '배우고 적용하겠다는 지원 방향을 설명할 수 있습니다.'),
)
BULLET = re.compile(r'^(\s*[-*]\s+(?:\*\*)?)(가장 강한 연결|준비할 부분|회사 맥락)((?:\*\*)?\s*[:：](?:\*\*)?\s*)(.*)$')
PROTECTED = re.compile(r'(`[^`]*`|\[[^\n]*?\]\([^)\n]+\)|"[^"\n]*"|“[^”\n]*”|「[^」\n]*」)')


def polish_contribution_report(markdown: str) -> str:
    summary = False
    fence = None
    output = []
    for line in markdown.splitlines(keepends=True):
        stripped = line.lstrip()
        marker = re.match(r'(`{3,}|~{3,})', stripped)
        if marker:
            current = marker[1][0]
            if fence is None:
                fence = current
            elif fence == current:
                fence = None
            output.append(line)
            continue
        if fence:
            output.append(line)
            continue
        heading = re.match(r'^#{1,2}\s+(.+?)\s*$', line)
        if heading:
            summary = heading[1] == '핵심 요약'
        match = BULLET.fullmatch(line.rstrip('\r\n')) if summary else None
        if match:
            prefix, label, suffix, body = match.groups()
            pieces = PROTECTED.split(body)
            for index in range(0, len(pieces), 2):
                for old, new in PHRASES:
                    pieces[index] = pieces[index].replace(old, new)
            ending = line[len(line.rstrip('\r\n')):]
            line = prefix + LABELS[label] + suffix + ''.join(pieces) + ending
        output.append(line)
    return ''.join(output)
