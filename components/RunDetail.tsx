"use client";

import useSWR from "swr";
import StatusBadge from "@/components/StatusBadge";
import JobSteps from "@/components/JobSteps";
import { duration, relativeTime } from "@/lib/format";
import type { JobSummary, RunSummary } from "@/lib/types";

const fetcher = (url: string) =>
  fetch(url).then((res) => {
    if (!res.ok) throw new Error("Failed to load run");
    return res.json();
  });

export default function RunDetail({
  owner,
  repo,
  runId,
}: {
  owner: string;
  repo: string;
  runId: string;
}) {
  const { data, error, isLoading } = useSWR<{
    run: RunSummary;
    jobs: JobSummary[];
  }>(`/api/repos/${owner}/${repo}/runs/${runId}`, fetcher, {
    refreshInterval: (latestData) =>
      !latestData || latestData.run.status !== "completed" ? 4000 : 0,
  });

  if (isLoading) {
    return (
      <p className="mt-6 text-sm text-zinc-500 dark:text-zinc-400">
        Loading run…
      </p>
    );
  }
  if (error || !data) {
    return (
      <p className="mt-6 text-sm" style={{ color: "var(--status-critical)" }}>
        Couldn&apos;t load this run.
      </p>
    );
  }

  const { run, jobs } = data;

  return (
    <div className="mt-4 flex flex-col gap-6">
      <div className="flex items-start justify-between gap-4 rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950">
        <div className="min-w-0">
          <p className="truncate text-base font-semibold text-zinc-900 dark:text-zinc-50">
            {run.workflowName ?? "Workflow run"}
          </p>
          <p className="truncate text-xs text-zinc-500 dark:text-zinc-400">
            {run.branch} · {run.commitMessage}
          </p>
          <div className="mt-2 flex items-center gap-3 text-[11px] text-zinc-400 dark:text-zinc-500">
            {run.actor && <span>{run.actor}</span>}
            <span>
              {duration(
                run.runStartedAt ?? run.createdAt,
                run.status === "completed" ? run.updatedAt : null
              )}
            </span>
            <span>{relativeTime(run.updatedAt)}</span>
            <a
              href={run.htmlUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-zinc-600 dark:hover:text-zinc-300"
            >
              View on GitHub ↗
            </a>
          </div>
        </div>
        <StatusBadge status={run.status} conclusion={run.conclusion} />
      </div>

      <div className="flex flex-col gap-4">
        {jobs.map((job) => (
          <JobSteps key={job.id} job={job} />
        ))}
        {jobs.length === 0 && (
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            No jobs for this run yet.
          </p>
        )}
      </div>
    </div>
  );
}
