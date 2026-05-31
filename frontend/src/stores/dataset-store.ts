import { create } from "zustand";
import { datasetApi } from "@/lib/api-client";
import { notify } from "@/lib/toast";
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
    } catch (e) {
      set({ isLoading: false });
      notify.error(`Failed to load datasets: ${(e as Error).message}`);
    }
  },

  fetchDataset: async (id) => {
    set({ isLoading: true });
    try {
      const data = await datasetApi.get(id);
      set({ currentDataset: data, isLoading: false });
    } catch (e) {
      set({ isLoading: false });
      notify.error(`Failed to load dataset: ${(e as Error).message}`);
    }
  },

  createDataset: async (name, description) => {
    try {
      await datasetApi.create({ name, description });
      notify.success("Dataset created");
      get().fetchDatasets();
    } catch (e) {
      notify.error(`Failed to create dataset: ${(e as Error).message}`);
    }
  },

  deleteDataset: async (id) => {
    try {
      await datasetApi.delete(id);
      notify.success("Dataset deleted");
      get().fetchDatasets();
    } catch (e) {
      notify.error(`Failed to delete dataset: ${(e as Error).message}`);
    }
  },

  addItem: async (id, input, expectedOutput) => {
    try {
      await datasetApi.addItem(id, { input, expected_output: expectedOutput });
      notify.success("Item added");
      get().fetchDataset(id);
    } catch (e) {
      notify.error(`Failed to add item: ${(e as Error).message}`);
    }
  },
}));
