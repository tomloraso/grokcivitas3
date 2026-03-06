import { Bot, ShieldAlert } from "lucide-react";

interface SchoolOverviewSectionProps {
  overviewText: string | null;
}

const DISCLAIMER =
  "This overview is AI-generated from public government data. It is not official advice. Always check the school's own website and the latest Ofsted report.";

export function SchoolOverviewSection({
  overviewText
}: SchoolOverviewSectionProps): JSX.Element {
  return (
    <section
      aria-labelledby="school-overview-heading"
      className="panel-surface space-y-5 rounded-lg p-5 sm:p-6"
    >
      <div className="space-y-1">
        <h2
          id="school-overview-heading"
          className="flex items-center gap-2 text-lg font-semibold text-primary sm:text-xl"
        >
          <span className="inline-block h-5 w-[3px] rounded-full bg-brand" aria-hidden />
          School Overview
        </h2>
        <p className="text-sm text-secondary">
          AI-generated summary grounded in the latest published profile data.
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_18rem]">
        <article className="rounded-md border border-border-subtle/60 bg-surface/40 p-4 sm:p-5">
          {overviewText ? (
            <div className="space-y-3">
              <div className="inline-flex items-center gap-2 rounded-full border border-brand/20 bg-brand/5 px-3 py-1 text-xs font-medium uppercase tracking-[0.08em] text-brand">
                <Bot className="h-3.5 w-3.5" aria-hidden />
                AI Summary
              </div>
              <p className="text-sm leading-7 text-secondary">{overviewText}</p>
            </div>
          ) : (
            <p className="text-sm leading-7 text-secondary">
              An AI-generated overview has not been published for this school yet.
            </p>
          )}
        </article>

        <div className="rounded-md border border-brand/20 bg-brand/5 p-4">
          <div className="flex items-start gap-3">
            <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-brand" aria-hidden />
            <p className="text-xs leading-6 text-secondary">{DISCLAIMER}</p>
          </div>
        </div>
      </div>
    </section>
  );
}
