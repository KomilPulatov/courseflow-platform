import axios from 'axios'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE ?? 'http://localhost:8000',
})

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('crsp_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

client.interceptors.response.use(
  (res) => res,
  (err) => {
    // Only redirect on 401 if the user already had a session (token was present).
    // During login the 401 means wrong credentials — let the page handle it.
    const hadToken = !!localStorage.getItem('crsp_token')
    if (err.response?.status === 401 && hadToken) {
      localStorage.removeItem('crsp_token')
      localStorage.removeItem('crsp_user_id')
      window.location.href = '/login/student'
    }
    return Promise.reject(err)
  },
)

export default client
