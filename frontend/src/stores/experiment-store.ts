import { create } from "zustand";
import { experimentApi } from "@/lib/api-client";
import { notify } from "@/lib/toast";
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
    } catch (e) {
      set({ isLoading: false });
      notify.error(`Failed to load experiments: ${(e as Error).message}`);
    }
  },

  fetchExperiment: async (id) => {
    set({ isLoading: true });
    try {
      const data = await experimentApi.get(id);
      set({ currentExperiment: data, isLoading: false });
    } catch (e) {
      set({ isLoading: false });
      notify.error(`Failed to load experiment: ${(e as Error).message}`);
    }
  },

  createExperiment: async (name, taskDescription, description) => {
    try {
      await experimentApi.create({ name, task_description: taskDescription, description });
      notify.success("Experiment created");
      get().fetchExperiments();
    } catch (e) {
      notify.error(`Failed to create experiment: ${(e as Error).message}`);
    }
  },

  runExperiment: async (id) => {
    try {
      await experimentApi.run(id);
      notify.success("Experiment started");
      get().fetchExperiments();
    } catch (e) {
      notify.error(`Failed to run experiment: ${(e as Error).message}`);
    }
  },

  deleteExperiment: async (id) => {
    try {
      await experimentApi.delete(id);
      notify.success("Experiment deleted");
      get().fetchExperiments();
    } catch (e) {
      notify.error(`Failed to delete experiment: ${(e as Error).message}`);
    }
  },
}));
