import Link from "next/link";
import RunHistory from "@/components/RunHistory";

export default async function RepoDetailPage({
  params,
}: {
  params: Promise<{ owner: string; repo: string }>;
}) {
  const { owner, repo } = await params;

  return (
    <main className="mx-auto w-full max-w-4xl flex-1 px-6 py-8">
      <div className="mb-6 flex items-center justify-between gap-4">
        <div className="min-w-0">
          <Link
            href="/"
            className="text-xs text-zinc-400 hover:text-zinc-600 dark:text-zinc-500 dark:hover:text-zinc-300"
          >
            ← All repositories
          </Link>
          <h1 className="mt-1 truncate text-lg font-semibold text-zinc-900 dark:text-zinc-50">
            {owner}/{repo}
          </h1>
        </div>
        <a
          href={`https://github.com/${owner}/${repo}`}
          target="_blank"
          rel="noopener noreferrer"
          className="shrink-0 text-xs text-zinc-400 hover:text-zinc-600 dark:text-zinc-500 dark:hover:text-zinc-300"
        >
          View on GitHub ↗
        </a>
      </div>
      <RunHistory owner={owner} repo={repo} />
    </main>
  );
}
