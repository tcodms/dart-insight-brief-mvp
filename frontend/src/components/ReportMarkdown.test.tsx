// @vitest-environment jsdom
import { afterEach, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import ReactMarkdown from 'react-markdown'
import ReportMarkdown from './ReportMarkdown'

afterEach(cleanup)
const evidence = [{ id: 'B01-E001', page: 9, section: '사업', quote: '저장된 실제 인용문' }]

it('preserves rendered text and existing annotation offsets when linking company facts', () => {
  const text = '# 기여 보고서\n\n## 연결 경험\n- **회사 사실:** [B01-E001] 전력망을 운영합니다.\n- 내 경험😀을 연결합니다.\n\n근거 `[B01-E001]` 원문 9쪽.\n\n```\n[B01-E001]\n```'
  const original = render(<ReactMarkdown>{text}</ReactMarkdown>)
  const renderedText = original.container.textContent!
  const quote = '전력망을 운영합니다.'
  const start = renderedText.indexOf(quote)
  original.unmount()
  const onId = vi.fn()
  const view = render(<ReportMarkdown text={text} kind="personal" evidence={evidence} selection={null} onEvidenceId={onId} onEvidencePage={vi.fn()} annotations={[{ id: 'note', start, end: start + quote.length, quote, note: '기존 메모', createdAt: 'today' }]} />)
  expect(view.container.textContent).toBe(renderedText)
  expect(view.container.querySelector('mark')?.textContent).toBe(quote)
  fireEvent.click(screen.getByRole('button', { name: '[B01-E001]' }))
  expect(onId).toHaveBeenCalledWith('B01-E001')
  fireEvent.click(view.container.querySelector('mark')!)
  expect(onId).toHaveBeenCalledTimes(1)
})

it('does not turn an unknown evidence ID into a working source link', () => {
  render(<ReportMarkdown text="[알 수 없는 사실](#evidence-id-B99-E999)" kind="brief" evidence={evidence} selection={null} annotations={[]} onEvidenceId={vi.fn()} onEvidencePage={vi.fn()} />)
  expect(screen.getByText('알 수 없는 사실')).toBeTruthy()
  expect(screen.queryByRole('button')).toBeNull()
})
