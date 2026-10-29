"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  ArrowRight,
  Calendar,
  CheckCircle2,
  Loader2,
  MapPin,
  Sparkles,
  Users,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import { formatDateDisplay, formatINR } from "@/lib/formatting";
import {
  eventCreateSchema,
  type EventCreateFormValues,
} from "@/lib/validation";
import type { EventDetail } from "@/types/event";
import {
  CloudSkyBanner,
  CoinIcon,
  ErrorBanner,
  QuestionBlockBadge,
  StarMilestoneIcon,
} from "@/components/ui/MarioMotifs";
import { SourceCitationsList } from "@/components/knowledge/SourceCitationsList";

function getDefaultFutureDate(daysAhead = 28): string {
  const d = new Date();
  d.setDate(d.getDate() + daysAhead);
  return d.toISOString().split("T")[0];
}

export function PlannerClient() {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [generatedEvent, setGeneratedEvent] = useState<EventDetail | null>(
    null
  );

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<EventCreateFormValues>({
    resolver: zodResolver(eventCreateSchema),
    defaultValues: {
      name: "",
      event_type: "birthday",
      location: "Chennai",
      total_budget: 25000,
      guest_count: 50,
      event_date: getDefaultFutureDate(28),
      preferred_theme: "Retro Starlight Adventure",
      dietary_requirements: "Pure Vegetarian Buffet",
      additional_preferences:
        "Use reusable fabric drapes, warm LED fairy lights, and preserve emergency reserve.",
    },
  });

  const applyPreset = (preset: "birthday" | "wedding" | "community") => {
    if (preset === "birthday") {
      setValue("name", "Ananya's 21st Starlight Birthday Bash");
      setValue("event_type", "birthday");
      setValue("location", "Chennai");
      setValue("total_budget", 25000);
      setValue("guest_count", 50);
      setValue("event_date", getDefaultFutureDate(25));
      setValue("preferred_theme", "Retro Starlight Adventure");
      setValue("dietary_requirements", "Pure Vegetarian Buffet & Live Chaat");
      setValue(
        "additional_preferences",
        "Keep ₹3,000 emergency reserve intact and include DIY photo booth props."
      );
    } else if (preset === "wedding") {
      setValue("name", "Karthik & Meera Royal South Indian Wedding");
      setValue("event_type", "wedding");
      setValue("location", "Chennai");
      setValue("total_budget", 500000);
      setValue("guest_count", 200);
      setValue("event_date", getDefaultFutureDate(75));
      setValue("preferred_theme", "Royal Temple Gold & Jasmine Heritage");
      setValue(
        "dietary_requirements",
        "Traditional South Indian Banana Leaf Sadhya (100% Pure Vegetarian)"
      );
      setValue(
        "additional_preferences",
        "Include Nadaswaram welcome ensemble, seasonal local marigold/jasmine mandap, and 10% emergency reserve."
      );
    } else {
      setValue("name", "Green Tech Neighborhood Eco-Cultural Festival");
      setValue("event_type", "community");
      setValue("location", "Bengaluru");
      setValue("total_budget", 75000);
      setValue("guest_count", 150);
      setValue("event_date", getDefaultFutureDate(35));
      setValue("preferred_theme", "Zero-Waste Botanical Fiesta");
      setValue(
        "dietary_requirements",
        "Vegetarian Refreshment Boxes, Millet Snacks & Filtered Water Stations"
      );
      setValue(
        "additional_preferences",
        "Arrange dual PA speakers, cordless microphones, and waste segregation bins."
      );
    }
  };

  const onSubmit = async (values: EventCreateFormValues) => {
    setSubmitting(true);
    setError(null);
    try {
      const created = await apiClient.createEvent({
        ...values,
        generate_initial_plan: true,
      });
      setGeneratedEvent(created);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to generate event plan. Check backend connectivity."
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <CloudSkyBanner
        badgeText="WORLD 2 • AI + RAG EVENT PLANNER"
        title="Create & Generate a Personalized Event Plan"
        subtitle="Enter your event requirements below. EventWise AI retrieves relevant passages from local ChromaDB, generates tailored recommendations via local Ollama, and computes deterministic budgets and milestone checklists in Python."
      />

      {error && <ErrorBanner message={error} />}

      {/* Preset Quick-Fill Bar */}
      <div className="rounded-2xl border-2 border-mario-navy bg-white p-4 shadow-retro-sm flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <QuestionBlockBadge label="?" />
          <div>
            <p className="text-sm font-bold text-mario-navy">
              Quick Demo Presets (Illustrative INR Templates)
            </p>
            <p className="text-xs text-mario-muted">
              Populate realistic event parameters with one click, then customize before generating.
            </p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => applyPreset("birthday")}
            className="px-3 py-1.5 rounded-xl bg-mario-gold/40 border-2 border-mario-navy text-xs font-bold text-mario-navy hover:bg-mario-gold transition-colors"
          >
            🎂 ₹25,000 Birthday (50 Guests)
          </button>
          <button
            type="button"
            onClick={() => applyPreset("wedding")}
            className="px-3 py-1.5 rounded-xl bg-mario-sky/40 border-2 border-mario-navy text-xs font-bold text-mario-navy hover:bg-mario-sky transition-colors"
          >
            💍 ₹5,00,000 Wedding (200 Guests)
          </button>
          <button
            type="button"
            onClick={() => applyPreset("community")}
            className="px-3 py-1.5 rounded-xl bg-emerald-100 border-2 border-mario-navy text-xs font-bold text-mario-navy hover:bg-mario-green hover:text-white transition-colors"
          >
            🎪 ₹75,000 Community (150 Guests)
          </button>
        </div>
      </div>

      {/* Main Form */}
      <form
        onSubmit={handleSubmit(onSubmit)}
        noValidate
        className="rounded-2xl border-2 border-mario-navy bg-white p-6 shadow-retro space-y-5"
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <label
              htmlFor="event-name"
              className="block text-sm font-extrabold text-mario-navy"
            >
              Event Name *
            </label>
            <span className="block text-xs text-mario-muted mb-1">
              Format: Descriptive title (2–200 characters)
            </span>
            <input
              id="event-name"
              type="text"
              required
              minLength={2}
              maxLength={200}
              placeholder="e.g., Rohan's 25th Birthday Celebration"
              {...register("name")}
              className="w-full rounded-xl border-2 border-mario-navy px-3.5 py-2.5 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-mario-red"
            />
            {errors.name && (
              <p className="mt-1 text-xs font-bold text-mario-red" role="alert">
                ❌ {errors.name.message}
              </p>
            )}
          </div>

          <div>
            <label
              htmlFor="event-type"
              className="block text-sm font-extrabold text-mario-navy"
            >
              Event Type *
            </label>
            <span className="block text-xs text-mario-muted mb-1">
              Determines budget allocation ratios and milestone templates
            </span>
            <select
              id="event-type"
              required
              {...register("event_type")}
              className="w-full rounded-xl border-2 border-mario-navy px-3.5 py-2.5 text-sm font-bold bg-white focus:outline-none focus:ring-2 focus:ring-mario-red"
            >
              <option value="birthday">Birthday Celebration</option>
              <option value="wedding">Wedding Ceremony & Reception</option>
              <option value="community">Community / Cultural Event</option>
            </select>
            {errors.event_type && (
              <p className="mt-1 text-xs font-bold text-mario-red" role="alert">
                ❌ {errors.event_type.message}
              </p>
            )}
          </div>

          <div>
            <label
              htmlFor="event-location"
              className="block text-sm font-extrabold text-mario-navy"
            >
              Location / City *
            </label>
            <span className="block text-xs text-mario-muted mb-1">
              Used for semantic RAG filtering (falls back to general India guidance if regional docs are absent)
            </span>
            <input
              id="event-location"
              type="text"
              required
              minLength={2}
              placeholder="e.g., Chennai, Bengaluru, Madurai"
              {...register("location")}
              className="w-full rounded-xl border-2 border-mario-navy px-3.5 py-2.5 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-mario-red"
            />
            {errors.location && (
              <p className="mt-1 text-xs font-bold text-mario-red" role="alert">
                ❌ {errors.location.message}
              </p>
            )}
          </div>

          <div>
            <label
              htmlFor="event-date"
              className="block text-sm font-extrabold text-mario-navy"
            >
              Event Date *
            </label>
            <span className="block text-xs text-mario-muted mb-1">
              Deadlines are calculated deterministically relative to this date
            </span>
            <input
              id="event-date"
              type="date"
              required
              {...register("event_date")}
              className="w-full rounded-xl border-2 border-mario-navy px-3.5 py-2.5 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-mario-red"
            />
            {errors.event_date && (
              <p className="mt-1 text-xs font-bold text-mario-red" role="alert">
                ❌ {errors.event_date.message}
              </p>
            )}
          </div>

          <div>
            <label
              htmlFor="total-budget"
              className="block text-sm font-extrabold text-mario-navy"
            >
              Total Budget in INR (₹) *
            </label>
            <span className="block text-xs text-mario-muted mb-1">
              Whole integer rupees (minimum ₹1,000 INR; e.g., 25000)
            </span>
            <input
              id="total-budget"
              type="number"
              required
              min={1000}
              step={100}
              {...register("total_budget")}
              className="w-full rounded-xl border-2 border-mario-navy px-3.5 py-2.5 text-sm font-bold focus:outline-none focus:ring-2 focus:ring-mario-red"
            />
            {errors.total_budget && (
              <p className="mt-1 text-xs font-bold text-mario-red" role="alert">
                ❌ {errors.total_budget.message}
              </p>
            )}
          </div>

          <div>
            <label
              htmlFor="guest-count"
              className="block text-sm font-extrabold text-mario-navy"
            >
              Number of Guests *
            </label>
            <span className="block text-xs text-mario-muted mb-1">
              Events with 150+ guests automatically add large-scale crowd milestones
            </span>
            <input
              id="guest-count"
              type="number"
              required
              min={1}
              max={100000}
              {...register("guest_count")}
              className="w-full rounded-xl border-2 border-mario-navy px-3.5 py-2.5 text-sm font-bold focus:outline-none focus:ring-2 focus:ring-mario-red"
            />
            {errors.guest_count && (
              <p className="mt-1 text-xs font-bold text-mario-red" role="alert">
                ❌ {errors.guest_count.message}
              </p>
            )}
          </div>

          <div>
            <label
              htmlFor="preferred-theme"
              className="block text-sm font-extrabold text-mario-navy"
            >
              Preferred Theme
            </label>
            <span className="block text-xs text-mario-muted mb-1">
              Optional visual style or color direction
            </span>
            <input
              id="preferred-theme"
              type="text"
              placeholder="e.g., Retro Starlight Adventure, Royal Garden"
              {...register("preferred_theme")}
              className="w-full rounded-xl border-2 border-mario-navy px-3.5 py-2.5 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-mario-red"
            />
          </div>

          <div>
            <label
              htmlFor="dietary-requirements"
              className="block text-sm font-extrabold text-mario-navy"
            >
              Dietary Requirements
            </label>
            <span className="block text-xs text-mario-muted mb-1">
              e.g., Pure Vegetarian, Jain counter, Vegan options
            </span>
            <input
              id="dietary-requirements"
              type="text"
              placeholder="e.g., 100% Pure Vegetarian Buffet with live counters"
              {...register("dietary_requirements")}
              className="w-full rounded-xl border-2 border-mario-navy px-3.5 py-2.5 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-mario-red"
            />
          </div>
        </div>

        <div>
          <label
            htmlFor="additional-preferences"
            className="block text-sm font-extrabold text-mario-navy"
          >
            Additional Preferences & Special Notes
          </label>
          <span className="block text-xs text-mario-muted mb-1">
            Any specific decor, entertainment, accessibility, or cost-saving constraints
          </span>
          <textarea
            id="additional-preferences"
            rows={3}
            placeholder="e.g., Prefer eco-friendly local flowers, indoor AC hall, and strict emergency reserve protection."
            {...register("additional_preferences")}
            className="w-full rounded-xl border-2 border-mario-navy px-3.5 py-2.5 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-mario-red"
          />
        </div>

        <div className="pt-2 flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-t border-slate-200">
          <p className="text-xs text-mario-muted">
            💡 <strong>Note:</strong> All generated budget allocations and sample prices are illustrative estimates in INR, calculated deterministically by Python.
          </p>
          <button
            type="submit"
            disabled={submitting}
            className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-mario-red text-white font-extrabold text-sm border-2 border-mario-navy shadow-retro hover:bg-[#d33b32] disabled:opacity-60 transition-all shrink-0"
          >
            {submitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Retrieving RAG Context & Generating Plan...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>Generate Complete Event Plan</span>
              </>
            )}
          </button>
        </div>
      </form>

      {/* Generated Result Preview */}
      {generatedEvent && (
        <section
          aria-label="Generated Event Plan Result"
          className="space-y-6 pt-4"
        >
          <div className="rounded-2xl border-2 border-mario-navy bg-emerald-50 p-5 shadow-retro flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-xl bg-mario-green text-white border-2 border-mario-navy flex items-center justify-center shrink-0">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <h2 className="text-xl font-extrabold text-mario-navy">
                    Plan Generated & Saved: {generatedEvent.name}
                  </h2>
                  <span className="px-2.5 py-0.5 rounded-full bg-white border border-mario-navy text-xs font-pixel text-mario-navy">
                    MODE: {generatedEvent.generation_mode.toUpperCase()}
                  </span>
                </div>
                <p className="mt-1 text-sm text-mario-navy">
                  {generatedEvent.summary}
                </p>
                <p className="mt-1 text-xs font-semibold text-mario-muted">
                  {generatedEvent.illustrative_price_notice}
                </p>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-2 shrink-0">
              <Link
                href={`/events/${generatedEvent.id}`}
                className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-mario-navy text-white text-xs font-bold border-2 border-mario-navy shadow-retro-sm hover:bg-mario-red transition-colors"
              >
                <span>Open Full Event Plan</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                href={`/budget?eventId=${generatedEvent.id}`}
                className="px-3.5 py-2.5 rounded-xl bg-mario-gold text-mario-navy text-xs font-bold border-2 border-mario-navy shadow-retro-sm"
              >
                Open Budget Planner
              </Link>
            </div>
          </div>

          {/* Themes + Deterministic Budget Summary */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="rounded-2xl border-2 border-mario-navy bg-white p-5 shadow-retro space-y-4">
              <div className="flex items-center gap-2">
                <StarMilestoneIcon className="w-6 h-6" />
                <h3 className="text-lg font-extrabold text-mario-navy">
                  Theme & Decor Recommendations
                </h3>
              </div>
              {generatedEvent.theme_recommendations.map((theme, idx) => (
                <div
                  key={idx}
                  className="rounded-xl border-2 border-mario-navy/80 bg-mario-bg p-4 space-y-2"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <h4 className="font-extrabold text-base text-mario-navy">
                      {theme.title}
                    </h4>
                    <span className="px-2 py-0.5 rounded bg-mario-gold text-mario-navy text-[11px] font-bold border border-mario-navy">
                      {theme.estimated_tier}
                    </span>
                  </div>
                  <p className="text-xs font-semibold text-mario-green">
                    {theme.tagline}
                  </p>
                  <p className="text-xs text-mario-navy leading-relaxed">
                    {theme.description}
                  </p>
                  <ul className="list-disc list-inside text-xs text-mario-navy space-y-1">
                    {theme.decor_highlights.map((h, i) => (
                      <li key={i}>{h}</li>
                    ))}
                  </ul>
                  <p className="text-xs font-semibold text-mario-muted pt-1 border-t border-slate-200">
                    🍽️ Catering Notes: {theme.catering_notes}
                  </p>
                </div>
              ))}
            </div>

            <div className="rounded-2xl border-2 border-mario-navy bg-white p-5 shadow-retro space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CoinIcon className="w-6 h-6" />
                  <h3 className="text-lg font-extrabold text-mario-navy">
                    Deterministic Python Budget Breakdown
                  </h3>
                </div>
                <span className="font-extrabold text-base text-mario-green">
                  {formatINR(generatedEvent.budget.total_budget)}
                </span>
              </div>
              <p className="text-xs text-mario-muted">
                {generatedEvent.budget.estimate_disclaimer}
              </p>
              <div className="space-y-2">
                {generatedEvent.budget.categories.map((cat) => (
                  <div
                    key={cat.name}
                    className={`flex items-center justify-between p-2.5 rounded-xl border ${
                      cat.is_emergency_reserve
                        ? "bg-amber-50 border-mario-navy font-bold"
                        : "bg-mario-bg border-slate-200"
                    }`}
                  >
                    <div>
                      <p className="text-xs font-bold text-mario-navy">
                        {cat.name}{" "}
                        {cat.is_emergency_reserve && (
                          <span className="ml-1 px-1.5 py-0.5 rounded bg-mario-gold text-[10px]">
                            Reserve
                          </span>
                        )}
                      </p>
                      <p className="text-[11px] text-mario-muted">{cat.notes}</p>
                    </div>
                    <div className="text-right shrink-0 ml-3">
                      <p className="text-sm font-extrabold text-mario-navy">
                        {formatINR(cat.planned_amount)}
                      </p>
                      <p className="text-[11px] text-mario-muted">
                        {cat.allocation_percent}%
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Citations */}
          <SourceCitationsList
            citations={generatedEvent.citations}
            missingEvidenceNote={generatedEvent.missing_evidence_note}
          />
        </section>
      )}
    </div>
  );
}
