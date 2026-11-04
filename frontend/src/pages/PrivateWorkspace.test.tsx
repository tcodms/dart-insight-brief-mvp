// @vitest-environment jsdom
import { afterEach, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import PrivateWorkspace from './PrivateWorkspace'
import App from '../App'
import type { Session } from '../api'

const session: Session = { authenticated: true, googleConfigured: true, user: { id: 'u', name: '테스트 사용자', email: 'test@example.test' }, csrfToken: 'csrf' }
const document = { id: 'doc', name: '보고서.pdf', kind: 'report', version: 'v1', date: '2026.10.28', pages: 1, bytes: 1024 }
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
afterEach(() => { cleanup(); vi.unstubAllGlobals(); vi.restoreAllMocks(); window.history.replaceState({}, '', '/') })

function libraryResponse(url: string, documents: unknown[]) {
  if (url === '/api/jobs') return json({ jobs: [] })
  if (url === '/api/analyses') return json({ briefs: [], personal: [] })
  return json({ documents })
}

function renderReportLibrary() {
  render(<PrivateWorkspace page="workspace" session={session} navigate={vi.fn()} onLogin={vi.fn()} />)
  return screen.findByRole('button', { name: '사업보고서 관리' }).then((button) => fireEvent.click(button))
}

it('loads private document records with an authenticated download link', async () => {
  vi.stubGlobal('fetch', vi.fn(async (url: string) => libraryResponse(url, [document])))
  await renderReportLibrary()
  expect(await screen.findByText('보고서.pdf')).toBeTruthy()
  expect(screen.getByRole('link', { name: '보고서.pdf 다운로드' }).getAttribute('href')).toBe('/api/documents/doc/file')
  expect(screen.queryByText('A기업')).toBeNull()
  expect(screen.queryByRole('button', { name: '홈' })).toBeNull()
  expect(screen.queryByRole('button', { name: '계속하기' })).toBeNull()
})

it('shows saved PDFs only on 내 자료 and keeps 내 분석 focused on analyses', async () => {
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    if (url === '/api/documents') return json({ documents: [document] })
    if (url === '/api/analyses') return json({ briefs: [], personal: [] })
    if (url === '/api/jobs') return json({ jobs: [] })
    if (url === '/api/analysis/capabilities') return json({ briefConfigured: true, personalConfigured: true, personalRequiresJd: true })
    return json({})
  }))
  render(<PrivateWorkspace page="workspace" session={session} navigate={vi.fn()} onLogin={vi.fn()} />)
  expect(await screen.findByText('아직 생성된 분석이 없어요')).toBeTruthy()
  expect(screen.queryByRole('tablist', { name: '저장된 자료 종류' })).toBeNull()
  expect(screen.queryByRole('link', { name: '보고서.pdf 다운로드' })).toBeNull()
})

it('finds a company and links its latest DART report from the PDF dialog', async () => {
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    if (url.startsWith('/api/dart/companies')) return json({ companies: [{ corpCode: '00000001', name: '녹십자', stockCode: '006280' }] })
    if (url.startsWith('/api/dart/reports')) return json({ reports: [{ name: '사업보고서 (2025.12)', company: '녹십자', date: '20260318', corrected: false, url: 'https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260318000001' }] })
    return libraryResponse(url, [])
  }))
  await renderReportLibrary()
  await screen.findByText('등록한 사업보고서가 없어요')
  fireEvent.click(screen.getByRole('button', { name: 'PDF 등록' }))
  const dialog = screen.getByRole('dialog')
  fireEvent.change(within(dialog).getByRole('textbox', { name: '기업명' }), { target: { value: '녹십자' } })
  fireEvent.click(await within(dialog).findByRole('button', { name: /녹십자/ }))
  const link = await within(dialog).findByRole('link', { name: /사업보고서/ })
  expect(link.getAttribute('href')).toBe('https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260318000001')
  expect(link.getAttribute('target')).toBe('_blank')
})

it('posts the selected PDF and CSRF token then reloads the persisted list', async () => {
  let saved = false
  const fetchMock = vi.fn(async (_url: string, options?: RequestInit) => {
    if (options?.method === 'POST') { saved = true; return json(document, 201) }
    return libraryResponse(_url, saved ? [document] : [])
  })
  vi.stubGlobal('fetch', fetchMock)
  await renderReportLibrary()
  await screen.findByText('등록한 사업보고서가 없어요')
  fireEvent.click(screen.getByRole('button', { name: 'PDF 등록' }))
  const dialog = screen.getByRole('dialog')
  fireEvent.change(within(dialog).getByLabelText('사업보고서 PDF 선택'), { target: { files: [new File(['%PDF-example'], '보고서.pdf', { type: 'application/pdf' })] } })
  fireEvent.click(within(dialog).getByRole('button', { name: 'PDF 등록' }))
  await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull())
  expect(await screen.findByRole('link', { name: '보고서.pdf 다운로드' })).toBeTruthy()
  const post = fetchMock.mock.calls.find(([, options]) => options?.method === 'POST')!
  expect(post[1]?.body).toBeInstanceOf(FormData)
  expect((post[1]?.body as FormData).get('kind')).toBe('report')
  expect(new Headers(post[1]?.headers).get('X-CSRF-Token')).toBe('csrf')
})

it('returns from registering a PDF to the analysis setup and opens the completed result', async () => {
  vi.spyOn(window, 'scrollTo').mockImplementation(() => {})
  const result = { id: 'brief', companyName: '기업 A', reportName: document.name, reportDocumentId: document.id, createdAt: '2026-10-28' }
  const job = { id: 'job', jobType: 'brief', status: 'succeeded', stage: '분석 완료', resultId: result.id, error: null }
  let started = false
  const fetchMock = vi.fn(async (url: string, options?: RequestInit) => {
    if (url === '/api/documents') return options?.method === 'POST' ? json(document, 201) : json({ documents: [] })
    if (url === '/api/jobs' && options?.method === 'POST') {
      started = true
      return json({ ...job, status: 'queued', resultId: null }, 202)
    }
    if (url === '/api/jobs') return json({ jobs: started ? [job] : [] })
    if (url === '/api/analyses') return json({ briefs: started ? [result] : [], personal: [] })
    if (url === '/api/analyses/brief/brief') return json({ id: result.id, kind: 'brief', reportDocumentId: document.id, result: { markdown: '# 완성된 분석' }, evidence: [] })
    if (url.endsWith('/annotations')) return json({ contentVersion: 'a'.repeat(64), annotations: [] })
    return json({ briefConfigured: true, personalConfigured: true, personalRequiresJd: true })
  })
  vi.stubGlobal('fetch', fetchMock)
  render(<PrivateWorkspace page="workspace" session={session} navigate={vi.fn()} onLogin={vi.fn()} />)
  fireEvent.click(await screen.findByRole('button', { name: /^새 기업 브리프$/ }))
  fireEvent.click(within(screen.getByRole('dialog', { name: '새 기업 브리프' })).getByRole('button', { name: '사업보고서 등록' }))
  const registration = screen.getByRole('dialog', { name: '사업보고서 등록' })
  fireEvent.change(within(registration).getByLabelText('사업보고서 PDF 선택'), { target: { files: [new File(['%PDF-example'], document.name)] } })
  fireEvent.click(within(registration).getByRole('button', { name: 'PDF 등록' }))
  expect((await screen.findByLabelText('등록한 사업보고서') as HTMLSelectElement).value).toBe(document.id)
  fireEvent.click(screen.getByRole('button', { name: '기업 분석 시작' }))
  fireEvent.click(await screen.findByRole('button', { name: '완료 결과 보기' }))
  expect(await screen.findByRole('heading', { name: '완성된 분석' })).toBeTruthy()
  const post = fetchMock.mock.calls.find(([url, options]) => url === '/api/jobs' && options?.method === 'POST')
  expect(JSON.parse(post?.[1]?.body as string)).toEqual({ jobType: 'brief', reportDocumentId: document.id })
})

it('does not permit deletion until its impact has been loaded and confirms affected results', async () => {
  let deleted = false
  const fetchMock = vi.fn(async (url: string, options?: RequestInit) => {
    if (url.endsWith('/impact')) return json({ briefs: 1, personalAnalyses: 2, preservesBriefs: false })
    if (options?.method === 'DELETE') { deleted = true; return new Response(null, { status: 204 }) }
    return libraryResponse(url, deleted ? [] : [document])
  })
  vi.stubGlobal('fetch', fetchMock)
  await renderReportLibrary()
  fireEvent.click(await screen.findByRole('button', { name: '보고서.pdf 삭제' }))
  await screen.findByText('기업 브리프 1개, 개인화 분석 2개가 함께 삭제됩니다.')
  fireEvent.click(within(screen.getByRole('dialog')).getByRole('button', { name: '삭제' }))
  await screen.findByText('등록한 사업보고서가 없어요')
  expect(fetchMock.mock.calls.some(([url, options]) => url === '/api/documents/doc' && options?.method === 'DELETE')).toBe(true)
})

it('clears private records and asks for login on an expired session', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => json({ detail: '로그인이 필요합니다.' }, 401)))
  const onLogin = vi.fn()
  render(<PrivateWorkspace page="materials" session={session} navigate={vi.fn()} onLogin={onLogin} />)
  fireEvent.click(await screen.findByRole('button', { name: '다시 로그인' }))
  expect(onLogin).toHaveBeenCalledOnce()
  expect(screen.queryByRole('link', { name: '보고서.pdf 다운로드' })).toBeNull()
})

it('keeps Google login disabled until the backend reports OAuth is configured', async () => {
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    if (url === '/api/auth/session') return json({ authenticated: false, googleConfigured: false, user: null, csrfToken: null })
    if (url === '/api/health') return json({ status: 'ok' })
    return json({ dataType: 'fictional_demo', companies: [], materials: [] })
  }))
  render(<App />)
  await screen.findByTitle('FastAPI 연결됨')
  fireEvent.click(screen.getByRole('button', { name: 'Google로 시작하기' }))
  expect((within(screen.getByRole('dialog')).getByRole('button', { name: 'Google로 로그인' }) as HTMLButtonElement).disabled).toBe(true)
})

it('opens an authenticated account in its own empty workspace instead of showing demo companies', async () => {
  vi.spyOn(window, 'scrollTo').mockImplementation(() => {})
  window.history.replaceState({}, '', '/?demo=1')
  let imported = false
  const fetchMock = vi.fn(async (url: string) => {
    if (url === '/api/auth/session') return json(session)
    if (url === '/api/health') return json({ status: 'ok' })
    if (url === '/api/public-briefs') return json({ briefs: [
      { id: 'a', companyName: '한국전력공사', reportName: '사업보고서 2025', filedOn: '2026-03-01' },
      { id: 'b', companyName: '녹십자', reportName: '사업보고서 2024', filedOn: '2025-03-01' },
    ] })
    if (url === '/api/public-briefs/b/import') {
      imported = true
      return json({ briefId: 'saved-b', companyName: '녹십자' })
    }
    if (url === '/api/documents') return json({ documents: [] })
    if (url === '/api/jobs') return json({ jobs: [] })
    if (url === '/api/analyses') return json({ briefs: imported ? [
      { id: 'saved-b', companyName: '녹십자', reportName: '사업보고서 2024', reportDocumentId: 'report', createdAt: '2026-11-04' },
    ] : [], personal: [] })
    if (url === '/api/analysis/capabilities') return json({ briefConfigured: true, personalConfigured: true, personalRequiresJd: true })
    return json({ dataType: 'fictional_demo', companies: [{ id: 'demo', name: 'A기업' }], materials: [] })
  })
  vi.stubGlobal('fetch', fetchMock)
  render(<App />)
  await screen.findByText('아직 생성된 분석이 없어요')
  expect(screen.queryByText('A기업')).toBeNull()
  expect(screen.queryByRole('button', { name: '홈' })).toBeNull()
  expect(screen.queryByRole('button', { name: '계속하기' })).toBeNull()
  expect(screen.getByRole('button', { name: /로그아웃/ })).toBeTruthy()
  expect(fetchMock.mock.calls.some(([url]) => url.includes('/api/demo/'))).toBe(false)
  expect(new URLSearchParams(window.location.search).has('demo')).toBe(false)
  expect(screen.queryByText('샘플 화면 보기')).toBeNull()
  expect(screen.queryByLabelText('완성된 기업 브리프')).toBeNull()
  const menu = within(screen.getByRole('navigation', { name: '주요 메뉴' }))
  expect(menu.getAllByRole('button').map((button) => button.textContent?.trim())).toEqual(['기업 분석', '기업 둘러보기', '기여 보고서', '내 자료'])
  fireEvent.click(menu.getByRole('button', { name: '기업 둘러보기' }))
  expect(await screen.findByRole('button', { name: /한국전력공사.*브리프 읽기/ })).toBeTruthy()
  expect(screen.getByRole('button', { name: /녹십자.*브리프 읽기/ })).toBeTruthy()
  fireEvent.change(screen.getByRole('searchbox'), { target: { value: '사업보고서 2024' } })
  expect(screen.queryByRole('button', { name: /한국전력공사.*브리프 읽기/ })).toBeNull()
  expect(screen.getByRole('button', { name: /녹십자.*브리프 읽기/ })).toBeTruthy()
  fireEvent.click(screen.getByRole('button', { name: '녹십자 브리프 가져오기' }))
  expect(await screen.findByRole('button', { name: /녹십자.*결과 보기/ })).toBeTruthy()
  expect(screen.getByText('공용 브리프를 내 기업 분석에 가져왔어요.')).toBeTruthy()
  fireEvent.click(menu.getByRole('button', { name: '기여 보고서' }))
  expect(await screen.findByRole('button', { name: '새 기여 보고서' })).toBeTruthy()
  expect(screen.queryByRole('button', { name: '새 기업 브리프' })).toBeNull()
  fireEvent.click(menu.getByRole('button', { name: '내 자료' }))
  const documentTabs = await screen.findByRole('tablist', { name: '저장된 자료 종류' })
  expect(within(documentTabs).getAllByRole('tab')).toHaveLength(2)
  expect(within(documentTabs).queryByRole('tab', { name: /사업보고서/ })).toBeNull()
})

it('requires login for private navigation and never shows fictional data to guests', async () => {
  const fetchMock = vi.fn(async (url: string) => url === '/api/health' ? json({ status: 'ok' }) : json({ authenticated: false, googleConfigured: true, user: null, csrfToken: null }))
  vi.stubGlobal('fetch', fetchMock)
  render(<App />)
  await screen.findByRole('button', { name: 'Google로 시작하기' })
  fireEvent.click(screen.getByRole('button', { name: '내 자료' }))
  expect(screen.getByRole('dialog')).toBeTruthy()
  expect(screen.queryByText('개발자_CV_v2.pdf')).toBeNull()
  expect(fetchMock.mock.calls.some(([url]) => url.includes('/api/demo/') || url === '/api/documents')).toBe(false)
})
