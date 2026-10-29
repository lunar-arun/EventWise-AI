import React from "react";

export function CoinIcon({ className = "w-6 h-6" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
    >
      <circle cx="16" cy="16" r="14" fill="#FFC928" stroke="#20304A" strokeWidth="2.5" />
      <circle cx="16" cy="16" r="10.5" fill="#FFE074" stroke="#B78400" strokeWidth="1.5" />
      <rect x="14" y="9" width="4" height="14" rx="1.5" fill="#20304A" />
    </svg>
  );
}

export function StarMilestoneIcon({
  className = "w-6 h-6",
  active = true,
}: {
  className?: string;
  active?: boolean;
}) {
  return (
    <svg
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
    >
      <path
        d="M16 3L19.8 10.7L28.3 11.9L22.1 17.9L23.6 26.4L16 22.4L8.4 26.4L9.9 17.9L3.7 11.9L12.2 10.7L16 3Z"
        fill={active ? "#FFC928" : "#E2E8F0"}
        stroke="#20304A"
        strokeWidth="2.2"
        strokeLinejoin="round"
      />
      <circle cx="13.5" cy="14.5" r="1.2" fill="#20304A" />
      <circle cx="18.5" cy="14.5" r="1.2" fill="#20304A" />
    </svg>
  );
}

export function QuestionBlockBadge({ label = "?" }: { label?: string }) {
  return (
    <span
      className="question-block-badge font-pixel inline-flex items-center justify-center w-8 h-8 rounded-lg text-sm select-none shrink-0"
      aria-hidden="true"
    >
      {label}
    </span>
  );
}

export function BrickDivider({ className = "my-6" }: { className?: string }) {
  return <div className={`brick-divider ${className}`} role="separator" />;
}

export function CloudSkyBanner({
  title,
  subtitle,
  badgeText,
  rightSlot,
}: {
  title: string;
  subtitle: string;
  badgeText?: string;
  rightSlot?: React.ReactNode;
}) {
  return (
    <section className="relative overflow-hidden rounded-2xl border-2 border-mario-navy bg-gradient-to-b from-[#8EDBFA] via-[#B9EAFF] to-[#E6F7FF] p-6 shadow-retro mb-6">
      {/* Decorative original SVG clouds and hills */}
      <svg
        className="pointer-events-none absolute -top-2 right-8 w-36 h-16 opacity-80"
        viewBox="0 0 160 70"
        fill="none"
        aria-hidden="true"
      >
        <path
          d="M35 55H128C140 55 148 47 148 36C148 26 140 18 129 18C126 8 116 2 104 2C90 2 79 11 76 23C72 20 66 18 60 18C47 18 37 28 37 40C27 41 20 47 20 55H35Z"
          fill="#FFFFFF"
          stroke="#20304A"
          strokeWidth="2.5"
        />
      </svg>
      <div className="pointer-events-none absolute bottom-0 left-0 right-0 h-3 bg-[#279B52]/30 border-t border-[#279B52]/50" />

      <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          {badgeText && (
            <div className="inline-flex items-center gap-2 rounded-full bg-mario-gold px-3 py-1 text-xs font-pixel text-mario-navy border-2 border-mario-navy shadow-retro-sm mb-2">
              <StarMilestoneIcon className="w-4 h-4" />
              <span>{badgeText}</span>
            </div>
          )}
          <h1 className="text-2xl md:text-3xl font-extrabold text-mario-navy tracking-tight">
            {title}
          </h1>
          <p className="mt-1 text-sm md:text-base text-mario-navy/85 max-w-3xl font-medium">
            {subtitle}
          </p>
        </div>
        {rightSlot && <div className="shrink-0">{rightSlot}</div>}
      </div>
    </section>
  );
}

export function ErrorBanner({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div
      role="alert"
      className="rounded-xl border-2 border-mario-navy bg-red-50 p-4 text-mario-navy shadow-retro-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3"
    >
      <div className="flex items-start gap-3">
        <span className="inline-flex items-center justify-center w-7 h-7 rounded-lg bg-mario-red text-white font-pixel text-xs border border-mario-navy shrink-0">
          !
        </span>
        <div>
          <p className="font-bold text-sm text-mario-red">Action Required / Error</p>
          <p className="text-sm text-mario-navy mt-0.5">{message}</p>
        </div>
      </div>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="px-3 py-1.5 rounded-lg bg-white border-2 border-mario-navy text-xs font-bold hover:bg-mario-gold transition-colors shadow-retro-sm"
        >
          Retry
        </button>
      )}
    </div>
  );
}

export function EmptyQuestState({
  title,
  description,
  actionSlot,
}: {
  title: string;
  description: string;
  actionSlot?: React.ReactNode;
}) {
  return (
    <div className="rounded-2xl border-2 border-dashed border-mario-navy/50 bg-white p-8 text-center">
      <div className="mx-auto mb-3 flex items-center justify-center w-12 h-12 rounded-xl bg-mario-gold border-2 border-mario-navy shadow-retro-sm">
        <StarMilestoneIcon className="w-7 h-7" />
      </div>
      <h3 className="text-lg font-bold text-mario-navy">{title}</h3>
      <p className="mt-1 text-sm text-mario-muted max-w-md mx-auto">{description}</p>
      {actionSlot && <div className="mt-4 flex justify-center">{actionSlot}</div>}
    </div>
  );
}
