import { create } from "zustand";
import { datasetApi } from "@/lib/api-client";
import type { Dataset, DatasetItem } from "@/types/dataset";

interface DatasetState {
  datasets: Dataset[];
  currentDataset: { dataset: Dataset; items: DatasetItem[] } | null;
  isLoading: boolean;
  total: number;

  fetchDatasets: () => Promise<void>;
  fetchDataset: (id: string) => Promise<void>;
  createDataset: (name: string, description?: string) => Promise<void>;
  deleteDataset: (id: string) => Promise<void>;
  addItem: (id: string, input: Record<string, unknown>, expectedOutput?: string) => Promise<void>;
}

export const useDatasetStore = create<DatasetState>((set, get) => ({
  datasets: [],
  currentDataset: null,
  isLoading: false,
  total: 0,

  fetchDatasets: async () => {
    set({ isLoading: true });
    try {
      const result = await datasetApi.list();
      set({ datasets: result.items, total: result.total, isLoading: false });
    } catch {
      set({ isLoading: false });
    }
  },

  fetchDataset: async (id) => {
    set({ isLoading: true });
    try {
      const data = await datasetApi.get(id);
      set({ currentDataset: data, isLoading: false });
    } catch {
      set({ isLoading: false });
    }
  },

  createDataset: async (name, description) => {
    await datasetApi.create({ name, description });
    get().fetchDatasets();
  },

  deleteDataset: async (id) => {
    await datasetApi.delete(id);
    get().fetchDatasets();
  },

  addItem: async (id, input, expectedOutput) => {
    await datasetApi.addItem(id, { input, expected_output: expectedOutput });
    get().fetchDataset(id);
  },
}));
