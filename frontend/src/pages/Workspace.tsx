import { ArrowDown, ArrowRight, ArrowUpRight, FileText, FolderOpen, LayoutGrid, List, Plus, Search } from 'lucide-react'
import { useMemo, useState } from 'react'
import type { Company, Material } from '../types'
import { Status } from '../components/ui'

export default function Workspace({ companies, materials, selectedId, onSelect, onOpen, onUpload, onCompare }: {
  companies: Company[]; materials: Material[]; selectedId: string; onSelect: (id: string) => void;
  onOpen: (company: Company) => void; onUpload: () => void; onCompare: () => void;
}) {
  const [query, setQuery] = useState('')
  const [view, setView] = useState<'grid' | 'list'>('grid')
  const [newest, setNewest] = useState(true)
  const filtered = useMemo(() => companies.filter((item) => `${item.name} ${item.industry} ${item.role}`.toLowerCase().includes(query.toLowerCase())).sort((a, b) => newest ? b.updated.localeCompare(a.updated) : a.name.localeCompare(b.name)), [companies, query, newest])
  const selected = companies.find((item) => item.id === selectedId) ?? companies[0]
  return <div className="workspace-page page-wrap">
    <div className="page-heading"><div><span className="eyebrow">YOUR RESEARCH, ORGANIZED</span><h1>내 분석<span className="heading-count">{companies.length.toString().padStart(2, '0')}</span></h1><p>차곡차곡 모은 기업의 이야기, 나의 다음 선택으로.</p></div><button className="button button-primary" onClick={onUpload}><Plus size={16} />새 기업 분석</button></div>
    <div className="workspace-layout"><div className="workspace-main">
      <div className="toolbar"><label className="search-field"><Search size={16} /><input aria-label="저장된 기업·직무 검색" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="저장된 기업·직무 찾기" /><kbd>⌕</kbd></label><button className="button button-quiet sort-button" onClick={() => setNewest(!newest)}><ArrowDown size={13} />{newest ? '최근 수정순' : '기업 이름순'}</button><div className="view-switch"><button aria-label="폴더 보기" aria-pressed={view === 'grid'} onClick={() => setView('grid')}><LayoutGrid size={15} /></button><button aria-label="목록 보기" aria-pressed={view === 'list'} onClick={() => setView('list')}><List size={16} /></button></div></div>
      <div className="section-title"><h2>기업 폴더</h2><span>{filtered.length}개 기업</span></div>
      {filtered.length === 0 ? <div className="empty-state"><Search size={25} /><h3>검색 결과가 없어요</h3><p>다른 기업명이나 직무로 찾아보세요.</p><button className="button" onClick={() => setQuery('')}>검색 초기화</button></div> : <div className={`company-folders ${view === 'list' ? 'folders-list' : ''}`}>{filtered.map((company) => <button className={`folder-card ${selected.id === company.id ? 'folder-selected' : ''}`} key={company.id} onClick={() => onSelect(company.id)} onDoubleClick={() => onOpen(company)} aria-pressed={selected.id === company.id}>
        <div className="folder-art"><span className="folder-paper paper-back" /><span className="folder-paper paper-front"><FileText size={16} /></span><span className="folder-face"><FolderOpen size={19} strokeWidth={1.1} /></span></div><div className="folder-info"><span className="folder-caption">2025 사업보고서</span><strong>{company.name}</strong><span className="folder-industry">{company.industry}</span><div className="folder-bottom"><Status /><span className="folder-arrow"><ArrowUpRight size={15} /></span></div></div>
      </button>)}</div>}
      <div className="section-title recent-heading"><h2>최근 분석 이력</h2><span>기업 · 지원 직무</span></div>
      <div className="table-scroll"><table className="data-table"><thead><tr><th>기업명</th><th>지원 직무</th><th>사용한 CV</th><th>상태</th><th>최근 수정일</th><th><span className="sr-only">열기</span></th></tr></thead><tbody>{filtered.map((company) => <tr key={company.id} className={selected.id === company.id ? 'row-selected' : ''}><td><button className="table-company" onClick={() => onOpen(company)}><span className="company-letter">{company.initial}</span>{company.name}</button></td><td>{company.role}</td><td>{materials.find((item) => item.id === company.cvId)?.version ?? 'CV 삭제됨'}</td><td><Status>{company.cvId ? '분석 완료' : '기업 브리프'}</Status></td><td className="muted">{company.updated}</td><td><button className="icon-button" aria-label={`${company.name} 결과 열기`} onClick={() => onOpen(company)}><ArrowUpRight size={15} /></button></td></tr>)}</tbody></table></div>
      <button className="compare-prompt" onClick={onCompare}><span>기업마다 다른 나의 가능성이 궁금하다면</span><strong>기업·직무 비교하기 <ArrowRight size={16} /></strong></button>
    </div><aside className="detail-panel"><div className="detail-panel-title">선택한 분석<span className="eyebrow">DETAILS</span></div><div className="selected-company-mark">{selected.initial}<span>↗</span></div><h2>{selected.name}</h2><p className="muted">{selected.industry}</p><div className="detail-section"><span>원본 문서</span><p><FileText size={14} />{selected.reportName}</p></div><div className="detail-section"><span>보고 기간</span><p>{selected.period}</p></div><div className="detail-section"><span>지원 직무</span><p>{selected.role}</p></div><div className="detail-section"><span>등록된 근거</span><p>{selected.evidence.length}개 핵심 근거 · 샘플</p></div><button className="button full-width" onClick={() => onOpen(selected)}>분석 결과 열기<ArrowRight size={15} /></button><p className="detail-disclaimer">예시 기업과 문서로 구성한<br />화면 미리보기입니다.</p></aside></div>
  </div>
}
