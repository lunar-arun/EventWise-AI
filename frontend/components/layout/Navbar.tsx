"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BookOpen,
  Bot,
  CalendarPlus,
  Coins,
  LayoutDashboard,
  Menu,
  Sparkles,
  X,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import type { LlmHealthStatus } from "@/types/event";
import { StarMilestoneIcon } from "@/components/ui/MarioMotifs";

const NAV_LINKS = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/planner", label: "Event Planner", icon: CalendarPlus },
  { href: "/budget", label: "Budget Planner", icon: Coins },
  { href: "/chat", label: "AI Chatbot", icon: Bot },
  { href: "/knowledge-base", label: "Knowledge Base", icon: BookOpen },
];

export function Navbar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [llmHealth, setLlmHealth] = useState<LlmHealthStatus | null>(null);

  useEffect(() => {
    let mounted = true;
    apiClient
      .getLlmHealth()
      .then((res) => {
        if (mounted) setLlmHealth(res);
      })
      .catch(() => {
        if (mounted) {
          setLlmHealth({
            status: "offline",
            ollama_reachable: false,
            configured_model: "local",
            configured_model_available: false,
            available_models: [],
          });
        }
      });
    return () => {
      mounted = false;
    };
  }, [pathname]);

  return (
    <header className="sticky top-0 z-40 border-b-2 border-mario-navy bg-white shadow-sm">
      {/* Top pipe-green bar */}
      <div className="bg-mario-navy text-white text-xs py-1.5 px-4">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="inline-block w-2.5 h-2.5 rounded-full bg-mario-gold" />
            <span className="font-pixel text-[11px] tracking-wider text-mario-gold">
              LOCAL-FIRST GEN-AI • ZERO EXTERNAL CLOUD APIS
            </span>
          </div>
          <div className="flex items-center gap-3 text-[11px]">
            <span className="inline-flex items-center gap-1.5">
              <span
                className={`w-2 h-2 rounded-full ${
                  llmHealth?.ollama_reachable ? "bg-mario-green" : "bg-amber-400"
                }`}
              />
              <span>
                Ollama:{" "}
                <strong>
                  {llmHealth
                    ? llmHealth.ollama_reachable
                      ? `${llmHealth.configured_model} (Ready)`
                      : "Fallback Mode (Offline)"
                    : "Checking..."}
                </strong>
              </span>
            </span>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <Link
          href="/"
          className="flex items-center gap-3 group focus:outline-none focus-visible:ring-2 focus-visible:ring-mario-red rounded-xl p-1"
        >
          <div className="w-10 h-10 rounded-xl bg-mario-red border-2 border-mario-navy shadow-retro-sm flex items-center justify-center group-hover:bg-mario-gold transition-colors">
            <StarMilestoneIcon className="w-6 h-6" />
          </div>
          <div>
            <span className="text-lg font-extrabold text-mario-navy tracking-tight flex items-center gap-1.5">
              EventWise <span className="text-mario-red">AI</span>
            </span>
            <span className="block text-[10px] font-pixel text-mario-green">
              SMART EVENT QUEST PLANNER
            </span>
          </div>
        </Link>

        {/* Desktop navigation */}
        <nav aria-label="Main Navigation" className="hidden md:flex items-center gap-2">
          {NAV_LINKS.map((item) => {
            const Icon = item.icon;
            const isActive =
              item.href === "/"
                ? pathname === "/"
                : pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-xl text-sm font-bold border-2 transition-all ${
                  isActive
                    ? "bg-mario-green text-white border-mario-navy shadow-retro-sm"
                    : "bg-white text-mario-navy border-transparent hover:border-mario-navy hover:bg-mario-bg"
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="hidden md:flex items-center gap-2">
          <Link
            href="/planner"
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-mario-gold text-mario-navy font-bold text-sm border-2 border-mario-navy shadow-retro-sm hover:bg-[#FFD84D] transition-colors"
          >
            <Sparkles className="w-4 h-4" />
            <span>New Event Quest</span>
          </Link>
        </div>

        {/* Mobile menu button */}
        <button
          type="button"
          onClick={() => setMobileOpen((prev) => !prev)}
          aria-expanded={mobileOpen}
          aria-label="Toggle navigation menu"
          className="md:hidden p-2 rounded-xl border-2 border-mario-navy bg-mario-bg text-mario-navy"
        >
          {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* Mobile navigation drawer */}
      {mobileOpen && (
        <nav
          aria-label="Mobile Navigation"
          className="md:hidden border-t-2 border-mario-navy bg-white px-4 py-3 space-y-2"
        >
          {NAV_LINKS.map((item) => {
            const Icon = item.icon;
            const isActive =
              item.href === "/"
                ? pathname === "/"
                : pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setMobileOpen(false)}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-bold border-2 ${
                  isActive
                    ? "bg-mario-green text-white border-mario-navy"
                    : "bg-mario-bg text-mario-navy border-transparent"
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
      )}
    </header>
  );
}
