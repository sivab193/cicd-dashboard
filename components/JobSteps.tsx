import StatusBadge from "@/components/StatusBadge";
import { duration } from "@/lib/format";
import type { JobSummary } from "@/lib/types";

export default function JobSteps({ job }: { job: JobSummary }) {
  return (
    <div className="rounded-xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950">
      <div className="flex items-center justify-between gap-4 border-b border-zinc-100 px-4 py-3 dark:border-zinc-900">
        <p className="truncate text-sm font-medium text-zinc-900 dark:text-zinc-50">
          {job.name}
        </p>
        <div className="flex shrink-0 items-center gap-3">
          <span className="text-xs text-zinc-400 dark:text-zinc-500">
            {duration(job.startedAt, job.completedAt)}
          </span>
          <StatusBadge status={job.status} conclusion={job.conclusion} />
        </div>
      </div>
      <ul className="divide-y divide-zinc-100 dark:divide-zinc-900">
        {job.steps.map((step) => (
          <li
            key={step.number}
            className="flex items-center justify-between gap-4 px-4 py-2"
          >
            <span className="truncate text-sm text-zinc-700 dark:text-zinc-300">
              {step.name}
            </span>
            <div className="flex shrink-0 items-center gap-3">
              <span className="text-xs text-zinc-400 dark:text-zinc-500">
                {duration(step.startedAt, step.completedAt)}
              </span>
              <StatusBadge status={step.status} conclusion={step.conclusion} />
            </div>
          </li>
        ))}
        {job.steps.length === 0 && (
          <li className="px-4 py-2 text-sm text-zinc-400 dark:text-zinc-500">
            No steps reported yet.
          </li>
        )}
      </ul>
    </div>
  );
}
