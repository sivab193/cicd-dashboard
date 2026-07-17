import Link from "next/link";
import RunDetail from "@/components/RunDetail";

export default async function RunDetailPage({
  params,
}: {
  params: Promise<{ owner: string; repo: string; runId: string }>;
}) {
  const { owner, repo, runId } = await params;

  return (
    <main className="mx-auto w-full max-w-4xl flex-1 px-6 py-8">
      <Link
        href={`/repo/${owner}/${repo}`}
        className="text-xs text-zinc-400 hover:text-zinc-600 dark:text-zinc-500 dark:hover:text-zinc-300"
      >
        ← {owner}/{repo}
      </Link>
      <RunDetail owner={owner} repo={repo} runId={runId} />
    </main>
  );
}
