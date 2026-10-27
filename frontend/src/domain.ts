import type { Company, Material, Workspace } from './types'

export function toggleComparison(selected: string[], id: string): string[] {
  if (selected.includes(id)) return selected.filter((item) => item !== id)
  return selected.length < 3 ? [...selected, id] : selected
}

export function hasDifferentCvs(companies: Company[]): boolean {
  return new Set(companies.map((company) => company.cvId)).size > 1
}

export function relatedCompanies(material: Material, companies: Company[]): Company[] {
  return companies.filter((company) => material.kind === 'cv' ? company.cvId === material.id : company.jdId === material.id)
}

export function removeDemoMaterial(workspace: Workspace, material: Material): Workspace {
  // Only the fictional in-memory contribution result is cleared; company briefs survive.
  return {
    ...workspace,
    materials: workspace.materials.filter((item) => item.id !== material.id),
    companies: workspace.companies.map((company) => {
      if (material.kind === 'cv' && company.cvId === material.id) {
        return { ...company, cvId: '', jdId: company.jdId }
      }
      if (material.kind === 'jd' && company.jdId === material.id) {
        return { ...company, cvId: '', jdId: null, requirements: null }
      }
      return company
    }),
  }
}
