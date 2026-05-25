import { create } from "zustand";
import { traceApi } from "@/lib/api-client";
import type { Trace, TraceDetail } from "@/types/trace";

interface TraceState {
  traces: Trace[];
  currentTrace: TraceDetail | null;
  isLoading: boolean;
  error: string | null;
  total: number;
  page: number;

  fetchTraces: (params?: Record<string, string | undefined>) => Promise<void>;
  fetchTrace: (id: string) => Promise<void>;
  deleteTrace: (id: string) => Promise<void>;
  setPage: (page: number) => void;
}

export const useTraceStore = create<TraceState>((set, get) => ({
  traces: [],
  currentTrace: null,
  isLoading: false,
  error: null,
  total: 0,
  page: 1,

  fetchTraces: async (params) => {
    set({ isLoading: true, error: null });
    try {
      const clean: Record<string, string> = {
        page: String(get().page),
        page_size: "20",
      };
      if (params) {
        for (const [k, v] of Object.entries(params)) {
          if (v !== undefined && v !== "") clean[k] = v;
        }
      }
      const result = await traceApi.list(clean);
      set({ traces: result.items, total: result.total, isLoading: false });
    } catch (e) {
      set({ error: (e as Error).message, isLoading: false });
    }
  },

  fetchTrace: async (id) => {
    set({ isLoading: true, error: null });
    try {
      const detail = await traceApi.get(id);
      set({ currentTrace: detail, isLoading: false });
    } catch (e) {
      set({ error: (e as Error).message, isLoading: false });
    }
  },

  deleteTrace: async (id) => {
    await traceApi.delete(id);
    get().fetchTraces();
  },

  setPage: (page) => set({ page }),
}));
