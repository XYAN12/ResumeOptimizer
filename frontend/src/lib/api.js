const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api";

async function parseJson(response) {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "Request failed");
  }
  return data;
}

export async function analyzeText(resumeText, jdText) {
  const response = await fetch(`${API_BASE}/resume/analyze-text`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ resume_text: resumeText, jd_text: jdText }),
  });
  return parseJson(response);
}

export async function analyzeFile(file, jdText) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("jd_text", jdText);

  const response = await fetch(`${API_BASE}/resume/analyze-file`, {
    method: "POST",
    body: formData,
  });
  return parseJson(response);
}

export async function generateRewrite(sessionId) {
  const response = await fetch(`${API_BASE}/resume/rewrite`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, confirmed: true }),
  });
  return parseJson(response);
}

export async function exportResume(sessionId, format) {
  const response = await fetch(`${API_BASE}/resume/export`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, format }),
  });
  return parseJson(response);
}
