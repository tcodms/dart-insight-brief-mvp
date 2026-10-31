import { useEffect, useRef, useState } from 'react'
import { getDocument, GlobalWorkerOptions, TextLayer } from 'pdfjs-dist'
import type { PDFDocumentProxy } from 'pdfjs-dist'
import workerUrl from 'pdfjs-dist/build/pdf.worker.min.mjs?url'
import { findQuoteSpans } from './pdfEvidence'

GlobalWorkerOptions.workerSrc = workerUrl

export default function PdfEvidenceViewer({ documentId, page, quote, onPageChange }: {
  documentId: string; page: number; quote: string | null; onPageChange: (page: number) => void
}) {
  const [pdf, setPdf] = useState<PDFDocumentProxy | null>(null)
  const [width, setWidth] = useState(0)
  const [status, setStatus] = useState('원본 PDF를 불러오는 중…')
  const hostRef = useRef<HTMLDivElement>(null)
  const viewportRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const host = hostRef.current
    if (!host) return
    const observer = new ResizeObserver(() => setWidth(host.clientWidth - 24))
    observer.observe(host)
    return () => observer.disconnect()
  }, [])

  useEffect(() => {
    let active = true
    const task = getDocument({ url: `/api/documents/${documentId}/preview`, withCredentials: true })
    task.promise.then((document) => { if (active) setPdf(document) })
      .catch(() => { if (active) setStatus('원본 PDF를 불러오지 못했습니다.') })
    return () => { active = false; setPdf(null); void task.destroy() }
  }, [documentId])

  useEffect(() => {
    const host = viewportRef.current
    if (!pdf || !host || width <= 0) return
    let active = true
    let renderTask: ReturnType<Awaited<ReturnType<PDFDocumentProxy['getPage']>>['render']> | undefined
    let textLayer: TextLayer | undefined
    setStatus('해당 쪽을 불러오는 중…')
    host.replaceChildren()
    const render = async () => {
      if (page < 1 || page > pdf.numPages) { setStatus('해당 쪽을 찾을 수 없습니다.'); return }
      const pdfPage = await pdf.getPage(page)
      if (!active) return
      const base = pdfPage.getViewport({ scale: 1 })
      const viewport = pdfPage.getViewport({ scale: width / base.width })
      const sheet = document.createElement('div')
      sheet.className = 'pdf-sheet'
      sheet.style.width = `${viewport.width}px`
      sheet.style.height = `${viewport.height}px`
      sheet.style.setProperty('--total-scale-factor', String(viewport.scale))
      const canvas = document.createElement('canvas')
      const context = canvas.getContext('2d')
      if (!context) throw new Error('Canvas unavailable')
      const pixelRatio = Math.min(window.devicePixelRatio || 1, 2)
      canvas.width = Math.round(viewport.width * pixelRatio)
      canvas.height = Math.round(viewport.height * pixelRatio)
      canvas.style.width = `${viewport.width}px`
      canvas.style.height = `${viewport.height}px`
      sheet.append(canvas)
      const layer = document.createElement('div')
      layer.className = 'textLayer'
      sheet.append(layer)
      host.append(sheet)
      renderTask = pdfPage.render({ canvas, canvasContext: context, viewport, transform: [pixelRatio, 0, 0, pixelRatio, 0, 0] })
      await renderTask.promise
      if (!active) return
      const content = await pdfPage.getTextContent()
      if (!active) return
      textLayer = new TextLayer({ textContentSource: content, container: layer, viewport })
      await textLayer.render()
      if (!active) return
      if (!quote) { setStatus(`${page} / ${pdf.numPages}쪽`); return }
      const divs = textLayer.textDivs
      const indices = findQuoteSpans(divs.map((div) => div.textContent ?? ''), quote)
      if (indices.length) {
        indices.forEach((index) => divs[index].classList.add('evidence-highlight'))
        divs[indices[0]].scrollIntoView({ block: 'center', inline: 'nearest' })
        setStatus('원문에서 인용문을 강조했습니다.')
      } else {
        setStatus('이 쪽의 텍스트에서 인용문 위치를 찾지 못했습니다.')
      }
    }
    void render().catch((error: unknown) => {
      if (active && !(error instanceof Error && error.name === 'RenderingCancelledException')) setStatus('PDF 쪽을 표시하지 못했습니다.')
    })
    return () => { active = false; renderTask?.cancel(); textLayer?.cancel(); host.replaceChildren() }
  }, [pdf, page, quote, width])

  return <div className="pdf-evidence-viewer" aria-label="사업보고서 원문" ref={hostRef}>
    <div className="pdf-viewer-toolbar"><button type="button" disabled={!pdf || page <= 1} onClick={() => onPageChange(page - 1)}>이전 쪽</button><span>{pdf ? `${page} / ${pdf.numPages}쪽` : `${page}쪽`}</span><button type="button" disabled={!pdf || page >= pdf.numPages} onClick={() => onPageChange(page + 1)}>다음 쪽</button></div>
    <p className="pdf-viewer-status" role="status">{status}</p>
    <div className="pdf-page-scroll"><div ref={viewportRef} /></div>
  </div>
}
