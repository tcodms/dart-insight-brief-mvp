import { Check, Download, FileText, Info, Plus, X } from 'lucide-react'
import { useState } from 'react'
import type { Company, Material } from '../types'
import { hasDifferentCvs, toggleComparison } from '../domain'
import { downloadJson, SourceButton } from '../components/ui'

export default function Compare({ companies, materials, onEvidence }: { companies: Company[]; materials: Material[]; onEvidence: (company: Company, id?: string) => void }) {
  const available = companies.filter((company) => materials.some((material) => material.id === company.cvId))
  const [ids, setIds] = useState<string[]>(companies.map((company) => company.id).slice(0, 3))
  const [pickerOpen, setPickerOpen] = useState(false)
  const selected = available.filter((company) => ids.includes(company.id))
  const rows: { label: string; render: (company: Company) => string }[] = [
    { label: '주요 사업', render: (company) => company.business },
    { label: '직무 요건', render: (company) => company.requirements ?? 'JD 미등록 · 판단 불가' },
    { label: '연결되는 경험', render: (company) => company.experience },
    { label: '연결 판단', render: (company) => `${company.connection}\n${company.reason}` },
    { label: '가능한 기여', render: (company) => company.contribution },
    { label: '준비할 점', render: (company) => company.gap },
  ]
  return <div className="page-wrap compare-page"><div className="page-heading"><div><span className="eyebrow">DIFFERENT COMPANIES, YOUR POSSIBILITIES</span><h1>기업·직무 비교</h1><p>기업마다 달라지는 나의 연결 지점과 준비할 점을 살펴보세요.</p></div><button className="button" disabled={selected.length < 2} onClick={() => downloadJson('기업직무비교_샘플.json', { demo: true, differentCvs: hasDifferentCvs(selected), targets: selected })}><Download size={15} />비교 결과 다운로드</button></div>
    <div className="comparison-picker"><div className="selected-targets">{selected.map((company) => <span className="target-chip" key={company.id}><span className="mini-company">{company.initial}</span><span>{company.name}<small>{company.role}</small></span><button className="icon-button" aria-label={`${company.name} 비교에서 제외`} onClick={() => setIds(ids.filter((id) => id !== company.id))}><X size={12} /></button></span>)}<div className="picker-anchor"><button className="button button-quiet" aria-expanded={pickerOpen} onClick={() => setPickerOpen(!pickerOpen)}><Plus size={14} />비교 대상 선택</button>{pickerOpen && <div className="target-dropdown">{available.length ? available.map((company) => <button key={company.id} onClick={() => setIds(toggleComparison(ids.filter((id) => available.some((item) => item.id === id)), company.id))} disabled={selected.length === 3 && !ids.includes(company.id)}><span className={`checkbox ${ids.includes(company.id) ? 'checked' : ''}`}>{ids.includes(company.id) && <Check size={11} />}</span><span>{company.name}<small>{company.role}</small></span></button>) : <p>CV가 연결된 분석이 없습니다.</p>}<button className="picker-done" onClick={() => setPickerOpen(false)}>선택 완료</button></div>}</div></div><span className="selection-count">{selected.length}<span>/ 3</span></span></div>
    {hasDifferentCvs(selected) && <div className="notice"><Info size={16} /><p><strong>서로 다른 CV가 포함되어 있어요.</strong> 입력 경험이 달라 동일 조건의 비교가 아닙니다. 각 열의 CV 버전을 확인하세요.</p></div>}
    {selected.length < 2 ? <div className="empty-state compare-empty"><FileText size={30} strokeWidth={1.1} /><h2>비교할 대상을 2개 이상 선택해 주세요</h2><p>기업 브리프는 CV를 삭제해도 유지됩니다.<br />개인화 비교에는 CV가 연결된 분석이 필요해요.</p><button className="button" onClick={() => setPickerOpen(true)}><Plus size={14} />비교 대상 선택</button></div> : <div className="comparison-table-scroll"><table className="comparison-table"><thead><tr><th><span className="eyebrow">A CLOSER LOOK</span><strong>무엇이 다른가요?</strong></th>{selected.map((company) => <th key={company.id}><span className="company-letter large">{company.initial}</span><h2>{company.name}</h2><span className="compare-role">{company.role}</span><span className="cv-version">사용 CV · {materials.find((item) => item.id === company.cvId)?.version}</span></th>)}</tr></thead><tbody>{rows.map((row) => <tr key={row.label}><th scope="row">{row.label}</th>{selected.map((company) => <td key={company.id} className={row.label === '직무 요건' && !company.jdId ? 'missing-data' : ''}>{row.render(company)}</td>)}</tr>)}<tr className="comparison-evidence-row"><th scope="row">기업 원문 근거</th>{selected.map((company) => <td key={company.id}><SourceButton onClick={() => onEvidence(company, company.evidence[0].id)}>원문 보기 · {company.evidence.length}개</SourceButton></td>)}</tr></tbody></table></div>}
    <div className="comparison-footnote"><span>순위가 아닌, 연결의 차이.</span><p>연결 판단은 자료에서 확인되는 관계를 설명합니다. 기업의 우열이나 합격 가능성을 뜻하지 않습니다.</p></div>
  </div>
}
