export type Analysis = {
  id: number;
  repo_url: string;
  pr_number: number | null;
  status: string;
  progress: number;
  summary: string | null;
  quality_score: number | null;
  extra_metadata?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
};

export type Issue = {
  id: number;
  file_path: string;
  line_start: number | null;
  line_end: number | null;
  severity: string;
  category: string;
  message: string;
  recommendation: string | null;
};

export type AnalysisDetail = Analysis & {
  issues: Issue[];
  extra_metadata?: Record<string, unknown> | null;
};

export type QueueItem = {
  id: string;
  threadName: string;
  repoUrl: string;
  prNumber: string;
  githubToken: string;
  allowGitClone: boolean;
};

export type ProgressMap = Record<number, { status: string; progress: number; message?: string }>;
