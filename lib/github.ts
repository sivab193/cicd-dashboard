import { Octokit } from "@octokit/rest";
import { auth } from "@/lib/auth";

export class GitHubAuthError extends Error {}

export async function getOctokit() {
  const session = await auth();
  if (!session?.accessToken) {
    throw new GitHubAuthError("Not authenticated");
  }
  return new Octokit({ auth: session.accessToken });
}
