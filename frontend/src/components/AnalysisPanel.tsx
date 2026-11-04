import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import type { ReactNode } from 'react'
import { ArrowLeft, ChevronRight, CircleCheck, Download, FileText, LoaderCircle, Play, Plus, RefreshCw, Trash2, Upload, X } from 'lucide-react'
import ReportMarkdown from './ReportMarkdown'
import type { EvidenceSelection } from './ReportEvidence'
import { api, ApiError } from '../api'
import type { Session } from '../api'
import { Modal } from './ui'
import PdfEvidenceViewer from './PdfEvidenceViewer'
import ReportReader from './ReportReader'
import CompanyFolderArt from './CompanyFolderArt'
import ListToolbar, { sortList } from './ListToolbar'
import type { ListOrder } from './ListToolbar'

interface InputDocument { id: string; name: string; kind: 'report' | 'cv' | 'jd'; version: string }
interface BriefRecord { id: string; companyName: string; reportName: string; reportDocumentId: string; createdAt: string }
interface PersonalRecord { id: string; briefId?: string; companyName: string; targetRole: string; cvDocumentId: string; jdDocumentId: string; cvVersion: string; createdAt: string }
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

export default function AnalysisPanel({ documents, session, onExpired, onUpload, onAnalysisUpload, mode = 'brief', onManageReports, onCreateContribution }: {
  documents: InputDocument[]; session: Session; onExpired: () => void; onUpload?: () => void;
  onAnalysisUpload?: (kind: InputDocument['kind'], onSaved: (document: InputDocument) => void, onClose: () => void) => void;
  mode?: Selection['kind'];
  onManageReports?: () => void;
  onCreateContribution?: (briefId: string) => void;
}) {
  const isBrief = mode === 'brief'
  const pageTitle = isBrief ? '기업 분석' : '기여 보고서'
  const createLabel = isBrief ? '새 기업 브리프' : '새 기여 보고서'
  const initialBriefId = isBrief ? '' : new URLSearchParams(window.location.search).get('fromBrief') ?? ''
  const heading = useRef<HTMLHeadingElement>(null)
  const [revision, setRevision] = useState(0)
  const [jobs, setJobs] = useState<Job[]>([])
  const dismissedFailuresKey = `dart-insight:dismissed-analysis-failures:${session.user?.id ?? ''}`
  const [dismissedFailures, setDismissedFailures] = useState<string[]>(() => {
    try {
      const saved: unknown = JSON.parse(localStorage.getItem(dismissedFailuresKey) ?? '[]')
      return Array.isArray(saved) ? saved.filter((id): id is string => typeof id === 'string') : []
    } catch {
      return []
    }
  })
  const [briefs, setBriefs] = useState<BriefRecord[]>([])
  const [personal, setPersonal] = useState<PersonalRecord[]>([])
  const [caps, setCaps] = useState<Capabilities | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [starting, setStarting] = useState(false)
  const [reportId, setReportId] = useState('')
  const [briefId, setBriefId] = useState(initialBriefId)
  const [cvId, setCvId] = useState('')
  const [jdId, setJdId] = useState('')
  const [selection, setSelection] = useState<Selection | null>(() => readLocation().selection)
  const [activeCompany, setActiveCompany] = useState(() => readLocation().company)
  const [folderSearch, setFolderSearch] = useState('')
  const [folderOrder, setFolderOrder] = useState<ListOrder>('newest')
  const [composer, setComposer] = useState<Selection['kind'] | null>(initialBriefId ? 'personal' : null)
  const [composerCompany, setComposerCompany] = useState('')
  const [uploading, setUploading] = useState(false)
  const [deleting, setDeleting] = useState<Selection | null>(null)
  const [deleteImpact, setDeleteImpact] = useState<number | null>(null)
  const [deleteError, setDeleteError] = useState('')
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
  const visibleFolders = companyFolders
    .filter((group) => (isBrief ? group.briefs : group.personal).length > 0)
    .sort((a, b) => (isBrief ? b.briefs : b.personal)[0].createdAt.localeCompare((isBrief ? a.briefs : a.personal)[0].createdAt))
  const composerBriefs = groups.get(composerCompany)?.briefs ?? briefs
  const shownFolders = isBrief ? [] : sortList(visibleFolders.filter((group) =>
    group.name.toLocaleLowerCase().includes(folderSearch.trim().toLocaleLowerCase())
  ), folderOrder, (group) => group.name, (group) => group.personal[0].createdAt)
  const latestJob = jobs.find((job) => job.jobType === mode)
  const completedResult = latestJob?.status === 'succeeded'
    ? (latestJob.jobType === 'brief' ? briefs : personal).find((item) => item.id === latestJob.resultId)
    : undefined
  const selectedCompany = selection
    ? companyFolders.find((group) => (selection.kind === 'brief' ? group.briefs : group.personal).some((item) => item.id === selection.id))
    : isBrief ? undefined : groups.get(activeCompany)

  useEffect(() => { if (!loading) heading.current?.focus({ preventScroll: true }) }, [activeCompany, selection?.id, loading])

  const openLocation = (company: string, result: Selection | null = null) => {
    setActiveCompany(company); setSelection(result)
    const url = new URL(window.location.href)
    url.search = ''
    url.searchParams.set('view', isBrief ? 'workspace' : 'contribution')
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
    setComposerCompany(selectedCompany?.briefs.length ? selectedCompany.name : '')
    setBriefId(selectedCompany?.briefs[0]?.id ?? '')
    setError(''); setComposer(mode)
  }


  const registerForAnalysis = (kind: InputDocument['kind']) => {
    if (!onAnalysisUpload) return
    setUploading(true)
    onAnalysisUpload(kind, (document) => {
      if (kind === 'report') setReportId(document.id)
      if (kind === 'cv') setCvId(document.id)
      if (kind === 'jd') setJdId(document.id)
      setUploading(false)
    }, () => setUploading(false))
  }

  useEffect(() => {
    setDeleteImpact(null); setDeleteError('')
    if (!deleting) return
    const controller = new AbortController()
    api<{ relatedPersonalAnalyses: number }>(`/api/analyses/${deleting.kind}/${deleting.id}/impact`, { signal: controller.signal })
      .then((result) => { if (!controller.signal.aborted) setDeleteImpact(result.relatedPersonalAnalyses) })
      .catch((err) => { if (!controller.signal.aborted) setDeleteError(err instanceof Error ? err.message : '삭제 영향을 확인하지 못했습니다.') })
    return () => controller.abort()
  }, [deleting])

  const removeResult = async () => {
    if (!deleting || deleteImpact === null) return
    setDeleteBusy(true); setDeleteError('')
    try {
      await api(`/api/analyses/${deleting.kind}/${deleting.id}`, { method: 'DELETE' }, session.csrfToken)
      openLocation(isBrief ? '' : activeCompany); setDeleting(null); setComposer(null); setRevision((value) => value + 1)
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : '분석 결과를 삭제하지 못했습니다.')
      if (err instanceof ApiError && err.status === 401) onExpired()
    } finally { setDeleteBusy(false) }
  }

  useEffect(() => {
    let active = true
    let timer: ReturnType<typeof setTimeout> | undefined
    const controller = new AbortController()
    const options = { signal: controller.signal }
    const resultsAfterJobs = api<{ jobs: Job[] }>('/api/jobs', options).then(async (status) => ({
      status,
      results: await api<{ briefs: BriefRecord[]; personal: PersonalRecord[] }>('/api/analyses', options),
    }))
    Promise.all([resultsAfterJobs, api<Capabilities>('/api/analysis/capabilities', options)])
      .then(([{ status, results }, config]) => {
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
      <div>{selectedCompany && <nav className="research-path" aria-label="기업 폴더 경로"><button onClick={() => openLocation('')}>{pageTitle}</button><ChevronRight size={13} /><button onClick={() => openLocation(selectedCompany.name)}>{selectedCompany.name}</button>{selection && <><ChevronRight size={13} /><span>{selection.kind === 'brief' ? '기업 브리프' : '기여 보고서'}</span></>}</nav>}
        <h1 ref={heading} tabIndex={-1} className={selection ? 'sr-only' : undefined}>{selectedCompany ? selectedCompany.name : pageTitle}</h1>
        {!selection && <p>{selectedCompany ? `${(isBrief ? selectedCompany.briefs : selectedCompany.personal).length}개 보고서` : `${visibleFolders.length}개 기업 · ${(isBrief ? briefs : personal).length}개 보고서`}</p>}
      </div>
      <div className="research-header-actions">{isBrief && onUpload && !selection && <button className="button" onClick={onUpload}><Upload size={15} />사업보고서 등록</button>}{isBrief && onManageReports && !selection && <button className="button" onClick={onManageReports}>사업보고서 관리</button>}{!selection && <button className="button button-primary" disabled={!!activeJob || starting} onClick={openComposer}><Plus size={16} />{createLabel}</button>}{selection && <button className="button" onClick={() => openLocation(selectedCompany?.name ?? '')}><ArrowLeft size={15} />{isBrief ? '브리프 목록으로 돌아가기' : '폴더로 돌아가기'}</button>}</div>
    </div></ReportNavigation>
      {activeJob && <div className="job-progress" role="status"><LoaderCircle size={19} className="spin" /><div><strong>{activeJob.jobType === 'brief' ? '기업 브리프' : '기여 보고서'} 분석 중</strong><p>{activeJob.stage}</p></div><span>화면을 이동해도 계속 진행됩니다.</span></div>}
      {!selection && !activeJob && completedResult && <div className="job-progress analysis-complete">
        <CircleCheck size={21} aria-hidden="true" />
        <div><strong>분석 완료</strong><p>{completedResult.companyName} · {isBrief ? '기업 브리프' : '기여 보고서'}</p></div>
        <button className="button button-primary" onClick={() => openLocation(completedResult.companyName.trim().replace(/\s+/g, ' '), { kind: mode, id: completedResult.id })}>완료 결과 보기</button>
      </div>}
      {jobs.filter((job) => job.jobType === mode && job.status === 'failed').slice(0, 2).filter((job) => !dismissedFailures.includes(job.id)).map((job) => (
        <div className="notice analysis-failure-notice" key={job.id}>
          <FileText size={16} aria-hidden="true" />
          <p>분석 실패 · {job.error}</p>
          <button type="button" className="icon-button" aria-label="분석 실패 안내 닫기" onClick={() => {
            const next = [job.id, ...dismissedFailures]
            setDismissedFailures(next)
            try { localStorage.setItem(dismissedFailuresKey, JSON.stringify(next)) } catch { /* Keep the notice hidden for this visit. */ }
          }}><X size={16} aria-hidden="true" /></button>
        </div>
      ))}

      {!selection && !selectedCompany && !visibleFolders.length && <div className="empty-state"><FileText size={28} /><h2>아직 생성된 분석이 없어요</h2><p>자료를 등록한 뒤 새 분석을 시작해 보세요.</p><button className="button" onClick={openComposer}>첫 분석 시작</button></div>}
      {!selection && isBrief && briefs.length > 0 && <BriefCards briefs={briefs}
        importedId={new URLSearchParams(window.location.search).get('imported')}
        onOpen={(item) => openLocation(item.companyName.trim().replace(/\s+/g, ' '), { kind: 'brief', id: item.id })}
        onDelete={(id) => setDeleting({ kind: 'brief', id })}
      />}
      {!isBrief && !selection && !selectedCompany && visibleFolders.length > 0 && <>
        <ListToolbar query={folderSearch} onSearch={setFolderSearch} order={folderOrder} onOrder={setFolderOrder}
          placeholder="기업명 검색" summary={`${shownFolders.length}개 기업`} nameLabel="기업명" />
        {shownFolders.length ? <div className="analysis-folder-grid">
        {shownFolders.map((group) => <button className="analysis-folder" key={group.name} onClick={() => openLocation(group.name)}>
          <CompanyFolderArt /><strong>{group.name}</strong><span>기여 보고서 {group.personal.length}</span><small>최근 분석 {group.personal[0].createdAt.slice(0, 10)}</small>
        </button>)}
        </div> : <p className="folder-section-empty">검색 조건에 맞는 기업이 없어요.</p>}
      </>}
      {!isBrief && selectedCompany && !selection && <CompanyFolderContents
        key={selectedCompany.name}
        briefs={selectedCompany.briefs}
        personal={selectedCompany.personal}
        documents={documents}
        onOpen={(result) => openLocation(selectedCompany.name, result)}
      />}
      {selection && selectedCompany && <SavedResult key={`${selection.kind}-${selection.id}`} selection={selection} documents={documents} session={session} onExpired={onExpired} onDelete={() => setDeleting(selection)} onCreateContribution={onCreateContribution} />}
      {composer && !uploading && <Modal title={createLabel} onClose={() => { if (!starting) setComposer(null) }}>
        {error && <p className="input-error" role="alert">{error}</p>}
        <fieldset className="analysis-controls live-controls analysis-setup" disabled={starting}>
          {composer === 'brief' ? <>
            <p className="analysis-step">1. 분석할 기업의 사업보고서</p>
            <p className="muted">등록된 PDF를 선택하거나, 사업보고서 등록에서 기업을 검색해 원문을 찾을 수 있어요.</p>
            <label>등록한 사업보고서<select value={reportId} onChange={(event) => setReportId(event.target.value)}>
              <option value="">사업보고서 선택</option>
              {documents.filter((document) => document.kind === 'report').map((document) => <option key={document.id} value={document.id}>{document.name}</option>)}
            </select></label>
            {onAnalysisUpload && <button className="text-button" onClick={() => registerForAnalysis('report')}><Upload size={14} />사업보고서 등록</button>}
            {!caps?.briefConfigured && <p className="muted">현재 기업 브리프 분석을 시작할 수 없어요.</p>}
            <p className="analysis-step">2. 분석 실행</p>
            <button className="button button-primary" disabled={!validDocument(reportId, 'report') || !caps?.briefConfigured || !!activeJob || starting} onClick={() => start('brief')}><Play size={14} />기업 분석 시작</button>
          </> : <>
            <p className="analysis-step">1. 기업과 브리프 선택</p>
            {!briefs.length && <p className="muted">기여 보고서를 만들려면 먼저 해당 기업의 브리프를 완료해 주세요.</p>}
            <label>분석할 기업<select value={composerCompany} onChange={(event) => {
              const company = event.target.value
              setComposerCompany(company)
              setBriefId(groups.get(company)?.briefs[0]?.id ?? '')
            }}>
              <option value="">전체 기업</option>
              {companyFolders.filter((group) => group.briefs.length > 0).map((group) => <option key={group.name} value={group.name}>{group.name}</option>)}
            </select></label>
            <label>완성된 기업 브리프<select value={briefId} onChange={(event) => setBriefId(event.target.value)}>
              <option value="">기업 브리프 선택</option>
              {composerBriefs.map((brief) => <option key={brief.id} value={brief.id}>{brief.companyName} · {brief.reportName}</option>)}
            </select></label>
            <p className="analysis-step">2. 분석에 사용할 자료</p>
            <label>직무기술서<select value={jdId} onChange={(event) => setJdId(event.target.value)}>
              <option value="">JD 선택</option>
              {documents.filter((document) => document.kind === 'jd').map((document) => <option key={document.id} value={document.id}>{document.name}</option>)}
            </select></label>
            {onAnalysisUpload && <button className="text-button" onClick={() => registerForAnalysis('jd')}><Upload size={14} />직무기술서 등록</button>}
            <label>CV<select value={cvId} onChange={(event) => setCvId(event.target.value)}>
              <option value="">CV 선택</option>
              {documents.filter((document) => document.kind === 'cv').map((document) => <option key={document.id} value={document.id}>{document.name} · {document.version}</option>)}
            </select></label>
            {onAnalysisUpload && <button className="text-button" onClick={() => registerForAnalysis('cv')}><Upload size={14} />CV 등록</button>}
            <p className="analysis-step">3. 분석 실행</p>
            <p className="analysis-scope-note">분석을 시작하면 선택한 CV와 직무기술서가 Upstage Agent로 전달됩니다.</p>
            {!caps?.personalConfigured && <p className="muted">현재 기여 보고서 분석을 시작할 수 없어요.</p>}
            <button className="button button-primary" disabled={!composerBriefs.some((brief) => brief.id === briefId) || !validDocument(cvId, 'cv') || !validDocument(jdId, 'jd') || !caps?.personalConfigured || !!activeJob || starting} onClick={() => start('personal')}><Play size={14} />기여 분석 시작</button>
          </>}
        </fieldset>
        <p className="analysis-scope-note">실행 후 진행 상태와 완료 결과는 기업 분석 화면에서 확인할 수 있어요.</p>
      </Modal>}
      {deleting && <Modal title="분석 결과를 삭제할까요?" onClose={() => { if (!deleteBusy) setDeleting(null) }}><p>{deleting.kind === 'brief' ? '기업 브리프를 삭제하면 이 브리프를 사용한 기여 보고서도 함께 삭제됩니다.' : '선택한 기여 보고서가 삭제됩니다. 기업 브리프와 원본 PDF는 유지됩니다.'}</p>{deleteError && <p className="input-error" role="alert">{deleteError}</p>}{deleteImpact === null ? !deleteError && <p role="status">연결된 결과를 확인하고 있습니다.</p> : <div className="modal-note">함께 삭제되는 기여 보고서: {deleteImpact}개 · 원본 PDF는 유지</div>}<div className="modal-actions"><button className="button" disabled={deleteBusy} onClick={() => setDeleting(null)}>취소</button><button className="button button-primary" disabled={deleteBusy || deleteImpact === null} onClick={removeResult}>{deleteBusy ? '삭제 중…' : '삭제'}</button></div></Modal>}
  </section>
}

function BriefCards({ briefs, importedId, onOpen, onDelete }: {
  briefs: BriefRecord[]; importedId: string | null;
  onOpen: (brief: BriefRecord) => void; onDelete: (id: string) => void;
}) {
  const [search, setSearch] = useState('')
  const [order, setOrder] = useState<ListOrder>('newest')
  const query = search.trim().toLocaleLowerCase()
  const shown = sortList(briefs.filter((item) => `${item.companyName} ${item.reportName}`.toLocaleLowerCase().includes(query)),
    order, (item) => item.companyName, (item) => item.createdAt)
  return <section aria-label="내 기업 브리프">
    {briefs.some((item) => item.id === importedId) && <div className="notice" role="status"><p>공용 브리프를 내 기업 분석에 가져왔어요.</p></div>}
    <ListToolbar query={search} onSearch={setSearch} order={order} onOrder={setOrder}
      placeholder="기업명 또는 사업보고서 제목 검색" summary={`${shown.length}개 브리프`} nameLabel="기업명" />
    {shown.length ? <div className="saved-analysis-grid owned-brief-grid">{shown.map((item) => (
      <article className="saved-analysis brief-card" key={item.id} data-imported={item.id === importedId || undefined}>
        <div className="brief-card-icon"><FileText size={17} /></div>
        <h3>{item.companyName}</h3>
        <p>{item.reportName}</p>
        <small><time dateTime={item.createdAt}>분석일 {item.createdAt.slice(0, 10).replaceAll('-', '.')}</time></small>
        <div className="brief-card-actions">
          <button className="button" onClick={() => onOpen(item)} aria-label={`${item.companyName} ${item.reportName} 결과 보기`}>브리프 열기</button>
          <button className="icon-button" onClick={() => onDelete(item.id)} aria-label={`${item.companyName} ${item.reportName} 브리프 삭제`} title="브리프 삭제"><Trash2 size={16} /></button>
        </div>
      </article>
    ))}</div> : <p className="folder-section-empty">검색 조건에 맞는 브리프가 없어요.</p>}
  </section>
}

function CompanyFolderContents({ briefs, personal, documents, onOpen }: {
  briefs: BriefRecord[]; personal: PersonalRecord[]; documents: InputDocument[];
  onOpen: (result: Selection) => void;
}) {
  const [search, setSearch] = useState('')
  const [order, setOrder] = useState<ListOrder>('newest')
  const query = search.trim().toLocaleLowerCase()
  const matches = (...fields: string[]) => fields.join(' ').toLocaleLowerCase().includes(query)
  const dateLabel = (date: string) => date.slice(0, 10).replaceAll('-', '.')
  const documentNames = new Map(documents.map(({ id, name }) => [id, name]))
  const briefNames = new Map(briefs.map(({ id, reportName }) => [id, reportName]))
  const visiblePersonal = sortList(personal.map((item) => ({
    ...item,
    briefName: briefNames.get(item.briefId ?? '') ?? '',
    jdName: documentNames.get(item.jdDocumentId) ?? '',
    cvName: documentNames.get(item.cvDocumentId) ?? '',
  })).filter((item) => matches(item.targetRole, item.cvVersion, item.briefName, item.jdName, item.cvName, dateLabel(item.createdAt), item.createdAt)),
  order, (item) => item.targetRole, (item) => item.createdAt)
  const emptyMessage = (total: number) => total && query ? '검색 조건에 맞는 항목이 없어요.' : '아직 저장된 항목이 없어요.'

  return <div className="company-folder-contents">
    <section aria-labelledby="folder-personal">
      <h2 id="folder-personal" className="sr-only">기여 보고서</h2>
      <ListToolbar query={search} onSearch={setSearch} order={order} onOrder={setOrder}
        placeholder="직무, 자료명 또는 날짜 검색" summary={`${visiblePersonal.length}개 기여 보고서`} nameLabel="직무명" />
      {visiblePersonal.length ? <div className="saved-analysis-grid">
        {visiblePersonal.map((item) => <article className="saved-analysis" key={item.id}>
          <span className="eyebrow">CV {item.cvVersion}</span>
          <h3>{item.targetRole}</h3>
          {(item.briefName || item.jdName || item.cvName) && <div className="folder-report-sources">
            {item.briefName && <p>브리프 · {item.briefName}</p>}
            {item.jdName && <a href={`/api/documents/${item.jdDocumentId}/preview`} target="_blank" rel="noreferrer">JD · {item.jdName}</a>}
            {item.cvName && <a href={`/api/documents/${item.cvDocumentId}/preview`} target="_blank" rel="noreferrer">CV · {item.cvName}</a>}
          </div>}
          <small><time dateTime={item.createdAt}>{dateLabel(item.createdAt)}</time>
            <button className="text-button" aria-label={`${item.targetRole} ${dateLabel(item.createdAt)} 결과 보기`} onClick={() => onOpen({ kind: 'personal', id: item.id })}>결과 보기 ↗</button>
          </small>
        </article>)}
      </div> : <p className="folder-section-empty">{emptyMessage(personal.length)}</p>}
    </section>
  </div>
}

function ReportNavigation({ active, children, slot = 'report-navigation' }: { active: boolean; children: ReactNode; slot?: string }) {
  const target = active ? document.getElementById(slot) : null
  return target ? createPortal(children, target) : children
}

function SavedResult({ selection, documents, session, onExpired, onDelete, onCreateContribution }: { documents: InputDocument[]; session: Session; selection: Selection; onExpired: () => void; onDelete: () => void; onCreateContribution?: (briefId: string) => void }) {
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
    <ReportNavigation active slot="report-actions">
      <div className="report-actions">
        <details>
          <summary><Download size={15} />내보내기</summary>
          <div className="report-action-menu">
            {selection.kind === "brief" && onCreateContribution && <button onClick={() => onCreateContribution(selection.id)}>이 브리프로 기여 분석</button>}
            <a href={`/api/analyses/${selection.kind}/${selection.id}/download`}>Markdown 다운로드</a>
            <button onClick={onDelete}><Trash2 size={15} />결과 삭제</button>
          </div>
        </details>
      </div>
    </ReportNavigation>
    <ReportReader externalDialogOpen={Boolean(pdf)} kind={selection.kind} resultId={selection.id} session={session} onExpired={onExpired} evidence={record.evidence} evidenceSelection={source} sourceName={sourceName} createdAt={record.createdAt} onSelectEvidence={selectId} onOpenSource={record.reportDocumentId ? (page, id) => setPdf({ page, id }) : undefined}>
      {(annotations) => <ReportMarkdown kind={selection.kind} text={record.result.markdown} annotations={annotations} evidence={record.evidence} selection={source} onEvidenceId={selectId} onEvidencePage={(page) => setSource({ page, ids: record.evidence.filter((item) => item.page === page).map((item) => item.id) })} />}
    </ReportReader>
    {pdf && record.reportDocumentId && <Modal wide title={`사업보고서 · ${pdf.page}쪽`} onClose={() => setPdf(null)}><a className="text-button" target="_blank" rel="noopener noreferrer" href={`/api/documents/${record.reportDocumentId}/preview#page=${pdf.page}`}>원본 PDF 새 창으로 열기 ↗</a><PdfEvidenceViewer documentId={record.reportDocumentId} page={pdf.page} quote={record.evidence.find((item) => item.id === pdf.id)?.quote ?? null} onPageChange={(page) => setPdf({ page })} /></Modal>}
  </section>
}
