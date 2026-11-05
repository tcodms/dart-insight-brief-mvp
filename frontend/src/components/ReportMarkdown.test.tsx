// @vitest-environment jsdom
import { afterEach, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import ReactMarkdown from 'react-markdown'
import ReportMarkdown from './ReportMarkdown'

afterEach(cleanup)
const evidence = [{ id: 'B01-E001', page: 9, section: '사업', quote: '저장된 실제 인용문' }]

it('links personal CV/JD pages and field references without changing annotation text', () => {
  const sources = [...evidence,
    { id: 'CV-hands_on_skills-1', page: 1, section: '', quote: '무균 조작', sourceKind: 'cv' as const, fieldRef: 'hands_on_skills[1]' },
    { id: 'JD-key_responsibilities-1', page: 1, section: '', quote: '시험 업무', sourceKind: 'jd' as const, fieldRef: 'key_responsibilities[1]' }]
  const text = '- 원본 위치: CV 1쪽 · JD 1쪽\n\n## 근거 확인\n\n- **CV:**\n  - `hands_on_skills[1]` · 무균 조작 · 원본 PDF 1쪽\n- **JD:**\n  - key_responsibilities[1] · 시험 업무 · 원본 PDF 1쪽\n- **기업 fact:**\n  - B01-E001 · 기업 활동 · 원문 9쪽'
  const original = render(<ReactMarkdown>{text}</ReactMarkdown>)
  const plainText = original.container.textContent
  original.unmount()
  const onId = vi.fn(), onPage = vi.fn()
  const view = render(<ReportMarkdown text={text} kind="personal" evidence={sources} selection={null} annotations={[]} onEvidenceId={onId} onEvidencePage={onPage} />)
  expect(view.container.textContent).toBe(plainText)
  fireEvent.click(screen.getByRole('button', { name: 'CV 1쪽' }))
  expect(onPage).toHaveBeenCalledWith(1, 'cv')
  fireEvent.click(screen.getByRole('button', { name: 'JD 1쪽' }))
  expect(onPage).toHaveBeenCalledWith(1, 'jd')
  fireEvent.click(screen.getByRole('button', { name: 'hands_on_skills[1]' }))
  expect(onId).toHaveBeenCalledWith('CV-hands_on_skills-1')
  fireEvent.click(screen.getByRole('button', { name: 'key_responsibilities[1]' }))
  expect(onId).toHaveBeenCalledWith('JD-key_responsibilities-1')
  fireEvent.click(screen.getByRole('button', { name: 'B01-E001' }))
  expect(onId).toHaveBeenCalledWith('B01-E001')
})

it('does not link unknown candidate fields or pages', () => {
  render(<ReportMarkdown text={'CV 7쪽 · JD 원본 쪽수 확인 필요\n\n- **CV:**\n  - hands_on_skills[999]\n\n[없는 쪽](#evidence-cv-page-7)'} kind="personal" evidence={evidence} selection={null} annotations={[]} onEvidenceId={vi.fn()} onEvidencePage={vi.fn()} />)
  expect(screen.queryByRole('button')).toBeNull()
})

it('keeps the active page specific to CV rather than all documents sharing page one', () => {
  const sources = [
    { id: 'CV-summary', page: 1, section: '', quote: '경험', sourceKind: 'cv' as const },
    { id: 'JD-summary', page: 1, section: '', quote: '업무', sourceKind: 'jd' as const }]
  render(<ReportMarkdown text="CV 1쪽 · JD 1쪽" kind="personal" evidence={sources} selection={{ ids: ['CV-summary'], page: 1 }} annotations={[]} onEvidenceId={vi.fn()} onEvidencePage={vi.fn()} />)
  expect(screen.getByRole('button', { name: 'CV 1쪽' }).getAttribute('aria-pressed')).toBe('true')
  expect(screen.getByRole('button', { name: 'JD 1쪽' }).getAttribute('aria-pressed')).toBe('false')
})

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

it('keeps grouped sources separate from the body and opens the original evidence', () => {
  const onId = vi.fn()
  const view = render(<ReportMarkdown text={'## 최근 주력 사업\n\n- 전력망을 운영합니다.\n\n출처 · [근거 1](#evidence-id-B01-E001)'} kind="brief" evidence={evidence} selection={null} annotations={[]} onEvidenceId={onId} onEvidencePage={vi.fn()} />)
  expect(view.container.querySelector('li a')).toBeNull()
  expect(view.container.querySelector('.report-section-sources')?.textContent).toBe('출처 · 근거 1')
  fireEvent.click(screen.getByRole('button', { name: '근거 1' }))
  expect(onId).toHaveBeenCalledWith('B01-E001')
})
