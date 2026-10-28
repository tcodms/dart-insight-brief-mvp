import { useEffect, useRef, useState } from 'react'
import { ArrowRight, Check, FileText, Info, LoaderCircle, RefreshCw, Upload, X } from 'lucide-react'
import type { Company, Material, Page, Workspace as WorkspaceData } from './types'
import Shell from './components/Shell'
import { Modal } from './components/ui'
import Home from './pages/Home'
import Workspace from './pages/Workspace'
import Brief from './pages/Brief'
import Materials from './pages/Materials'
import Contribution from './pages/Contribution'
import Compare from './pages/Compare'
import PrivateWorkspace from './pages/PrivateWorkspace'
import { api, ApiError } from './api'
import type { Session } from './api'
import { relatedCompanies, removeDemoMaterial } from './domain'

const pages: Page[] = ['home', 'workspace', 'brief', 'materials', 'contribution', 'compare']
function readPage(): Page {
  const value = new URLSearchParams(window.location.search).get('view')
  return pages.includes(value as Page) ? value as Page : 'home'
}

export default function App() {
  const [page, setPage] = useState<Page>(readPage)
  const [theme, setTheme] = useState<'dark' | 'light'>(() => { try { return localStorage.getItem('dart-theme') === 'light' ? 'light' : 'dark' } catch { return 'dark' } })
  const [workspace, setWorkspace] = useState<WorkspaceData | null>(null)
  const [phase, setPhase] = useState<'loading' | 'ready' | 'error'>('loading')
  const [refresh, setRefresh] = useState(0)
  const [session, setSession] = useState<Session>({ authenticated: false, googleConfigured: false, user: null, csrfToken: null })
  const [preview, setPreview] = useState(() => new URLSearchParams(window.location.search).get('demo') === '1')
  const privateMode = session.authenticated && !preview
  const [companyId, setCompanyId] = useState(() => new URLSearchParams(window.location.search).get('company') ?? 'company-a')
  const [evidenceId, setEvidenceId] = useState<string>()
  const [dialog, setDialog] = useState<'login' | 'analysis' | 'upload' | null>(null)
  const [uploadKind, setUploadKind] = useState<'report' | 'cv' | 'jd'>('report')
  const [deleting, setDeleting] = useState<Material | null>(null)
  const [toast, setToast] = useState('')
  const toastTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)
  useEffect(() => {
    document.documentElement.dataset.theme = theme
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', theme === 'dark' ? '#151515' : '#f6f6f4')
    try { localStorage.setItem('dart-theme', theme) } catch { /* Theme still works if storage is disabled. */ }
  }, [theme])
  useEffect(() => {
    const handle = () => { setPage(readPage()); setPreview(new URLSearchParams(window.location.search).get('demo') === '1'); setCompanyId(new URLSearchParams(window.location.search).get('company') ?? 'company-a') }
    window.addEventListener('popstate', handle)
    return () => window.removeEventListener('popstate', handle)
  }, [])
  useEffect(() => {
    const controller = new AbortController()
    let active = true
    const timeout = setTimeout(() => controller.abort(), 10000)
    setPhase('loading')
    Promise.all(['/api/health', '/api/demo/workspace', '/api/auth/session'].map(async (url) => {
      const response = await fetch(url, { signal: controller.signal })
      if (!response.ok) throw new Error('API unavailable')
      return response.json()
    })).then(([health, data, auth]) => {
      if (!active) return
      if (health.status !== 'ok' || data.dataType !== 'fictional_demo' || !Array.isArray(data.companies) || !Array.isArray(data.materials)) throw new Error('Invalid preview response')
      setWorkspace(data as WorkspaceData)
      setSession(auth as Session)
      setPhase('ready')
    }).catch(() => { if (active) setPhase('error') }).finally(() => clearTimeout(timeout))
    return () => { active = false; clearTimeout(timeout); controller.abort() }
  }, [refresh])
  useEffect(() => () => clearTimeout(toastTimer.current), [])

  const navigate = (target: Page, company?: Company) => {
    const nextCompany = company?.id ?? companyId
    setPage(target)
    setCompanyId(nextCompany)
    const url = new URL(window.location.href)
    url.search = ''
    if (target !== 'home') url.searchParams.set('view', target)
    if (preview && session.authenticated) url.searchParams.set('demo', '1')
    if (target === 'brief' || target === 'contribution') url.searchParams.set('company', nextCompany)
    window.history.pushState({}, '', url)
    window.scrollTo({ top: 0, behavior: 'instant' })
  }
  const notify = (message: string) => { setToast(message); clearTimeout(toastTimer.current); toastTimer.current = setTimeout(() => setToast(''), 4000) }
  const switchWorkspace = () => {
    const next = !preview
    setPreview(next); setPage('workspace')
    window.history.pushState({}, '', next ? '/?view=workspace&demo=1' : '/?view=workspace')
    window.scrollTo({ top: 0, behavior: 'instant' })
  }
  const logout = async () => {
    try { await api('/api/auth/logout', { method: 'POST' }, session.csrfToken); window.location.assign('/') }
    catch (err) { if (err instanceof ApiError && err.status === 401) window.location.assign('/'); else notify(err instanceof Error ? err.message : '로그아웃하지 못했습니다.') }
  }
  const openUpload = (kind: 'report' | 'cv' | 'jd') => { setUploadKind(kind); setDialog('upload') }
  const openEvidence = (company: Company, id?: string) => { setEvidenceId(id); navigate('brief', company) }
  const company = workspace?.companies.find((item) => item.id === companyId) ?? workspace?.companies[0]

  return <><a className="skip-link" href="#main-content">본문으로 건너뛰기</a><Shell page={page} navigate={navigate} theme={theme} toggleTheme={() => setTheme(theme === 'dark' ? 'light' : 'dark')} connected={phase === 'ready'} onLogin={() => setDialog('login')} accountName={session.user?.name} privateMode={privateMode} onLogout={logout} onSwitchWorkspace={switchWorkspace}>
    {new URLSearchParams(window.location.search).get('auth') === 'failed' && <div className="notice" role="alert"><Info size={16} /><p>Google 로그인을 완료하지 못했습니다. 다시 시도해 주세요.</p></div>}
    {privateMode ? <PrivateWorkspace page={page} session={session} onDemo={switchWorkspace} onLogin={() => { window.location.assign('/api/auth/login') }} /> : <>
    {page === 'home' ? <Home onExplore={() => navigate('workspace')} onLogin={() => setDialog('login')} /> : phase === 'loading' ? <div className="page-loading" role="status"><LoaderCircle size={25} className="spin" /><h2>작업 공간을 불러오고 있어요</h2><p>잠시만 기다려 주세요.</p></div> : phase === 'error' || !workspace || !company ? <div className="page-loading"><Info size={29} /><h2>작업 공간에 연결할 수 없어요</h2><p>백엔드 실행 상태를 확인한 후 다시 시도해 주세요.</p><button className="button" onClick={() => setRefresh(refresh + 1)}><RefreshCw size={15} />다시 연결</button></div> : <>
      {page === 'workspace' && <Workspace companies={workspace.companies} materials={workspace.materials} selectedId={companyId} onSelect={setCompanyId} onOpen={(item) => navigate('brief', item)} onUpload={() => openUpload('report')} onCompare={() => navigate('compare')} />}
      {page === 'brief' && <Brief company={company} evidenceId={evidenceId} onBack={() => navigate('workspace')} onContribution={() => navigate('contribution', company)} />}
      {page === 'materials' && <Materials materials={workspace.materials} companies={workspace.companies} onUpload={openUpload} onDelete={setDeleting} onCompany={(item) => navigate('contribution', item)} />}
      {page === 'contribution' && <Contribution company={company} companies={workspace.companies} materials={workspace.materials} onCompany={(item) => navigate('contribution', item)} onEvidence={openEvidence} onAnalyze={() => setDialog('analysis')} onMaterials={() => navigate('materials')} />}
      {page === 'compare' && <Compare companies={workspace.companies} materials={workspace.materials} onEvidence={openEvidence} />}
    </>}
    </>}
  </Shell>
  {dialog === 'login' && <Modal title={session.googleConfigured ? 'Google 계정으로 시작하세요' : 'Google 로그인 설정을 기다리고 있어요'} onClose={() => setDialog(null)}><div className="modal-feature-icon">G</div><p>{session.googleConfigured ? '로그인하면 PDF를 내 계정에 저장하고 다시 조회할 수 있습니다.' : '서비스의 Google OAuth 인증 정보가 아직 등록되지 않았습니다. 설정 후 실제 로그인과 PDF 저장을 사용할 수 있어요.'}</p><div className="modal-note"><Info size={16} />샘플 화면과 실제 계정 자료는 별도로 표시합니다.</div><div className="modal-actions"><button className="button" onClick={() => { setDialog(null); navigate('workspace') }}>샘플 둘러보기</button><button className="button button-primary" disabled={!session.googleConfigured || phase !== 'ready'} onClick={() => { window.location.assign('/api/auth/login') }}>Google로 로그인 <ArrowRight size={15} /></button></div></Modal>}
  {dialog === 'analysis' && <Modal title="실제 분석은 다음 단계에서 연결됩니다" onClose={() => setDialog(null)}><p>현재는 화면과 API 연결을 확인하는 미리보기입니다. 선택한 자료로 Agent를 실행하거나 비용이 발생하는 요청을 보내지 않습니다.</p><div className="modal-note"><FileText size={17} />현재 화면에는 저장된 예시 결과만 표시됩니다.</div><div className="modal-actions"><button className="button button-primary" onClick={() => setDialog(null)}>확인</button></div></Modal>}
  {dialog === 'upload' && <UploadDialog kind={uploadKind} onClose={() => setDialog(null)} />}
  {deleting && workspace && <Modal title={`${deleting.kind === 'cv' ? 'CV' : 'JD'}를 삭제할까요?`} onClose={() => setDeleting(null)}><div className="delete-file"><FileText size={19} /><strong>{deleting.name}</strong></div><p>연결된 개인화 결과 {relatedCompanies(deleting, workspace.companies).length}개가 미리보기에서 초기화됩니다. 기업 브리프는 유지됩니다.</p><div className="modal-note"><Info size={16} />샘플 화면에서만 삭제됩니다. 새로고침하면 복원됩니다.</div><div className="modal-actions"><button className="button" onClick={() => setDeleting(null)}>취소</button><button className="button button-primary" onClick={() => { setWorkspace(removeDemoMaterial(workspace, deleting)); setDeleting(null); notify('샘플 자료와 연결된 개인화 표시를 초기화했어요.') }}>삭제</button></div></Modal>}
  {toast && <div className="toast" role="status"><Check size={16} />{toast}<button className="icon-button" aria-label="알림 닫기" onClick={() => setToast('')}><X size={15} /></button></div>}
  </>
}

function UploadDialog({ kind, onClose }: { kind: 'report' | 'cv' | 'jd'; onClose: () => void }) {
  const [files, setFiles] = useState<File[]>([])
  const [error, setError] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)
  const label = kind === 'report' ? '사업보고서' : kind === 'cv' ? 'CV' : '직무기술서'
  const accept = (next: FileList | File[]) => {
    const candidates = Array.from(next)
    if (candidates.some((file) => !file.name.toLowerCase().endsWith('.pdf'))) { setError('PDF 파일을 선택해 주세요.'); return }
    setFiles(candidates); setError('')
  }
  return <Modal title={`${label} 등록`} onClose={onClose}><p>파일 선택 동작을 미리 확인할 수 있어요.<br />실제 PDF 등록은 로그인 후 내 작업 공간에서 이용할 수 있어요. 분석 기능은 준비 중입니다.</p><input ref={inputRef} className="sr-only" type="file" accept=".pdf,application/pdf" multiple onChange={(event) => { if (event.target.files) accept(event.target.files) }} aria-label={`${label} PDF 선택`} /><button className="upload-dropzone modal-dropzone" onClick={() => inputRef.current?.click()} onDragOver={(event) => event.preventDefault()} onDrop={(event) => { event.preventDefault(); accept(event.dataTransfer.files) }}><Upload size={25} strokeWidth={1.2} /><strong>PDF를 놓거나 클릭해 선택하세요</strong><span>내 기기의 파일 선택</span></button>{error && <p role="alert" className="input-error">{error}</p>}{files.length > 0 && <ul className="chosen-files">{files.map((file, index) => <li key={`${file.name}-${index}`}><FileText size={15} /><span>{file.name}</span><small>{(file.size / 1024 / 1024).toFixed(1)} MB</small></li>)}</ul>}<div className="modal-note"><Info size={16} />파일 내용은 읽거나 서버로 전송하지 않습니다.</div><div className="modal-actions"><button className="button" onClick={onClose}>닫기</button><button className="button button-primary" disabled>업로드 연동 준비 중</button></div></Modal>
}
