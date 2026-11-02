import { ArrowUpRight, FileText, Quote } from 'lucide-react'

export interface Evidence { id: string; page: number; quote: string; section: string }
export interface EvidenceSelection { ids: string[]; page: number }

export default function ReportEvidence({ evidence, selection, sourceName, canOpenSource, onSelect, onOpenSource }: {
  evidence: Evidence[]; selection: EvidenceSelection | null; sourceName?: string; canOpenSource: boolean;
  onSelect: (id: string) => void; onOpenSource: (page: number, evidenceId?: string) => void;
}) {
  const selected = evidence.filter((item) => selection?.ids.includes(item.id))
  return <div className="report-evidence">
    <h3>{selection ? '선택한 내용의 근거' : '보고서의 원문 근거'}</h3>
    <p className="evidence-description">본문의 밑줄 표시나 근거를 누르면 저장된 인용문을 확인할 수 있어요.</p>
    {!selection && <div className="evidence-empty"><Quote size={24} strokeWidth={1.3} /><p>{evidence.length ? '확인하고 싶은 기업 사실을 눌러보세요.' : '이 보고서에 연결된 인용문이 없습니다.'}</p></div>}
    {selection && !selected.length && <div className="evidence-empty"><p>{selection.page}쪽에 저장된 인용문이 없습니다.</p>{canOpenSource && <button className="text-button" onClick={() => onOpenSource(selection.page)}>PDF {selection.page}쪽 확인 <ArrowUpRight size={14} /></button>}</div>}
    {selected.length > 1 && <p className="evidence-description">같은 쪽의 근거 {selected.length}개입니다. 확인할 인용문을 선택해 주세요.</p>}
    {selected.map((item) => <article className="evidence-quote-card" key={item.id}>
      <div className="evidence-card-heading"><FileText size={18} strokeWidth={1.5} /><div><strong>사업보고서 · {item.page}쪽</strong>{sourceName && <small title={sourceName}>{sourceName}</small>}</div></div>
      {item.section && <p className="evidence-section">{item.section}</p>}
      <blockquote>{item.quote}</blockquote>
      <div className="evidence-card-footer"><span>저장된 원문 인용</span>{canOpenSource && <button className="text-button" onClick={() => onOpenSource(item.page, item.id)}>원문 열기 <ArrowUpRight size={14} /></button>}</div>
    </article>)}
    {evidence.length > 0 && <details className="evidence-index"><summary>전체 근거 {evidence.length}개</summary><div>{evidence.map((item) => <button key={item.id} aria-pressed={selection?.ids.includes(item.id) ?? false} onClick={() => onSelect(item.id)}><strong>사업보고서 {item.page}쪽</strong><span>{item.quote}</span></button>)}</div></details>}
  </div>
}
