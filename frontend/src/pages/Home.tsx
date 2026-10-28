import { ArrowRight, ArrowUpRight, FileText, GitCompareArrows, Link2, Quote } from 'lucide-react'

export default function Home({ onExplore, onLogin }: { onExplore: () => void; onLogin: () => void }) {
  return <div className="home-page">
    <div className="home-nav"><span className="eyebrow">A BETTER WAY TO UNDERSTAND COMPANIES</span><button className="text-button" onClick={onLogin}>Google로 시작하기 <ArrowUpRight size={15} /></button></div>
    <section className="hero">
      <div className="hero-copy"><div className="section-kicker"><span />문서에서 발견하는 나의 다음 기회</div><h1>기업을 이해하고,<br />나의 경험을<br /><span className="hero-last">연결하세요<span className="title-dot">.</span></span></h1><p>긴 사업보고서 속 중요한 이야기부터<br />내 경험을 활용할 수 있는 지점까지.<br />근거와 함께, 나만의 기업 분석을 시작하세요.</p><div className="hero-actions"><button className="button button-primary" onClick={onExplore}>기업 분석 시작하기 <ArrowRight size={16} /></button><span className="microcopy">Google 로그인 후 내 문서를 등록하세요</span></div></div>
      <div className="hero-visual" aria-label="기업 사실과 개인 경험을 연결하는 예시"><div className="visual-grid" /><div className="hero-paper"><div className="paper-topline"><FileText size={16} /><span>업로드한 사업보고서</span><span>분석 흐름</span></div><div className="paper-content"><span className="eyebrow">BUSINESS REPORT</span><h3>기업의 방향을 읽는 일.</h3><div className="skeleton-line width-95" /><div className="skeleton-line width-80" /><div className="sample-highlight">문서에서 확인한 사업과 전략을<br />원문 근거와 함께 정리합니다.</div><div className="skeleton-line width-95" /><div className="skeleton-line width-65" /><div className="mini-table"><span>구분</span><span>당기</span><span>전기</span><span>사업 현황</span><span>—</span><span>—</span><span>투자 계획</span><span>—</span><span>—</span></div></div></div><div className="floating-evidence"><span className="floating-icon"><Quote size={17} /></span><div><span className="eyebrow">원문에서 찾은 연결</span><strong>내 경험과 기업의 연결</strong><p>나의 경험을 기업의 실제 활동과 연결합니다.</p><span className="source-note">사업보고서 <span>↗</span> CV·JD</span></div></div><span className="visual-caption">EVERY INSIGHT STARTS WITH EVIDENCE.</span></div>
    </section>
    <div className="home-divider"><span>읽는 것을 넘어, 연결하는 분석.</span><span>01 — 03</span></div>
    <section className="feature-grid">{[
      { number: '01', icon: FileText, title: '기업의 핵심을 한눈에', text: '사업·전략·실적·조직 정보를 취업 준비에 필요한 관점으로 정리합니다.' },
      { number: '02', icon: Link2, title: '내 경험과의 연결', text: 'CV와 직무기술서를 바탕으로 가능한 기여와 더 준비할 점을 살펴봅니다.' },
      { number: '03', icon: GitCompareArrows, title: '나란히 보는 가능성', text: '최대 3개 기업·직무를 공통 항목으로 비교하고, 판단의 근거를 확인합니다.' },
    ].map(({ number, icon: Icon, title, text }) => <article className="feature-item" key={number}><div><Icon size={21} strokeWidth={1.3} /><span>{number}</span></div><h2>{title}</h2><p>{text}</p></article>)}</section>
  </div>
}
