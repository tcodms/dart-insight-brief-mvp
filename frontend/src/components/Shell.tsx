import { ArrowUpRight, ChevronsLeft, Files, GitCompareArrows, Home, Menu, Moon, Sun, X } from 'lucide-react'
import { useState } from 'react'
import type { ReactNode } from 'react'
import type { Page } from '../types'

const navigation = [
  { page: 'home' as Page, label: '홈', icon: Home },
  { page: 'workspace' as Page, label: '내 분석', icon: Files },
  { page: 'materials' as Page, label: '내 자료', icon: Files },
  { page: 'compare' as Page, label: '기업 비교', icon: GitCompareArrows },
]

export default function Shell({ page, navigate, theme, toggleTheme, connected, onLogin, children, accountName, privateMode = false, onLogout, onSwitchWorkspace }: {
  page: Page; navigate: (page: Page) => void; theme: 'dark' | 'light'; toggleTheme: () => void;
  connected: boolean; onLogin: () => void; children: ReactNode;
  accountName?: string; privateMode?: boolean; onLogout?: () => void; onSwitchWorkspace?: () => void;
}) {
  const [open, setOpen] = useState(false)
  const current = page === 'brief' || page === 'contribution' ? 'workspace' : page
  return <div className="app-shell">
    {open && <button className="sidebar-scrim" aria-label="탐색 메뉴 닫기" onClick={() => setOpen(false)} />}
    <aside className={`sidebar ${open ? 'sidebar-open' : ''}`}>
      <button className="brand" onClick={() => { navigate('home'); setOpen(false) }} aria-label="DART Insight 홈">
        <span className="brand-symbol"><i /><i /><i /></span><span>DART<span className="brand-light"> Insight</span></span>
      </button>
      <button className="icon-button sidebar-collapse" aria-label="탐색 메뉴 닫기" onClick={() => setOpen(false)}><ChevronsLeft size={17} /></button>
      <div className="workspace-label">나의 리서치 공간 <span>01</span></div>
      <nav aria-label="주요 메뉴">{navigation.map(({ page: target, label, icon: Icon }) =>
        <button key={target} className={`nav-item ${current === target ? 'nav-active' : ''}`} onClick={() => { navigate(target); setOpen(false) }} aria-current={current === target ? 'page' : undefined}>
          <Icon size={17} strokeWidth={1.5} /><span>{label}</span>{current === target && <span className="nav-dot" />}
        </button>
      )}</nav>
      <div className="sidebar-note"><span className="eyebrow">DOCUMENT TO INSIGHT</span><p>기업의 방향과<br />나의 경험이 만나는 곳.</p><span className="note-rule" /></div>
      <div className="sidebar-bottom">
        <div className="preview-label"><span className="connection-dot" />{privateMode ? '내 작업 공간' : '샘플 워크스페이스'}<span title={connected ? 'FastAPI 연결됨' : 'API 연결 확인 중'} className="connection-label">{connected ? 'API 연결됨' : '연결 확인'}</span></div>
        {accountName ? <><button className="account-button" onClick={onSwitchWorkspace}><span className="avatar">{accountName.slice(0, 1)}</span><span><strong>{accountName}</strong><small>{privateMode ? '샘플 화면 보기' : '내 작업 공간으로'}</small></span><ArrowUpRight size={16} /></button><button className="text-button account-logout" onClick={onLogout}>로그아웃</button></> : <button className="account-button" onClick={onLogin}><span className="avatar">G</span><span><strong>나만의 공간 만들기</strong><small>Google 계정으로 시작</small></span><ArrowUpRight size={16} /></button>}
      </div>
    </aside>
    <div className="main-column">
      <header className="topbar">
        <button className="icon-button mobile-menu" aria-label="탐색 메뉴 열기" onClick={() => setOpen(!open)}>{open ? <X size={19} /> : <Menu size={19} />}</button>
        <div className="breadcrumb"><span>워크스페이스</span><span>/</span><strong>{page === 'home' ? '시작하기' : page === 'materials' ? '내 자료' : page === 'compare' ? '기업 비교' : '내 분석'}</strong></div>
        <div className="topbar-actions"><span className="preview-chip">{privateMode ? '개인 작업 공간' : '샘플 미리보기'}</span><div className="theme-switch" aria-label="화면 테마"><button aria-label="라이트 모드" aria-pressed={theme === 'light'} onClick={() => { if (theme !== 'light') toggleTheme() }}><Sun size={15} /></button><button aria-label="다크 모드" aria-pressed={theme === 'dark'} onClick={() => { if (theme !== 'dark') toggleTheme() }}><Moon size={14} /></button></div></div>
      </header>
      <main id="main-content" key={page}>{children}</main>
      <footer className="app-footer"><span>DART Insight</span><span>근거를 읽고, 가능성을 발견하세요.</span><span>{privateMode ? '개인 문서 저장 · Agent 연결 전' : '예시 데이터 · 실제 분석 전'}</span></footer>
    </div>
  </div>
}
