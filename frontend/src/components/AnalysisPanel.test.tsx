// @vitest-environment jsdom
import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import AnalysisPanel from './AnalysisPanel'
import type { Session } from '../api'

vi.mock('./PdfEvidenceViewer', () => ({ default: ({ page, quote }: { page: number; quote: string | null }) => <div aria-label="사업보고서 원문" data-page={page} data-quote={quote ?? ''} /> }))

const session: Session = { authenticated: true, googleConfigured: true, csrfToken: 'csrf', user: { id: 'u', name: '테스트', email: 'u@example.test' } }
const documents = [{ id: 'report', name: '사업보고서.pdf', kind: 'report' as const, version: 'v1' }]
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status })
beforeEach(() => { vi.spyOn(window, 'scrollTo').mockImplementation(() => {}) })
afterEach(() => { cleanup(); vi.unstubAllGlobals(); vi.restoreAllMocks(); window.history.replaceState({}, '', '/') })

it('starts analysis with selected document ID and shows the persisted job stage', async () => {
  let started = false
  const job = { id: 'job', jobType: 'brief', status: 'queued', stage: '분석 대기 중', resultId: null, error: null }
  const fetchMock = vi.fn(async (url: string, options?: RequestInit) => {
    if (options?.method === 'POST') { started = true; return json(job, 202) }
    if (url.endsWith('/annotations')) return json({ contentVersion: 'a'.repeat(64), annotations: [] })
    if (url === '/api/jobs') return json({ jobs: started ? [job] : [] })
    if (url === '/api/analyses') return json({ briefs: [], personal: [] })
    return json({ briefConfigured: true, personalConfigured: true, personalRequiresJd: true })
  })
  vi.stubGlobal('fetch', fetchMock)
  render(<AnalysisPanel documents={documents} session={session} onExpired={vi.fn()} />)
  fireEvent.click(await screen.findByRole('button', { name: /^새 기업 브리프$/ }))
  fireEvent.change(await screen.findByLabelText('등록한 사업보고서'), { target: { value: 'report' } })
  fireEvent.click(screen.getByRole('button', { name: '기업 분석 시작' }))
  await screen.findByText('분석 대기 중')
  const post = fetchMock.mock.calls.find(([, options]) => options?.method === 'POST')!
  expect(JSON.parse(post[1]!.body as string)).toEqual({ jobType: 'brief', reportDocumentId: 'report' })
  expect(new Headers(post[1]?.headers).get('X-CSRF-Token')).toBe('csrf')
  expect((screen.getByRole('button', { name: /^새 기업 브리프$/ }) as HTMLButtonElement).disabled).toBe(true)
})

it('renders saved Agent markdown and connects evidence to the original PDF page', async () => {
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    if (url.endsWith('/annotations')) return json({ contentVersion: 'a'.repeat(64), annotations: [] })
    if (url === '/api/jobs') return json({ jobs: [] })
    if (url === '/api/analyses') return json({ briefs: [{ id: 'b', companyName: '기업 A', reportName: '사업보고서.pdf', reportDocumentId: 'report', createdAt: '2026-10-28' }], personal: [] })
    if (url === '/api/analyses/brief/b') return json({ id: 'b', kind: 'brief', reportDocumentId: 'report', result: { markdown: '# 저장된 기업 브리프\n[검증한 결과 내용](#evidence-id-B01-E002)\n\n- **기업 사실:** 백신 사업을 운영합니다.\n- **왜 중요한가:** 회사의 사업 방향입니다.\n- **출처:** 원본 7쪽 · 근거 B01-E001\n\n![외부 이미지](https://example.test/tracker.png)' }, evidence: [{ id: 'B01-E001', page: 7, quote: '원문 인용', section: '사업' }, { id: 'B01-E002', page: 8, quote: '두 번째 인용', section: '사업' }] })
    return json({ briefConfigured: true, personalConfigured: true, personalRequiresJd: true })
  }))
  render(<AnalysisPanel documents={documents} session={session} onExpired={vi.fn()} />)
  fireEvent.click(await screen.findByRole('button', { name: /기업 A.*기업 브리프 1/ }))
  fireEvent.click(screen.getByRole('button', { name: /사업보고서.pdf.*결과 보기/ }))
  await screen.findByRole('heading', { name: '저장된 기업 브리프' })
  expect(screen.queryByLabelText('사업보고서 원문')).toBeNull()
  fireEvent.click(screen.getByRole('button', { name: '검증한 결과 내용' }))
  expect(await screen.findByText('두 번째 인용', { selector: 'blockquote' })).toBeTruthy()
  fireEvent.click(screen.getByRole('button', { name: '원문 열기' }))
  expect(screen.getByLabelText('사업보고서 원문').getAttribute('data-page')).toBe('8')
  expect(screen.getByLabelText('사업보고서 원문').getAttribute('data-quote')).toBe('두 번째 인용')
  fireEvent.click(screen.getByRole('button', { name: '닫기' }))
  fireEvent.click(screen.getByLabelText('패널 닫기'))
  fireEvent.click(screen.getByText('내보내기'))
  expect(screen.getByRole('link', { name: 'Markdown 다운로드' }).getAttribute('href')).toBe('/api/analyses/brief/b/download')
  expect(screen.queryByRole('img')).toBeNull()
  expect(new URLSearchParams(window.location.search).get('result')).toBe('b')
  expect(screen.queryByRole('button', { name: /기업 A.*기업 브리프 1/ })).toBeNull()
  expect(screen.queryByLabelText('등록한 사업보고서')).toBeNull()
  fireEvent.click(screen.getByRole('button', { name: '폴더로 돌아가기' }))
  expect(screen.getByRole('button', { name: /사업보고서.pdf.*결과 보기/ })).toBeTruthy()
  expect(screen.queryByRole('link', { name: 'Markdown 다운로드' })).toBeNull()
})

it('connects contribution facts to saved quotes and opens the PDF only on request', async () => {
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    if (url.endsWith('/annotations')) return json({ contentVersion: 'a'.repeat(64), annotations: [] })
    if (url === '/api/jobs') return json({ jobs: [] })
    if (url === '/api/analyses') return json({ briefs: [], personal: [{ id: 'p', companyName: '기업 A', targetRole: '품질관리', cvVersion: 'v1', createdAt: '2026-10-28' }] })
    if (url === '/api/analyses/personal/p') return json({ id: 'p', kind: 'personal', reportDocumentId: 'report', result: { markdown: '# 기여 보고서\n\n## 핵심 요약\n- **회사 사실:** [B01-E032] 품질관리 체계를 운영합니다.\n\n## 지원 동기\n이 경험을 연결합니다.' }, evidence: [{ id: 'B01-E032', page: 40, quote: '품질관리 체계', section: '사업' }] })
    return json({ briefConfigured: true, personalConfigured: true, personalRequiresJd: true })
  }))
  render(<AnalysisPanel mode="personal" documents={documents} session={session} onExpired={vi.fn()} />)
  fireEvent.click(await screen.findByRole('button', { name: /기업 A.*기여 보고서 1/ }))
  fireEvent.click(screen.getByRole('button', { name: /품질관리.*결과 보기/ }))
  await screen.findByText(/품질관리 체계를 운영합니다/)
  expect(screen.queryByLabelText('사업보고서 원문')).toBeNull()
  expect(screen.queryByText('원문 근거')).toBeNull()
  expect(screen.getByRole('navigation', { name: '보고서 목차' })).toBeTruthy()
  expect(screen.getByRole('heading', { name: '지원 동기' })).toBeTruthy()
  expect(screen.getByText('이 경험을 연결합니다.')).toBeTruthy()
  fireEvent.click(screen.getByRole('button', { name: '품질관리 체계를 운영합니다.' }))
  expect(await screen.findByText('품질관리 체계', { selector: 'blockquote' })).toBeTruthy()
  fireEvent.click(screen.getByRole('button', { name: '원문 열기' }))
  expect(screen.getByLabelText('사업보고서 원문').getAttribute('data-page')).toBe('40')
  expect(screen.getByLabelText('사업보고서 원문').getAttribute('data-quote')).toBe('품질관리 체계')
})

it('groups repeated analyses under one company folder', async () => {
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    if (url.endsWith('/annotations')) return json({ contentVersion: 'a'.repeat(64), annotations: [] })
    if (url === '/api/jobs') return json({ jobs: [] })
    if (url === '/api/analyses') return json({ briefs: [
      { id: 'b1', companyName: '기업 A', reportName: '2025.pdf', reportDocumentId: 'report', createdAt: '2026-10-28' },
      { id: 'b2', companyName: '기업 A', reportName: '2026.pdf', reportDocumentId: 'report', createdAt: '2026-10-29' },
    ], personal: [{ id: 'p1', companyName: '기업 B', targetRole: '개발', cvVersion: 'v1', createdAt: '2026-10-30' }] })
    return json({ briefConfigured: true, personalConfigured: true, personalRequiresJd: true })
  }))
  render(<AnalysisPanel documents={documents} session={session} onExpired={vi.fn()} />)
  const folder = await screen.findByRole('button', { name: /기업 A.*기업 브리프 2/ })
  expect(screen.getAllByRole('button', { name: /기업 [AB].*기업 브리프/ })).toHaveLength(1)
  expect(screen.queryByLabelText('등록한 사업보고서')).toBeNull()
  expect(screen.queryByRole('button', { name: /2025.pdf.*결과 보기/ })).toBeNull()
  fireEvent.click(folder)
  expect(new URLSearchParams(window.location.search).get('company')).toBe('기업 A')
  expect(document.activeElement).toBe(screen.getByRole('heading', { name: '기업 A', level: 1 }))
  expect(screen.getByRole('button', { name: /2025.pdf.*결과 보기/ })).toBeTruthy()
  expect(screen.getByRole('button', { name: /2026.pdf.*결과 보기/ })).toBeTruthy()
  expect(screen.queryByRole('button', { name: /개발.*결과 보기/ })).toBeNull()
  window.history.replaceState({}, '', '/')
  fireEvent.popState(window)
  expect(screen.getAllByRole('button', { name: /기업 [AB].*기업 브리프/ })).toHaveLength(1)
  expect(screen.queryByRole('button', { name: /2025.pdf.*결과 보기/ })).toBeNull()
})

it('opens personal analysis only when requested and submits the chosen inputs', async () => {
  let started = false
  const brief = { id: 'b', companyName: '기업 A', reportName: '사업보고서.pdf', reportDocumentId: 'report', createdAt: '2026-11-02' }
  const job = { id: 'j', jobType: 'personal', status: 'queued', stage: '기여 분석 대기', resultId: null, error: null }
  const mock = vi.fn(async (url: string, options?: RequestInit) => {
    if (options?.method === 'POST') { started = true; return json(job, 202) }
    if (url === '/api/jobs') return json({ jobs: started ? [job] : [] })
    if (url === '/api/analyses') return json({ briefs: [brief], personal: [] })
    return json({ briefConfigured: true, personalConfigured: true, personalRequiresJd: true })
  })
  vi.stubGlobal('fetch', mock)
  window.history.replaceState({}, "", "/?view=contribution&fromBrief=b")
  render(<AnalysisPanel mode="personal" documents={[...documents, { id: 'cv', name: 'CV.pdf', kind: 'cv', version: 'v1' }, { id: 'jd', name: 'JD.pdf', kind: 'jd', version: 'v1' }]} session={session} onExpired={vi.fn()} />)
  await screen.findByRole("dialog", { name: "새 기여 보고서" })
  expect((screen.getByLabelText('완성된 기업 브리프') as HTMLSelectElement).value).toBe('b')
  fireEvent.change(screen.getByLabelText('직무기술서'), { target: { value: 'jd' } })
  fireEvent.change(screen.getByLabelText('CV'), { target: { value: 'cv' } })
  fireEvent.click(screen.getByRole('button', { name: '기여 분석 시작' }))
  await screen.findByText('기여 분석 대기')
  expect(screen.queryByRole('dialog')).toBeNull()
  const post = mock.mock.calls.find(([, options]) => options?.method === 'POST')!
  expect(JSON.parse(post[1]!.body as string)).toEqual({ jobType: 'personal', briefId: 'b', cvDocumentId: 'cv', jdDocumentId: 'jd' })
})

it('shows the JD name on contribution cards and keeps document management separate', async () => {
  const jd = { id: 'jd-a', name: '기계직무.pdf', kind: 'jd' as const, version: 'v1' }
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    if (url.endsWith('/annotations')) return json({ contentVersion: 'a'.repeat(64), annotations: [] })
    if (url === '/api/jobs') return json({ jobs: [] })
    if (url === '/api/analyses') return json({ briefs: [], personal: [
      { id: 'p1', companyName: '기업 A', targetRole: '기계', cvVersion: 'v1', jdDocumentId: 'jd-a', createdAt: '2026-10-28' },
      { id: 'p2', companyName: '기업 A', targetRole: '기계', cvVersion: 'v2', jdDocumentId: 'jd-a', createdAt: '2026-10-29' },
      { id: 'p3', companyName: '기업 B', targetRole: '기계', cvVersion: 'v1', jdDocumentId: 'jd-b', createdAt: '2026-10-30' },
    ] })
    return json({ briefConfigured: true, personalConfigured: true, personalRequiresJd: true })
  }))
  render(<AnalysisPanel mode="personal" documents={[jd]} session={session} onExpired={vi.fn()} />)
  const folder = await screen.findByRole('button', { name: /기업 A.*기여 보고서 2/ })
  fireEvent.click(folder)
  expect(screen.getAllByText("JD · 기계직무.pdf")).toHaveLength(2)
  expect(screen.queryByRole("link", { name: /원본 PDF 보기/ })).toBeNull()
})
