import { Bot, LineChart, ShieldAlert } from "lucide-react";

import { PremiumPreviewGate } from "../../premium-access/components/PremiumPreviewGate";
import type { AnalystSectionVM } from "../types";

export function SchoolAnalystSection({
  analyst,
}: {
  analyst: AnalystSectionVM;
}): JSX.Element {
  return (
    <section
      aria-labelledby="school-analyst-heading"
      className="panel-surface space-y-4 rounded-lg p-4 sm:space-y-5 sm:p-6"
    >
      <div className="space-y-1">
        <h2
          id="school-analyst-heading"
          className="flex items-center gap-2 text-lg font-semibold text-primary sm:text-xl"
        >
          <span className="inline-block h-5 w-[3px] rounded-full bg-brand" aria-hidden />
          Analyst View
        </h2>
        <p className="text-sm text-secondary">
          AI-generated reading of the recent profile, trend, and context signals.
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_18rem]">
        <PremiumPreviewGate
          access={analyst.access}
          className="h-full"
          teaser={
            <article className="space-y-3">
              <div className="inline-flex items-center gap-2 rounded-full border border-brand/20 bg-brand/5 px-3 py-1 text-xs font-medium uppercase tracking-[0.08em] text-brand">
                <LineChart className="h-3.5 w-3.5" aria-hidden />
                Analyst Preview
              </div>
              <p className="whitespace-pre-line text-sm leading-7 text-secondary">
                {analyst.teaserText ?? "A Premium analyst summary is available for this school."}
              </p>
            </article>
          }
          unavailable={
            <article className="rounded-md border border-border-subtle/60 bg-surface/40 p-4 sm:p-5">
              <p className="text-sm leading-7 text-secondary">
                An AI-generated analyst view has not been published for this school yet.
              </p>
            </article>
          }
        >
          <article className="space-y-3">
            <div className="inline-flex items-center gap-2 rounded-full border border-brand/20 bg-brand/5 px-3 py-1 text-xs font-medium uppercase tracking-[0.08em] text-brand">
              <LineChart className="h-3.5 w-3.5" aria-hidden />
              Analyst Summary
            </div>
            <p className="whitespace-pre-line text-sm leading-7 text-secondary">
              {analyst.text}
            </p>
          </article>
        </PremiumPreviewGate>

        <div className="rounded-md border border-brand/20 bg-brand/5 p-4">
          <div className="flex items-start gap-3">
            <div className="mt-0.5 flex items-center gap-2 text-brand">
              <Bot className="h-4 w-4 shrink-0" aria-hidden />
              <ShieldAlert className="h-4 w-4 shrink-0" aria-hidden />
            </div>
            <p className="text-xs leading-6 text-secondary">
              {analyst.disclaimer ?? "This analyst view is AI-generated from public government data."}
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
