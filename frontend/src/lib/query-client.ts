import { QueryClient } from "@tanstack/react-query";

/**
 * TanStack Query client — shared across the app.
 * staleTime 30s: dashboards re-render predictably without thrashing.
 * refetchOnWindowFocus false: avoids accidental load spikes when alt-tabbing.
 * retry 1: one automatic retry on transient errors; api.ts owns 401-refresh.
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});
