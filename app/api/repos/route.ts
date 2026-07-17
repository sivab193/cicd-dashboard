import { NextResponse } from "next/server";
import { getOctokit } from "@/lib/github";
import { toRunSummary } from "@/lib/github-mappers";
import { handleApiError } from "@/lib/api-utils";
import type { RepoSummary } from "@/lib/types";

export const dynamic = "force-dynamic";

// Cap how many repos we sync per request to keep the overview fast and
// stay well under GitHub's rate limits for accounts with a lot of repos.
const MAX_REPOS = 200;

export async function GET() {
  try {
    const octokit = await getOctokit();

    const repos: Awaited<
      ReturnType<typeof octokit.repos.listForAuthenticatedUser>
    >["data"] = [];
    for await (const { data } of octokit.paginate.iterator(
      octokit.repos.listForAuthenticatedUser,
      { affiliation: "owner", sort: "updated", per_page: 100 }
    )) {
      repos.push(...data);
      if (repos.length >= MAX_REPOS) break;
    }

    const summaries: RepoSummary[] = await Promise.all(
      repos.slice(0, MAX_REPOS).map(async (repo) => {
        const [owner, name] = repo.full_name.split("/");
        let latestRun: RepoSummary["latestRun"] = null;
        try {
          const { data } = await octokit.actions.listWorkflowRunsForRepo({
            owner,
            repo: name,
            per_page: 1,
          });
          const run = data.workflow_runs[0];
          if (run) latestRun = toRunSummary(run);
        } catch {
          // Actions disabled or inaccessible for this repo — leave latestRun null.
        }
        return {
          owner,
          name,
          fullName: repo.full_name,
          private: repo.private,
          htmlUrl: repo.html_url,
          updatedAt: repo.updated_at,
          latestRun,
        };
      })
    );

    return NextResponse.json({ repos: summaries });
  } catch (error) {
    return handleApiError(error);
  }
}
