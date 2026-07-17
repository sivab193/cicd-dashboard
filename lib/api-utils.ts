import { NextResponse } from "next/server";
import { GitHubAuthError } from "@/lib/github";

export function handleApiError(error: unknown) {
  if (error instanceof GitHubAuthError) {
    return NextResponse.json({ error: "Not authenticated" }, { status: 401 });
  }
  console.error(error);
  return NextResponse.json(
    { error: "GitHub API request failed" },
    { status: 502 }
  );
}
