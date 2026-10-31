export function findQuoteSpans(spans: readonly string[], quote: string): number[] {
  const normalize = (value: string) => value.normalize('NFKC').toLocaleLowerCase().replace(/[^\p{L}\p{N}]/gu, '')
  const needle = normalize(quote)
  if (!needle) return []
  let text = ''
  const owners: number[] = []
  spans.forEach((span, index) => {
    for (const char of normalize(span)) { text += char; owners.push(index) }
  })
  const start = text.indexOf(needle)
  return start < 0 ? [] : [...new Set(owners.slice(start, start + needle.length))]
}
