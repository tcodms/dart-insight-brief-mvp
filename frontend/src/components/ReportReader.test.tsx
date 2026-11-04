// @vitest-environment jsdom
import { afterEach, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import ReactMarkdown from 'react-markdown'
import ReportReader from './ReportReader'
import { annotationPlugin } from './reportAnnotations'
import type { Annotation } from './reportAnnotations'
import type { Session } from '../api'

const session: Session = { authenticated: true, googleConfigured: true, csrfToken: 'csrf', user: { id: 'u', name: '사용자', email: 'u@example.test' } }
const markdown = '# 보고서\n\n같은 문장입니다.\n\n- **같은 문장**입니다.\n- 다음 항목😀\n\n마지막 단락입니다.'
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status })
const contentVersion = 'a'.repeat(64)

it('moves focus to the document heading from the generated outline', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => json({ contentVersion, annotations: [] })))
  vi.stubGlobal('requestAnimationFrame', (callback: FrameRequestCallback) => { callback(0); return 1 })
  reader()
  await screen.findByText('읽으며 떠오른 생각을 모아두세요')
  const heading = screen.getByRole('heading', { name: /^보고서$/ })
  const scroll = vi.fn()
  heading.scrollIntoView = scroll
  fireEvent.click(screen.getByRole('button', { name: /^보고서$/ }))
  expect(scroll).toHaveBeenCalled()
  expect(document.activeElement).toBe(heading)
})

it('opens a mobile evidence drawer and restores focus when Escape closes it', async () => {
  vi.stubGlobal('innerWidth', 390)
  vi.stubGlobal('fetch', vi.fn(async () => json({ contentVersion, annotations: [] })))
  render(<ReportReader kind="brief" resultId="b" session={session} onExpired={vi.fn()} evidence={[]}>{() => <h1>기업 브리프 본문</h1>}</ReportReader>)
  await waitFor(() => expect(screen.queryByText('하이라이트와 메모를 불러오는 중…')).toBeNull())
  const open = screen.getByRole('button', { name: /^근거$/ })
  open.focus(); fireEvent.click(open)
  const drawer = screen.getByRole('dialog', { name: '근거와 메모' })
  expect(drawer.contains(document.activeElement)).toBe(true)
  fireEvent.keyDown(document, { key: 'Escape' })
  expect(screen.queryByRole('dialog')).toBeNull()
  expect(document.activeElement).toBe(open)
})
afterEach(() => { cleanup(); window.getSelection()?.removeAllRanges(); vi.unstubAllGlobals(); vi.restoreAllMocks() })

function reader() {
  vi.stubGlobal('innerWidth', 1440)
  return render(<ReportReader kind="personal" resultId="p" session={session} onExpired={vi.fn()}>{(annotations) => <div className="analysis-markdown"><ReactMarkdown rehypePlugins={[annotationPlugin(annotations)]}>{markdown}</ReactMarkdown></div>}</ReportReader>)
}

function select(root: HTMLElement, quote: string, occurrence = 0) {
  const text = root.textContent!
  let start = -1
  for (let i = 0; i <= occurrence; i++) start = text.indexOf(quote, start + 1)
  if (start < 0) throw new Error('Test passage missing')
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT)
  const range = document.createRange()
  let offset = 0, began = false
  while (walker.nextNode()) {
    const node = walker.currentNode
    const length = node.textContent!.length
    if (!began && offset + length > start) { range.setStart(node, start - offset); began = true }
    if (offset + length >= start + quote.length) { range.setEnd(node, start + quote.length - offset); break }
    offset += length
  }
  window.getSelection()!.removeAllRanges(); window.getSelection()!.addRange(range)
  fireEvent.pointerUp(root)
  return start
}

it('anchors duplicate text across formatting, persists on reopen, edits and deletes a note', async () => {
  let stored: Annotation[] = []
  const mock = vi.fn(async (_url: string, options?: RequestInit) => {
    if (options?.method === 'POST') { const body = JSON.parse(options.body as string); stored = [{ ...body, id: 'note-1', createdAt: 'today' }]; return json(stored[0], 201) }
    if (options?.method === 'PATCH') { stored[0] = { ...stored[0], ...JSON.parse(options.body as string) }; return json(stored[0]) }
    if (options?.method === 'DELETE') { stored = []; return new Response(null, { status: 204 }) }
    return json({ contentVersion, annotations: stored })
  })
  vi.stubGlobal('fetch', mock)
  let view = reader()
  await screen.findByText('읽으며 떠오른 생각을 모아두세요')
  const paper = view.container.querySelector<HTMLElement>('.report-paper')!
  const offset = select(paper, '같은 문장입니다.', 1)
  fireEvent.click(screen.getByRole('button', { name: '메모 남기기' }))
  fireEvent.change(screen.getByLabelText('이 문장에 대한 메모'), { target: { value: '내 경험 연결하기' } })
  fireEvent.click(screen.getByRole('button', { name: '메모 저장' }))
  await screen.findByText('하이라이트와 메모를 저장했어요.')
  expect(stored[0].start).toBe(offset)
  expect(paper.querySelector('p mark')).toBeNull()
  expect([...paper.querySelectorAll('li mark')].map((mark) => mark.textContent).join('')).toBe('같은 문장입니다.')
  const post = mock.mock.calls.find(([, options]) => options?.method === 'POST')!
  expect(new Headers(post[1]?.headers).get('X-CSRF-Token')).toBe('csrf')
  view.unmount(); view = reader()
  await screen.findByText('내 경험 연결하기')
  fireEvent.click(screen.getByRole('button', { name: '메모 수정' }))
  fireEvent.change(screen.getByLabelText('이 문장에 대한 메모'), { target: { value: '수정된 메모' } })
  fireEvent.click(screen.getByRole('button', { name: '메모 저장' }))
  await screen.findByText('수정된 메모')
  fireEvent.click(screen.getByRole('button', { name: '하이라이트 삭제: 같은 문장입니다.' }))
  await screen.findByText('하이라이트와 메모를 삭제했어요.')
  expect(view.container.querySelector('mark')).toBeNull()
})

it('keeps a draft after a failed save and saves a highlight without a note', async () => {
  let fail = true
  vi.stubGlobal('fetch', vi.fn(async (_url: string, options?: RequestInit) => options?.method === 'POST'
    ? fail ? json({ detail: '저장 실패' }, 503) : json({ ...JSON.parse(options.body as string), id: 'h', createdAt: 'today' }, 201)
    : json({ contentVersion, annotations: [] })))
  const view = reader()
  await screen.findByText('읽으며 떠오른 생각을 모아두세요')
  select(view.container.querySelector<HTMLElement>('.report-paper')!, '다음 항목😀')
  fireEvent.click(screen.getByRole('button', { name: /^하이라이트$/ }))
  await screen.findByText('저장 실패')
  expect(screen.getByRole('toolbar')).toBeTruthy()
  fail = false
  fireEvent.click(screen.getByRole('button', { name: /^하이라이트$/ }))
  await screen.findByText('하이라이트를 저장했어요.')
  expect(view.container.querySelector('mark')?.textContent).toBe('다음 항목😀')
})

it('recovers annotation loading errors without hiding the report', async () => {
  let fail = true
  vi.stubGlobal('fetch', vi.fn(async () => fail ? json({ detail: '메모 연결 실패' }, 503) : json({ contentVersion, annotations: [] })))
  reader()
  await screen.findByRole('alert')
  expect(screen.getByRole('heading', { name: '보고서' })).toBeTruthy()
  fail = false
  fireEvent.click(screen.getByRole('button', { name: '다시 불러오기' }))
  await waitFor(() => expect(screen.queryByRole('alert')).toBeNull())
  await screen.findByText('읽으며 떠오른 생각을 모아두세요')
})
