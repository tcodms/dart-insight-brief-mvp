import { useEffect, useRef, useState } from 'react'
import { ArrowLeft, ArrowUpRight, FileText } from 'lucide-react'
import { api, ApiError } from '../api'
import type { Session } from '../api'
import { Modal } from './ui'
import ReportMarkdown from './ReportMarkdown'
import ReportEvidence from './ReportEvidence'
import type { Evidence, EvidenceSelection } from './ReportEvidence'
import PdfEvidenceViewer from './PdfEvidenceViewer'
import ListToolbar, { sortList } from './ListToolbar'
import type { ListOrder } from './ListToolbar'

interface CatalogEntry {
  id: string; companyName: string; reportName: string; filedOn: string; sourceUrl: string
}
interface PublicBrief extends CatalogEntry { markdown: string; evidence: Evidence[] }
interface ImportedBrief { briefId: string; companyName: string }

export default function PublicBriefCatalog({ session, onExpired, onImport }: {
  session: Session; onExpired: () => void;
  onImport: (brief: ImportedBrief, contribution: boolean) => void;
}) {
  const [entries, setEntries] = useState<CatalogEntry[] | null>(null)
  const [search, setSearch] = useState('')
  const [order, setOrder] = useState<ListOrder>('newest')
  const [selectedId, setSelectedId] = useState('')
  const [record, setRecord] = useState<PublicBrief | null>(null)
  const [evidence, setEvidence] = useState<EvidenceSelection | null>(null)
  const [showEvidenceLinks, setShowEvidenceLinks] = useState(false)
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
    setShowEvidenceLinks(false)
    window.scrollTo({ top: 0, behavior: 'instant' })
  }

  const save = async (id: string, contribution: boolean) => {
    if (busy) return
    setBusy(true); setError('')
    try {
      const imported = await api<ImportedBrief>(`/api/public-briefs/${id}/import`, { method: 'POST' }, session.csrfToken)
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
  const query = search.trim().normalize('NFKC').toLocaleLowerCase()
  const matchingEntries = sortList((entries ?? []).filter((item) => {
    const text = `${item.companyName} ${item.reportName}`.normalize('NFKC').toLocaleLowerCase()
    return query.split(/\s+/).every((term) => text.includes(term))
  }), order, (item) => item.companyName, (item) => item.filedOn)

  return <section className="public-catalog">
    {selectedId && <button className="text-button" disabled={busy} onClick={() => open('')}>
      <ArrowLeft size={15} />기업 목록으로 돌아가기
    </button>}
    <div className="research-header">
      <div>
        <h1>{record?.companyName ?? '기업 둘러보기'}</h1>
        <p>{record ? `${record.reportName} · 공시일 ${record.filedOn}` : '공개 사업보고서로 미리 만든 기업 브리프를 읽어보세요.'}</p>
      </div>
      {record && <div className="research-header-actions">
        <button className="button" disabled={busy} onClick={() => save(record.id, false)}>내 기업 분석으로 가져오기</button>
        <button className="button button-primary" disabled={busy} onClick={() => save(record.id, true)}>이 브리프로 기여 분석</button>
      </div>}
    </div>
    {error && <div className="notice" role="alert"><p>{error}</p>
      {!record && <button className="text-button" onClick={() => { setError(''); setRevision((value) => value + 1) }}>다시 조회</button>}
    </div>}
    {!selectedId && entries && <section aria-labelledby="featured-companies">
      <h2 id="featured-companies" className="sr-only">등록된 기업</h2>
      <ListToolbar query={search} onSearch={setSearch} order={order} onOrder={setOrder}
        placeholder="기업명 또는 사업보고서 제목 검색" summary={`${matchingEntries.length}개 기업`} nameLabel="기업명" />
      {matchingEntries.length ? <div className="saved-analysis-grid catalog-grid">{matchingEntries.map((item) => (
        <article className="saved-analysis brief-card" key={item.id}>
          <div className="brief-card-icon"><FileText size={17} /></div>
          <h3>{item.companyName}</h3><p>{item.reportName}</p>
          <small><time dateTime={item.filedOn}>공시일 {item.filedOn}</time></small>
          <div className="brief-card-actions">
            <button className="button" disabled={busy} onClick={() => open(item.id)} aria-label={`${item.companyName} 브리프 읽기`}>브리프 읽기</button>
            <button className="button" disabled={busy} onClick={() => save(item.id, false)} aria-label={`${item.companyName} 브리프 가져오기`}>가져오기</button>
          </div>
        </article>
      ))}</div> : <div className="empty-state">
        <h3>{entries.length ? '검색 결과가 없어요' : '아직 공개된 브리프가 없어요'}</h3>
        <p>{entries.length ? '다른 기업명이나 보고서 제목으로 검색해 보세요.' : '검토를 마친 기업 브리프가 이곳에 표시됩니다.'}</p>
        {entries.length > 0 && <button className="button" onClick={() => setSearch('')}>전체 기업 보기</button>}
      </div>}
    </section>}
    {!error && (selectedId ? !record : !entries) && <p role="status">공용 브리프를 불러오는 중입니다.</p>}
    {record && <>
      <p className="public-catalog-source">
        <a href={record.sourceUrl} target="_blank" rel="noreferrer">DART 공시 열기 <ArrowUpRight size={14} /></a>
        <a href={previewUrl} target="_blank" rel="noreferrer">원본 PDF 열기 <ArrowUpRight size={14} /></a>
      </p>
      <div className="report-reader public-brief-layout" data-show-evidence={showEvidenceLinks || undefined}>
        <article className="report-paper">
          <ReportMarkdown kind="brief" text={record.markdown} evidence={record.evidence} selection={evidence} annotations={[]}
            onEvidenceId={selectId} onEvidencePage={(page) => selectEvidence({ page, ids: record.evidence.filter((item) => item.page === page).map((item) => item.id) })} />
        </article>
        <aside ref={evidencePanel} className="public-brief-evidence" aria-label="원문 근거">
          <ReportEvidence evidence={record.evidence} selection={evidence} sourceName={record.reportName} canOpenSource
            showLinks={showEvidenceLinks} onToggleLinks={() => setShowEvidenceLinks(!showEvidenceLinks)}
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
