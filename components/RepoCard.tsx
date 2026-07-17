import Link from "next/link";
import StatusBadge from "@/components/StatusBadge";
import { duration, relativeTime } from "@/lib/format";
import type { RepoSummary } from "@/lib/types";

export default function RepoCard({ repo }: { repo: RepoSummary }) {
  const run = repo.latestRun;

  return (
    <Link
      href={`/repo/${repo.owner}/${repo.name}`}
      className="flex flex-col gap-3 rounded-xl border border-zinc-200 bg-white p-4 transition hover:border-zinc-300 hover:shadow-sm dark:border-zinc-800 dark:bg-zinc-950 dark:hover:border-zinc-700"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate text-sm font-medium text-zinc-900 dark:text-zinc-50">
            {repo.name}
          </p>
          {run?.branch && (
            <p className="truncate text-xs text-zinc-500 dark:text-zinc-400">
              {run.branch}
            </p>
          )}
        </div>
        {run ? (
          <StatusBadge status={run.status} conclusion={run.conclusion} />
        ) : (
          <span className="shrink-0 rounded-full bg-zinc-100 px-2.5 py-1 text-xs font-medium text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400">
            No runs
          </span>
        )}
      </div>

      {run?.commitMessage && (
        <p className="truncate text-xs text-zinc-600 dark:text-zinc-400">
          {run.commitMessage}
        </p>
      )}

      {run && (
        <div className="flex items-center gap-2 text-[11px] text-zinc-400 dark:text-zinc-500">
          {run.actor && <span className="truncate">{run.actor}</span>}
          <span>·</span>
          <span>
            {duration(
              run.runStartedAt ?? run.createdAt,
              run.status === "completed" ? run.updatedAt : null
            )}
          </span>
          <span>·</span>
          <span>{relativeTime(run.updatedAt)}</span>
        </div>
      )}
    </Link>
  );
}
