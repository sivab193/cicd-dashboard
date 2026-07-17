export type RepoSummary = {
  owner: string;
  name: string;
  fullName: string;
  private: boolean;
  htmlUrl: string;
  updatedAt: string | null;
  latestRun: RunSummary | null;
};

export type RunSummary = {
  id: number;
  workflowName: string | null;
  status: string;
  conclusion: string | null;
  branch: string | null;
  event: string;
  actor: string | null;
  commitMessage: string | null;
  htmlUrl: string;
  createdAt: string;
  updatedAt: string;
  runStartedAt: string | null;
};

export type JobStep = {
  name: string;
  status: string;
  conclusion: string | null;
  number: number;
  startedAt: string | null;
  completedAt: string | null;
};

export type JobSummary = {
  id: number;
  name: string;
  status: string;
  conclusion: string | null;
  startedAt: string | null;
  completedAt: string | null;
  htmlUrl: string;
  steps: JobStep[];
};
