// @vitest-environment jsdom
import { afterEach, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import HomeDashboard from './HomeDashboard'

const json = (body: unknown) => new Response(JSON.stringify(body), { status: 200 })
afterEach(() => { cleanup(); vi.unstubAllGlobals(); vi.restoreAllMocks() })

it('offers report upload as the first action when no report is registered', async () => {
  vi.stubGlobal('fetch', vi.fn(async (url: string) => url === '/api/jobs' ? json({ jobs: [] }) : json({ briefs: [], personal: [] })))
  const onUpload = vi.fn()
  render(<HomeDashboard name="테스트" documents={[]} navigate={vi.fn()} onUpload={onUpload} />)
  await screen.findByText('사업보고서를 등록해 주세요.')
  fireEvent.click(screen.getByRole('button', { name: '계속하기' }))
  expect(onUpload).toHaveBeenCalledOnce()
  const guide = screen.getByRole('region', { name: '이렇게 시작하세요' })
  expect(guide.compareDocumentPosition(screen.getByText('지금 상태')) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
  fireEvent.click(screen.getByRole('button', { name: '사업보고서 등록' }))
  expect(onUpload).toHaveBeenCalledTimes(2)
  expect(screen.queryByText('보고서.pdf')).toBeNull()
})

it('uses a finished brief to suggest the contribution step without listing all records', async () => {
  vi.stubGlobal('fetch', vi.fn(async (url: string) => url === '/api/jobs' ? json({ jobs: [] }) : json({ briefs: [{ id: 'b', companyName: '기업 A', createdAt: '2026-10-31' }], personal: [] })))
  const navigate = vi.fn()
  render(<HomeDashboard name="테스트" documents={[{ kind: 'report' }]} navigate={navigate} onUpload={vi.fn()} />)
  await screen.findByText('내 경험을 기업과 연결해 보세요.')
  expect(screen.getByText('기업 A')).toBeTruthy()
  fireEvent.click(screen.getByRole('button', { name: '계속하기' }))
  expect(navigate).toHaveBeenCalledWith('workspace')
  fireEvent.click(screen.getByRole('button', { name: 'JD·CV 등록' }))
  expect(navigate).toHaveBeenCalledWith('materials')
})
