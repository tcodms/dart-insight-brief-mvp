import { expect, it } from 'vitest'
import { removeDemoMaterial } from './domain'
import type { Company, Workspace } from './types'

it('removes a CV and its personal link without removing the independent company brief', () => {
  const cv = { id: 'cv', name: 'CV.pdf', kind: 'cv' as const, version: 'v1', date: '', pages: 1 }
  const workspace: Workspace = {
    dataType: 'fictional_demo', materials: [cv],
    companies: [{ id: 'a', cvId: 'cv', jdId: 'jd', summary: '기업 브리프' }] as Company[],
  }
  const result = removeDemoMaterial(workspace, cv)
  expect(result.materials).toHaveLength(0)
  expect(result.companies[0].cvId).toBe('')
  expect(result.companies[0].summary).toBe('기업 브리프')
  expect(workspace.companies[0].cvId).toBe('cv')
})

it('invalidates the saved personal result when its JD is removed', () => {
  const jd = { id: 'jd', name: 'JD.pdf', kind: 'jd' as const, version: 'v1', date: '', pages: 1 }
  const workspace: Workspace = {
    dataType: 'fictional_demo', materials: [jd],
    companies: [{ id: 'a', cvId: 'cv', jdId: 'jd', requirements: '요건', summary: '기업 브리프' }] as Company[],
  }
  const result = removeDemoMaterial(workspace, jd)
  expect(result.companies[0].cvId).toBe('')
  expect(result.companies[0].jdId).toBeNull()
  expect(result.companies[0].requirements).toBeNull()
  expect(result.companies[0].summary).toBe('기업 브리프')
})
