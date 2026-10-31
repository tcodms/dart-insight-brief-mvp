import { useEffect, useState } from 'react'
import { ArrowRight, FileText, LoaderCircle } from 'lucide-react'
import { api } from '../api'
import type { Page } from '../types'

interface HomeDocument { kind: 'report' | 'cv' | 'jd' }
interface HomeAnalysis { id: string; companyName: string; createdAt: string }
interface HomeJob { id: string; status: string; stage: string; jobType: 'brief' | 'personal' }

export default function HomeDashboard({ name, documents, navigate, onUpload }: {
  name: string; documents: HomeDocument[]; navigate: (page: Page) => void; onUpload: () => void
}) {
  const [briefs, setBriefs] = useState<HomeAnalysis[]>([])
  const [personal, setPersonal] = useState<HomeAnalysis[]>([])
  const [jobs, setJobs] = useState<HomeJob[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [revision, setRevision] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    let timer: ReturnType<typeof setTimeout> | undefined
    Promise.all([
      api<{ briefs: HomeAnalysis[]; personal: HomeAnalysis[] }>('/api/analyses', { signal: controller.signal }),
      api<{ jobs: HomeJob[] }>('/api/jobs', { signal: controller.signal }),
    ]).then(([analyses, status]) => {
      setBriefs(analyses.briefs); setPersonal(analyses.personal); setJobs(status.jobs); setError(false)
      if (status.jobs.some((job) => job.status === 'queued' || job.status === 'running')) timer = setTimeout(() => setRevision((value) => value + 1), 3000)
    }).catch(() => { if (!controller.signal.aborted) setError(true) })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => { controller.abort(); clearTimeout(timer) }
  }, [revision])

  const activeJob = jobs.find((job) => job.status === 'queued' || job.status === 'running')
  const hasReport = documents.some((document) => document.kind === 'report')
  const latest = [...briefs.map((item) => ({ ...item, kind: '기업 브리프' })), ...personal.map((item) => ({ ...item, kind: '기여 보고서' }))]
    .sort((a, b) => b.createdAt.localeCompare(a.createdAt))[0]
  const isFirstUse = briefs.length === 0 && personal.length === 0
  const next = activeJob ? { label: '진행 중인 분석 확인', title: '분석이 진행 중입니다.', detail: activeJob.stage || '결과를 준비하고 있습니다.', action: () => navigate('workspace') }
    : !hasReport ? { label: '첫 번째 단계', title: '사업보고서를 등록해 주세요.', detail: '기업 브리프를 만들기 위해 사업보고서 PDF가 필요합니다.', action: onUpload }
    : !briefs.length ? { label: '다음 단계', title: '첫 기업 브리프를 만들어 보세요.', detail: '등록한 사업보고서에서 사업·실적·전략을 정리합니다.', action: () => navigate('workspace') }
    : !personal.length ? { label: '다음 단계', title: '내 경험을 기업과 연결해 보세요.', detail: '기업 브리프에 CV와 직무기술서를 더해 기여 보고서를 만듭니다.', action: () => navigate('workspace') }
    : { label: '이어서 보기', title: '최근 분석에서 이어가세요.', detail: `${latest?.companyName ?? '기업'}의 결과를 확인하거나 새 분석을 시작할 수 있습니다.`, action: () => navigate('workspace') }

  const guide = <section className="dashboard-guide" aria-labelledby="dashboard-guide-title"><div className="dashboard-guide-heading"><span className="eyebrow">HOW IT WORKS</span><h2 id="dashboard-guide-title">이렇게 시작하세요</h2></div><div className="dashboard-guide-steps">
    <div className="dashboard-guide-step"><span>01</span><h3>사업보고서 등록</h3><p>PDF를 등록하세요. 파일이 없다면 DART에서 보고서를 찾을 수 있습니다.</p><button onClick={onUpload}>사업보고서 등록 <ArrowRight size={15} /></button></div>
    <div className="dashboard-guide-step"><span>02</span><h3>기업 브리프 생성</h3><p>등록한 보고서를 분석하고 기업 내용과 원문 근거를 확인하세요.</p><button onClick={() => navigate('workspace')}>분석 화면으로 <ArrowRight size={15} /></button></div>
    <div className="dashboard-guide-step"><span>03</span><h3>내 경험 연결</h3><p>JD와 CV를 등록한 뒤 기여 보고서에서 직무와 내 경험을 연결하세요.</p><button onClick={() => navigate('materials')}>JD·CV 등록 <ArrowRight size={15} /></button></div>
  </div></section>

  return <section className="dashboard-home" aria-label="내 작업 홈">
    <div className="dashboard-home-intro"><span className="eyebrow">YOUR NEXT STEP</span><h1>{name}님, 안녕하세요.</h1><p>오늘 이어서 할 작업을 확인하세요.</p></div>
    {loading ? <div className="dashboard-home-loading" role="status"><LoaderCircle className="spin" size={22} />작업 상태를 불러오는 중입니다.</div>
      : error ? <div className="dashboard-home-loading" role="alert">작업 상태를 불러오지 못했습니다. <button className="text-button" onClick={() => { setLoading(true); setRevision((value) => value + 1) }}>다시 시도</button></div>
      : <>
        <div className="dashboard-next"><div><span className="eyebrow">{next.label}</span><h2>{next.title}</h2><p>{next.detail}</p></div><button className="button button-primary" onClick={next.action}>계속하기 <ArrowRight size={17} /></button></div>
        {isFirstUse && guide}
        <div className="dashboard-home-bottom">
          <div className="dashboard-status"><span className="eyebrow">CURRENT STATUS</span><h2>지금 상태</h2><p>{activeJob ? <><span className="dashboard-live-dot" />{activeJob.jobType === 'brief' ? '기업 브리프' : '기여 보고서'} 분석 중 · {activeJob.stage}</> : '진행 중인 분석이 없습니다.'}</p></div>
          <div className="dashboard-recent"><span className="eyebrow">LAST WORK</span><h2>최근 작업</h2>{latest ? <button onClick={() => navigate('workspace')}><FileText size={20} /><span><strong>{latest.companyName}</strong><small>{latest.kind} · {latest.createdAt.slice(0, 10)}</small></span><ArrowRight size={17} /></button> : <p>완료된 분석이 생기면 여기에 표시됩니다.</p>}</div>
        </div>
        {!isFirstUse && guide}
        <div className="dashboard-shortcuts"><button onClick={() => navigate('workspace')}>내 분석 보기 <ArrowRight size={15} /></button><button onClick={() => navigate('materials')}>내 자료 관리 <ArrowRight size={15} /></button></div>
      </>}
  </section>
}
