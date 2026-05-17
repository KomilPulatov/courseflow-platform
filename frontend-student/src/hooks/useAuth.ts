import { useCallback } from 'react'
import { useNavigate } from 'react-router-dom'

export function useAuth() {
  const navigate = useNavigate()

  const isLoggedIn = !!localStorage.getItem('crsp_token')

  const saveAuth = useCallback((token: string, userId: string) => {
    localStorage.setItem('crsp_token', token)
    localStorage.setItem('crsp_user_id', userId)
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('crsp_token')
    localStorage.removeItem('crsp_user_id')
    navigate('/')
  }, [navigate])

  const getUserId = useCallback(
    () => localStorage.getItem('crsp_user_id') ?? '',
    [],
  )

  return { isLoggedIn, saveAuth, logout, getUserId }
}
