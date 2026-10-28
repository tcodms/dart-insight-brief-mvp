import { useEffect, useRef, useState } from 'react'
import { Download, FileText, LoaderCircle, Plus, RefreshCw, Trash2, Upload } from 'lucide-react'
import { api, ApiError } from '../api'
import type { Session } from '../api'
import type { Page } from '../types'
import { Modal } from '../components/ui'
import AnalysisPanel from '../components/AnalysisPanel'

type Kind = 'report' | 'cv' | 'jd'
interface DocumentRecord {
  id: string; name: string; kind: Kind; version: string; date: string; pages: number; bytes: number
}
interface Impact { briefs: number; personalAnalyses: number; preservesBriefs: boolean }
const labels: Record<Kind, string> = { report: '사업보고서', cv: 'CV', jd: '직무기술서' }

export default function PrivateWorkspace({ page, session, onLogin }: {
  page: Page; session: Session; onLogin: () => void;
}) {
  const [documents, setDocuments] = useState<DocumentRecord[]>([])
  const [tab, setTab] = useState<Kind>('report')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [expired, setExpired] = useState(false)
  const [reload, setReload] = useState(0)
  const [uploadKind, setUploadKind] = useState<Kind | null>(null)
  const [deleting, setDeleting] = useState<DocumentRecord | null>(null)
  const [impact, setImpact] = useState<Impact | null>(null)
  const [impactError, setImpactError] = useState('')
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState('')

  useEffect(() => {
    let active = true
    const controller = new AbortController()
    setLoading(true); setError('')
    api<{ documents: DocumentRecord[] }>('/api/documents', { signal: controller.signal })
      .then((data) => { if (active) { setDocuments(data.documents); setExpired(false) } })
      .catch((err) => { if (active) { setError(err instanceof Error ? err.message : '자료를 불러오지 못했습니다.'); if (err instanceof ApiError && err.status === 401) { setExpired(true); setDocuments([]) } } })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false; controller.abort() }
  }, [reload])

  useEffect(() => {
    setImpact(null); setImpactError('')
    if (!deleting) return
    let active = true
    api<Impact>(`/api/documents/${deleting.id}/impact`)
      .then((value) => { if (active) setImpact(value) })
      .catch((err) => { if (active) setImpactError(err instanceof Error ? err.message : '삭제 영향을 확인하지 못했습니다.') })
    return () => { active = false }
  }, [deleting])

  const remove = async () => {
    if (!deleting) return
    setBusy(true); setImpactError('')
    try {
      await api(`/api/documents/${deleting.id}`, { method: 'DELETE' }, session.csrfToken)
      setDeleting(null); setNotice('자료와 연결된 분석 결과를 삭제했습니다.'); setReload((value) => value + 1)
    } catch (err) { setImpactError(err instanceof Error ? err.message : '삭제하지 못했습니다.') }
    finally { setBusy(false) }
  }
  const filtered = documents.filter((document) => document.kind === tab)
  const isMaterials = page === 'materials'
  const noResultsPage = ['brief', 'contribution', 'compare'].includes(page)

  return <div className="page-wrap private-workspace"><div className="page-heading"><div><span className="eyebrow">YOUR PRIVATE WORKSPACE</span><h1>{isMaterials ? '내 자료' : noResultsPage ? '분석 결과' : '내 작업 공간'}</h1><p>{isMaterials ? '등록한 PDF는 내 계정에 저장되고, 다시 방문해도 유지됩니다.' : `${session.user?.name ?? ''}님의 기업 분석을 준비하는 공간입니다.`}</p></div><button className="button button-primary" disabled={expired || loading} onClick={() => setUploadKind(isMaterials ? tab : 'report')}><Plus size={16} />{isMaterials ? 'PDF 등록' : '사업보고서 등록'}</button></div>
    <div className="notice"><FileText size={17} /><p>① 사업보고서 PDF 등록 → ② 내 분석에서 기업 분석 시작 → ③ 완료된 결과 확인</p></div>
    {notice && <div className="notice" role="status"><p>{notice}</p></div>}
    {loading ? <div className="empty-state" role="status"><LoaderCircle className="spin" size={26} /><p>내 자료를 불러오는 중입니다.</p></div> : error ? <div className="empty-state" role="alert"><h2>자료를 불러오지 못했어요</h2><p>{error}</p><button className="button" onClick={() => expired ? onLogin() : setReload((value) => value + 1)}><RefreshCw size={15} />{expired ? '다시 로그인' : '다시 시도'}</button></div> : <>
      {(!isMaterials || noResultsPage) && <AnalysisPanel documents={documents} session={session} comparison={page === 'compare'} onExpired={() => { setExpired(true); setDocuments([]); setError('로그인이 만료되었습니다. 다시 로그인해 주세요.') }} />}
      <div className="tabs" role="tablist" aria-label="저장된 자료 종류">{(Object.keys(labels) as Kind[]).map((kind) => <button key={kind} role="tab" aria-selected={tab === kind} onClick={() => setTab(kind)}>{labels[kind]} <span>{documents.filter((document) => document.kind === kind).length}</span></button>)}</div>
      {filtered.length ? <div className="table-scroll"><table className="data-table private-documents"><thead><tr><th>파일명</th><th>버전</th><th>쪽수·용량</th><th>등록일</th><th>관리</th></tr></thead><tbody>{filtered.map((document) => <tr key={document.id}><td><span className="file-name"><FileText size={17} />{document.name}</span></td><td>{document.version}</td><td>{document.pages}쪽 · {(document.bytes / 1024 / 1024).toFixed(2)} MB</td><td>{document.date}</td><td><div className="document-actions"><a className="icon-button" href={`/api/documents/${document.id}/file`} aria-label={`${document.name} 다운로드`}><Download size={16} /></a><button className="icon-button" aria-label={`${document.name} 삭제`} onClick={() => setDeleting(document)}><Trash2 size={16} /></button></div></td></tr>)}</tbody></table></div> : <div className="empty-state"><FileText size={30} strokeWidth={1.2} /><h2>등록한 {labels[tab]}가 없어요</h2><p>PDF를 등록하면 이곳에서 다시 조회하고 다운로드할 수 있어요.</p><button className="button" onClick={() => setUploadKind(tab)}><Upload size={15} />{labels[tab]} 등록</button></div>}
    </>}
    {uploadKind && <RegisterDocument kind={uploadKind} csrfToken={session.csrfToken} onClose={() => setUploadKind(null)} onSaved={(document) => { setUploadKind(null); setTab(document.kind); setNotice(`${document.name} 등록을 완료했습니다.`); setReload((value) => value + 1) }} />}
    {deleting && <Modal title="자료를 삭제할까요?" onClose={() => { if (!busy) setDeleting(null) }}><div className="delete-file"><FileText size={19} /><strong>{deleting.name}</strong></div>{impact ? <><p>기업 브리프 {impact.briefs}개, 개인화 분석 {impact.personalAnalyses}개가 함께 삭제됩니다.{impact.preservesBriefs && ' 독립된 기업 브리프는 유지됩니다.'}</p><div className="modal-note">원본 PDF도 삭제되며 되돌릴 수 없습니다.</div></> : !impactError && <p role="status">연결된 자료를 확인하고 있습니다.</p>}{impactError && <p className="input-error" role="alert">{impactError}</p>}<div className="modal-actions"><button className="button" disabled={busy} onClick={() => setDeleting(null)}>취소</button><button className="button button-primary" disabled={!impact || busy} onClick={remove}>{busy ? '삭제 중…' : '삭제'}</button></div></Modal>}
  </div>
}

function RegisterDocument({ kind, csrfToken, onClose, onSaved }: {
  kind: Kind; csrfToken: string | null; onClose: () => void; onSaved: (document: DocumentRecord) => void;
}) {
  const [file, setFile] = useState<File | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const input = useRef<HTMLInputElement>(null)
  const accept = (candidate?: File) => {
    if (!candidate) return
    if (!candidate.name.toLowerCase().endsWith('.pdf')) { setFile(null); setError('PDF 파일을 선택해 주세요.'); return }
    if (candidate.size > 20 * 1024 * 1024) { setFile(null); setError('20MB 이하의 PDF를 선택해 주세요.'); return }
    setFile(candidate); setError('')
  }
  const submit = async () => {
    if (!file) return
    setBusy(true); setError('')
    const body = new FormData(); body.set('kind', kind); body.set('file', file)
    try { onSaved(await api<DocumentRecord>('/api/documents', { method: 'POST', body }, csrfToken)) }
    catch (err) { setError(err instanceof Error ? err.message : '등록에 실패했습니다.'); setBusy(false) }
  }
  return <Modal title={`${labels[kind]} 등록`} onClose={() => { if (!busy) onClose() }}><p>PDF를 내 계정에 저장합니다. 암호가 없는 PDF, 최대 20MB·2,000쪽까지 등록할 수 있어요.</p><input className="sr-only" ref={input} type="file" accept=".pdf,application/pdf" aria-label={`${labels[kind]} PDF 선택`} disabled={busy} onChange={(event) => accept(event.target.files?.[0])} /><button className="upload-dropzone modal-dropzone" disabled={busy} onClick={() => input.current?.click()} onDragOver={(event) => event.preventDefault()} onDrop={(event) => { event.preventDefault(); if (!busy) accept(event.dataTransfer.files[0]) }}><Upload size={26} /><strong>{file ? file.name : 'PDF를 놓거나 클릭해 선택하세요'}</strong><span>{file ? `${(file.size / 1024 / 1024).toFixed(2)} MB · 다른 파일 선택` : 'PDF 파일 1개 선택'}</span></button>{error && <p className="input-error" role="alert">{error}</p>}<div className="modal-note"><FileText size={17} />문서 등록만 진행하며 외부 Agent로 전송하지 않습니다.</div><div className="modal-actions"><button className="button" disabled={busy} onClick={onClose}>취소</button><button className="button button-primary" disabled={!file || busy} onClick={submit}>{busy && <LoaderCircle size={15} className="spin" />}{busy ? '등록 중…' : 'PDF 등록'}</button></div></Modal>
}
