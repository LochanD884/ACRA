import { useEffect, useState } from "react";

import { apiBase, apiHeaders, getApiKey } from "../api/client";
import { Analysis, AnalysisDetail, ProgressMap, QueueItem } from "../types";

export function useAnalysesState() {
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [selected, setSelected] = useState<AnalysisDetail | null>(null);
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [running, setRunning] = useState<{ queueId: string; analysisId: number } | null>(null);
  const [progressMap, setProgressMap] = useState<ProgressMap>({});
  const [error, setError] = useState<string | null>(null);

  const loadAnalyses = async () => {
    const res = await fetch(`${apiBase}/analyses`, { headers: apiHeaders() });
    const data = await res.json();
    setAnalyses(data.items || []);
  };

  const loadDetail = async (id: number) => {
    const res = await fetch(`${apiBase}/analyses/${id}`, { headers: apiHeaders() });
    if (!res.ok) return;
    const data = await res.json();
    setSelected(data);
  };

  const deleteAnalysis = async (id: number) => {
    const ok = window.confirm("Delete this review?");
    if (!ok) return;
    const res = await fetch(`${apiBase}/analyses/${id}`, { method: "DELETE", headers: apiHeaders() });
    if (!res.ok) return;
    if (selected?.id === id) setSelected(null);
    await loadAnalyses();
  };

  const startProgressStream = (analysisId: number) => {
    const apiKey = getApiKey();
    const url = apiKey
      ? `${apiBase}/analyses/${analysisId}/events?api_key=${encodeURIComponent(apiKey)}`
      : `${apiBase}/analyses/${analysisId}/events`;
    const es = new EventSource(url);
    es.onmessage = () => {
      // no-op
    };
    es.addEventListener("progress", (event) => {
      const data = JSON.parse((event as MessageEvent).data);
      setProgressMap((prev) => ({
        ...prev,
        [analysisId]: { status: data.status, progress: data.progress, message: data.message }
      }));
      if (data.status === "completed" || data.status === "failed") {
        es.close();
        setRunning((curr) => (curr?.analysisId === analysisId ? null : curr));
        loadAnalyses();
        loadDetail(analysisId);
      }
    });
    es.onerror = () => {
      es.close();
    };
  };

  const submitReview = async (payload: {
    thread_name: string | null;
    repo_url: string;
    pr_number: number | null;
    github_token: string | null;
    allow_git_clone: boolean;
    queueId?: string;
  }) => {
    setError(null);
    const res = await fetch(`${apiBase}/analyze`, {
      method: "POST",
      headers: apiHeaders(),
      body: JSON.stringify({
        thread_name: payload.thread_name,
        repo_url: payload.repo_url,
        pr_number: payload.pr_number,
        github_token: payload.github_token,
        allow_git_clone: payload.allow_git_clone
      })
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      setError(data.detail || "Failed to start analysis");
      setRunning(null);
      return;
    }
    const analysis = await res.json();
    await loadAnalyses();
    startProgressStream(analysis.id);
    if (payload.queueId) {
      setRunning({ queueId: payload.queueId, analysisId: analysis.id });
    }
  };

  const addToQueue = (item: QueueItem) => {
    setQueue((prev) => [...prev, item]);
  };

  useEffect(() => {
    loadAnalyses();
    const interval = setInterval(loadAnalyses, 10000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (running || queue.length === 0) return;
    const next = queue[0];
    submitReview({
      thread_name: next.threadName || null,
      repo_url: next.repoUrl,
      pr_number: next.prNumber ? Number(next.prNumber) : null,
      github_token: next.githubToken || null,
      allow_git_clone: next.allowGitClone,
      queueId: next.id
    });
    setQueue((prev) => prev.filter((q) => q.id !== next.id));
  }, [queue, running]);

  return {
    analyses,
    selected,
    queue,
    running,
    progressMap,
    error,
    setError,
    loadDetail,
    addToQueue,
    deleteAnalysis
  };
}

export type AnalysesState = ReturnType<typeof useAnalysesState>;
