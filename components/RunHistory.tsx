"use client";

import Link from "next/link";
import useSWR from "swr";
import StatusBadge from "@/components/StatusBadge";
import { duration, relativeTime } from "@/lib/format";
import type { RunSummary } from "@/lib/types";

const fetcher = (url: string) =>
  fetch(url).then((res) => {
    if (!res.ok) throw new Error("Failed to load runs");
    return res.json();
  });

export default function RunHistory({
  owner,
  repo,
}: {
  owner: string;
  repo: string;
}) {
  const { data, error, isLoading } = useSWR<{ runs: RunSummary[] }>(
    `/api/repos/${owner}/${repo}/runs`,
    fetcher,
    { refreshInterval: 10000 }
  );

  if (isLoading) {
    return (
      <p className="text-sm text-zinc-500 dark:text-zinc-400">
        Loading runs…
      </p>
    );
  }
  if (error) {
    return (
      <p className="text-sm" style={{ color: "var(--status-critical)" }}>
        Couldn&apos;t load workflow runs.
      </p>
    );
  }
  if (!data || data.runs.length === 0) {
    return (
      <p className="text-sm text-zinc-500 dark:text-zinc-400">
        No workflow runs yet.
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      {data.runs.map((run) => (
        <Link
          key={run.id}
          href={`/repo/${owner}/${repo}/run/${run.id}`}
          className="flex items-center justify-between gap-4 rounded-lg border border-zinc-200 bg-white px-4 py-3 transition hover:border-zinc-300 hover:shadow-sm dark:border-zinc-800 dark:bg-zinc-950 dark:hover:border-zinc-700"
        >
          <div className="min-w-0">
            <p className="truncate text-sm font-medium text-zinc-900 dark:text-zinc-50">
              {run.workflowName ?? "Workflow run"}
            </p>
            <p className="truncate text-xs text-zinc-500 dark:text-zinc-400">
              {run.branch} · {run.commitMessage}
            </p>
          </div>
          <div className="flex shrink-0 items-center gap-3 text-xs text-zinc-400 dark:text-zinc-500">
            <span>
              {duration(
                run.runStartedAt ?? run.createdAt,
                run.status === "completed" ? run.updatedAt : null
              )}
            </span>
            <span>{relativeTime(run.updatedAt)}</span>
            <StatusBadge status={run.status} conclusion={run.conclusion} />
          </div>
        </Link>
      ))}
    </div>
  );
}
