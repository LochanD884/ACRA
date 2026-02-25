import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { jsPDF } from "jspdf";

import { apiBase, apiHeaders } from "../api/client";
import { AppHeader } from "../components/AppHeader";
import { NavTabs } from "../components/NavTabs";
import { AnalysesState } from "../hooks/useAnalysesState";
import { AnalysisDetail, Issue } from "../types";

export function InsightsPage(props: AnalysesState) {
  const { selected, loadDetail, deleteAnalysis } = props;
  const { id } = useParams();
  const [chatQuestion, setChatQuestion] = useState("");
  const [chatAnswer, setChatAnswer] = useState("");
  const selectedThreadName =
    typeof selected?.extra_metadata?.thread_name === "string" && selected?.extra_metadata?.thread_name
      ? selected.extra_metadata.thread_name
      : selected?.repo_url;

  const plainText = (input: string) =>
    input
      .replace(/```[\s\S]*?```/g, (block) => block.replace(/```/g, ""))
      .replace(/^#{1,6}\s*/gm, "")
      .replace(/\*\*(.*?)\*\*/g, "$1")
      .replace(/\*(.*?)\*/g, "$1")
      .replace(/`([^`]+)`/g, "$1");

  useEffect(() => {
    if (!id) return;
    const numeric = Number(id);
    if (Number.isFinite(numeric)) {
      loadDetail(numeric);
    }
  }, [id]);

  const groupedIssues = useMemo(() => {
    if (!selected) return [] as { file: string; issues: Issue[] }[];
    const map = new Map<string, Issue[]>();
    selected.issues.forEach((issue) => {
      if (!map.has(issue.file_path)) map.set(issue.file_path, []);
      map.get(issue.file_path)?.push(issue);
    });
    return Array.from(map.entries()).map(([file, issues]) => ({ file, issues }));
  }, [selected]);

  const sendChat = async () => {
    if (!chatQuestion.trim()) return;
    setChatAnswer("Thinking...");
    const res = await fetch(`${apiBase}/chat`, {
      method: "POST",
      headers: apiHeaders(),
      body: JSON.stringify({
        analysis_id: selected?.id || null,
        question: chatQuestion
      })
    });
    const data = await res.json();
    setChatAnswer(data.answer || "No answer");
  };

  const buildExportText = (analysis: AnalysisDetail | null) => {
    if (!analysis) return "";
    const lines: string[] = [];
    lines.push("# ACRA AI Review Summary");
    lines.push(`Thread: ${selectedThreadName ?? "N/A"}`);
    lines.push(`Repo: ${analysis.repo_url}`);
    lines.push(`PR: ${analysis.pr_number ?? "N/A"}`);
    lines.push(`Status: ${analysis.status}`);
    lines.push(`Score: ${analysis.quality_score ?? "N/A"}`);
    lines.push("");
    lines.push("SUMMARY");
    lines.push(plainText(analysis.summary || "No summary yet."));
    lines.push("");
    lines.push("ISSUES");
    if (!analysis.issues.length) {
      lines.push("No issues found.");
    } else {
      groupedIssues.forEach((group) => {
        lines.push(`- ${group.file}`);
        group.issues.forEach((issue) => {
          const loc =
            issue.line_start && issue.line_end
              ? ` (lines ${issue.line_start}-${issue.line_end})`
              : issue.line_start
                ? ` (line ${issue.line_start})`
                : "";
          lines.push(`  [${issue.severity}] ${issue.category}${loc}: ${plainText(issue.message)}`);
          if (issue.recommendation) {
            lines.push(`  Recommendation: ${plainText(issue.recommendation)}`);
          }
        });
      });
    }
    return lines.join("\n");
  };

  const downloadTxt = () => {
    if (!selected) return;
    const text = buildExportText(selected);
    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `acra-summary-${selected.id}.txt`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const downloadPdf = () => {
    if (!selected) return;
    const text = buildExportText(selected);
    const doc = new jsPDF({ unit: "pt", format: "a4" });
    const margin = 40;
    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
    const width = pageWidth - margin * 2;
    const lines = doc.splitTextToSize(text, width);
    doc.setFont("courier", "normal");
    doc.setFontSize(10);
    const lineHeight = 14;
    let y = margin;
    lines.forEach((line: string, index: number) => {
      if (index > 0 && y + lineHeight > pageHeight - margin) {
        doc.addPage();
        y = margin;
      }
      doc.text(line, margin, y);
      y += lineHeight;
    });
    doc.save(`acra-summary-${selected.id}.pdf`);
  };

  return (
    <div className="min-h-screen bg-midnight text-white bg-aurora">
      <div className="max-w-7xl mx-auto px-6 py-10">
        <AppHeader />
        <NavTabs insightsHref={selected ? `/insights/${selected.id}` : "/insights"} inInsights />

        {!selected && (
          <div className="glass p-6 rounded-2xl mt-8">
            <h2 className="text-xl font-semibold text-neon">Insights</h2>
            <p className="text-slate-400 mt-4">Select a review from the dashboard to view summary and chat.</p>
          </div>
        )}

        {selected && (
          <section className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
            <div className="glass p-6 rounded-2xl">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-300">{selectedThreadName}</p>
                  <p className="text-xs text-slate-400 mt-1">{selected.repo_url}</p>
                  <p className="text-xs text-cyan mt-1">{selected.status}</p>
                </div>
                <button
                  className="bg-black/40 border border-ember/50 text-ember text-xs font-semibold px-3 py-1 rounded-md"
                  onClick={() => deleteAnalysis(selected.id)}
                >
                  Delete Review
                </button>
              </div>
              <div className="flex flex-wrap items-center gap-2 mt-3">
                <button
                  className="bg-black/40 border border-cyan/40 text-cyan text-xs px-3 py-1 rounded-md hover:shadow-cyan transition"
                  onClick={downloadTxt}
                >
                  Download TXT
                </button>
                <button
                  className="bg-black/40 border border-cyan/40 text-cyan text-xs px-3 py-1 rounded-md hover:shadow-cyan transition"
                  onClick={downloadPdf}
                >
                  Download PDF
                </button>
              </div>
              <div className="text-slate-300 text-sm mt-4 prose prose-invert max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{selected.summary || "No summary yet."}</ReactMarkdown>
              </div>

              <div className="mt-6 space-y-4">
                {groupedIssues.map((group) => (
                  <div key={group.file} className="bg-black/40 border border-white/10 rounded-md p-3">
                    <p className="text-cyan text-sm">{group.file}</p>
                    <ul className="mt-2 space-y-2">
                      {group.issues.map((issue) => (
                        <li key={issue.id} className="text-sm text-slate-200">
                          <span className="text-neon">[{issue.severity}]</span> {issue.message}
                          {issue.recommendation && (
                            <div className="text-xs text-slate-400 mt-1">
                              <ReactMarkdown remarkPlugins={[remarkGfm]}>{issue.recommendation}</ReactMarkdown>
                            </div>
                          )}
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </div>

            <div className="glass p-6 rounded-2xl border border-white/10">
              <h2 className="text-xl font-semibold text-neon">Talk To Codebase</h2>
              <p className="text-slate-400 text-sm mt-2">Ask about risks, hotspots, or refactor ideas.</p>
              <textarea
                className="w-full mt-4 bg-black/40 border border-cyan/30 rounded-md px-3 py-2 h-28"
                placeholder="What is the most critical security risk?"
                value={chatQuestion}
                onChange={(e) => setChatQuestion(e.target.value)}
              />
              <button
                className="w-full bg-cyan text-black font-semibold py-2 rounded-md mt-3 hover:shadow-cyan transition"
                onClick={sendChat}
              >
                Ask ACRA
              </button>
              {chatAnswer && (
                <div className="mt-4 bg-black/40 border border-white/10 rounded-md p-3 text-sm text-slate-200 prose prose-invert max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{chatAnswer}</ReactMarkdown>
                </div>
              )}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
