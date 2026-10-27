export interface Evidence {
  id: string
  title: string
  page: number
  section: string
  quote: string
  explanation: string
}

export interface Company {
  id: string
  name: string
  initial: string
  industry: string
  role: string
  period: string
  updated: string
  reportName: string
  pages: number
  cvId: string
  jdId: string | null
  status: 'ready'
  summary: string
  business: string
  strategy: string
  finance: string
  organization: string
  requirements: string | null
  experience: string
  connection: '직접 연결' | '간접 연결' | '자료 부족'
  reason: string
  contribution: string
  gap: string
  evidence: Evidence[]
}

export interface Material {
  id: string
  name: string
  kind: 'cv' | 'jd'
  version: string
  date: string
  pages: number
}

export interface Workspace {
  dataType: 'fictional_demo'
  companies: Company[]
  materials: Material[]
}

export type Page = 'home' | 'workspace' | 'brief' | 'materials' | 'contribution' | 'compare'
