import { useEffect, useRef, useState } from 'react'
import { ArrowRight, Check, Info, LoaderCircle, RefreshCw, X } from 'lucide-react'
import type { Page } from './types'
import Shell from './components/Shell'
import { Modal } from './components/ui'
import Home from './pages/Home'
import PrivateWorkspace from './pages/PrivateWorkspace'
import { api, ApiError } from './api'
import type { Session } from './api'

const pages: Page[] = ['home', 'workspace', 'brief', 'materials', 'contribution', 'compare']
function readPage(): Page {
  const value = new URLSearchParams(window.location.search).get('view')
  return pages.includes(value as Page) ? value as Page : 'home'
}

export default function App() {
  const [page, setPage] = useState<Page>(readPage)
  const [theme, setTheme] = useState<'dark' | 'light'>(() => { try { return localStorage.getItem('dart-theme') === 'light' ? 'light' : 'dark' } catch { return 'dark' } })
  const [phase, setPhase] = useState<'loading' | 'ready' | 'error'>('loading')
  const [refresh, setRefresh] = useState(0)
  const [session, setSession] = useState<Session>({ authenticated: false, googleConfigured: false, user: null, csrfToken: null })
  const [loginOpen, setLoginOpen] = useState(false)
  const [toast, setToast] = useState('')
  const toastTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', theme === 'dark' ? '#151515' : '#f6f6f4')
    try { localStorage.setItem('dart-theme', theme) } catch { /* Theme works without storage. */ }
  }, [theme])
  useEffect(() => {
    const url = new URL(window.location.href)
    if (url.searchParams.has('demo')) {
      url.searchParams.delete('demo')
      window.history.replaceState({}, '', url)
    }
    const handle = () => setPage(readPage())
    window.addEventListener('popstate', handle)
    return () => window.removeEventListener('popstate', handle)
  }, [])
  useEffect(() => {
    const controller = new AbortController()
    let active = true
    const timeout = setTimeout(() => controller.abort(), 10000)
    setPhase('loading')
    Promise.all([api<{ status: string }>('/api/health', { signal: controller.signal }), api<Session>('/api/auth/session', { signal: controller.signal })])
      .then(([health, auth]) => {
        if (!active) return
        if (health.status !== 'ok' || typeof auth.authenticated !== 'boolean' || (auth.authenticated && !auth.user)) throw new Error('Invalid session response')
        setSession(auth); setPhase('ready')
      }).catch(() => { if (active) setPhase('error') }).finally(() => clearTimeout(timeout))
    return () => { active = false; clearTimeout(timeout); controller.abort() }
  }, [refresh])
  useEffect(() => () => clearTimeout(toastTimer.current), [])

  const navigate = (target: Page) => {
    if (!session.authenticated && target !== 'home') { setLoginOpen(true); return }
    setPage(target)
    const url = new URL(window.location.href)
    url.search = ''
    if (target !== 'home') url.searchParams.set('view', target)
    window.history.pushState({}, '', url)
    window.scrollTo({ top: 0, behavior: 'instant' })
  }
  const logout = async () => {
    try { await api('/api/auth/logout', { method: 'POST' }, session.csrfToken); window.location.assign('/') }
    catch (err) {
      if (err instanceof ApiError && err.status === 401) { window.location.assign('/'); return }
      setToast(err instanceof Error ? err.message : '로그아웃하지 못했습니다.')
      clearTimeout(toastTimer.current); toastTimer.current = setTimeout(() => setToast(''), 4000)
    }
  }

  return <><a className="skip-link" href="#main-content">본문으로 건너뛰기</a><Shell page={page} navigate={navigate} theme={theme} toggleTheme={() => setTheme(theme === 'dark' ? 'light' : 'dark')} connected={phase === 'ready'} onLogin={() => setLoginOpen(true)} accountName={session.user?.name} privateMode={session.authenticated} onLogout={logout}>
    {new URLSearchParams(window.location.search).get('auth') === 'failed' && <div className="notice" role="alert"><Info size={16} /><p>Google 로그인을 완료하지 못했습니다. 다시 시도해 주세요.</p></div>}
    {phase === 'loading' ? <div className="page-loading" role="status"><LoaderCircle size={25} className="spin" /><h2>로그인 상태를 확인하고 있어요</h2></div> : phase === 'error' ? <div className="page-loading"><Info size={29} /><h2>서비스에 연결할 수 없어요</h2><p>잠시 후 다시 시도해 주세요.</p><button className="button" onClick={() => setRefresh((value) => value + 1)}><RefreshCw size={15} />다시 연결</button></div> : session.authenticated ? <PrivateWorkspace page={page} session={session} onLogin={() => { window.location.assign('/api/auth/login') }} /> : <Home onExplore={() => setLoginOpen(true)} onLogin={() => setLoginOpen(true)} />}
  </Shell>
  {loginOpen && <Modal title={session.googleConfigured ? 'Google 계정으로 시작하세요' : 'Google 로그인 설정을 기다리고 있어요'} onClose={() => setLoginOpen(false)}><div className="modal-feature-icon">G</div><p>{session.googleConfigured ? '로그인하면 내 PDF를 등록하고 기업 분석을 시작할 수 있습니다.' : '서비스의 Google OAuth 인증 정보가 아직 등록되지 않았습니다.'}</p><div className="modal-note"><Info size={16} />내가 등록한 자료와 실제 분석 결과만 표시합니다.</div><div className="modal-actions"><button className="button" onClick={() => setLoginOpen(false)}>닫기</button><button className="button button-primary" disabled={!session.googleConfigured || phase !== 'ready'} onClick={() => { window.location.assign('/api/auth/login') }}>Google로 로그인 <ArrowRight size={15} /></button></div></Modal>}
  {toast && <div className="toast" role="status"><Check size={16} />{toast}<button className="icon-button" aria-label="알림 닫기" onClick={() => setToast('')}><X size={15} /></button></div>}
  </>
}
