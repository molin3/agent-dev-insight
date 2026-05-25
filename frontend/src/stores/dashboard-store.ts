import { create } from "zustand";
import { dashboardApi } from "@/lib/api-client";
import type { DashboardOverview } from "@/types/dashboard";

interface DashboardState {
  overview: DashboardOverview | null;
  isLoading: boolean;
  fetchOverview: () => Promise<void>;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  overview: null,
  isLoading: false,

  fetchOverview: async () => {
    set({ isLoading: true });
    try {
      const data = await dashboardApi.overview();
      set({ overview: data, isLoading: false });
    } catch {
      set({ isLoading: false });
    }
  },
}));
