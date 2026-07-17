import type { Endpoints } from "@octokit/types";
import type { JobStep, JobSummary, RunSummary } from "@/lib/types";

type WorkflowRun =
  Endpoints["GET /repos/{owner}/{repo}/actions/runs"]["response"]["data"]["workflow_runs"][number];

type WorkflowJob =
  Endpoints["GET /repos/{owner}/{repo}/actions/runs/{run_id}/jobs"]["response"]["data"]["jobs"][number];

export function toRunSummary(run: WorkflowRun): RunSummary {
  return {
    id: run.id,
    workflowName: run.name ?? null,
    status: run.status ?? "unknown",
    conclusion: run.conclusion,
    branch: run.head_branch,
    event: run.event,
    actor: run.actor?.login ?? null,
    commitMessage: run.head_commit?.message?.split("\n")[0] ?? null,
    htmlUrl: run.html_url,
    createdAt: run.created_at,
    updatedAt: run.updated_at,
    runStartedAt: run.run_started_at ?? null,
  };
}

export function toJobSummary(job: WorkflowJob): JobSummary {
  return {
    id: job.id,
    name: job.name,
    status: job.status,
    conclusion: job.conclusion,
    startedAt: job.started_at ?? null,
    completedAt: job.completed_at ?? null,
    htmlUrl: job.html_url ?? "",
    steps: (job.steps ?? []).map(
      (step): JobStep => ({
        name: step.name,
        status: step.status,
        conclusion: step.conclusion,
        number: step.number,
        startedAt: step.started_at ?? null,
        completedAt: step.completed_at ?? null,
      })
    ),
  };
}
