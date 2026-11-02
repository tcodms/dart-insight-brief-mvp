import { useEffect, useState } from 'react'
import { Download, FileText, Folder, LoaderCircle, Play, RefreshCw, Trash2 } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { api, ApiError } from '../api'
import type { Session } from '../api'
import { Modal } from './ui'
import PdfEvidenceViewer from './PdfEvidenceViewer'
import ReportReader from './ReportReader'
import { annotationPlugin } from './reportAnnotations'
import type { Annotation } from './reportAnnotations'

interface InputDocument { id: string; name: string; kind: 'report' | 'cv' | 'jd'; version: string }
interface BriefRecord { id: string; companyName: string; reportName: string; reportDocumentId: string; createdAt: string }
interface PersonalRecord { id: string; companyName: string; targetRole: string; cvDocumentId: string; jdDocumentId: string; cvVersion: string; createdAt: string }
interface Job { id: string; jobType: 'brief' | 'personal'; status: string; stage: string; resultId: string | null; error: string | null }
interface Capabilities { briefConfigured: boolean; personalConfigured: boolean; personalRequiresJd: boolean }
interface ResultRecord {
  id: string; kind: 'brief' | 'personal'; reportDocumentId: string | null;
  result: { markdown: string }; evidence: { id: string; page: number; quote: string; section: string }[]
}
type Selection = { kind: 'brief' | 'personal'; id: string }

function linkBriefFacts(text: string): string {
  return text.replace(/(- \*\*기업 사실:\*\* )([^\n]+)(\n(?:- \*\*(?:왜 중요한가|생각해볼 질문):\*\*[^\n]*\n)*- \*\*출처:\*\*[^\n]*?원본\s+([\d,\s]+)쪽[^\n]*)/g,
    (_match, prefix: string, fact: string, following: string, pages: string) => {
      const page = Number(pages.match(/\d+/)?.[0])
      return page > 0 ? `${prefix}[${fact}](#evidence-page-${page})${following}` : `${prefix}${fact}${following}`
    })
}

function linkContributionFacts(text: string, evidenceIds: Set<string>): string {
  return text.replace(/(- \*\*회사 (?:근거|사실):\*\* )\[(B\d+-E\d+)\] ([^\n]+)/g,
    (match, prefix: string, id: string, fact: string) => evidenceIds.has(id) ? `${prefix}[${id}] [${fact}](#evidence-id-${id})` : match)
}

function Markdown({ text, onEvidencePage, onEvidenceId, evidenceIds, annotations = [] }: { annotations?: Annotation[]; text: string; onEvidencePage?: (page: number) => void; onEvidenceId?: (id: string) => void; evidenceIds?: Set<string> }) {
  return <div className="analysis-markdown"><ReactMarkdown skipHtml rehypePlugins={[annotationPlugin(annotations)]} components={{
    img: ({ alt }) => <span>{alt}</span>,
    a: ({ href, children }) => {
      const page = href?.match(/^#evidence-page-(\d+)$/)
      const evidenceId = href?.match(/^#evidence-id-(B\d+-E\d+)$/)
      return page && onEvidencePage ? <button type="button" className="evidence-fact-link" onClick={(event) => { if (!(event.target as HTMLElement).closest('mark') && window.getSelection()?.isCollapsed !== false) onEvidencePage(Number(page[1])) }} title={`${page[1]}쪽 원문 근거 보기`}>{children}</button>
        : evidenceId && onEvidenceId ? <button type="button" className="evidence-fact-link" onClick={(event) => { if (!(event.target as HTMLElement).closest('mark') && window.getSelection()?.isCollapsed !== false) onEvidenceId(evidenceId[1]) }} title="해당 기업 사실의 원문 근거 보기">{children}</button>
        : <a href={href?.startsWith('https://') || href?.startsWith('http://') ? href : undefined} target="_blank" rel="noreferrer noopener">{children}</a>
    },
  }}>{onEvidenceId ? (onEvidencePage ? (text.includes('#evidence-id-') ? text : linkBriefFacts(text)) : linkContributionFacts(text, evidenceIds ?? new Set())).replace(/\[(B\d+-E\d+)\]/g, (match, id: string) => evidenceIds?.has(id) ? `[${match}](#evidence-id-${id})` : match) : text}</ReactMarkdown></div>
}

export default function AnalysisPanel({ documents, session, onExpired }: {
  documents: InputDocument[]; session: Session; onExpired: () => void;
}) {
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
  const [selection, setSelection] = useState<Selection | null>(null)
  const [activeCompany, setActiveCompany] = useState('')
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
  const selectedCompany = groups.get(activeCompany) ?? companyFolders[0]
  const companyJds = (group: (typeof companyFolders)[number]) => {
    const ids = new Set(group.personal.map((result) => result.jdDocumentId).filter(Boolean))
    return documents.filter((document) => document.kind === 'jd' && ids.has(document.id))
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
      setSelection(null); setDeleting(null); setRevision((value) => value + 1)
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
      setRevision((value) => value + 1)
    } catch (err) {
      setError(err instanceof Error ? err.message : '분석을 시작하지 못했습니다.')
      if (err instanceof ApiError && err.status === 401) onExpired()
    } finally { setStarting(false) }
  }

  if (loading) return <section className="empty-state" role="status"><LoaderCircle className="spin" /><p>분석 이력을 불러오는 중입니다.</p></section>
  return <section className="live-analysis">
    {error && <div className="notice" role="alert"><p>{error}</p><button className="text-button" onClick={() => { setError(''); setRevision((value) => value + 1) }}><RefreshCw size={14} />다시 조회</button></div>}
      <div className="section-title"><h2>기업 분석 시작</h2><span>BUSINESS REPORT</span></div>
      <div className="analysis-controls live-controls"><label>등록한 사업보고서<select value={reportId} onChange={(event) => setReportId(event.target.value)}><option value="">사업보고서 선택</option>{documents.filter((document) => document.kind === 'report').map((document) => <option key={document.id} value={document.id}>{document.name}</option>)}</select></label><button className="button button-primary" disabled={!validDocument(reportId, 'report') || !caps?.briefConfigured || !!activeJob || starting} onClick={() => start('brief')}><Play size={14} />기업 분석 시작</button></div>
      {!caps?.briefConfigured && <p className="muted">기업 Agent 실행 설정이 필요합니다.</p>}
      {briefs.length > 0 && <><div className="section-title"><h2>내 경험 연결</h2><span>PERSONAL CONTRIBUTION</span></div>
      <div className="analysis-controls live-controls"><label>완성된 기업 브리프<select value={briefId} onChange={(event) => setBriefId(event.target.value)}><option value="">기업 브리프 선택</option>{briefs.map((brief) => <option key={brief.id} value={brief.id}>{brief.companyName} · {brief.reportName}</option>)}</select></label><label>직무기술서<select value={jdId} onChange={(event) => setJdId(event.target.value)}><option value="">JD 선택</option>{documents.filter((document) => document.kind === 'jd').map((document) => <option key={document.id} value={document.id}>{document.name}</option>)}</select></label><label>CV<select value={cvId} onChange={(event) => setCvId(event.target.value)}><option value="">CV 선택</option>{documents.filter((document) => document.kind === 'cv').map((document) => <option key={document.id} value={document.id}>{document.name} · {document.version}</option>)}</select></label><button className="button button-primary" disabled={!briefs.some((brief) => brief.id === briefId) || !validDocument(cvId, 'cv') || !validDocument(jdId, 'jd') || !caps?.personalConfigured || !!activeJob || starting} onClick={() => start('personal')}><Play size={14} />기여 분석 시작</button></div>
      <p className="analysis-scope-note">현재 기여 Agent는 CV와 JD가 모두 필요합니다. 선택한 문서는 분석 시작 시 Upstage Agent로 전달됩니다. 등록만으로 분석을 실행하지 않습니다.</p></>}
      {activeJob && <div className="job-progress" role="status"><LoaderCircle size={19} className="spin" /><div><strong>{activeJob.jobType === 'brief' ? '기업 브리프' : '기여 보고서'} 분석 중</strong><p>{activeJob.stage}</p></div><span>화면을 이동해도 계속 진행됩니다.</span></div>}
      {jobs.filter((job) => job.status === 'failed').slice(0, 2).map((job) => <div className="notice" key={job.id}><FileText size={16} /><p>분석 실패 · {job.error}</p></div>)}
      <div className="section-title"><h2>저장된 기업 폴더</h2><span>{companyFolders.length}개 기업 · {briefs.length + personal.length}개 결과</span></div>
      {!companyFolders.length ? <div className="empty-state"><FileText size={28} /><h2>아직 생성된 분석이 없어요</h2><p>사업보고서를 등록하고 기업 분석을 시작해 주세요.</p></div> : <>
        <div className="analysis-folder-grid">{companyFolders.map((group) => <button className={`analysis-folder ${selectedCompany?.name === group.name ? 'analysis-folder-active' : ''}`} key={group.name} aria-pressed={selectedCompany?.name === group.name} onClick={() => { setActiveCompany(group.name); setSelection(null) }}><Folder size={31} strokeWidth={1.2} /><strong>{group.name}</strong><span>기업 브리프 {group.briefs.length} · 기여 보고서 {group.personal.length} · JD {companyJds(group).length}</span><small>최근 분석 {group.latest.slice(0, 10)}</small></button>)}</div>
        <div className="section-title"><h2>{selectedCompany.name} 분석 이력</h2><span>{selectedCompany.briefs.length + selectedCompany.personal.length}개 결과</span></div>
        <div className="saved-analysis-grid">{selectedCompany.briefs.map((brief) => <button className="saved-analysis" key={brief.id} onClick={() => setSelection({ kind: 'brief', id: brief.id })}><span className="eyebrow">기업 브리프</span><h3>{brief.reportName}</h3><small>{brief.createdAt.slice(0, 10)} · 결과 보기 ↗</small></button>)}{selectedCompany.personal.map((result) => <button className="saved-analysis" key={result.id} onClick={() => setSelection({ kind: 'personal', id: result.id })}><span className="eyebrow">기여 보고서 · CV {result.cvVersion}</span><h3>{result.targetRole}</h3><small>{result.createdAt.slice(0, 10)} · 결과 보기 ↗</small></button>)}{companyJds(selectedCompany).map((document) => <a className="saved-analysis" key={document.id} href={`/api/documents/${document.id}/preview`} target="_blank" rel="noopener noreferrer"><span className="eyebrow">분석에 사용한 직무기술서</span><h3>{document.name}</h3><small>원본 PDF 보기 ↗</small></a>)}</div>
      </>}
      {selection && <SavedResult key={`${selection.kind}-${selection.id}`} selection={selection} session={session} onExpired={onExpired} onDelete={() => setDeleting(selection)} />}
      {deleting && <Modal title="분석 결과를 삭제할까요?" onClose={() => { if (!deleteBusy) setDeleting(null) }}><p>{deleting.kind === 'brief' ? '기업 브리프를 삭제하면 이 브리프를 사용한 기여 보고서도 함께 삭제됩니다.' : '선택한 기여 보고서가 삭제됩니다. 기업 브리프와 원본 PDF는 유지됩니다.'}</p>{deleteImpact === null ? <p role="status">연결된 결과를 확인하고 있습니다.</p> : <div className="modal-note">함께 삭제되는 기여 보고서: {deleteImpact}개 · 원본 PDF는 유지</div>}<div className="modal-actions"><button className="button" disabled={deleteBusy} onClick={() => setDeleting(null)}>취소</button><button className="button button-primary" disabled={deleteBusy || deleteImpact === null} onClick={removeResult}>{deleteBusy ? '삭제 중…' : '삭제'}</button></div></Modal>}
  </section>
}

function SavedResult({ selection, session, onExpired, onDelete }: { session: Session; selection: Selection; onExpired: () => void; onDelete: () => void }) {
  const [record, setRecord] = useState<ResultRecord | null>(null)
  const [error, setError] = useState('')
  const [page, setPage] = useState(1)
  const [activeEvidenceId, setActiveEvidenceId] = useState<string | null>(null)
  useEffect(() => {
    let active = true
    api<ResultRecord>(`/api/analyses/${selection.kind}/${selection.id}`).then((data) => { if (active) { setRecord(data); setPage(data.evidence[0]?.page ?? 1); setActiveEvidenceId(data.evidence[0]?.id ?? null) } })
      .catch((err) => { if (active) { setError(err instanceof Error ? err.message : '결과 조회 실패'); if (err instanceof ApiError && err.status === 401) onExpired() } })
    return () => { active = false }
  }, [selection.id, selection.kind])
  if (error) return <p className="input-error" role="alert">{error}</p>
  if (!record) return <p role="status">저장된 결과를 불러오고 있습니다.</p>
  const showSourcePdf = selection.kind === 'brief' && Boolean(record.reportDocumentId)
  return <section className="saved-result"><div className="section-title"><h2>{selection.kind === 'brief' ? '기업 브리프' : '개인화 기여 보고서'}</h2><div className="result-actions"><a className="button" href={`/api/analyses/${selection.kind}/${selection.id}/download`}><Download size={14} />Markdown 다운로드</a><button className="button" onClick={onDelete}><Trash2 size={14} />결과 삭제</button></div></div>
    {showSourcePdf && <div className="evidence-toolbar"><div><strong>원문 근거</strong><span className="muted">보고서의 기업 사실이나 근거 ID를 누르면 원문으로 이동합니다.</span></div><a className="text-button" target="_blank" rel="noreferrer" href={`/api/documents/${record.reportDocumentId}/preview#page=${page}`}>원본 PDF {page}쪽 새 창으로 열기 ↗</a></div>}
    {selection.kind === 'personal' ? <ReportReader kind={selection.kind} resultId={selection.id} session={session} onExpired={onExpired}>{(annotations) => <article className="personal-report"><Markdown text={record.result.markdown} annotations={annotations} /></article>}</ReportReader> : <div className={`live-result-layout ${showSourcePdf ? '' : 'result-text-only'}`}><ReportReader kind={selection.kind} resultId={selection.id} session={session} onExpired={onExpired}>{(annotations) => <Markdown annotations={annotations} text={record.result.markdown} evidenceIds={new Set(record.evidence.map((evidence) => evidence.id))} onEvidencePage={showSourcePdf ? (nextPage) => { setPage(nextPage); const candidates = record.evidence.filter((evidence) => evidence.page === nextPage); setActiveEvidenceId(candidates.length === 1 ? candidates[0].id : null) } : undefined} onEvidenceId={showSourcePdf ? (id) => { const evidence = record.evidence.find((item) => item.id === id); if (evidence) { setPage(evidence.page); setActiveEvidenceId(id) } } : undefined} />}</ReportReader>{showSourcePdf && record.reportDocumentId && <aside className="live-evidence"><PdfEvidenceViewer documentId={record.reportDocumentId} page={page} quote={record.evidence.find((evidence) => evidence.id === activeEvidenceId)?.quote ?? null} onPageChange={(nextPage) => { setPage(nextPage); setActiveEvidenceId(null) }} /></aside>}</div>}
  </section>
}
