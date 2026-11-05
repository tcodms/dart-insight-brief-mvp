import { ArrowUpRight, FileText, Quote } from 'lucide-react'

export interface Evidence { id: string; page: number; quote: string; section: string; sourceKind?: 'report' | 'cv' | 'jd'; documentId?: string; sourceName?: string; fieldRef?: string }
export interface EvidenceSelection { ids: string[]; page: number }

export default function ReportEvidence({ evidence, selection, sourceName, canOpenSource, onSelect, onOpenSource, showLinks, onToggleLinks }: {
  evidence: Evidence[]; selection: EvidenceSelection | null; sourceName?: string; canOpenSource: boolean;
  onSelect: (id: string) => void; onOpenSource: (page: number, evidenceId?: string) => void;
  showLinks: boolean; onToggleLinks: () => void;
}) {
  const selected = evidence.filter((item) => selection?.ids.includes(item.id))
  return <div className="report-evidence">
    <h3>{selection ? '선택한 내용의 근거' : '보고서의 원문 근거'}</h3>
    {evidence.length > 0 && <button type="button" className="button evidence-visibility" aria-pressed={showLinks} onClick={onToggleLinks}>본문 근거 표시</button>}
    {!selection && <div className="evidence-empty"><Quote size={22} strokeWidth={1.5} /><p>{evidence.length ? '본문 근거 표시를 켜거나 아래 목록에서 원문을 확인하세요.' : '이 보고서에 연결된 인용문이 없습니다.'}</p></div>}
    {selection && !selected.length && <div className="evidence-empty"><p>{selection.page}쪽에 저장된 인용문이 없습니다.</p>{canOpenSource && <button className="text-button" onClick={() => onOpenSource(selection.page)}>PDF {selection.page}쪽 확인 <ArrowUpRight size={14} /></button>}</div>}
    {selected.length > 1 && <p className="evidence-description">같은 쪽의 근거 {selected.length}개입니다. 확인할 인용문을 선택해 주세요.</p>}
    {selected.map((item) => <article className="evidence-quote-card" key={item.id}>
      <div className="evidence-card-heading">
        <FileText size={16} strokeWidth={1.5} />
        <strong title={item.sourceName || sourceName}>{item.sourceName || sourceName || '사업보고서'}</strong>
        <span className="evidence-page">{item.page}쪽</span>
      </div>
      {item.section && <p className="evidence-section">{item.section}</p>}
      <blockquote>{item.quote}</blockquote>
      <div className="evidence-card-footer"><span>저장된 원문 인용</span>{canOpenSource && <button className="text-button" onClick={() => onOpenSource(item.page, item.id)}>원문 열기 <ArrowUpRight size={14} /></button>}</div>
    </article>)}
    {evidence.length > 0 && <details className="evidence-index"><summary>전체 근거 {evidence.length}개</summary><div>{evidence.map((item) => <button key={item.id} aria-pressed={selection?.ids.includes(item.id) ?? false} onClick={() => onSelect(item.id)}><strong>{item.sourceKind === 'cv' ? 'CV' : item.sourceKind === 'jd' ? 'JD' : '사업보고서'} {item.page}쪽</strong><span>{item.quote}</span></button>)}</div></details>}
  </div>
}
