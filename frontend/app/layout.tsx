import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/layout/Navbar";

export const metadata: Metadata = {
  title: "EventWise AI — Smart Event Planning Assistant",
  description:
    "Local-first Generative AI assistant for weddings, birthdays, and community events powered by custom Python RAG, ChromaDB, Sentence Transformers, SQLite, and local Ollama.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen flex flex-col bg-mario-bg text-mario-navy antialiased">
        <Navbar />
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {children}
        </main>
        <footer className="border-t-2 border-mario-navy bg-white py-5 mt-12">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-mario-muted">
            <p className="font-semibold text-mario-navy">
              EventWise AI — Local-First Smart Event Planning Assistant
            </p>
            <p className="text-center sm:text-right">
              All sample prices are illustrative estimates in INR. Original retro platformer-inspired design; not affiliated with Nintendo.
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
