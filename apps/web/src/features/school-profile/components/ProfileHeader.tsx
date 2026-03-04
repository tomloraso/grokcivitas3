import { Calendar, MapPin, GraduationCap, Building2, FileCheck } from "lucide-react";

import { GlossaryTerm } from "../../../components/data/GlossaryTerm";
import { Badge } from "../../../components/ui/Badge";
import type {
  AreaContextVM,
  DemographicsVM,
  OfstedVM,
  SectionCompletenessVM,
  SchoolIdentityVM,
} from "../types";

interface ProfileHeaderProps {
  school: SchoolIdentityVM;
  ofsted: OfstedVM | null;
  ofstedCompleteness: SectionCompletenessVM;
  demographics: DemographicsVM | null;
  areaContext: AreaContextVM;
}

/* ------------------------------------------------------------------ */
/* Ofsted accent colour helpers                                        */
/* ------------------------------------------------------------------ */

const OFSTED_COLORS: Record<string, { bg: string; text: string; ring: string; glow: string }> = {
  "1": {
    bg: "bg-success/15",
    text: "text-success",
    ring: "ring-success/30",
    glow: "shadow-[0_0_20px_rgba(34,197,94,0.15)]",
  },
  "2": {
    bg: "bg-info/15",
    text: "text-info",
    ring: "ring-info/30",
    glow: "shadow-[0_0_20px_rgba(59,130,246,0.15)]",
  },
  "3": {
    bg: "bg-warning/15",
    text: "text-warning",
    ring: "ring-warning/30",
    glow: "shadow-[0_0_20px_rgba(245,158,11,0.15)]",
  },
  "4": {
    bg: "bg-danger/15",
    text: "text-danger",
    ring: "ring-danger/30",
    glow: "shadow-[0_0_20px_rgba(239,68,68,0.15)]",
  },
};

const OFSTED_LABELS: Record<string, string> = {
  "1": "Outstanding",
  "2": "Good",
  "3": "Requires Improvement",
  "4": "Inadequate",
};

/* ------------------------------------------------------------------ */
/* Ofsted signal — the rating as a bold visual element                 */
/* ------------------------------------------------------------------ */

function OfstedSignal({ ofsted }: { ofsted: OfstedVM }): JSX.Element {
  const isUngraded = !ofsted.isGraded;
  const code = ofsted.ratingCode;
  const colors = code ? OFSTED_COLORS[code] : null;
  const label = ofsted.ratingLabel ?? (code ? OFSTED_LABELS[code] : null);

  return (
    <div className="flex items-center gap-4">
      {/* Rating circle */}
      {code && colors ? (
        <div
          className={`flex h-14 w-14 shrink-0 items-center justify-center rounded-full ring-2 ${colors.bg} ${colors.ring} ${colors.glow}`}
        >
          <span className={`font-display text-2xl font-bold ${colors.text}`}>{code}</span>
        </div>
      ) : (
        <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-surface/60 ring-2 ring-border-subtle/60">
          <span className="font-display text-lg font-bold text-disabled">—</span>
        </div>
      )}

      <div className="flex flex-col gap-0.5">
        <span className="text-[10px] font-medium uppercase tracking-[0.1em] text-disabled">
          <GlossaryTerm term="ofsted">Ofsted</GlossaryTerm>
        </span>
        <span
          className={`text-sm font-semibold leading-tight ${colors?.text ?? "text-secondary"}`}
          aria-label={`Ofsted rating: ${isUngraded ? "Ungraded" : (label ?? "Not rated")}`}
        >
          {isUngraded ? "Ungraded" : (label ?? "Not rated")}
        </span>
        {ofsted.inspectionDate ? (
          <span className="text-[11px] text-disabled">
            Inspected {ofsted.inspectionDate}
          </span>
        ) : null}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Mini deprivation scale — compact 10-segment gauge for the hero      */
/* ------------------------------------------------------------------ */

const GAUGE_COLORS = [
  "bg-danger",    // 1 – most deprived
  "bg-danger",    // 2
  "bg-warning",   // 3
  "bg-warning",   // 4
  "bg-amber-400", // 5
  "bg-amber-400", // 6
  "bg-emerald-400", // 7
  "bg-emerald-400", // 8
  "bg-success",   // 9
  "bg-success",   // 10 – least deprived
];

function deprivationLabel(decile: number): string {
  if (decile <= 2) return "Most deprived";
  if (decile <= 4) return "Higher deprivation";
  if (decile <= 6) return "Mid-range";
  if (decile <= 8) return "Lower deprivation";
  return "Least deprived";
}

function MiniDeprivationGauge({ decile }: { decile: number }): JSX.Element {
  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-[10px] font-medium uppercase tracking-[0.1em] text-disabled">
        <GlossaryTerm term="imd">Deprivation</GlossaryTerm>
      </span>

      <div className="flex items-end gap-1">
        {/* Big decile number */}
        <span className="font-display text-2xl font-bold leading-none tracking-tight text-primary">
          {decile}
        </span>
        <span className="mb-0.5 text-xs text-disabled">/10</span>
      </div>

      {/* 10-segment gauge — all segments always visible */}
      <div className="flex gap-[2px]" aria-hidden>
        {Array.from({ length: 10 }, (_, i) => {
          const pos = i + 1;
          const isActive = pos === decile;
          return (
            <div
              key={pos}
              className={`flex-1 rounded-sm transition-all ${GAUGE_COLORS[i]} ${
                isActive
                  ? "h-2.5 opacity-100 shadow-[0_0_6px_rgba(255,255,255,0.2)]"
                  : "h-1.5 opacity-25"
              }`}
            />
          );
        })}
      </div>

      <span className="text-[11px] text-secondary">{deprivationLabel(decile)}</span>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Need signal                                                         */
/* ------------------------------------------------------------------ */

interface NeedSignalProps {
  label: string;
  glossaryTerm: "fsm" | "disadvantaged";
  value: string;
  year: string;
  definitionHint: string;
}

function NeedSignal({
  label,
  glossaryTerm,
  value,
  year,
  definitionHint
}: NeedSignalProps): JSX.Element {
  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-[10px] font-medium uppercase tracking-[0.1em] text-disabled">
        <GlossaryTerm term={glossaryTerm}>{label}</GlossaryTerm>
      </span>
      <span className="font-display text-2xl font-bold leading-none tracking-tight text-primary">
        {value}
      </span>
      <span className="text-[11px] text-disabled">{year}</span>
      <span className="text-[11px] text-secondary">{definitionHint}</span>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Component                                                           */
/* ------------------------------------------------------------------ */

export function ProfileHeader({
  school,
  ofsted,
  ofstedCompleteness,
  demographics,
  areaContext,
}: ProfileHeaderProps): JSX.Element {
  const isUngraded = ofsted ? !ofsted.isGraded : false;
  const fsmDirect = demographics?.metrics.find((m) => m.metricKey === "fsm_pct");
  const disadvantaged = demographics?.metrics.find(
    (m) => m.metricKey === "disadvantaged_pct"
  );
  const showDirectFsm = Boolean(demographics?.coverage.fsmSupported && fsmDirect?.value);

  const needSignal = showDirectFsm
    ? {
        label: "Free School Meals (direct)",
        glossaryTerm: "fsm" as const,
        value: fsmDirect!.value!,
        definitionHint: "Current eligibility rate"
      }
    : disadvantaged?.value
      ? {
          label: "Disadvantaged (DfE measure)",
          glossaryTerm: "disadvantaged" as const,
          value: disadvantaged.value,
          definitionHint: demographics?.coverage.fsmSupported
            ? "Direct FSM not published for this year"
            : "Fallback measure when direct FSM is unavailable"
        }
      : null;

  const hasSignals =
    ofsted || areaContext.deprivation || needSignal;

  return (
    <header className="space-y-6">
      {/* Identity */}
      <div className="space-y-3">
        <p className="eyebrow">School Profile</p>
        <h1 className="text-3xl font-bold leading-tight tracking-tight text-primary sm:text-4xl lg:text-5xl">
          {school.name}
        </h1>

        {/* Meta badges */}
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="default" className="gap-1.5">
            <GraduationCap className="h-3 w-3" aria-hidden />
            {school.phase}
          </Badge>
          <Badge variant="outline" className="gap-1.5">
            <Building2 className="h-3 w-3" aria-hidden />
            {school.type}
          </Badge>
          <Badge variant="outline" className="gap-1.5">
            <MapPin className="h-3 w-3" aria-hidden />
            {school.postcode}
          </Badge>
          {isUngraded ? (
            <Badge variant="outline" className="gap-1.5">
              <FileCheck className="h-3 w-3" aria-hidden />
              Ungraded
            </Badge>
          ) : null}
        </div>

        {/* Status indicator */}
        {school.status !== "Open" && school.status !== "Unknown" ? (
          <p className="text-sm font-medium text-warning">
            Status: {school.status}
          </p>
        ) : null}
      </div>

      {/* ── Signal strip ─────────────────────────────── */}
      {hasSignals ? (
        <>
          <div className="h-px bg-gradient-to-r from-brand/40 via-brand/10 to-transparent" aria-hidden />

          <div
            className="flex flex-wrap items-start gap-8 sm:gap-10"
            role="region"
            aria-label="Key facts"
          >
            {ofsted ? <OfstedSignal ofsted={ofsted} /> : null}

            {/* Vertical divider between signals */}
            {ofsted && (areaContext.deprivation || needSignal) ? (
              <div className="hidden h-16 w-px self-center bg-border-subtle/60 sm:block" aria-hidden />
            ) : null}

            {areaContext.deprivation ? (
              <MiniDeprivationGauge decile={areaContext.deprivation.imdDecile} />
            ) : null}

            {/* Vertical divider */}
            {areaContext.deprivation && needSignal ? (
              <div className="hidden h-16 w-px self-center bg-border-subtle/60 sm:block" aria-hidden />
            ) : null}

            {needSignal && demographics ? (
              <NeedSignal
                label={needSignal.label}
                glossaryTerm={needSignal.glossaryTerm}
                value={needSignal.value}
                year={demographics.academicYear}
                definitionHint={needSignal.definitionHint}
              />
            ) : null}
          </div>
        </>
      ) : null}

      {/* Ofsted detail — ungraded outcome */}
      {ofsted?.ungradedOutcome ? (
        <p className="text-sm text-secondary">
          Outcome: <span className="font-medium text-primary">{ofsted.ungradedOutcome}</span>
          {ofsted.publicationDate ? (
            <span className="ml-3 inline-flex items-center gap-1 text-xs text-disabled">
              <Calendar className="h-3 w-3" aria-hidden />
              Published {ofsted.publicationDate}
            </span>
          ) : null}
        </p>
      ) : null}

      {/* Completeness notice for Ofsted if needed */}
      {ofstedCompleteness.status === "unavailable" ? (
        <div className="rounded-md border border-border-subtle/80 bg-surface/60 px-3 py-2.5 text-sm text-secondary">
          Ofsted data hasn&apos;t been published by the data source yet.
        </div>
      ) : null}
    </header>
  );
}
