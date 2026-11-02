import { useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { Highlighter, List, MessageSquare, Pencil, Trash2, X } from 'lucide-react'
import { api, ApiError } from '../api'
import type { Session } from '../api'
import { selectedText } from './reportAnnotations'
import type { Annotation } from './reportAnnotations'
import ReportEvidence from './ReportEvidence'
import type { Evidence, EvidenceSelection } from './ReportEvidence'

type Passage = { start: number; end: number; quote: string }
type Draft = Passage & { id?: string; note: string }

export default function ReportReader({ kind, resultId, session, onExpired, children, evidence, evidenceSelection = null, sourceName, onSelectEvidence, onOpenSource, createdAt, externalDialogOpen = false }: {
  kind: 'brief' | 'personal'; resultId: string; session: Session; onExpired: () => void;
  children: (annotations: Annotation[]) => ReactNode;
  evidence?: Evidence[]; evidenceSelection?: EvidenceSelection | null; sourceName?: string; createdAt?: string;
  onSelectEvidence?: (id: string) => void; onOpenSource?: (page: number, evidenceId?: string) => void;
  externalDialogOpen?: boolean;
}) {
  const root = useRef<HTMLDivElement>(null)
  const editor = useRef<HTMLTextAreaElement>(null)
  const panelRef = useRef<HTMLElement>(null)
  const [panel, setPanel] = useState<'evidence' | 'notes'>(evidence ? 'evidence' : 'notes')
  const [smallScreen, setSmallScreen] = useState(() => window.innerWidth <= 1100)
  const [tocOpen, setTocOpen] = useState(false)
  const [outline, setOutline] = useState<{ id: string; title: string; depth: number }[]>([])
  const [activeHeading, setActiveHeading] = useState('')
  const [annotations, setAnnotations] = useState<Annotation[]>([])
  const [version, setVersion] = useState('')
  const [loading, setLoading] = useState(true)
  const [revision, setRevision] = useState(0)
  const [error, setError] = useState('')
  const [status, setStatus] = useState('')
  const [candidate, setCandidate] = useState<Passage | null>(null)
  const [draft, setDraft] = useState<Draft | null>(null)
  const [busy, setBusy] = useState(false)
  const [notesOpen, setNotesOpen] = useState(() => window.innerWidth > 1100)
  const base = `/api/analyses/${kind}/${resultId}/annotations`

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true); setError('')
    api<{ contentVersion: string; annotations: Annotation[] }>(base, { signal: controller.signal })
      .then((data) => {
        if (typeof data.contentVersion !== 'string' || !Array.isArray(data.annotations)) throw new Error('메모 응답을 확인하지 못했습니다. 다시 불러와 주세요.')
        if (!controller.signal.aborted) { setVersion(data.contentVersion); setAnnotations(data.annotations) }
      })
      .catch((err) => { if (!controller.signal.aborted) { setError(err instanceof Error ? err.message : '메모를 불러오지 못했습니다.'); if (err instanceof ApiError && err.status === 401) onExpired() } })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [base, revision])
  useEffect(() => { if (draft) editor.current?.focus() }, [draft?.id, Boolean(draft)])

  useEffect(() => {
    const resize = () => setSmallScreen(window.innerWidth <= 1100)
    window.addEventListener('resize', resize)
    return () => window.removeEventListener('resize', resize)
  }, [])
  useEffect(() => { setNotesOpen(!smallScreen) }, [smallScreen])
  useEffect(() => {
    if (evidenceSelection) { setPanel('evidence'); setNotesOpen(true) }
  }, [evidenceSelection])
  useEffect(() => {
    const all = Array.from(root.current?.querySelectorAll<HTMLElement>('h2,h3') ?? [])
    const headings = all.length ? all : Array.from(root.current?.querySelectorAll<HTMLElement>('h1') ?? [])
    const sections = headings.map((node, index) => {
      node.id = `report-${resultId}-section-${index}`; node.tabIndex = -1
      return { id: node.id, title: node.textContent ?? '', depth: node.tagName === 'H3' ? 3 : 2 }
    })
    setOutline(sections); setActiveHeading(sections[0]?.id ?? '')
    const update = () => {
      let current = sections[0]?.id ?? ''
      for (const node of headings) { if (node.getBoundingClientRect().top <= 150) current = node.id }
      setActiveHeading(current)
    }
    window.addEventListener('scroll', update, { passive: true })
    return () => window.removeEventListener('scroll', update)
  }, [kind, resultId, loading])
  useEffect(() => {
    if (!smallScreen || !notesOpen || !panelRef.current || externalDialogOpen) return
    const side = panelRef.current
    const previous = document.activeElement as HTMLElement | null
    const focusables = () => Array.from(side.querySelectorAll<HTMLElement>('button:not(:disabled),a[href],textarea:not(:disabled),[tabindex="0"]'))
    const initialFocus = draft ? editor.current : focusables()[0]
    initialFocus?.focus()
    const keydown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') { event.preventDefault(); setNotesOpen(false) }
      if (event.key !== 'Tab') return
      const items = focusables(), first = items[0], last = items[items.length - 1]
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus() }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus() }
    }
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    document.addEventListener('keydown', keydown)
    return () => { document.body.style.overflow = previousOverflow; document.removeEventListener('keydown', keydown); previous?.focus() }
  }, [notesOpen, smallScreen, externalDialogOpen])
  const goToSection = (id: string) => {
    const node = document.getElementById(id)
    const reduced = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
    setActiveHeading(id); setTocOpen(false)
    requestAnimationFrame(() => {
      node?.scrollIntoView({ behavior: reduced ? 'instant' : 'smooth', block: 'start' })
      node?.focus({ preventScroll: true })
    })
  }

  const capture = () => {
    if (!root.current || draft || busy) return
    setCandidate(selectedText(root.current))
  }
  const beginNote = (passage: Passage | Annotation) => {
    setDraft({ ...passage, note: 'note' in passage ? passage.note : '' })
    setCandidate(null); setPanel('notes'); setNotesOpen(true); setError(''); setStatus('')
  }
  const save = async (passage: Draft) => {
    if (busy || !version) return
    if (!passage.id && annotations.some((item) => item.start < passage.end && item.end > passage.start)) {
      setError('이미 강조된 문장과 겹칩니다. 기존 하이라이트를 눌러 메모를 추가해 주세요.'); return
    }
    setBusy(true); setError(''); setStatus('')
    try {
      const saved = await api<Annotation>(passage.id ? `${base}/${passage.id}` : base, {
        method: passage.id ? 'PATCH' : 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(passage.id ? { note: passage.note } : { start: passage.start, end: passage.end, quote: passage.quote, note: passage.note, contentVersion: version }),
      }, session.csrfToken)
      setAnnotations((items) => [...items.filter((item) => item.id !== saved.id), saved].sort((a, b) => a.start - b.start))
      setDraft(null); setCandidate(null); window.getSelection()?.removeAllRanges()
      setStatus(saved.note ? '하이라이트와 메모를 저장했어요.' : '하이라이트를 저장했어요.')
    } catch (err) { setError(err instanceof Error ? err.message : '저장하지 못했습니다.'); if (err instanceof ApiError && err.status === 401) onExpired() }
    finally { setBusy(false) }
  }
  const remove = async (item: Annotation) => {
    setBusy(true); setError(''); setStatus('')
    try {
      await api(`${base}/${item.id}`, { method: 'DELETE' }, session.csrfToken)
      setAnnotations((items) => items.filter((entry) => entry.id !== item.id)); setDraft(null); setStatus('하이라이트와 메모를 삭제했어요.')
    } catch (err) { setError(err instanceof Error ? err.message : '삭제하지 못했습니다.'); if (err instanceof ApiError && err.status === 401) onExpired() }
    finally { setBusy(false) }
  }
  const jump = (item: Annotation) => {
    if (window.innerWidth <= 1100) setNotesOpen(false)
    const mark = root.current?.querySelector<HTMLElement>(`mark[data-annotation-id="${item.id}"]`)
    mark?.scrollIntoView({ behavior: 'smooth', block: 'center' }); mark?.focus({ preventScroll: true })
  }
  return <div className="report-reader">
    <div className="reading-toolbar"><button className="button reader-toc-toggle" aria-expanded={tocOpen} onClick={() => setTocOpen(!tocOpen)}><List size={15} />목차</button><span><Highlighter size={15} />문장을 선택해 나의 생각을 남겨보세요</span><div>{evidence && <button className="button" onClick={() => { setPanel('evidence'); setNotesOpen(true) }}>근거</button>}<button className="button" aria-expanded={notesOpen && panel === 'notes'} onClick={() => { setPanel('notes'); setNotesOpen(true) }}><MessageSquare size={14} />메모 · {annotations.length}</button></div></div>
    {error && <div className="notice" role="alert"><p>{error}</p>{!version && <button className="text-button" onClick={() => setRevision((value) => value + 1)}>다시 불러오기</button>}</div>}
    <p className="reading-status" role="status">{loading ? '하이라이트와 메모를 불러오는 중…' : status}</p>
    <div className={`reader-layout ${notesOpen ? '' : 'reader-notes-hidden'}`}>
      <nav className={`reader-toc ${tocOpen ? 'toc-open' : ''}`} aria-label="보고서 목차"><h2>목차</h2>{outline.map((item) => <button key={item.id} className={item.depth === 3 ? 'toc-subsection' : ''} aria-current={activeHeading === item.id ? 'location' : undefined} onClick={() => goToSection(item.id)}>{item.title}</button>)}</nav>
      <div className="report-paper-wrap">
        <div className="report-document-meta"><span>{kind === 'brief' ? '기업 브리프' : '기여 보고서'}</span>{createdAt && <time dateTime={createdAt}>{createdAt.slice(0, 10).replaceAll('-', '.')}</time>}</div>
        {candidate && <div className="selection-tools" role="toolbar" aria-label="선택한 문장 편집" onMouseDown={(event) => event.preventDefault()}><span>{candidate.quote.length.toLocaleString()}자 선택</span><button className="button" disabled={loading || busy || !version || candidate.quote.length > 10000} onClick={() => save({ ...candidate, note: '' })}><Highlighter size={15} />하이라이트</button><button className="button" disabled={loading || busy || !version || candidate.quote.length > 10000} onClick={() => beginNote(candidate)}><MessageSquare size={15} />메모 남기기</button><button className="icon-button" aria-label="문장 선택 취소" onClick={() => { setCandidate(null); window.getSelection()?.removeAllRanges() }}><X size={15} /></button>{candidate.quote.length > 10000 && <span>10,000자 이내로 선택해 주세요.</span>}</div>}
        <div className="report-paper" ref={root} onPointerUp={capture} onKeyUp={(event) => { if (event.key === 'Shift' || event.key.startsWith('Arrow')) capture(); if (event.key === 'Enter' || event.key === ' ') { const id = (event.target as HTMLElement).closest('mark')?.dataset.annotationId; const item = annotations.find((entry) => entry.id === id); if (item) { event.preventDefault(); beginNote(item) } } }} onClick={(event) => { const id = (event.target as HTMLElement).closest('mark')?.dataset.annotationId; const item = annotations.find((entry) => entry.id === id); if (item && window.getSelection()?.isCollapsed && !busy) beginNote(item) }}>{children(annotations)}</div>
      </div>
      {notesOpen && <><button className="notes-scrim" aria-label="메모 패널 닫기" onClick={() => setNotesOpen(false)} /><aside ref={panelRef} className="reading-notes report-side-panel" aria-label="근거와 메모" role={smallScreen ? 'dialog' : undefined} aria-modal={smallScreen ? true : undefined} tabIndex={-1}><div className="reader-panel-tabs">{evidence && <button aria-pressed={panel === 'evidence'} onClick={() => setPanel('evidence')}>근거</button>}<button aria-pressed={panel === 'notes'} onClick={() => setPanel('notes')}>메모 · {annotations.length}</button><button className="icon-button" aria-label="메모 닫기" disabled={busy} onClick={() => setNotesOpen(false)}><X size={15} /></button></div>
        {panel === 'evidence' && evidence && <ReportEvidence evidence={evidence} selection={evidenceSelection} sourceName={sourceName} canOpenSource={Boolean(onOpenSource)} onSelect={onSelectEvidence ?? (() => {})} onOpenSource={onOpenSource ?? (() => {})} />}
        <div hidden={panel !== 'notes'}><div className="reading-notes-heading"><h3>나의 메모</h3><span>{annotations.length}</span></div>
        {draft && <form className="note-editor" onSubmit={(event) => { event.preventDefault(); save(draft) }}><blockquote>{draft.quote}</blockquote><label htmlFor={`note-${resultId}`}>이 문장에 대한 메모</label><textarea ref={editor} id={`note-${resultId}`} value={draft.note} maxLength={5000} rows={5} disabled={busy} placeholder="지원 동기나 면접에서 연결할 생각을 적어보세요." onChange={(event) => setDraft({ ...draft, note: event.target.value })} /><small>{draft.note.length.toLocaleString()} / 5,000</small><div className="note-actions"><button className="button" type="button" disabled={busy} onClick={() => setDraft(null)}>취소</button><button className="button button-primary" disabled={busy || !version}>{busy ? '저장 중…' : '메모 저장'}</button></div></form>}
        {!loading && !annotations.length && !draft && <div className="notes-empty"><MessageSquare size={23} /><strong>읽으며 떠오른 생각을 모아두세요</strong><p>문장을 드래그해 강조하거나 메모를 남길 수 있어요. 저장한 메모는 이 보고서를 다시 열어도 유지됩니다.</p></div>}
        {annotations.map((item) => <div className="reading-note" key={item.id}><button className="note-quote" onClick={() => jump(item)} title="보고서의 해당 문장으로 이동">{item.quote}</button>{item.note ? <p>{item.note}</p> : <span className="muted">하이라이트</span>}<div className="note-actions"><button className="text-button" disabled={busy} onClick={() => beginNote(item)}><Pencil size={12} />{item.note ? '메모 수정' : '메모 추가'}</button><button className="icon-button" aria-label={`하이라이트 삭제: ${item.quote}`} disabled={busy} onClick={() => remove(item)}><Trash2 size={13} /></button></div></div>)}
        </div></aside></>}
    </div>
  </div>
}
