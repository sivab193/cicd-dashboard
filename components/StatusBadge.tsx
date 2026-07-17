import { getBuildState, BUILD_STATE_META } from "@/lib/status";

export default function StatusBadge({
  status,
  conclusion,
}: {
  status: string;
  conclusion: string | null;
}) {
  const state = getBuildState(status, conclusion);
  const meta = BUILD_STATE_META[state];

  return (
    <span
      className={`inline-flex shrink-0 items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium text-zinc-700 dark:text-zinc-300 ${meta.bgClass}`}
    >
      <span
        className={`h-1.5 w-1.5 rounded-full ${meta.dotClass} ${
          meta.pulse ? "animate-pulse" : ""
        }`}
      />
      {meta.label}
    </span>
  );
}
