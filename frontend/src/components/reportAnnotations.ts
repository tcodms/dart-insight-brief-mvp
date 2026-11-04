export interface Annotation { id: string; start: number; end: number; quote: string; note: string; createdAt: string }
interface HtmlNode { type: string; value?: string; tagName?: string; properties?: Record<string, unknown>; children?: HtmlNode[] }

// Offsets use rendered text (UTF-16), so Markdown syntax is never highlighted.
export function annotationPlugin(annotations: Annotation[]) {
  return () => (tree: HtmlNode) => {
    let offset = 0
    function walk(parent: HtmlNode) {
      if (!parent.children) return
      parent.children = parent.children.flatMap((node): HtmlNode[] => {
        if (node.type === 'element' && node.tagName === 'img') node = { type: 'element', tagName: 'span', properties: {}, children: [{ type: 'text', value: String(node.properties?.alt ?? '') }] }
        if (node.type !== 'text') { walk(node); return [node] }
        const text = node.value ?? ''
        const start = offset
        offset += text.length
        const matches = annotations.filter((item) => item.start < offset && item.end > start)
        if (!matches.length) return [node]
        const cuts = [...new Set([0, text.length, ...matches.flatMap((item) => [Math.max(0, item.start - start), Math.min(text.length, item.end - start)])])].sort((a, b) => a - b)
        return cuts.slice(0, -1).map((from, index) => {
          const to = cuts[index + 1]
          const item = matches.find((match) => match.start <= start + from && match.end >= start + to)
          const child = { type: 'text', value: text.slice(from, to) }
          return item ? { type: 'element', tagName: 'mark', properties: { 'data-annotation-id': item.id, tabIndex: 0, role: 'button', ariaLabel: item.note ? `메모 보기: ${item.note.slice(0, 100)}` : '하이라이트 메모 추가' }, children: [child] } : child
        })
      })
    }
    walk(tree)
  }
}

export function selectedText(root: HTMLElement): { start: number; end: number; quote: string } | null {
  const selection = window.getSelection()
  if (!selection?.rangeCount || selection.isCollapsed) return null
  const range = selection.getRangeAt(0)
  if (!root.contains(range.startContainer) || !root.contains(range.endContainer)) return null
  const before = range.cloneRange()
  before.selectNodeContents(root)
  before.setEnd(range.startContainer, range.startOffset)
  const start = before.toString().length
  const quote = range.toString()
  return quote.trim() ? { start, end: start + quote.length, quote } : null
}
