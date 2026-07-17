"use client";

import useSWR from "swr";
import RepoCard from "@/components/RepoCard";
import type { RepoSummary } from "@/lib/types";

const fetcher = (url: string) =>
  fetch(url).then((res) => {
    if (!res.ok) throw new Error("Failed to load repositories");
    return res.json();
  });

export default function DashboardPage() {
  const { data, error, isLoading } = useSWR<{ repos: RepoSummary[] }>(
    "/api/repos",
    fetcher,
    { refreshInterval: 20000, revalidateOnFocus: true }
  );

  return (
    <main className="mx-auto w-full max-w-6xl flex-1 px-6 py-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">
          Repositories
        </h1>
        {data && (
          <span className="text-xs text-zinc-400 dark:text-zinc-500">
            {data.repos.length} repo{data.repos.length === 1 ? "" : "s"}
          </span>
        )}
      </div>

      {isLoading && (
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          Loading repositories…
        </p>
      )}
      {error && (
        <p className="text-sm" style={{ color: "var(--status-critical)" }}>
          Couldn&apos;t load repositories. Try refreshing.
        </p>
      )}
      {data && data.repos.length === 0 && (
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          No repositories found.
        </p>
      )}

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {data?.repos.map((repo) => (
          <RepoCard key={repo.fullName} repo={repo} />
        ))}
      </div>
    </main>
  );
}
