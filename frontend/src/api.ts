export interface Session {
  authenticated: boolean
  googleConfigured: boolean
  user: { id: string; name: string; email: string } | null
  csrfToken: string | null
}

export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message) }
}

export async function api<T>(url: string, options: RequestInit = {}, csrfToken?: string | null): Promise<T> {
  const headers = new Headers(options.headers)
  if (csrfToken) headers.set('X-CSRF-Token', csrfToken)
  const response = await fetch(url, { ...options, headers, credentials: 'same-origin' })
  if (!response.ok) {
    let message = response.status === 401 ? '로그인이 만료되었습니다. 다시 로그인해 주세요.' : '요청을 완료하지 못했습니다. 다시 시도해 주세요.'
    try { const body = await response.json(); if (typeof body.detail === 'string') message = body.detail } catch { /* Non-JSON gateway errors use the fallback. */ }
    throw new ApiError(response.status, message)
  }
  return response.status === 204 ? undefined as T : response.json()
}
