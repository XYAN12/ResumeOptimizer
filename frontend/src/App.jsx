import { useState } from "react";
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

export default function App() {
  const [resumeText, setResumeText] = useState("");
  const [jdText, setJdText] = useState("");
  const [file, setFile] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [rewriteResult, setRewriteResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

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
      setError("");
      setRewriteResult(null);
      const result = file
        ? await analyzeFile(file, jdText)
        : await analyzeText(resumeText, jdText);
      setAnalysisResult(result);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateRewrite = async () => {
    if (!analysisResult?.session_id) {
      return;
    }
    try {
      setLoading(true);
      setError("");
      const result = await generateRewrite(analysisResult.session_id);
      setRewriteResult(result);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format) => {
    if (!analysisResult?.session_id) {
      return;
    }
    try {
      setLoading(true);
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
            <div className="button-row">
              <button onClick={handleGenerateRewrite} disabled={loading}>
                用户确认后生成优化版简历
              </button>
            </div>
          </SectionCard>
        ) : null}

        {rewriteResult ? (
          <SectionCard title="优化结果" accent="ink">
            <pre className="markdown-preview">{rewriteResult.rewrite.markdown}</pre>
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
          </SectionCard>
        ) : null}
      </main>
    </div>
  );
}
