import { useState, useRef, useEffect } from "react";

const COMMANDS = [
  { cmd: "/engineer analyze", icon: "🔍", desc: "Анализ структуры проекта" },
  { cmd: "/engineer fix", icon: "🔧", desc: "Исправить ошибки" },
  { cmd: "/engineer generate", icon: "⚡", desc: "Генерация кода" },
  { cmd: "/engineer deps", icon: "📦", desc: "Проверка зависимостей" },
  { cmd: "/engineer security", icon: "🛡️", desc: "Скан безопасности" },
  { cmd: "/engineer readme", icon: "📄", desc: "Создать README" },
];

const MODELS = [
  { id: "claude", label: "Claude", color: "#e8773a", active: true },
  { id: "codex", label: "Codex", color: "#10a37f", active: false },
  { id: "grok", label: "Grok", color: "#1d9bf0", active: false },
  { id: "deepseek", label: "DeepSeek", color: "#6366f1", active: false },
  { id: "qwen", label: "Qwen", color: "#f59e0b", active: false },
  { id: "perplexity", label: "Perplexity", color: "#20b2aa", active: false },
];

const SYSTEM_PROMPT = `You are WKAgent — an elite AI software engineer for the WebKurier ecosystem.
You assist a developer (beginner-friendly) with:
- Analyzing project structure and architecture
- Writing, reviewing, and fixing code
- Generating bash scripts, Python, JS/TS modules
- Identifying dependency issues and security leaks
- Creating documentation

Project context: WebKurierX — multi-layer platform (web, AI routing, communications, transport/drone, blockchain, security) running on Ubuntu 22.04. Tools: wk, wkagent, wkdoc, wksetup, wkapply. Secrets stored only in /opt/wktools/conf/secrets.env.

Rules:
- NEVER include API keys or secrets in output
- Keep code minimal and safe
- Explain every step in simple Russian
- For shell scripts: always add set -euo pipefail
- Format code with proper markdown blocks

Respond in Russian unless code.`;

function Spinner() {
  const [frame, setFrame] = useState(0);
  const frames = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"];
  useEffect(() => {
    const t = setInterval(() => setFrame(f => (f + 1) % frames.length), 80);
    return () => clearInterval(t);
  }, []);
  return (
    <span style={{ color: "#e8773a", fontFamily: "monospace" }}>
      {frames[frame]}
    </span>
  );
}

export default function WKAgentDashboard() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([
    { role: "system_ui", content: "=== WKAgent v2.0 — WebKurier AI Engineer ===" },
    { role: "system_ui", content: "✅ Claude подключён | Repo: WebKurierX" },
    { role: "system_ui", content: "Используй кнопки команд или введи задачу свободно:" },
    { role: "system_ui", content: "" },
  ]);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]);
  const [activeModel, setActiveModel] = useState("claude");
  const [repoContext, setRepoContext] = useState("WebKurierX");
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const addLines = (lines) => {
    setMessages(prev => [
      ...prev,
      ...lines.map(l => ({ role: "system_ui", content: l }))
    ]);
  };

  const sendToAI = async (userMsg) => {
    if (!userMsg.trim() || loading) return;

    setMessages(prev => [
      ...prev,
      { role: "user", content: `$ wkagent> ${userMsg}` }
    ]);

    const newHistory = [...history, { role: "user", content: userMsg }];
    setHistory(newHistory);
    setLoading(true);

    try {
      const response = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: "claude-sonnet-4-20250514",
          max_tokens: 1000,
          system: SYSTEM_PROMPT + `\n\nТекущий репозиторий: ${repoContext}`,
          messages: newHistory,
        }),
      });

      const data = await response.json();
      const text = data.content?.find(b => b.type === "text")?.text || "Нет ответа";

      const assistantHistory = [...newHistory, { role: "assistant", content: text }];
      setHistory(assistantHistory);

      setMessages(prev => [
        ...prev,
        { role: "assistant_header", content: `\n[WKAgent → ${repoContext}]` },
        ...text.split("\n").map(l => ({ role: "assistant", content: l })),
        { role: "system_ui", content: "" },
      ]);

    } catch (err) {
      addLines([`❌ Ошибка API: ${err.message}`, ""]);
    } finally {
      setLoading(false);
    }
  };

  const handleCommand = (cmd) => {
    sendToAI(cmd);
    setInput("");
  };

  const handleSubmit = () => {
    if (!input.trim()) return;
    sendToAI(input);
    setInput("");
  };

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const clearTerminal = () => {
    setMessages([{ role: "system_ui", content: "=== Terminal cleared ===" }]);
    setHistory([]);
  };

  return (
    <div style={{
      minHeight: "100vh",
      background: "#0a0e1a",
      display: "flex",
      flexDirection: "column",
      fontFamily: "'JetBrains Mono', monospace",
      color: "#e2e8f0",
    }}>

      {/* Header */}
      <div style={{
        background: "linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%)",
        borderBottom: "1px solid #1e293b",
        padding: "12px 16px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        position: "sticky",
        top: 0,
        zIndex: 10,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <div style={{
            width: 36, height: 36, borderRadius: "8px",
            background: "linear-gradient(135deg, #e8773a, #f59e0b)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: "18px", fontWeight: "bold",
          }}>⚡</div>
          <div>
            <div style={{ fontSize: "14px", fontWeight: "700", color: "#f1f5f9", letterSpacing: "0.05em" }}>
              WKAGENT
            </div>
            <div style={{ fontSize: "10px", color: "#64748b" }}>WebKurier AI Engineer</div>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <div style={{ fontSize: "10px", color: "#64748b" }}>REPO:</div>
          <select
            value={repoContext}
            onChange={e => setRepoContext(e.target.value)}
            style={{
              background: "#1e293b", border: "1px solid #334155",
              color: "#94a3b8", fontSize: "11px", borderRadius: "4px",
              padding: "3px 6px", cursor: "pointer",
            }}
          >
            <option>WebKurierX</option>
            <option>WebKurierCore</option>
            <option>WebKurierSite</option>
            <option>wktools</option>
          </select>
        </div>
      </div>

      {/* Model selector */}
      <div style={{
        padding: "8px 16px",
        background: "#0d1117",
        borderBottom: "1px solid #161b22",
        display: "flex", gap: "6px", alignItems: "center", flexWrap: "wrap",
      }}>
        <span style={{ fontSize: "10px", color: "#475569" }}>ENGINE:</span>
        {MODELS.map(m => (
          <button
            key={m.id}
            onClick={() => setActiveModel(m.id)}
            style={{
              padding: "3px 10px", borderRadius: "20px",
              border: `1px solid ${activeModel === m.id ? m.color : "#1e293b"}`,
              background: activeModel === m.id ? `${m.color}22` : "transparent",
              color: activeModel === m.id ? m.color : "#475569",
              fontSize: "11px", cursor: "pointer", transition: "all 0.2s",
            }}
          >
            {m.label}
          </button>
        ))}
        <div style={{ marginLeft: "auto", fontSize: "10px", color: "#22c55e" }}>
          ● ONLINE
        </div>
      </div>

      {/* Quick commands */}
      <div style={{
        padding: "10px 16px", background: "#0d1117",
        borderBottom: "1px solid #161b22",
        display: "flex", gap: "6px", flexWrap: "wrap",
      }}>
        {COMMANDS.map(c => (
          <button
            key={c.cmd}
            onClick={() => handleCommand(c.cmd)}
            disabled={loading}
            title={c.desc}
            style={{
              padding: "5px 10px", borderRadius: "6px",
              border: "1px solid #1e293b", background: "#0f172a",
              color: "#94a3b8", fontSize: "11px",
              cursor: loading ? "not-allowed" : "pointer",
              display: "flex", alignItems: "center", gap: "4px",
              opacity: loading ? 0.5 : 1, transition: "all 0.15s",
            }}
          >
            {c.icon} {c.cmd.replace("/engineer ", "")}
          </button>
        ))}
      </div>

      {/* Terminal output */}
      <div style={{
        flex: 1, padding: "16px", overflowY: "auto",
        background: "#0a0e1a", minHeight: "300px", maxHeight: "50vh",
      }}>
        {messages.map((m, i) => (
          <div key={i} style={{
            color: m.role === "assistant_header" ? "#e8773a"
                 : m.role === "user"            ? "#7dd3fc"
                 : m.role === "assistant"        ? "#e2e8f0"
                 :                                "#64748b",
            fontFamily: "'JetBrains Mono', 'Courier New', monospace",
            fontSize: "12px", lineHeight: "1.8",
            whiteSpace: "pre-wrap", wordBreak: "break-word",
          }}>
            {m.content}
          </div>
        ))}
        {loading && (
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginTop: "4px" }}>
            <Spinner />
            <span style={{ fontSize: "12px", color: "#e8773a", fontFamily: "monospace" }}>
              WKAgent думает...
            </span>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div style={{ padding: "12px 16px", background: "#0d1117", borderTop: "1px solid #1e293b" }}>
        <div style={{
          display: "flex", alignItems: "center", gap: "8px",
          background: "#0f172a", border: "1px solid #334155",
          borderRadius: "8px", padding: "8px 12px",
        }}>
          <span style={{ color: "#e8773a", fontSize: "13px", fontFamily: "monospace", flexShrink: 0 }}>
            $ wkagent&gt;
          </span>
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Опиши задачу или используй /engineer команду..."
            disabled={loading}
            rows={1}
            style={{
              flex: 1, background: "transparent", border: "none", outline: "none",
              color: "#f1f5f9", fontSize: "13px",
              fontFamily: "'JetBrains Mono', monospace",
              resize: "none", lineHeight: "1.5",
            }}
          />
          <button
            onClick={handleSubmit}
            disabled={loading || !input.trim()}
            style={{
              padding: "6px 14px", borderRadius: "6px", border: "none",
              background: loading ? "#1e293b" : "linear-gradient(135deg, #e8773a, #f59e0b)",
              color: loading ? "#475569" : "#0a0e1a",
              fontSize: "12px", fontWeight: "700",
              cursor: loading ? "not-allowed" : "pointer",
              flexShrink: 0, transition: "all 0.2s",
            }}
          >
            RUN
          </button>
        </div>
        <div style={{
          display: "flex", justifyContent: "space-between",
          marginTop: "8px", padding: "0 2px",
        }}>
          <span style={{ fontSize: "10px", color: "#334155" }}>
            Enter = отправить • Shift+Enter = новая строка
          </span>
          <button
            onClick={clearTerminal}
            style={{
              background: "none", border: "none",
              color: "#475569", fontSize: "10px",
              cursor: "pointer", textDecoration: "underline",
            }}
          >
            clear
          </button>
        </div>
      </div>

      {/* Status bar */}
      <div style={{
        padding: "4px 16px", background: "#020617",
        borderTop: "1px solid #0f172a",
        display: "flex", gap: "16px", alignItems: "center",
      }}>
        <span style={{ fontSize: "10px", color: "#1d4ed8" }}>Ubuntu 22.04</span>
        <span style={{ fontSize: "10px", color: "#475569" }}>/opt/wktools</span>
        <span style={{ fontSize: "10px", color: "#475569", marginLeft: "auto" }}>
          WebKurier Ecosystem
        </span>
      </div>

    </div>
  );
}
