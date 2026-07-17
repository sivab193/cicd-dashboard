import { NextResponse } from "next/server";
import { getOctokit } from "@/lib/github";
import { toRunSummary } from "@/lib/github-mappers";
import { handleApiError } from "@/lib/api-utils";

export const dynamic = "force-dynamic";

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ owner: string; repo: string }> }
) {
  try {
    const { owner, repo } = await params;
    const octokit = await getOctokit();
    const { data } = await octokit.actions.listWorkflowRunsForRepo({
      owner,
      repo,
      per_page: 30,
    });
    return NextResponse.json({
      runs: data.workflow_runs.map(toRunSummary),
    });
  } catch (error) {
    return handleApiError(error);
  }
}
