import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CortexRAG — Enterprise Document Intelligence & Auditable RAG",
  description: "High-performance hybrid RAG engine with pgvector, semantic cache, and auditable citations.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR" className="dark">
      <body className="antialiased bg-slate-950 text-slate-100 min-h-screen">
        {children}
      </body>
    </html>
  );
}
