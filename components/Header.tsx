import Image from "next/image";
import Link from "next/link";
import { auth, signOut } from "@/lib/auth";

export default async function Header() {
  const session = await auth();
  if (!session) return null;

  return (
    <header className="flex items-center justify-between border-b border-zinc-200 bg-white px-6 py-3 dark:border-zinc-800 dark:bg-zinc-950">
      <Link href="/" className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">
        CI/CD Dashboard
      </Link>
      <div className="flex items-center gap-3">
        {session.user?.image && (
          <Image
            src={session.user.image}
            alt={session.user.name ?? "avatar"}
            width={24}
            height={24}
            className="rounded-full"
          />
        )}
        <span className="text-sm text-zinc-600 dark:text-zinc-400">
          {session.user?.name}
        </span>
        <form
          action={async () => {
            "use server";
            await signOut({ redirectTo: "/login" });
          }}
        >
          <button
            type="submit"
            className="rounded-md border border-zinc-300 px-2.5 py-1 text-xs font-medium text-zinc-600 transition hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-900"
          >
            Sign out
          </button>
        </form>
      </div>
    </header>
  );
}
