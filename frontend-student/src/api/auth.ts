import client from './client'

export interface INSLoginRequest {
  student_number: string
  password: string
}

export interface ManualStartRequest {
  student_number: string
  full_name: string
  email: string
  password: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  role: string
  profile_source: string
  student_number?: string
  full_name?: string
  requires_profile_completion?: boolean
}

export async function insLogin(data: INSLoginRequest): Promise<AuthResponse> {
  const res = await client.post('/api/v1/auth/student/ins-login', data)
  return res.data
}

export async function manualStart(data: ManualStartRequest): Promise<AuthResponse> {
  const res = await client.post('/api/v1/auth/student/manual-start', data)
  return res.data
}

export async function manualLogin(email: string, password: string): Promise<AuthResponse> {
  const res = await client.post('/api/v1/auth/student/manual-login', { email, password })
  return res.data
}
