import { NextResponse } from "next/server";
import { getOctokit } from "@/lib/github";
import { toJobSummary, toRunSummary } from "@/lib/github-mappers";
import { handleApiError } from "@/lib/api-utils";

export const dynamic = "force-dynamic";

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ owner: string; repo: string; runId: string }> }
) {
  try {
    const { owner, repo, runId } = await params;
    const octokit = await getOctokit();

    const [{ data: run }, { data: jobsData }] = await Promise.all([
      octokit.actions.getWorkflowRun({ owner, repo, run_id: Number(runId) }),
      octokit.actions.listJobsForWorkflowRun({
        owner,
        repo,
        run_id: Number(runId),
        per_page: 100,
      }),
    ]);

    return NextResponse.json({
      run: toRunSummary(run),
      jobs: jobsData.jobs.map(toJobSummary),
    });
  } catch (error) {
    return handleApiError(error);
  }
}
