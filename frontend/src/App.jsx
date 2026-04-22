import { useEffect, useState } from "react";
import SectionCard from "./components/SectionCard";
import { analyzeFile, analyzeText, exportResume, generateRewrite } from "./lib/api";

function FactList({ title, items }) {
  return (
    <div className="list-block">
      <h3>{title}</h3>
      {items.length ? (
        <ul>
          {items.map((item, index) => (
            <li key={`${title}-${index}`}>
              <strong>{item.title}</strong>
              <span>{item.detail}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="muted">暂无内容</p>
      )}
    </div>
  );
}

function ResumePreview({ rewrite }) {
  const normalizeItems = (items = []) =>
    items
      .map((item) => (typeof item === "string" ? item.trim() : ""))
      .filter(Boolean);

  return (
    <article className="resume-preview">
      {rewrite.sections.map((section, index) =>
        section.title.toLowerCase() === "header" ? (
          <header className="resume-preview-header" key={`section-${index}`}>
            {normalizeItems(section.items).map((item, itemIndex) => (
              <p key={`header-item-${itemIndex}`}>{item}</p>
            ))}
          </header>
        ) : (
          <section className="resume-preview-section" key={`section-${index}`}>
            <h3>{section.title}</h3>
            {normalizeItems(section.items).length ? (
              <ul>
                {normalizeItems(section.items).map((item, itemIndex) => (
                  <li key={`section-item-${itemIndex}`}>{item}</li>
                ))}
              </ul>
            ) : (
              <p className="muted">该 section 暂无可展示内容</p>
            )}
          </section>
        ),
      )}
    </article>
  );
}

export default function App() {
  const [resumeText, setResumeText] = useState("");
  const [jdText, setJdText] = useState("");
  const [file, setFile] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [rewriteResult, setRewriteResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingStage, setLoadingStage] = useState("");
  const [loadingScope, setLoadingScope] = useState("");
  const [loadingSeconds, setLoadingSeconds] = useState(0);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!loading) {
      setLoadingSeconds(0);
      return undefined;
    }
    const timerId = window.setInterval(() => {
      setLoadingSeconds((value) => value + 1);
    }, 1000);
    return () => window.clearInterval(timerId);
  }, [loading]);

  const handleAnalyze = async () => {
    if (!jdText.trim()) {
      setError("请输入目标岗位 JD。");
      return;
    }
    if (!file && !resumeText.trim()) {
      setError("请上传简历文件或粘贴简历文本。");
      return;
    }

    try {
      setLoading(true);
      setLoadingScope("analyze");
      setLoadingStage("正在分析简历与 JD（调用 DeepSeek，可能需要 30-90 秒）...");
      setError("");
      setRewriteResult(null);
      const result = file
        ? await analyzeFile(file, jdText)
        : await analyzeText(resumeText, jdText);
      setAnalysisResult(result);
    } catch (requestError) {
      setError(`分析失败：${requestError.message}。请重试，系统不会使用 rule-based 分析。`);
    } finally {
      setLoading(false);
      setLoadingStage("");
      setLoadingScope("");
    }
  };

  const handleGenerateRewrite = async () => {
    if (!analysisResult?.session_id) {
      return;
    }
    try {
      setLoading(true);
      setLoadingScope("rewrite");
      setLoadingStage("正在生成优化版简历（调用 DeepSeek，可能需要较长时间）...");
      setError("");
      const result = await generateRewrite(analysisResult.session_id);
      setRewriteResult(result);
    } catch (requestError) {
      setError(`生成失败：${requestError.message}。请重试，系统不会使用 rule-based 改写。`);
    } finally {
      setLoading(false);
      setLoadingStage("");
      setLoadingScope("");
    }
  };

  const handleExport = async (format) => {
    if (!analysisResult?.session_id) {
      return;
    }
    try {
      setLoading(true);
      setLoadingScope("export");
      setLoadingStage("正在导出文件，请稍候...");
      setError("");
      const result = await exportResume(analysisResult.session_id, format);
      const link = document.createElement("a");
      link.href = `data:application/octet-stream;base64,${result.content_base64}`;
      link.download = result.filename;
      link.click();
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
      setLoadingStage("");
      setLoadingScope("");
    }
  };

  return (
    <div className="app-shell">
      <header className="hero">
        <div className="hero-copy">
          <p className="eyebrow">Fact-Constrained Resume Agent</p>
          <h1>简历优化 Agent</h1>
          <p className="hero-text">
            上传或粘贴原始简历，输入目标岗位 JD，先看匹配分析，再由你确认生成忠于事实的优化版简历。
          </p>
        </div>
      </header>

      <main className="content-grid">
        <SectionCard title="输入区" accent="clay">
          <label className="field">
            <span>上传简历文件（pdf / docx / md / txt）</span>
            <input
              type="file"
              accept=".pdf,.docx,.md,.txt"
              onChange={(event) => setFile(event.target.files?.[0] || null)}
            />
          </label>
          <label className="field">
            <span>或直接粘贴简历文本</span>
            <textarea
              rows="12"
              placeholder="在这里粘贴原始简历内容"
              value={resumeText}
              onChange={(event) => setResumeText(event.target.value)}
            />
          </label>
          <label className="field">
            <span>目标岗位 JD</span>
            <textarea
              rows="12"
              placeholder="在这里粘贴目标岗位描述"
              value={jdText}
              onChange={(event) => setJdText(event.target.value)}
            />
          </label>
          <div className="button-row">
            <button onClick={handleAnalyze} disabled={loading}>
              {loading ? "处理中..." : "开始分析"}
            </button>
          </div>
          {loading && loadingScope === "analyze" ? <p className="loading-text">{loadingStage}</p> : null}
          {loading && loadingScope === "analyze" ? (
            <p className="loading-text">已等待：{loadingSeconds} 秒</p>
          ) : null}
          {error ? <p className="error-text">{error}</p> : null}
        </SectionCard>

        <SectionCard title="流程约束" accent="sage">
          <ul className="constraint-list">
            <li>原始简历事实优先级最高，Agent 会先抽取结构化 facts。</li>
            <li>JD 作为目标上下文，只能影响分析和重排，不可覆盖原始事实。</li>
            <li>你确认前只输出分析，不生成最终优化版简历。</li>
            <li>改写阶段必须引用结构化 facts，不允许自由发挥。</li>
          </ul>
        </SectionCard>

        {analysisResult ? (
          <SectionCard title="匹配分析" accent="sand">
            <div className="analysis-grid">
              <FactList title="匹配亮点" items={analysisResult.analysis.highlights} />
              <FactList title="主要缺口" items={analysisResult.analysis.gaps} />
              <FactList title="优化建议" items={analysisResult.analysis.suggestions} />
            </div>
            <div className="fact-box">
              <h3>事实约束</h3>
              <ul>
                {analysisResult.analysis.fact_constraints.map((item, index) => (
                  <li key={`constraint-${index}`}>{item}</li>
                ))}
              </ul>
            </div>
            <div className="result-note">
              {analysisResult.analysis?.trace?.llm_used
                ? "本次匹配分析由 DeepSeek 生成。"
                : "本次匹配分析未完成（DeepSeek 调用失败）。请重试。"}
            </div>
            <div className="button-row">
              <button onClick={handleGenerateRewrite} disabled={loading}>
                用户确认后生成优化版简历
              </button>
            </div>
            {loading && loadingScope === "rewrite" ? <p className="loading-text">{loadingStage}</p> : null}
            {loading && loadingScope === "rewrite" ? (
              <p className="loading-text">已等待：{loadingSeconds} 秒</p>
            ) : null}
          </SectionCard>
        ) : null}

        {rewriteResult ? (
          <SectionCard title="优化结果" accent="ink">
            <div className="result-note">
              已按原始简历的 section 结构展示优化结果，未改变原有结构顺序。
            </div>
            <div className="result-note">
              {rewriteResult.rewrite?.trace?.llm_used
                ? "本次改写由 DeepSeek 生成。"
                : "本次改写未完成（DeepSeek 调用失败）。请重试。"}
            </div>
            <ResumePreview rewrite={rewriteResult.rewrite} />
            <div className="button-row">
              <button onClick={() => handleExport("md")} disabled={loading}>
                导出 Markdown
              </button>
              <button onClick={() => handleExport("docx")} disabled={loading}>
                导出 DOCX
              </button>
              <button onClick={() => handleExport("pdf")} disabled={loading}>
                导出 PDF
              </button>
            </div>
            {loading && loadingScope === "export" ? <p className="loading-text">{loadingStage}</p> : null}
            {loading && loadingScope === "export" ? (
              <p className="loading-text">已等待：{loadingSeconds} 秒</p>
            ) : null}
          </SectionCard>
        ) : null}
      </main>
    </div>
  );
}
