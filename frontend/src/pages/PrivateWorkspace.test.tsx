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

it('loads private document records with an authenticated download link', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => json({ documents: [document] })))
  render(<PrivateWorkspace page="materials" session={session} onDemo={vi.fn()} onLogin={vi.fn()} />)
  expect(await screen.findByText('보고서.pdf')).toBeTruthy()
  expect(screen.getByRole('link', { name: '보고서.pdf 다운로드' }).getAttribute('href')).toBe('/api/documents/doc/file')
  expect(screen.queryByText('A기업')).toBeNull()
})

it('posts the selected PDF and CSRF token then reloads the persisted list', async () => {
  let saved = false
  const fetchMock = vi.fn(async (_url: string, options?: RequestInit) => {
    if (options?.method === 'POST') { saved = true; return json(document, 201) }
    return json({ documents: saved ? [document] : [] })
  })
  vi.stubGlobal('fetch', fetchMock)
  render(<PrivateWorkspace page="materials" session={session} onDemo={vi.fn()} onLogin={vi.fn()} />)
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

it('does not permit deletion until its impact has been loaded and confirms affected results', async () => {
  let deleted = false
  const fetchMock = vi.fn(async (url: string, options?: RequestInit) => {
    if (url.endsWith('/impact')) return json({ briefs: 1, personalAnalyses: 2, preservesBriefs: false })
    if (options?.method === 'DELETE') { deleted = true; return new Response(null, { status: 204 }) }
    return json({ documents: deleted ? [] : [document] })
  })
  vi.stubGlobal('fetch', fetchMock)
  render(<PrivateWorkspace page="materials" session={session} onDemo={vi.fn()} onLogin={vi.fn()} />)
  fireEvent.click(await screen.findByRole('button', { name: '보고서.pdf 삭제' }))
  await screen.findByText('기업 브리프 1개, 개인화 분석 2개가 함께 삭제됩니다.')
  fireEvent.click(within(screen.getByRole('dialog')).getByRole('button', { name: '삭제' }))
  await screen.findByText('등록한 사업보고서가 없어요')
  expect(fetchMock.mock.calls.some(([url, options]) => url === '/api/documents/doc' && options?.method === 'DELETE')).toBe(true)
})

it('clears private records and asks for login on an expired session', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => json({ detail: '로그인이 필요합니다.' }, 401)))
  const onLogin = vi.fn()
  render(<PrivateWorkspace page="materials" session={session} onDemo={vi.fn()} onLogin={onLogin} />)
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
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    if (url === '/api/auth/session') return json(session)
    if (url === '/api/health') return json({ status: 'ok' })
    if (url === '/api/documents') return json({ documents: [] })
    return json({ dataType: 'fictional_demo', companies: [{ id: 'demo', name: 'A기업' }], materials: [] })
  }))
  render(<App />)
  await screen.findByText('아직 생성된 분석이 없어요')
  expect(screen.queryByText('A기업')).toBeNull()
  expect(screen.getByRole('button', { name: /로그아웃/ })).toBeTruthy()
})
