import { create } from "zustand";
import { experimentApi } from "@/lib/api-client";
import type { Experiment, ExperimentRun } from "@/types/experiment";

interface ExperimentState {
  experiments: Experiment[];
  currentExperiment: { experiment: Experiment; comparison: unknown; runs: ExperimentRun[] } | null;
  isLoading: boolean;
  total: number;

  fetchExperiments: () => Promise<void>;
  fetchExperiment: (id: string) => Promise<void>;
  createExperiment: (name: string, taskDescription: string, description?: string) => Promise<void>;
  runExperiment: (id: string) => Promise<void>;
  deleteExperiment: (id: string) => Promise<void>;
}

export const useExperimentStore = create<ExperimentState>((set, get) => ({
  experiments: [],
  currentExperiment: null,
  isLoading: false,
  total: 0,

  fetchExperiments: async () => {
    set({ isLoading: true });
    try {
      const result = await experimentApi.list();
      set({ experiments: result.items, total: result.total, isLoading: false });
    } catch {
      set({ isLoading: false });
    }
  },

  fetchExperiment: async (id) => {
    set({ isLoading: true });
    try {
      const data = await experimentApi.get(id);
      set({ currentExperiment: data, isLoading: false });
    } catch {
      set({ isLoading: false });
    }
  },

  createExperiment: async (name, taskDescription, description) => {
    await experimentApi.create({ name, task_description: taskDescription, description });
    get().fetchExperiments();
  },

  runExperiment: async (id) => {
    await experimentApi.run(id);
    get().fetchExperiments();
  },

  deleteExperiment: async (id) => {
    await experimentApi.delete(id);
    get().fetchExperiments();
  },
}));
