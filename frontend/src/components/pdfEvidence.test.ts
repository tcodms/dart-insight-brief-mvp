import { expect, it } from 'vitest'
import { findQuoteSpans } from './pdfEvidence'

it('finds a Korean quote across PDF text spans and spacing differences', () => {
  expect(findQuoteSpans(['녹십자는 ', '백신 및', ' 혈액제제를 생산한다.'], '백신 및 혈액제제')).toEqual([1, 2])
})

it('does not highlight a quote that is absent from the page', () => {
  expect(findQuoteSpans(['백신 및 혈액제제를 생산한다.'], '신규 해외 공장 설립')).toEqual([])
})
