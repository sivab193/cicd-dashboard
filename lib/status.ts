export type BuildState =
  | "queued"
  | "running"
  | "success"
  | "failure"
  | "warning"
  | "cancelled"
  | "skipped"
  | "neutral"
  | "unknown";

export function getBuildState(
  status: string,
  conclusion: string | null
): BuildState {
  if (
    status === "queued" ||
    status === "waiting" ||
    status === "requested" ||
    status === "pending"
  ) {
    return "queued";
  }
  if (status !== "completed") {
    return "running";
  }
  switch (conclusion) {
    case "success":
      return "success";
    case "failure":
    case "timed_out":
      return "failure";
    case "action_required":
      return "warning";
    case "cancelled":
      return "cancelled";
    case "skipped":
      return "skipped";
    case "neutral":
      return "neutral";
    default:
      return "unknown";
  }
}

type StateMeta = {
  label: string;
  dotClass: string;
  bgClass: string;
  pulse?: boolean;
};

export const BUILD_STATE_META: Record<BuildState, StateMeta> = {
  queued: {
    label: "Queued",
    dotClass: "bg-[var(--status-neutral)]",
    bgClass: "bg-[var(--status-neutral)]/10",
  },
  running: {
    label: "Running",
    dotClass: "bg-[var(--status-info)]",
    bgClass: "bg-[var(--status-info)]/10",
    pulse: true,
  },
  success: {
    label: "Passing",
    dotClass: "bg-[var(--status-good)]",
    bgClass: "bg-[var(--status-good)]/10",
  },
  failure: {
    label: "Failing",
    dotClass: "bg-[var(--status-critical)]",
    bgClass: "bg-[var(--status-critical)]/10",
  },
  warning: {
    label: "Action required",
    dotClass: "bg-[var(--status-warning)]",
    bgClass: "bg-[var(--status-warning)]/10",
  },
  cancelled: {
    label: "Cancelled",
    dotClass: "bg-[var(--status-neutral)]",
    bgClass: "bg-[var(--status-neutral)]/10",
  },
  skipped: {
    label: "Skipped",
    dotClass: "bg-[var(--status-neutral)]",
    bgClass: "bg-[var(--status-neutral)]/10",
  },
  neutral: {
    label: "Neutral",
    dotClass: "bg-[var(--status-neutral)]",
    bgClass: "bg-[var(--status-neutral)]/10",
  },
  unknown: {
    label: "Unknown",
    dotClass: "bg-[var(--status-neutral)]",
    bgClass: "bg-[var(--status-neutral)]/10",
  },
};
