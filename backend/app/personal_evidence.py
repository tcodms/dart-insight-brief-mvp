"""Resolve saved candidate citations only against the analysis's owned documents."""

import re

REFERENCE = re.compile(r'^([a-z_]+(?:\[[1-9]\d*\])?)\s*\|\s*원본\s*PDF\s*(\d+)쪽\s*\|\s*(.+)$')


def candidate_evidence(extracts, documents):
    result = []
    if not isinstance(extracts, dict):
        return result
    for kind in ('cv', 'jd'):
        data, doc = extracts.get(kind), documents.get(kind)
        if not isinstance(data, dict) or not doc:
            continue
        refs = data.get('source_page_references', [])
        if not isinstance(refs, list):
            continue
        found, ambiguous = {}, set()
        for raw in refs:
            match = REFERENCE.fullmatch(raw.strip()) if isinstance(raw, str) else None
            if not match:
                continue
            field, page, quote = match.groups()
            name = field.split('[')[0]
            value = data.get(name)
            index = re.search(r'\[(\d+)\]', field)
            if index:
                if not isinstance(value, list) or int(index[1]) > len(value) or not value[int(index[1]) - 1]:
                    continue
            elif not isinstance(value, str) or not value.strip():
                continue
            page = int(page)
            if not 1 <= page <= doc['pages'] or not quote.strip():
                continue
            item = {'id': f'{kind.upper()}-{field.replace("[", "-").replace("]", "")}',
                    'page': page, 'quote': quote.strip(), 'section': field,
                    'fieldRef': field, 'sourceKind': kind, 'documentId': doc['id'],
                    'sourceName': doc['original_name']}
            if field in found and found[field] != item:
                ambiguous.add(field)
            found[field] = item
        result.extend(item for field, item in found.items() if field not in ambiguous)
    return result
