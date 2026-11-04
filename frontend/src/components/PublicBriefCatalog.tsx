import { useEffect, useRef, useState } from 'react'
import { ArrowLeft, ArrowUpRight, FileText } from 'lucide-react'
import { api, ApiError } from '../api'
import type { Session } from '../api'
import { Modal } from './ui'
import ReportMarkdown from './ReportMarkdown'
import ReportEvidence from './ReportEvidence'
import type { Evidence, EvidenceSelection } from './ReportEvidence'
import PdfEvidenceViewer from './PdfEvidenceViewer'

interface CatalogEntry {
  id: string; companyName: string; reportName: string; filedOn: string; sourceUrl: string
}
interface PublicBrief extends CatalogEntry { markdown: string; evidence: Evidence[] }
interface ImportedBrief { briefId: string; companyName: string }

export default function PublicBriefCatalog({ session, onBack, onExpired, onImport }: {
  session: Session; onBack: () => void; onExpired: () => void;
  onImport: (brief: ImportedBrief, contribution: boolean) => void;
}) {
  const [entries, setEntries] = useState<CatalogEntry[] | null>(null)
  const [selectedId, setSelectedId] = useState('')
  const [record, setRecord] = useState<PublicBrief | null>(null)
  const [evidence, setEvidence] = useState<EvidenceSelection | null>(null)
  const [pdf, setPdf] = useState<{ page: number; id?: string } | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [revision, setRevision] = useState(0)
  const evidencePanel = useRef<HTMLElement>(null)

  useEffect(() => {
    const controller = new AbortController()
    const options = { signal: controller.signal }
    const request = selectedId
      ? api<PublicBrief>(`/api/public-briefs/${selectedId}`, options).then((result) => {
        if (!controller.signal.aborted) setRecord(result)
      })
      : api<{ briefs: CatalogEntry[] }>('/api/public-briefs', options).then((result) => {
        if (!controller.signal.aborted) setEntries(result.briefs)
      })
    request.catch((err) => {
      if (controller.signal.aborted) return
      if (err instanceof ApiError && err.status === 401) onExpired()
      else setError(err instanceof Error ? err.message : '공용 브리프를 불러오지 못했습니다.')
    })
    return () => controller.abort()
  }, [selectedId, revision])

  const open = (id: string) => {
    setError(''); setRecord(null); setEvidence(null); setPdf(null); setSelectedId(id)
    window.scrollTo({ top: 0, behavior: 'instant' })
  }

  const save = async (contribution: boolean) => {
    if (!record || busy) return
    setBusy(true); setError('')
    try {
      const imported = await api<ImportedBrief>(`/api/public-briefs/${record.id}/import`, { method: 'POST' }, session.csrfToken)
      onImport(imported, contribution)
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) onExpired()
      else setError(err instanceof Error ? err.message : '브리프를 저장하지 못했습니다.')
    } finally { setBusy(false) }
  }

  const selectEvidence = (selection: EvidenceSelection) => {
    setEvidence(selection)
    if (window.innerWidth <= 900) evidencePanel.current?.scrollIntoView({ block: 'start' })
  }
  const selectId = (id: string) => {
    const item = record?.evidence.find((entry) => entry.id === id)
    if (item) selectEvidence({ ids: [item.id], page: item.page })
  }
  const previewUrl = `/api/public-briefs/${selectedId}/preview`

  return <section className="public-catalog">
    <button className="text-button" disabled={busy} onClick={() => selectedId ? open('') : onBack()}>
      <ArrowLeft size={15} />{selectedId ? '기업 둘러보기' : '내 기업 브리프'}
    </button>
    <div className="research-header">
      <div>
        <h1>{record?.companyName ?? '기업 둘러보기'}</h1>
        <p>{record ? `${record.reportName} · 공시일 ${record.filedOn}` : '공개 사업보고서로 미리 만든 기업 브리프를 읽어보세요.'}</p>
      </div>
      {record && <div className="research-header-actions">
        <button className="button" disabled={busy} onClick={() => save(false)}>내 브리프에 저장</button>
        <button className="button button-primary" disabled={busy} onClick={() => save(true)}>이 브리프로 기여 분석</button>
      </div>}
    </div>
    {error && <div className="notice" role="alert"><p>{error}</p>
      {!record && <button className="text-button" onClick={() => { setError(''); setRevision((value) => value + 1) }}>다시 조회</button>}
    </div>}
    {!selectedId && entries && <section aria-labelledby="featured-companies">
      <div className="section-title"><h2 id="featured-companies">추천 기업</h2></div>
      {entries.length ? <div className="saved-analysis-grid">{entries.map((item) => (
        <button className="saved-analysis" key={item.id} onClick={() => open(item.id)}>
          <FileText size={18} /><h3>{item.companyName}</h3><p>{item.reportName}</p>
          <small><time dateTime={item.filedOn}>공시일 {item.filedOn}</time><span>브리프 읽기 ↗</span></small>
        </button>
      ))}</div> : <div className="empty-state"><h3>아직 공개된 브리프가 없어요</h3><p>검토를 마친 기업 브리프가 이곳에 표시됩니다.</p></div>}
    </section>}
    {!error && (selectedId ? !record : !entries) && <p role="status">공용 브리프를 불러오는 중입니다.</p>}
    {record && <>
      <p className="public-catalog-source">
        <a href={record.sourceUrl} target="_blank" rel="noreferrer">DART 공시 열기 <ArrowUpRight size={14} /></a>
        <a href={previewUrl} target="_blank" rel="noreferrer">원본 PDF 열기 <ArrowUpRight size={14} /></a>
      </p>
      <div className="report-reader public-brief-layout">
        <article className="report-paper">
          <ReportMarkdown kind="brief" text={record.markdown} evidence={record.evidence} selection={evidence} annotations={[]}
            onEvidenceId={selectId} onEvidencePage={(page) => selectEvidence({ page, ids: record.evidence.filter((item) => item.page === page).map((item) => item.id) })} />
        </article>
        <aside ref={evidencePanel} className="public-brief-evidence" aria-label="원문 근거">
          <ReportEvidence evidence={record.evidence} selection={evidence} sourceName={record.reportName} canOpenSource
            onSelect={selectId} onOpenSource={(page, id) => setPdf({ page, id })} />
        </aside>
      </div>
      {pdf && <Modal wide title={`사업보고서 · ${pdf.page}쪽`} onClose={() => setPdf(null)}>
        <PdfEvidenceViewer previewUrl={previewUrl} page={pdf.page} quote={record.evidence.find((item) => item.id === pdf.id)?.quote ?? null}
          onPageChange={(page) => setPdf({ page })} />
      </Modal>}
    </>}
  </section>
}
