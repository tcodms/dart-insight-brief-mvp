import type { Evidence } from './ReportEvidence'

/** Add links without adding/removing visible text: annotation offsets must stay stable. */
export function linkPersonalSources(text: string, evidence: Evidence[]): string {
  let section: 'cv' | 'jd' | undefined
  return text.split(/(```[\s\S]*?```|~~~[\s\S]*?~~~)/g).map((block, blockIndex) => {
    if (blockIndex % 2) return block
    return block.split('\n').map((line) => {
      const heading = line.match(/^\s*(?:[-*]\s*)?(?:\*\*)?(CV|JD|기업\s*(?:fact|근거|사실))\s*[:：]/i)
      if (heading) section = heading[1].toLowerCase() === 'cv' ? 'cv' : heading[1].toLowerCase() === 'jd' ? 'jd' : undefined
      return line.split(/(\[[^\n]*?\]\([^)\n]+\)|`[^`]*`)/g).map((part, index) => {
        if (index % 2) {
          if (!part.startsWith('`')) return part
          const token = part.slice(1, -1)
          const item = evidence.find((entry) => (entry.sourceKind === section && entry.fieldRef === token)
            || (/^B\d+-E\d+$/.test(token) && entry.id === token))
          return item ? `[${part}](#evidence-id-${item.id})` : part
        }
        return part.replace(/\b(?:CV|JD)\s+\d+쪽|\bB\d+-E\d+\b|\b[a-z_]+(?:\[\d+\])?/g, (token, offset: number) => {
          const page = token.match(/^(CV|JD)\s+(\d+)쪽$/)
          if (page) {
            const kind = page[1].toLowerCase(), number = Number(page[2])
            return evidence.some((entry) => entry.sourceKind === kind && entry.page === number)
              ? `[${token}](#evidence-${kind}-page-${number})` : token
          }
          if (/^B\d+-E\d+$/.test(token) && (part[offset - 1] === '[' || part[offset + token.length] === ']')) return token
          const item = evidence.find((entry) => entry.id === token || (entry.sourceKind === section && entry.fieldRef === token))
          return item ? `[${token}](#evidence-id-${item.id})` : token
        })
      }).join('')
    }).join('\n')
  }).join('')
}
