import { ArrowRight, Files } from 'lucide-react'

export default function Home({ onLogin }: { onExplore: () => void; onLogin: () => void }) {
  return <section className="workspace-signin">
    <Files size={30} strokeWidth={1.2} />
    <h1>내 기업 분석</h1>
    <p>Google 계정으로 로그인해 저장한 기업과 보고서를 열어보세요.</p>
    <button className="button button-primary" onClick={onLogin}>Google로 시작하기 <ArrowRight size={16} /></button>
  </section>
}
