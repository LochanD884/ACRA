import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { AppHeader } from "../components/AppHeader";
import { NavTabs } from "../components/NavTabs";
import { AnalysesState } from "../hooks/useAnalysesState";

export function ReviewPage(props: AnalysesState) {
  const { analyses, queue, running, progressMap, error, setError, addToQueue, loadDetail, deleteAnalysis } = props;
  const [threadName, setThreadName] = useState("");
  const [repoUrl, setRepoUrl] = useState("");
  const [prNumber, setPrNumber] = useState("");
  const [githubToken, setGithubToken] = useState("");
  const [allowGitClone, setAllowGitClone] = useState(false);
  const navigate = useNavigate();

  const addItem = () => {
    setError(null);
    if (!repoUrl.trim()) {
      setError("Repo URL is required.");
      return;
    }
    addToQueue({
      id: crypto.randomUUID(),
      threadName: threadName.trim(),
      repoUrl: repoUrl.trim(),
      prNumber: prNumber.trim(),
      githubToken: githubToken.trim(),
      allowGitClone
    });
    setThreadName("");
    setRepoUrl("");
    setPrNumber("");
    setGithubToken("");
    setAllowGitClone(false);
  };

  const latestStatus = useMemo(() => {
    if (!running) return "Idle";
    const info = progressMap[running.analysisId];
    if (!info) return "Working...";
    return `${info.status} - ${info.progress}% ${info.message || ""}`.trim();
  }, [running, progressMap]);

  return (
    <div className="min-h-screen bg-midnight text-white bg-aurora">
      <div className="max-w-7xl mx-auto px-6 py-10">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <AppHeader />
          <div className="glass p-4 rounded-xl neon-border floaty w-full lg:w-auto">
            <p className="text-lg font-semibold">{latestStatus}</p>
          </div>
        </div>

        <NavTabs insightsHref="/insights" inInsights={false} />

        <section className="grid grid-cols-1 lg:grid-cols-[1.2fr_1.8fr] gap-6 mt-8">
          <div className="glass p-6 rounded-2xl space-y-6">
            <div className="glass p-5 rounded-xl border border-white/10">
              <h2 className="text-lg font-semibold text-neon">Review Input</h2>
              <div className="mt-4 space-y-3">
                <input
                  className="w-full bg-black/40 border border-cyan/30 rounded-md px-3 py-2"
                  placeholder="Thread name (optional)"
                  value={threadName}
                  onChange={(e) => setThreadName(e.target.value)}
                />
                <input
                  className="w-full bg-black/40 border border-cyan/30 rounded-md px-3 py-2"
                  placeholder="GitHub repo URL"
                  value={repoUrl}
                  onChange={(e) => setRepoUrl(e.target.value)}
                />
                <input
                  className="w-full bg-black/40 border border-cyan/30 rounded-md px-3 py-2"
                  placeholder="PR number (optional)"
                  value={prNumber}
                  onChange={(e) => setPrNumber(e.target.value)}
                />
                <input
                  className="w-full bg-black/40 border border-cyan/30 rounded-md px-3 py-2"
                  placeholder="GitHub token (optional)"
                  type="password"
                  value={githubToken}
                  onChange={(e) => setGithubToken(e.target.value)}
                />
                <label className="flex items-center gap-2 text-sm text-slate-300">
                  <input
                    type="checkbox"
                    checked={allowGitClone}
                    onChange={(e) => setAllowGitClone(e.target.checked)}
                  />
                  Allow git clone (faster, requires token if private)
                </label>
                <button
                  className="w-full bg-neon text-black font-semibold py-2 rounded-md hover:shadow-glow transition"
                  onClick={addItem}
                >
                  Add To Queue
                </button>
                {error && <p className="text-ember text-sm">{error}</p>}
              </div>
            </div>

            <div className="glass p-5 rounded-xl border border-white/10">
              <h3 className="text-lg font-semibold text-cyan">Dashboard</h3>
              <div className="mt-3 space-y-2">
                {analyses.map((item) => {
                  const threadLabel =
                    typeof item.extra_metadata?.thread_name === "string" && item.extra_metadata?.thread_name
                      ? item.extra_metadata.thread_name
                      : item.repo_url;
                  return (
                    <div
                      key={item.id}
                      className="w-full text-left bg-black/30 border border-white/10 rounded-md px-3 py-2 hover:border-cyan/50 transition cursor-pointer"
                      role="button"
                      tabIndex={0}
                      onClick={() => {
                        loadDetail(item.id);
                        navigate(`/insights/${item.id}`);
                      }}
                      onKeyDown={(event) => {
                        if (event.key === "Enter" || event.key === " ") {
                          event.preventDefault();
                          loadDetail(item.id);
                          navigate(`/insights/${item.id}`);
                        }
                      }}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-slate-200">{threadLabel}</span>
                        <span className="text-xs text-cyan">{item.status}</span>
                      </div>
                      <p className="text-xs text-slate-400 mt-1">{item.repo_url}</p>
                      <p className="text-xs text-slate-400">Score: {item.quality_score ?? "-"} - Progress: {item.progress}%</p>
                      <div className="flex items-center gap-2 mt-2">
                        <button
                          className="bg-black/40 border border-ember/50 text-ember text-xs font-semibold px-3 py-1 rounded-md"
                          onClick={(event) => {
                            event.stopPropagation();
                            deleteAnalysis(item.id);
                          }}
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  );
                })}
                {analyses.length === 0 && <p className="text-xs text-slate-400">No reviews yet.</p>}
              </div>
            </div>
          </div>

          <div className="glass p-6 rounded-2xl space-y-6">
            <div className="glass p-5 rounded-xl border border-white/10">
              <h3 className="text-lg font-semibold text-cyan">Queue</h3>
              <div className="mt-3 space-y-2">
                {queue.length === 0 && <p className="text-xs text-slate-400">No queued items.</p>}
                {queue.map((item) => (
                  <div key={item.id} className="w-full text-left bg-black/30 border border-white/10 rounded-md px-3 py-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-slate-200">{item.threadName || item.repoUrl}</span>
                      <span className="text-xs text-cyan">PR {item.prNumber || "N/A"}</span>
                    </div>
                    <p className="text-xs text-slate-400 mt-1">{item.repoUrl}</p>
                    <p className="text-xs text-slate-400 mt-1">{item.allowGitClone ? "Git clone enabled" : "API fetch"}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="glass p-5 rounded-xl border border-white/10">
              <h2 className="text-xl font-semibold text-neon">Dashboard</h2>
              <p className="text-slate-400 mt-4">
                Click any thread card in Dashboard to open Insights and Chat directly. Queue runs automatically in FIFO order once you add items.
              </p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
