import { useEffect, useId, useRef } from 'react'
import type { ReactNode } from 'react'
import { ArrowUpRight, Check, Circle, X } from 'lucide-react'

export function Modal({ title, children, onClose, wide = false }: { title: string; children: ReactNode; onClose: () => void; wide?: boolean }) {
  const id = useId()
  const ref = useRef<HTMLDivElement>(null)
  const close = useRef(onClose)
  close.current = onClose
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null
    const dialog = ref.current!
    const focusables = () => Array.from(dialog.querySelectorAll<HTMLElement>('button:not(:disabled), a[href], input, select, [tabindex="0"]'))
    focusables()[0]?.focus()
    const handle = (event: KeyboardEvent) => {
      if (event.key === 'Escape') close.current()
      if (event.key !== 'Tab') return
      const items = focusables()
      const first = items[0]
      const last = items[items.length - 1]
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus() }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus() }
    }
    const overflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    document.addEventListener('keydown', handle)
    return () => { document.body.style.overflow = overflow; document.removeEventListener('keydown', handle); previous?.focus() }
  }, [])
  return <div className="modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose() }}>
    <div className={`modal ${wide ? 'modal-wide' : ''}`} role="dialog" aria-modal="true" aria-labelledby={id} ref={ref}>
      <div className="modal-heading"><h2 id={id}>{title}</h2><button className="icon-button" aria-label="닫기" onClick={onClose}><X size={19} /></button></div>
      {children}
    </div>
  </div>
}

export function Status({ children = '분석 완료' }: { children?: ReactNode }) {
  return <span className="status"><Circle size={6} fill="currentColor" />{children}</span>
}

export function SourceButton({ children, onClick }: { children: ReactNode; onClick: () => void }) {
  return <button className="source-button" onClick={onClick}><span className="source-square"><Check size={10} /></span>{children}<ArrowUpRight size={12} /></button>
}

export function downloadJson(name: string, value: unknown) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(value, null, 2)], { type: 'application/json' }))
  const link = document.createElement('a')
  link.href = url
  link.download = name
  link.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
