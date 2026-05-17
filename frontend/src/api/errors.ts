import axios from 'axios'

export function apiErrorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError(error)) {
    const detail =
      typeof error.response?.data === 'object' &&
      error.response?.data !== null &&
      'detail' in error.response.data
        ? (error.response.data as { detail?: unknown }).detail
        : undefined
    if (typeof detail === 'string') return detail
  }
  return fallback
}
