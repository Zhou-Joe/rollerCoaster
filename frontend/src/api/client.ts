import axios from 'axios'
import type { Project, SimulationState, InterpolatedPath } from '../types'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

export const healthCheck = async () => {
  const response = await axios.get('/health')
  return response.data
}

// Project APIs
export const createProject = async (name: string): Promise<Project> => {
  const response = await api.post('/projects/', { metadata: { name } })
  return response.data
}

export const getProject = async (id: string): Promise<Project> => {
  const response = await api.get(`/projects/${id}`)
  return response.data
}

export const listProjects = async (): Promise<Project[]> => {
  const response = await api.get('/projects/')
  return response.data
}

export const updateProject = async (id: string, data: Partial<Project>): Promise<Project> => {
  const response = await api.put(`/projects/${id}`, data)
  return response.data
}

export const deleteProject = async (id: string): Promise<void> => {
  await api.delete(`/projects/${id}`)
}

// Geometry APIs
export const getInterpolatedPath = async (projectId: string, pathId: string): Promise<InterpolatedPath> => {
  const response = await api.get(`/geometry/projects/${projectId}/paths/${pathId}`)
  return response.data
}

export const validateGeometry = async (projectId: string): Promise<{ valid: boolean; warnings: string[]; errors: string[] }> => {
  const response = await api.get(`/geometry/projects/${projectId}/geometry/validate`)
  return response.data
}

// Simulation APIs
export const startSimulation = async (projectId: string): Promise<void> => {
  await api.post(`/physics/projects/${projectId}/simulate/start`)
}

export const stopSimulation = async (projectId: string): Promise<void> => {
  await api.post(`/physics/projects/${projectId}/simulate/stop`)
}

export const resetSimulation = async (projectId: string): Promise<void> => {
  await api.post(`/physics/projects/${projectId}/simulate/reset`)
}

export const getSimulationState = async (projectId: string): Promise<SimulationState> => {
  const response = await api.get(`/physics/projects/${projectId}/simulate/state`)
  return response.data
}

export const stepSimulation = async (projectId: string, steps: number = 1): Promise<SimulationState> => {
  const response = await api.post(`/physics/projects/${projectId}/simulate/step`, { steps })
  return response.data
}

export const runSimulation = async (projectId: string, duration_s: number): Promise<SimulationState[]> => {
  const response = await api.post(`/physics/projects/${projectId}/simulate/run`, { duration_s })
  return response.data
}

// Points API - uses project update
export const addPoint = async (projectId: string, point: { x: number; y: number; z: number; bank_deg: number }): Promise<void> => {
  // Get current project and add point
  const project = await getProject(projectId)
  const newPoint = {
    id: `point_${Date.now()}`,
    ...point,
    editable: true
  }
  await updateProject(projectId, {
    points: [...project.points, newPoint]
  })
}

export const updatePoint = async (projectId: string, pointId: string, data: { x?: number; y?: number; z?: number; bank_deg?: number }): Promise<void> => {
  const project = await getProject(projectId)
  const points = project.points.map(p =>
    p.id === pointId ? { ...p, ...data } : p
  )
  await updateProject(projectId, { points })
}

export const deletePoint = async (projectId: string, pointId: string): Promise<void> => {
  const project = await getProject(projectId)
  const points = project.points.filter(p => p.id !== pointId)
  await updateProject(projectId, { points })
}

// Paths API
export const createPath = async (projectId: string, name: string, pointIds: string[]): Promise<{ id: string }> => {
  const project = await getProject(projectId)
  const newPath = {
    id: `path_${Date.now()}`,
    name,
    point_ids: pointIds
  }
  await updateProject(projectId, {
    paths: [...project.paths, newPath]
  })
  return { id: newPath.id }
}

// Trains API
export const createTrain = async (projectId: string, vehicleIds: string[], pathId: string, position: number): Promise<{ id: string }> => {
  const project = await getProject(projectId)
  const newTrain = {
    id: `train_${Date.now()}`,
    vehicle_ids: vehicleIds,
    current_path_id: pathId,
    front_position_s: position
  }
  await updateProject(projectId, {
    trains: [...project.trains, newTrain]
  })
  return { id: newTrain.id }
}

export const setTrainPosition = async (projectId: string, trainId: string, pathId: string, position: number): Promise<void> => {
  await api.put(`/physics/projects/${projectId}/trains/${trainId}/position`, { path_id: pathId, position_s: position })
}

export const setTrainVelocity = async (projectId: string, trainId: string, velocity: number): Promise<void> => {
  await api.put(`/physics/projects/${projectId}/trains/${trainId}/velocity`, { velocity_mps: velocity })
}

export default api