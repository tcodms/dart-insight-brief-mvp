import { useEffect, useState } from 'react'
import { Download, FileText, LoaderCircle, Play, RefreshCw } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { api, ApiError } from '../api'
import type { Session } from '../api'

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

function Markdown({ text }: { text: string }) {
  return <div className="analysis-markdown"><ReactMarkdown skipHtml components={{
    img: ({ alt }) => <span>{alt}</span>,
    a: ({ href, children }) => <a href={href?.startsWith('https://') || href?.startsWith('http://') ? href : undefined} target="_blank" rel="noreferrer noopener">{children}</a>,
  }}>{text}</ReactMarkdown></div>
}

export default function AnalysisPanel({ documents, session, onExpired, comparison = false }: {
  documents: InputDocument[]; session: Session; onExpired: () => void; comparison?: boolean;
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
  const [role, setRole] = useState('')
  const [selection, setSelection] = useState<Selection | null>(null)
  const documentKey = documents.map((document) => document.id).join(',')
  const activeJob = jobs.find((job) => job.status === 'queued' || job.status === 'running')
  const validDocument = (id: string, kind: string) => documents.some((document) => document.id === id && document.kind === kind)

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
    const input = kind === 'brief' ? { jobType: kind, reportDocumentId: reportId } : { jobType: kind, briefId, cvDocumentId: cvId, jdDocumentId: jdId, targetRole: role.trim() }
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
    {comparison ? <PersonalComparison personal={personal} onExpired={onExpired} /> : <>
      <div className="section-title"><h2>기업 분석 시작</h2><span>BUSINESS REPORT</span></div>
      <div className="analysis-controls live-controls"><label>등록한 사업보고서<select value={reportId} onChange={(event) => setReportId(event.target.value)}><option value="">사업보고서 선택</option>{documents.filter((document) => document.kind === 'report').map((document) => <option key={document.id} value={document.id}>{document.name}</option>)}</select></label><button className="button button-primary" disabled={!validDocument(reportId, 'report') || !caps?.briefConfigured || !!activeJob || starting} onClick={() => start('brief')}><Play size={14} />기업 분석 시작</button></div>
      {!caps?.briefConfigured && <p className="muted">기업 Agent 실행 설정이 필요합니다.</p>}
      <div className="section-title"><h2>내 경험 연결</h2><span>PERSONAL CONTRIBUTION</span></div>
      <div className="analysis-controls live-controls"><label>완성된 기업 브리프<select value={briefId} onChange={(event) => setBriefId(event.target.value)}><option value="">기업 브리프 선택</option>{briefs.map((brief) => <option key={brief.id} value={brief.id}>{brief.companyName} · {brief.reportName}</option>)}</select></label><label>CV<select value={cvId} onChange={(event) => setCvId(event.target.value)}><option value="">CV 선택</option>{documents.filter((document) => document.kind === 'cv').map((document) => <option key={document.id} value={document.id}>{document.name} · {document.version}</option>)}</select></label><label>직무기술서<select value={jdId} onChange={(event) => setJdId(event.target.value)}><option value="">JD 선택</option>{documents.filter((document) => document.kind === 'jd').map((document) => <option key={document.id} value={document.id}>{document.name}</option>)}</select></label><label>지원 직무<input aria-label="지원 직무" value={role} maxLength={120} onChange={(event) => setRole(event.target.value)} placeholder="예: 데이터 분석" /></label><button className="button button-primary" disabled={!briefs.some((brief) => brief.id === briefId) || !validDocument(cvId, 'cv') || !validDocument(jdId, 'jd') || !role.trim() || !caps?.personalConfigured || !!activeJob || starting} onClick={() => start('personal')}><Play size={14} />기여 분석 시작</button></div>
      <p className="analysis-scope-note">현재 기여 Agent는 CV와 JD가 모두 필요합니다. 선택한 문서는 분석 시작 시 Upstage Agent로 전달됩니다. 등록만으로 분석을 실행하지 않습니다.</p>
      {activeJob && <div className="job-progress" role="status"><LoaderCircle size={19} className="spin" /><div><strong>{activeJob.jobType === 'brief' ? '기업 브리프' : '기여 보고서'} 분석 중</strong><p>{activeJob.stage}</p></div><span>화면을 이동해도 계속 진행됩니다.</span></div>}
      {jobs.filter((job) => job.status === 'failed').slice(0, 2).map((job) => <div className="notice" key={job.id}><FileText size={16} /><p>분석 실패 · {job.error}</p></div>)}
      <div className="section-title"><h2>저장된 분석 결과</h2><span>{briefs.length + personal.length} RESULTS</span></div>
      {!briefs.length && !personal.length ? <div className="empty-state"><FileText size={28} /><h2>아직 생성된 분석이 없어요</h2><p>사업보고서를 등록하고 기업 분석을 시작해 주세요.</p></div> : <div className="saved-analysis-grid">{briefs.map((brief) => <button className="saved-analysis" key={brief.id} onClick={() => setSelection({ kind: 'brief', id: brief.id })}><span className="eyebrow">기업 브리프</span><h3>{brief.companyName}</h3><p>{brief.reportName}</p><small>{brief.createdAt.slice(0, 10)} · 결과 보기 ↗</small></button>)}{personal.map((result) => <button className="saved-analysis" key={result.id} onClick={() => setSelection({ kind: 'personal', id: result.id })}><span className="eyebrow">기여 보고서 · CV {result.cvVersion}</span><h3>{result.companyName}</h3><p>{result.targetRole}</p><small>{result.createdAt.slice(0, 10)} · 결과 보기 ↗</small></button>)}</div>}
      {selection && <SavedResult key={`${selection.kind}-${selection.id}`} selection={selection} onExpired={onExpired} />}
    </>}
  </section>
}

function SavedResult({ selection, onExpired }: { selection: Selection; onExpired: () => void }) {
  const [record, setRecord] = useState<ResultRecord | null>(null)
  const [error, setError] = useState('')
  const [page, setPage] = useState(1)
  useEffect(() => {
    let active = true
    api<ResultRecord>(`/api/analyses/${selection.kind}/${selection.id}`).then((data) => { if (active) { setRecord(data); setPage(data.evidence[0]?.page ?? 1) } })
      .catch((err) => { if (active) { setError(err instanceof Error ? err.message : '결과 조회 실패'); if (err instanceof ApiError && err.status === 401) onExpired() } })
    return () => { active = false }
  }, [selection.id, selection.kind])
  if (error) return <p className="input-error" role="alert">{error}</p>
  if (!record) return <p role="status">저장된 결과를 불러오고 있습니다.</p>
  return <section className="saved-result"><div className="section-title"><h2>{selection.kind === 'brief' ? '기업 브리프' : '개인화 기여 보고서'}</h2><a className="button" href={`/api/analyses/${selection.kind}/${selection.id}/download`}><Download size={14} />Markdown 다운로드</a></div><div className={`live-result-layout ${record.reportDocumentId ? '' : 'result-text-only'}`}><Markdown text={record.result.markdown} />{record.reportDocumentId && <aside className="live-evidence"><h3>원문 근거</h3>{record.evidence.length ? <div className="live-evidence-list">{record.evidence.map((evidence) => <button key={evidence.id} aria-pressed={page === evidence.page} onClick={() => setPage(evidence.page)}><strong>{evidence.page}쪽 · {evidence.section}</strong><span>{evidence.quote}</span></button>)}</div> : <p className="muted">확인 가능한 원문 근거가 없습니다.</p>}<a className="text-button" target="_blank" rel="noreferrer" href={`/api/documents/${record.reportDocumentId}/preview#page=${page}`}>원본 PDF {page}쪽 새 창으로 열기 ↗</a><iframe title="사업보고서 원문" src={`/api/documents/${record.reportDocumentId}/preview#page=${page}`} key={page} /></aside>}</div></section>
}

function PersonalComparison({ personal, onExpired }: { personal: PersonalRecord[]; onExpired: () => void }) {
  const [ids, setIds] = useState<string[]>([])
  const [reports, setReports] = useState<ResultRecord[]>([])
  const [error, setError] = useState('')
  const selected = personal.filter((result) => ids.includes(result.id))
  const key = selected.map((result) => result.id).join(',')
  useEffect(() => {
    let active = true
    setReports([]); setError('')
    if (selected.length >= 2) Promise.all(selected.map((result) => api<ResultRecord>(`/api/analyses/personal/${result.id}`)))
      .then((data) => { if (active) setReports(data) }).catch((err) => { if (active) { setError(err instanceof Error ? err.message : '비교 결과 조회 실패'); if (err instanceof ApiError && err.status === 401) onExpired() } })
    return () => { active = false }
  }, [key])
  return <section><div className="section-title"><h2>기여 보고서 나란히 보기</h2><span>최대 3개</span></div><p className="analysis-scope-note">현재 Agent의 Markdown 보고서 원문을 비교합니다. 항목별 구조화 비교는 Agent 출력 형식 합의 후 연결합니다.</p><div className="comparison-target-list">{personal.map((result) => <label key={result.id}><input type="checkbox" checked={ids.includes(result.id)} disabled={selected.length >= 3 && !ids.includes(result.id)} onChange={() => setIds(ids.includes(result.id) ? ids.filter((id) => id !== result.id) : [...ids, result.id])} />{result.companyName} · {result.targetRole}<small>CV {result.cvVersion}</small></label>)}</div>{new Set(selected.map((result) => result.cvDocumentId)).size > 1 && <div className="notice"><p>서로 다른 CV로 만든 결과입니다. 동일 조건의 비교가 아니므로 입력 버전을 확인해 주세요.</p></div>}{error && <p className="input-error" role="alert">{error}</p>}{selected.length < 2 ? <div className="empty-state"><h3>기여 보고서를 2~3개 선택해 주세요</h3><p>기업 브리프와 CV·JD로 기여 분석을 완료하면 이곳에서 비교할 수 있어요.</p></div> : !reports.length && !error ? <p role="status">비교 결과를 불러오고 있습니다.</p> : <div className="live-comparison">{reports.map((report) => <article key={report.id}><h3>{personal.find((item) => item.id === report.id)?.companyName}</h3><Markdown text={report.result.markdown} /></article>)}</div>}</section>
}
