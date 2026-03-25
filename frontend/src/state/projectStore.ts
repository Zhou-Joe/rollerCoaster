import { create } from 'zustand'
import type { Project, SimulationState, InterpolatedPath, TrainPhysicsState } from '../types'

interface ProjectState {
  // Project data
  currentProject: Project | null
  projects: Project[]

  // Simulation state
  simulationState: SimulationState | null
  interpolatedPaths: Map<string, InterpolatedPath>
  selectedTrainId: string | null

  // UI state
  playbackSpeed: number
  showTelemetry: boolean
  selectedPathId: string | null
  editingMode: 'view' | 'edit' | 'simulate'

  // Actions
  setCurrentProject: (project: Project | null) => void
  setProjects: (projects: Project[]) => void
  setSimulationState: (state: SimulationState) => void
  setInterpolatedPath: (pathId: string, path: InterpolatedPath) => void
  setSelectedTrain: (trainId: string | null) => void
  setPlaybackSpeed: (speed: number) => void
  toggleTelemetry: () => void
  setSelectedPath: (pathId: string | null) => void
  setEditingMode: (mode: 'view' | 'edit' | 'simulate') => void
  updateTrainState: (trainId: string, state: Partial<TrainPhysicsState>) => void
}

export const useProjectStore = create<ProjectState>((set) => ({
  // Project data
  currentProject: null,
  projects: [],

  // Simulation state
  simulationState: null,
  interpolatedPaths: new Map(),
  selectedTrainId: null,

  // UI state
  playbackSpeed: 1.0,
  showTelemetry: true,
  selectedPathId: null,
  editingMode: 'view',

  // Actions
  setCurrentProject: (project) => set({ currentProject: project }),
  setProjects: (projects) => set({ projects }),
  setSimulationState: (state) => set({ simulationState: state }),
  setInterpolatedPath: (pathId, path) => set((state) => {
    const newPaths = new Map(state.interpolatedPaths)
    newPaths.set(pathId, path)
    return { interpolatedPaths: newPaths }
  }),
  setSelectedTrain: (trainId) => set({ selectedTrainId: trainId }),
  setPlaybackSpeed: (speed) => set({ playbackSpeed: speed }),
  toggleTelemetry: () => set((state) => ({ showTelemetry: !state.showTelemetry })),
  setSelectedPath: (pathId) => set({ selectedPathId: pathId }),
  setEditingMode: (mode) => set({ editingMode: mode }),
  updateTrainState: (trainId, trainState) => set((state) => {
    if (!state.simulationState) return state
    const trains = state.simulationState.trains.map((t) =>
      t.train_id === trainId ? { ...t, ...trainState } : t
    )
    return { simulationState: { ...state.simulationState, trains } }
  }),
}))