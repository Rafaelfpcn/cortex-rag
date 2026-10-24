"use client";

import React, { useState, useEffect } from "react";
import { useCortexChat } from "@/hooks/useCortexChat";
import { CitationBadge } from "@/components/CitationBadge";
import { DocumentItem, SystemMetrics } from "@/types";

export default function DashboardPage() {
  const [token, setToken] = useState<string | null>(null);
  const [tenantName, setTenantName] = useState<string>("Enterprise");
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [metrics, setMetrics] = useState<SystemMetrics>({
    total_queries: 0,
    cache_hits: 0,
    cache_hit_rate_pct: 0,
    avg_latency_ms: 0,
    total_documents: 0,
    total_chunks: 0,
  });
  const [inputQuery, setInputQuery] = useState("");
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);

  const { messages, isStreaming, sendMessage } = useCortexChat(token);

  useEffect(() => {
    const savedToken = localStorage.getItem("cortex_token");
    const savedTenant = localStorage.getItem("cortex_tenant_name");
    if (savedToken) {
      setToken(savedToken);
      if (savedTenant) setTenantName(savedTenant);
    }
  }, []);

  const refreshDocuments = async () => {
    if (!token) return;
    try {
      const res = await fetch("/api/v1/documents/list", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setDocuments(data.documents);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const refreshMetrics = async () => {
    if (!token) return;
    try {
      const res = await fetch("/api/v1/chat/metrics", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setMetrics(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    if (token) {
      refreshDocuments();
      refreshMetrics();
    }
  }, [token]);

  const handleDemoLogin = async () => {
    try {
      const res = await fetch("/api/v1/auth/demo-login", { method: "POST" });
      const data = await res.json();
      setToken(data.access_token);
      setTenantName(data.tenant_name);
      localStorage.setItem("cortex_token", data.access_token);
      localStorage.setItem("cortex_tenant_name", data.tenant_name);
    } catch (err) {
      alert("Erro ao realizar login de demonstração: " + err);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !token) return;

    setUploadStatus("Processando e gerando embeddings...");
    const formData = new FormData();
    formData.append("file", file);
    formData.append("title", file.name);

    try {
      const res = await fetch("/api/v1/documents/upload", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      const data = await res.json();
      setUploadStatus(data.message);
      setTimeout(() => setUploadStatus(null), 3000);
      refreshDocuments();
      refreshMetrics();
    } catch (err: any) {
      setUploadStatus("Falha no upload: " + err.message);
    }
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputQuery.trim()) return;
    if (!token) {
      await handleDemoLogin();
    }
    const q = inputQuery;
    setInputQuery("");
    await sendMessage(q);
    refreshMetrics();
  };

  return (
    <div className="flex flex-col h-screen overflow-hidden font-sans bg-slate-950 text-slate-100">
      {/* Top Navbar */}
      <header className="bg-slate-900/80 border-b border-slate-800 backdrop-blur px-6 py-3 flex items-center justify-between z-10">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/20">
            🧠
          </div>
          <div>
            <h1 className="font-bold text-lg leading-tight flex items-center gap-2">
              CortexRAG{" "}
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                Next.js 15
              </span>
            </h1>
            <p className="text-xs text-slate-400">Enterprise Auditable RAG Platform</p>
          </div>
        </div>

        {/* Real-time Telemetry Metrics */}
        <div className="hidden md:flex items-center space-x-6 text-xs bg-slate-800/60 border border-slate-700/60 px-4 py-1.5 rounded-full">
          <div>
            Consultas:{" "}
            <span className="font-mono font-bold text-indigo-400">
              {metrics.total_queries}
            </span>
          </div>
          <div className="w-px h-3 bg-slate-700" />
          <div>
            Cache Hit Rate:{" "}
            <span className="font-mono font-bold text-emerald-400">
              {metrics.cache_hit_rate_pct}%
            </span>
          </div>
          <div className="w-px h-3 bg-slate-700" />
          <div>
            Latência Média:{" "}
            <span className="font-mono font-bold text-amber-400">
              {metrics.avg_latency_ms}ms
            </span>
          </div>
        </div>

        {/* Auth / Demo Button */}
        <div>
          {!token ? (
            <button
              onClick={handleDemoLogin}
              className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium px-4 py-2 rounded-lg transition-all shadow-md shadow-indigo-600/30 flex items-center gap-1.5"
            >
              <span>⚡</span> Acessar Demo (1-Clique)
            </button>
          ) : (
            <div className="flex items-center space-x-3 text-xs">
              <span className="text-slate-400">
                Tenant: <strong className="text-white">{tenantName}</strong>
              </span>
              <button
                onClick={() => {
                  localStorage.removeItem("cortex_token");
                  setToken(null);
                }}
                className="text-slate-400 hover:text-white px-2.5 py-1 border border-slate-700 rounded"
              >
                Sair
              </button>
            </div>
          )}
        </div>
      </header>

      {/* Main Layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className="w-80 bg-slate-900 border-r border-slate-800 flex flex-col">
          <div className="p-4 border-b border-slate-800 flex items-center justify-between">
            <h2 className="font-semibold text-sm text-slate-200">
              📄 Base Indexada
            </h2>
            <span className="text-xs bg-slate-800 px-2 py-0.5 rounded text-slate-400">
              {documents.length} docs
            </span>
          </div>

          <div className="p-4 border-b border-slate-800">
            <label className="border-2 border-dashed border-slate-700 hover:border-indigo-500 rounded-lg p-3 flex flex-col items-center justify-center cursor-pointer transition-colors bg-slate-950/40">
              <span className="text-xs text-slate-300 font-medium">
                Upload de Documento
              </span>
              <span className="text-[10px] text-slate-500">
                PDF, Markdown ou TXT
              </span>
              <input
                type="file"
                className="hidden"
                onChange={handleFileUpload}
                accept=".pdf,.md,.txt"
              />
            </label>
            {uploadStatus && (
              <div className="text-xs mt-2 text-indigo-400 font-mono">
                {uploadStatus}
              </div>
            )}
          </div>

          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            {documents.length === 0 ? (
              <div className="text-xs text-slate-500 text-center py-8">
                Nenhum documento indexado. Clique em &ldquo;Acessar Demo&rdquo;
                para provisionar a base padrão.
              </div>
            ) : (
              documents.map((d) => (
                <div
                  key={d.id}
                  className="bg-slate-800/60 border border-slate-700/60 rounded-lg p-3"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span
                      className="font-medium text-xs text-slate-200 truncate"
                      title={d.title}
                    >
                      {d.title}
                    </span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      {d.status}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-[10px] text-slate-400">
                    <span>{d.chunk_count} chunks</span>
                    <span>SHA: {d.file_hash.substring(0, 6)}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </aside>

        {/* Chat Feed */}
        <main className="flex-1 flex flex-col bg-slate-950">
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {messages.length === 0 && (
              <div className="max-w-2xl mx-auto text-center py-16">
                <div className="w-14 h-14 bg-indigo-600/10 border border-indigo-500/20 text-indigo-400 rounded-2xl flex items-center justify-center mx-auto mb-4 text-2xl">
                  ⚡
                </div>
                <h2 className="text-xl font-bold text-white mb-2">
                  Motor de Busca Híbrida & RAG Auditável
                </h2>
                <p className="text-sm text-slate-400 max-w-lg mx-auto mb-6">
                  Faça perguntas aos documentos indexados com rastreabilidade
                  matemática de fontes e cache semântico de baixa latência.
                </p>
                <div className="flex flex-wrap gap-2 justify-center">
                  <button
                    onClick={() => {
                      setInputQuery("Qual o RTO e política de MFA exigidos na nuvem?");
                    }}
                    className="text-xs bg-slate-900 hover:bg-slate-800 border border-slate-800 px-3 py-1.5 rounded-full text-slate-300"
                  >
                    🔒 RTO e MFA na Nuvem
                  </button>
                  <button
                    onClick={() => {
                      setInputQuery("Como funciona o Exponential Backoff e a DLQ no PulseQueue?");
                    }}
                    className="text-xs bg-slate-900 hover:bg-slate-800 border border-slate-800 px-3 py-1.5 rounded-full text-slate-300"
                  >
                    ⏱️ Exponential Backoff e DLQ
                  </button>
                </div>
              </div>
            )}

            {messages.map((m) => (
              <div
                key={m.id}
                className={`flex ${
                  m.sender === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`text-sm rounded-2xl p-4 shadow-md max-w-2xl ${
                    m.sender === "user"
                      ? "bg-indigo-600 text-white rounded-tr-sm"
                      : "bg-slate-900 border border-slate-800 text-slate-200 rounded-tl-sm w-full"
                  }`}
                >
                  {m.sender === "assistant" && (
                    <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-3 text-xs">
                      <span className="font-semibold text-indigo-400 flex items-center gap-1.5">
                        <span>🧠</span> CortexRAG
                      </span>
                      {m.cacheHit ? (
                        <span className="text-emerald-400 font-mono text-[11px] font-semibold">
                          ⚡ Semantic Cache Hit ({m.latencyMs}ms)
                        </span>
                      ) : (
                        <span className="text-slate-500 font-mono text-[11px]">
                          {m.latencyMs ? `RAG Híbrido (${m.latencyMs}ms)` : "Buscando..."}
                        </span>
                      )}
                    </div>
                  )}

                  {m.citations && m.citations.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mb-3">
                      {m.citations.map((c, i) => (
                        <CitationBadge key={i} citation={c} index={i + 1} />
                      ))}
                    </div>
                  )}

                  <div
                    className={`leading-relaxed whitespace-pre-wrap ${
                      m.isStreaming ? "typing-cursor" : ""
                    }`}
                  >
                    {m.text}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Input Bar */}
          <div className="p-4 border-t border-slate-800 bg-slate-900/40">
            <form
              onSubmit={handleFormSubmit}
              className="max-w-3xl mx-auto relative flex items-center"
            >
              <input
                type="text"
                value={inputQuery}
                onChange={(e) => setInputQuery(e.target.value)}
                placeholder="Faça uma pergunta sobre a documentação indexada..."
                className="w-full bg-slate-900 border border-slate-700 focus:border-indigo-500 rounded-xl px-4 py-3 pr-24 text-sm text-slate-100 placeholder-slate-500 focus:outline-none"
              />
              <button
                type="submit"
                disabled={isStreaming}
                className="absolute right-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium text-xs px-4 py-2 rounded-lg transition-all"
              >
                Perguntar
              </button>
            </form>
          </div>
        </main>
      </div>
    </div>
  );
}
