import { FileText } from 'lucide-react'

export default function CompanyFolderArt() {
  return <span className="company-folder-art" aria-hidden="true">
    <span className="company-folder-back" />
    <span className="company-folder-sheet sheet-first"><FileText size={13} strokeWidth={1.6} /><i /><i /><i /></span>
    <span className="company-folder-sheet sheet-second"><FileText size={13} strokeWidth={1.6} /><i /><i /></span>
    <span className="company-folder-front" />
  </span>
}
