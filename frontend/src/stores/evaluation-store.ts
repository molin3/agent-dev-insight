import { create } from "zustand";
import { evaluationsApi } from "@/lib/api-client";
import { notify } from "@/lib/toast";

export interface EvalSummary {
  traceId: string;
  traceName: string;
  status: string;
  scores: { name: string; value: number }[];
}

interface EvaluationState {
  evaluations: EvalSummary[];
  isLoading: boolean;
  fetchEvaluations: () => Promise<void>;
}

export const useEvaluationStore = create<EvaluationState>((set) => ({
  evaluations: [],
  isLoading: false,

  fetchEvaluations: async () => {
    set({ isLoading: true });
    try {
      const data = await evaluationsApi.list();
      set({ evaluations: data, isLoading: false });
    } catch (e) {
      set({ isLoading: false });
      notify.error(`Failed to load evaluations: ${(e as Error).message}`);
    }
  },
}));
