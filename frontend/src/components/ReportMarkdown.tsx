import ReactMarkdown from 'react-markdown'
import { annotationPlugin } from './reportAnnotations'
import type { Annotation } from './reportAnnotations'
import type { Evidence, EvidenceSelection } from './ReportEvidence'
import { linkPersonalSources } from './personalSourceLinks'

function linkBriefFacts(text: string): string {
  return text.replace(/(- \*\*기업 사실:\*\* )([^\n]+)(\n(?:- \*\*(?:왜 중요한가|생각해볼 질문):\*\*[^\n]*\n)*- \*\*출처:\*\*[^\n]*?원본\s+([\d,\s]+)쪽[^\n]*)/g,
    (_match, prefix: string, fact: string, following: string, pages: string) => {
      const page = Number(pages.match(/\d+/)?.[0])
      return page > 0 ? `${prefix}[${fact}](#evidence-page-${page})${following}` : `${prefix}${fact}${following}`
    })
}

export default function ReportMarkdown({ text, kind, evidence, selection, annotations, onEvidencePage, onEvidenceId }: {
  text: string; kind: 'brief' | 'personal'; evidence: Evidence[]; selection: EvidenceSelection | null;
  annotations: Annotation[]; onEvidencePage: (page: number, sourceKind?: 'report' | 'cv' | 'jd') => void; onEvidenceId: (id: string) => void;
}) {
  const ids = new Set(evidence.map((item) => item.id))
  let content = kind === 'brief' ? (text.includes('#evidence-id-') ? text : linkBriefFacts(text))
    : text.replace(/(- \*\*회사 (?:근거|사실):\*\* )\[(B\d+-E\d+)\] ([^\n]+)/g,
      (match, prefix: string, id: string, fact: string) => ids.has(id) ? `${prefix}[${id}] [${fact}](#evidence-id-${id})` : match)
  content = content.split(/(```[\s\S]*?```|~~~[\s\S]*?~~~|`[^`]*`)/g).map((part, index) => index % 2 ? part : part.replace(/\[(B\d+-E\d+)\](?!\]?\()/g, (match, id: string) => ids.has(id) ? `[${match}](#evidence-id-${id})` : match)).join('')
  if (kind === 'personal') content = linkPersonalSources(content, evidence)
  return <div className="analysis-markdown"><ReactMarkdown skipHtml rehypePlugins={[annotationPlugin(annotations)]} components={{
    img: ({ alt }) => <span>{alt}</span>,
    p: ({ node, children }) => {
      const first = node?.children[0]
      const isSource = kind === 'brief' && first?.type === 'text' && first.value.startsWith('출처 · ')
      return <p className={isSource ? 'report-section-sources' : undefined}>{children}</p>
    },
    a: ({ href, children }) => {
      const page = href?.match(/^#evidence-page-(\d+)$/)
      const candidatePage = href?.match(/^#evidence-(cv|jd)-page-(\d+)$/)
      const id = href?.match(/^#evidence-id-((?:B\d+-E\d+)|(?:(?:CV|JD)-[a-z_]+(?:-\d+)?))$/)?.[1]
      const item = evidence.find((entry) => entry.id === id)
      const verifiedPage = candidatePage && evidence.some((entry) => entry.sourceKind === candidatePage[1] && entry.page === Number(candidatePage[2]))
      if (page || item || verifiedPage) {
        const pageNumber = item?.page ?? Number(candidatePage?.[2] ?? page![1])
        const sourceKind = candidatePage?.[1] as 'cv' | 'jd' | undefined
        const label = (item?.sourceKind ?? sourceKind) === 'cv' ? 'CV' : (item?.sourceKind ?? sourceKind) === 'jd' ? 'JD' : '사업보고서'
        const selectedKind = evidence.find((entry) => selection?.ids.includes(entry.id))?.sourceKind ?? 'report'
        const active = item ? selection?.ids.includes(item.id) : selection?.page === pageNumber && selectedKind === (sourceKind ?? 'report')
        // Keep rendered text unchanged so saved annotation offsets remain valid.
        return <a href={href} role="button" className="evidence-fact-link" data-current={active || undefined} title={`${label} ${pageNumber}쪽 근거 보기`} aria-pressed={Boolean(active)} onKeyDown={(event) => { if (event.key === ' ') { event.preventDefault(); event.currentTarget.click() } }} onClick={(event) => {
          event.preventDefault()
          if ((event.target as HTMLElement).closest('mark') || window.getSelection()?.isCollapsed === false) return
          if (item) onEvidenceId(item.id); else if (sourceKind) onEvidencePage(pageNumber, sourceKind); else onEvidencePage(pageNumber)
        }}>{children}</a>
      }
      if (href?.startsWith('#evidence-')) return <span title="연결된 근거를 찾을 수 없습니다.">{children}</span>
      return <a href={href?.startsWith('https://') || href?.startsWith('http://') ? href : undefined} target="_blank" rel="noreferrer noopener">{children}</a>
    },
  }}>{content}</ReactMarkdown></div>
}
