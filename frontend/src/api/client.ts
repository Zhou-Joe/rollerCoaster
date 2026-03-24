import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface Project {
  id: string
  metadata: {
    name: string
    units: string
    version: number
  }
}

export const healthCheck = async () => {
  const response = await axios.get('/health')
  return response.data
}

export const createProject = async (name: string): Promise<Project> => {
  const response = await api.post('/projects', { name })
  return response.data
}

export const getProject = async (id: string): Promise<Project> => {
  const response = await api.get(`/projects/${id}`)
  return response.data
}

export const listProjects = async (): Promise<Project[]> => {
  const response = await api.get('/projects')
  return response.data
}

export default api