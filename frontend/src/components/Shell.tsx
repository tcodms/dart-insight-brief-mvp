import { ArrowUpRight, ChevronsLeft, Compass, FileText, Files, Menu, X } from 'lucide-react'
import { useState } from 'react'
import type { ReactNode } from 'react'
import type { Page } from '../types'

const navigation = [
  { page: 'workspace' as Page, label: '기업 분석', icon: Files },
  { page: 'catalog' as Page, label: '기업 둘러보기', icon: Compass },
  { page: 'contribution' as Page, label: '기여 보고서', icon: FileText },
  { page: 'materials' as Page, label: '내 자료', icon: Files },
]

export default function Shell({ page, navigate, connected, onLogin, children, accountName, privateMode = false, onLogout }: {
  page: Page; navigate: (page: Page) => void;
  connected: boolean; onLogin: () => void; children: ReactNode;
  accountName?: string; privateMode?: boolean; onLogout?: () => void;
}) {
  const [open, setOpen] = useState(false)
  const current = page === 'home' || page === 'brief' ? 'workspace' : page
  return <div className="app-shell">
    {open && <button className="sidebar-scrim" aria-label="탐색 메뉴 닫기" onClick={() => setOpen(false)} />}
    <aside className={`sidebar ${open ? 'sidebar-open' : ''}`}>
      <button className="brand" onClick={() => { navigate('workspace'); setOpen(false) }} aria-label="DART Insight 홈">
        <span className="brand-symbol"><i /><i /><i /></span><span>DART<span className="brand-light"> Insight</span></span>
      </button>
      <button className="icon-button sidebar-collapse" aria-label="탐색 메뉴 닫기" onClick={() => setOpen(false)}><ChevronsLeft size={17} /></button>
      <div className="workspace-label">나의 리서치 공간</div>
      <nav aria-label="주요 메뉴">{navigation.map(({ page: target, label, icon: Icon }) =>
        <button key={target} className={`nav-item ${current === target ? 'nav-active' : ''}`} onClick={() => { navigate(target); setOpen(false) }} aria-current={current === target ? 'page' : undefined}>
          <Icon size={17} strokeWidth={1.5} /><span>{label}</span>{current === target && <span className="nav-dot" />}
        </button>
      )}</nav>
      <div className="sidebar-bottom">
        <div className="preview-label"><span className="connection-dot" />{privateMode ? '내 작업 공간' : '로그인 후 이용'}<span title={connected ? 'FastAPI 연결됨' : 'API 연결 확인 중'} className="connection-label">{connected ? '연결됨' : '연결 확인'}</span></div>
        {accountName ? <><button className="account-button" onClick={() => navigate('workspace')}><span className="avatar">{accountName.slice(0, 1)}</span><span><strong>{accountName}</strong><small>Google 계정 로그인됨</small></span><ArrowUpRight size={16} /></button><button className="text-button account-logout" onClick={onLogout}>로그아웃</button></> : <button className="account-button" onClick={onLogin}><span className="avatar">G</span><span><strong>나만의 공간 만들기</strong><small>Google 계정으로 시작</small></span><ArrowUpRight size={16} /></button>}
      </div>
    </aside>
    <div className="main-column">
      <header className="topbar">
        <button className="icon-button mobile-menu" aria-label="탐색 메뉴 열기" onClick={() => setOpen(!open)}>{open ? <X size={19} /> : <Menu size={19} />}</button>
        <div className="breadcrumb"><span>워크스페이스</span><span>/</span><strong>{navigation.find((item) => item.page === current)?.label}</strong></div>
        <div id="report-navigation" />
        <div id="report-actions" />
        <div className="topbar-actions"><span className="preview-chip">{privateMode ? '개인 작업 공간' : '로그인'}</span></div>
      </header>
      <main id="main-content" key={page}>{children}</main>
      <footer className="app-footer"><span>DART Insight</span><span>근거를 읽고, 가능성을 발견하세요.</span><span>{privateMode ? '개인 자료 · 실제 Agent 분석' : '사업보고서 기반 기업 분석'}</span></footer>
    </div>
  </div>
}
