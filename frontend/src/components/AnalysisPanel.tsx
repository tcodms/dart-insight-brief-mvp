import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import type { ReactNode } from 'react'
import { ArrowLeft, ChevronRight, Download, FileText, LoaderCircle, Play, Plus, RefreshCw, Trash2, Upload } from 'lucide-react'
import ReportMarkdown from './ReportMarkdown'
import type { EvidenceSelection } from './ReportEvidence'
import { api, ApiError } from '../api'
import type { Session } from '../api'
import { Modal } from './ui'
import PdfEvidenceViewer from './PdfEvidenceViewer'
import ReportReader from './ReportReader'
import CompanyFolderArt from './CompanyFolderArt'

interface InputDocument { id: string; name: string; kind: 'report' | 'cv' | 'jd'; version: string }
interface BriefRecord { id: string; companyName: string; reportName: string; reportDocumentId: string; createdAt: string }
interface PersonalRecord { id: string; companyName: string; targetRole: string; cvDocumentId: string; jdDocumentId: string; cvVersion: string; createdAt: string }
interface Job { id: string; jobType: 'brief' | 'personal'; status: string; stage: string; resultId: string | null; error: string | null }
interface Capabilities { briefConfigured: boolean; personalConfigured: boolean; personalRequiresJd: boolean }
interface ResultRecord {
  id: string; kind: 'brief' | 'personal'; reportDocumentId: string | null; createdAt?: string;
  result: { markdown: string }; evidence: { id: string; page: number; quote: string; section: string }[]
}
type Selection = { kind: 'brief' | 'personal'; id: string }

function readLocation(): { company: string; selection: Selection | null } {
  const params = new URLSearchParams(window.location.search)
  const kind = params.get('kind'), id = params.get('result')
  return { company: params.get('company') ?? '', selection: id && (kind === 'brief' || kind === 'personal') ? { kind, id } : null }
}

export default function AnalysisPanel({ documents, session, onExpired, onUpload }: {
  documents: InputDocument[]; session: Session; onExpired: () => void; onUpload?: () => void;
}) {
  const heading = useRef<HTMLHeadingElement>(null)
  const [revision, setRevision] = useState(0)
  const [jobs, setJobs] = useState<Job[]>([])
  const [briefs, setBriefs] = useState<BriefRecord[]>([])
  const [personal, setPersonal] = useState<PersonalRecord[]>([])
  const [caps, setCaps] = useState<Capabilities | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [starting, setStarting] = useState(false)
  const [reportId, setReportId] = useState('')
  const [briefId, setBriefId] = useState('')
  const [cvId, setCvId] = useState('')
  const [jdId, setJdId] = useState('')
  const [selection, setSelection] = useState<Selection | null>(() => readLocation().selection)
  const [activeCompany, setActiveCompany] = useState(() => readLocation().company)
  const [composer, setComposer] = useState<'brief' | 'personal' | null>(null)
  const [deleting, setDeleting] = useState<Selection | null>(null)
  const [deleteImpact, setDeleteImpact] = useState<number | null>(null)
  const [deleteBusy, setDeleteBusy] = useState(false)
  const documentKey = documents.map((document) => document.id).join(',')
  const activeJob = jobs.find((job) => job.status === 'queued' || job.status === 'running')
  const validDocument = (id: string, kind: string) => documents.some((document) => document.id === id && document.kind === kind)
  const groups = new Map<string, { name: string; briefs: BriefRecord[]; personal: PersonalRecord[]; latest: string }>()
  for (const item of [...briefs, ...personal]) {
    const key = item.companyName.trim().replace(/\s+/g, ' ')
    const group = groups.get(key) ?? { name: key, briefs: [], personal: [], latest: item.createdAt }
    if ('reportName' in item) group.briefs.push(item)
    else group.personal.push(item)
    if (item.createdAt > group.latest) group.latest = item.createdAt
    groups.set(key, group)
  }
  const companyFolders = [...groups.values()].sort((a, b) => b.latest.localeCompare(a.latest))
  const selectedCompany = (selection ? companyFolders.find((group) => (selection.kind === 'brief' ? group.briefs : group.personal).some((item) => item.id === selection.id)) : undefined) ?? groups.get(activeCompany)
  const companyJds = (group: (typeof companyFolders)[number]) => {
    const ids = new Set(group.personal.map((result) => result.jdDocumentId).filter(Boolean))
    return documents.filter((document) => document.kind === 'jd' && ids.has(document.id))
  }

  useEffect(() => { if (!loading) heading.current?.focus({ preventScroll: true }) }, [activeCompany, selection?.id, loading])

  const openLocation = (company: string, result: Selection | null = null) => {
    setActiveCompany(company); setSelection(result)
    const url = new URL(window.location.href)
    url.search = ''
    url.searchParams.set('view', 'workspace')
    if (company) url.searchParams.set('company', company)
    if (result) { url.searchParams.set('kind', result.kind); url.searchParams.set('result', result.id) }
    window.history.pushState({}, '', url)
    window.scrollTo({ top: 0, behavior: 'instant' })
  }
  useEffect(() => {
    const changed = () => { const location = readLocation(); setActiveCompany(location.company); setSelection(location.selection) }
    window.addEventListener('popstate', changed)
    return () => window.removeEventListener('popstate', changed)
  }, [])
  const openComposer = () => {
    setBriefId(selectedCompany?.briefs[0]?.id ?? '')
    setError(''); setComposer('brief')
  }

  useEffect(() => {
    setDeleteImpact(null)
    if (!deleting) return
    api<{ relatedPersonalAnalyses: number }>(`/api/analyses/${deleting.kind}/${deleting.id}/impact`)
      .then((result) => setDeleteImpact(result.relatedPersonalAnalyses))
      .catch((err) => setError(err instanceof Error ? err.message : '삭제 영향을 확인하지 못했습니다.'))
  }, [deleting])

  const removeResult = async () => {
    if (!deleting || deleteImpact === null) return
    setDeleteBusy(true)
    try {
      await api(`/api/analyses/${deleting.kind}/${deleting.id}`, { method: 'DELETE' }, session.csrfToken)
      openLocation(activeCompany); setDeleting(null); setComposer(null); setRevision((value) => value + 1)
    } catch (err) {
      setError(err instanceof Error ? err.message : '분석 결과를 삭제하지 못했습니다.')
      if (err instanceof ApiError && err.status === 401) onExpired()
    } finally { setDeleteBusy(false) }
  }

  useEffect(() => {
    let active = true
    let timer: ReturnType<typeof setTimeout> | undefined
    const controller = new AbortController()
    const options = { signal: controller.signal }
    Promise.all([api<{ jobs: Job[] }>('/api/jobs', options), api<{ briefs: BriefRecord[]; personal: PersonalRecord[] }>('/api/analyses', options), api<Capabilities>('/api/analysis/capabilities', options)])
      .then(([status, results, config]) => {
        if (!active) return
        setJobs(status.jobs); setBriefs(results.briefs); setPersonal(results.personal); setCaps(config)
        setSelection((selected) => selected && !(selected.kind === 'brief' ? results.briefs : results.personal).some((result) => result.id === selected.id) ? null : selected)
        if (status.jobs.some((job) => job.status === 'queued' || job.status === 'running')) timer = setTimeout(() => setRevision((value) => value + 1), 2500)
      }).catch((err) => {
        if (!active) return
        setError(err instanceof Error ? err.message : '분석 상태를 확인하지 못했습니다.')
        if (err instanceof ApiError && err.status === 401) onExpired()
      }).finally(() => { if (active) setLoading(false) })
    return () => { active = false; controller.abort(); clearTimeout(timer) }
  }, [revision, documentKey])

  const start = async (kind: 'brief' | 'personal') => {
    setStarting(true); setError('')
    const input = kind === 'brief' ? { jobType: kind, reportDocumentId: reportId } : { jobType: kind, briefId, cvDocumentId: cvId, jdDocumentId: jdId }
    try {
      const job = await api<Job>('/api/jobs', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(input) }, session.csrfToken)
      setJobs((items) => [job, ...items.filter((item) => item.id !== job.id)])
      setComposer(null); setRevision((value) => value + 1)
    } catch (err) {
      setError(err instanceof Error ? err.message : '분석을 시작하지 못했습니다.')
      if (err instanceof ApiError && err.status === 401) onExpired()
    } finally { setStarting(false) }
  }

  if (loading) return <section className="empty-state" role="status"><LoaderCircle className="spin" /><p>분석 이력을 불러오는 중입니다.</p></section>
  return <section className="live-analysis">
    {error && <div className="notice" role="alert"><p>{error}</p><button className="text-button" onClick={() => { setError(''); setRevision((value) => value + 1) }}><RefreshCw size={14} />다시 조회</button></div>}
    <ReportNavigation active={Boolean(selection)}><div className={`research-header ${selection ? 'research-header-reading' : ''}`}>
      <div>{selectedCompany && <nav className="research-path" aria-label="기업 폴더 경로"><button onClick={() => openLocation('')}>기업 분석</button><ChevronRight size={13} /><button onClick={() => openLocation(selectedCompany.name)}>{selectedCompany.name}</button>{selection && <><ChevronRight size={13} /><span>{selection.kind === 'brief' ? '기업 브리프' : '기여 보고서'}</span></>}</nav>}
        <h1 ref={heading} tabIndex={-1} className={selection ? 'sr-only' : undefined}>{selectedCompany ? selectedCompany.name : '기업 분석'}</h1>
        {!selection && <p>{selectedCompany ? `기업 브리프 ${selectedCompany.briefs.length} · 기여 보고서 ${selectedCompany.personal.length} · 직무기술서 ${companyJds(selectedCompany).length}` : `${companyFolders.length}개 기업 · ${briefs.length + personal.length}개 보고서`}</p>}
      </div>
      <div className="research-header-actions">{onUpload && !selection && <button className="button" onClick={onUpload}><Upload size={15} />자료 등록</button>}{!selection && <button className="button button-primary" disabled={!!activeJob || starting} onClick={openComposer}><Plus size={16} />새 분석</button>}{selection && <button className="button" onClick={() => openLocation(selectedCompany?.name ?? '')}><ArrowLeft size={15} />폴더로 돌아가기</button>}</div>
    </div></ReportNavigation>
      {activeJob && <div className="job-progress" role="status"><LoaderCircle size={19} className="spin" /><div><strong>{activeJob.jobType === 'brief' ? '기업 브리프' : '기여 보고서'} 분석 중</strong><p>{activeJob.stage}</p></div><span>화면을 이동해도 계속 진행됩니다.</span></div>}
      {jobs.filter((job) => job.status === 'failed').slice(0, 2).map((job) => <div className="notice" key={job.id}><FileText size={16} /><p>분석 실패 · {job.error}</p></div>)}

      {!selectedCompany && (!companyFolders.length ? <div className="empty-state"><FileText size={28} /><h2>아직 생성된 분석이 없어요</h2><p>자료를 등록한 뒤 새 분석을 시작해 보세요.</p><button className="button" onClick={openComposer}>첫 분석 시작</button></div> : <>
        <div className="analysis-folder-grid">{companyFolders.map((group) => <button className={`analysis-folder ${activeCompany === group.name ? 'analysis-folder-active' : ''}`} key={group.name} aria-pressed={activeCompany === group.name} onClick={() => openLocation(group.name)}><CompanyFolderArt /><strong>{group.name}</strong><span>기업 브리프 {group.briefs.length} · 기여 보고서 {group.personal.length} · JD {companyJds(group).length}</span><small>최근 분석 {group.latest.slice(0, 10)}</small></button>)}</div>
      </>)}
      {selectedCompany && !selection && <>
        <div className="section-title"><h2>보고서와 자료</h2><span>{selectedCompany.briefs.length + selectedCompany.personal.length}개 결과</span></div>
        <div className="saved-analysis-grid">{selectedCompany.briefs.map((brief) => <button className="saved-analysis" key={brief.id} onClick={() => openLocation(selectedCompany.name, { kind: 'brief', id: brief.id })}><span className="eyebrow">기업 브리프</span><h3>{brief.reportName}</h3><small>{brief.createdAt.slice(0, 10)} · 결과 보기 ↗</small></button>)}{selectedCompany.personal.map((result) => <button className="saved-analysis" key={result.id} onClick={() => openLocation(selectedCompany.name, { kind: 'personal', id: result.id })}><span className="eyebrow">기여 보고서 · CV {result.cvVersion}</span><h3>{result.targetRole}</h3><small>{result.createdAt.slice(0, 10)} · 결과 보기 ↗</small></button>)}{companyJds(selectedCompany).map((document) => <a className="saved-analysis" key={document.id} href={`/api/documents/${document.id}/preview`} target="_blank" rel="noopener noreferrer"><span className="eyebrow">분석에 사용한 직무기술서</span><h3>{document.name}</h3><small>원본 PDF 보기 ↗</small></a>)}</div>
      </>}
      {selection && selectedCompany && <SavedResult key={`${selection.kind}-${selection.id}`} selection={selection} documents={documents} session={session} onExpired={onExpired} onDelete={() => setDeleting(selection)} />}
      {composer && <Modal title="새 분석" onClose={() => { if (!starting) setComposer(null) }}>
        <div className="tabs analysis-kind-tabs" role="tablist" aria-label="분석 종류"><button role="tab" disabled={starting} aria-selected={composer === 'brief'} onClick={() => { setComposer('brief'); setError('') }}>기업 브리프</button><button role="tab" aria-selected={composer === 'personal'} disabled={!briefs.length || starting} onClick={() => { setComposer('personal'); setError('') }}>기여 보고서</button></div>
        {error && <p className="input-error" role="alert">{error}</p>}
      {composer === 'brief' && <>
      <div className="analysis-controls live-controls"><label>등록한 사업보고서<select value={reportId} onChange={(event) => setReportId(event.target.value)}><option value="">사업보고서 선택</option>{documents.filter((document) => document.kind === 'report').map((document) => <option key={document.id} value={document.id}>{document.name}</option>)}</select></label><button className="button button-primary" disabled={!validDocument(reportId, 'report') || !caps?.briefConfigured || !!activeJob || starting} onClick={() => start('brief')}><Play size={14} />기업 분석 시작</button></div>
      {!caps?.briefConfigured && <p className="muted">기업 Agent 실행 설정이 필요합니다.</p>}
      </>}
      {composer === 'personal' && <>
      <div className="analysis-controls live-controls"><label>완성된 기업 브리프<select value={briefId} onChange={(event) => setBriefId(event.target.value)}><option value="">기업 브리프 선택</option>{briefs.map((brief) => <option key={brief.id} value={brief.id}>{brief.companyName} · {brief.reportName}</option>)}</select></label><label>직무기술서<select value={jdId} onChange={(event) => setJdId(event.target.value)}><option value="">JD 선택</option>{documents.filter((document) => document.kind === 'jd').map((document) => <option key={document.id} value={document.id}>{document.name}</option>)}</select></label><label>CV<select value={cvId} onChange={(event) => setCvId(event.target.value)}><option value="">CV 선택</option>{documents.filter((document) => document.kind === 'cv').map((document) => <option key={document.id} value={document.id}>{document.name} · {document.version}</option>)}</select></label><button className="button button-primary" disabled={!briefs.some((brief) => brief.id === briefId) || !validDocument(cvId, 'cv') || !validDocument(jdId, 'jd') || !caps?.personalConfigured || !!activeJob || starting} onClick={() => start('personal')}><Play size={14} />기여 분석 시작</button></div>
      <p className="analysis-scope-note">현재 기여 Agent는 CV와 JD가 모두 필요합니다. 선택한 문서는 분석 시작 시 Upstage Agent로 전달됩니다. 등록만으로 분석을 실행하지 않습니다.</p></>}
        {onUpload && <button className="text-button" disabled={starting} onClick={() => { setComposer(null); onUpload() }}><Upload size={14} />자료를 먼저 등록할게요</button>}
      </Modal>}
      {deleting && <Modal title="분석 결과를 삭제할까요?" onClose={() => { if (!deleteBusy) setDeleting(null) }}><p>{deleting.kind === 'brief' ? '기업 브리프를 삭제하면 이 브리프를 사용한 기여 보고서도 함께 삭제됩니다.' : '선택한 기여 보고서가 삭제됩니다. 기업 브리프와 원본 PDF는 유지됩니다.'}</p>{deleteImpact === null ? <p role="status">연결된 결과를 확인하고 있습니다.</p> : <div className="modal-note">함께 삭제되는 기여 보고서: {deleteImpact}개 · 원본 PDF는 유지</div>}<div className="modal-actions"><button className="button" disabled={deleteBusy} onClick={() => setDeleting(null)}>취소</button><button className="button button-primary" disabled={deleteBusy || deleteImpact === null} onClick={removeResult}>{deleteBusy ? '삭제 중…' : '삭제'}</button></div></Modal>}
  </section>
}

function ReportNavigation({ active, children, slot = 'report-navigation' }: { active: boolean; children: ReactNode; slot?: string }) {
  const target = active ? document.getElementById(slot) : null
  return target ? createPortal(children, target) : children
}

function SavedResult({ selection, documents, session, onExpired, onDelete }: { documents: InputDocument[]; session: Session; selection: Selection; onExpired: () => void; onDelete: () => void }) {
  const [record, setRecord] = useState<ResultRecord | null>(null)
  const [error, setError] = useState('')
  const [source, setSource] = useState<EvidenceSelection | null>(null)
  const [pdf, setPdf] = useState<{ page: number; id?: string } | null>(null)
  useEffect(() => {
    const controller = new AbortController()
    api<ResultRecord>(`/api/analyses/${selection.kind}/${selection.id}`, { signal: controller.signal }).then(setRecord)
      .catch((err) => { if (!controller.signal.aborted) { setError(err instanceof Error ? err.message : '결과 조회 실패'); if (err instanceof ApiError && err.status === 401) onExpired() } })
    return () => controller.abort()
  }, [selection.id, selection.kind])
  if (error) return <p className="input-error" role="alert">{error}</p>
  if (!record) return <p role="status">저장된 결과를 불러오고 있습니다.</p>
  const selectId = (id: string) => { const item = record.evidence.find((entry) => entry.id === id); if (item) setSource({ ids: [id], page: item.page }) }
  const sourceName = documents.find((item) => item.id === record.reportDocumentId)?.name
  return <section className="saved-result">
    <ReportNavigation active slot="report-actions"><div className="report-actions"><details><summary><Download size={14} />내보내기</summary><a href={`/api/analyses/${selection.kind}/${selection.id}/download`}>Markdown 다운로드</a><button onClick={onDelete}><Trash2 size={14} />결과 삭제</button></details></div></ReportNavigation>
    <ReportReader externalDialogOpen={Boolean(pdf)} kind={selection.kind} resultId={selection.id} session={session} onExpired={onExpired} evidence={record.evidence} evidenceSelection={source} sourceName={sourceName} createdAt={record.createdAt} onSelectEvidence={selectId} onOpenSource={record.reportDocumentId ? (page, id) => setPdf({ page, id }) : undefined}>
      {(annotations) => <ReportMarkdown kind={selection.kind} text={record.result.markdown} annotations={annotations} evidence={record.evidence} selection={source} onEvidenceId={selectId} onEvidencePage={(page) => setSource({ page, ids: record.evidence.filter((item) => item.page === page).map((item) => item.id) })} />}
    </ReportReader>
    {pdf && record.reportDocumentId && <Modal wide title={`사업보고서 · ${pdf.page}쪽`} onClose={() => setPdf(null)}><a className="text-button" target="_blank" rel="noopener noreferrer" href={`/api/documents/${record.reportDocumentId}/preview#page=${pdf.page}`}>원본 PDF 새 창으로 열기 ↗</a><PdfEvidenceViewer documentId={record.reportDocumentId} page={pdf.page} quote={record.evidence.find((item) => item.id === pdf.id)?.quote ?? null} onPageChange={(page) => setPdf({ page })} /></Modal>}
  </section>
}
