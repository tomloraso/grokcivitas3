import type { ReactNode } from "react";
import {
  Building2,
  Globe,
  Landmark,
  MapPinned,
  Phone,
  Users2
} from "lucide-react";

import type { SchoolIdentityVM } from "../types";

interface SchoolDetailsSectionProps {
  school: SchoolIdentityVM;
}

interface DetailRow {
  label: string;
  value: ReactNode;
}

interface DetailCardProps {
  title: string;
  description: string;
  icon: JSX.Element;
  rows: DetailRow[];
}

function isDetailRow(row: DetailRow | null): row is DetailRow {
  return row !== null;
}

function formatPercent(value: number | null): string | null {
  return value === null ? null : `${value.toFixed(1)}%`;
}

function formatIntakeLabel(school: SchoolIdentityVM): string | null {
  if (school.numberOfBoys === null && school.numberOfGirls === null) {
    return null;
  }
  if (school.numberOfBoys !== null && school.numberOfGirls !== null) {
    return `${school.numberOfBoys} boys / ${school.numberOfGirls} girls`;
  }
  if (school.numberOfBoys !== null) {
    return `${school.numberOfBoys} boys`;
  }
  return `${school.numberOfGirls} girls`;
}

function DetailCard({ title, description, icon, rows }: DetailCardProps): JSX.Element {
  return (
    <section className="rounded-lg border border-border-subtle/60 bg-surface/40 p-4">
      <div className="flex items-start gap-3">
        <div className="rounded-md bg-brand/10 p-2 text-brand">{icon}</div>
        <div className="space-y-1">
          <h3 className="text-sm font-semibold text-primary">{title}</h3>
          <p className="text-xs leading-5 text-secondary">{description}</p>
        </div>
      </div>

      {rows.length > 0 ? (
        <dl className="mt-4 space-y-3">
          {rows.map((row) => (
            <div
              key={row.label}
              className="flex flex-col gap-1 border-t border-border-subtle/40 pt-3 first:border-t-0 first:pt-0"
            >
              <dt className="text-[11px] font-medium uppercase tracking-[0.08em] text-disabled">
                {row.label}
              </dt>
              <dd className="text-sm text-secondary">{row.value}</dd>
            </div>
          ))}
        </dl>
      ) : (
        <p className="mt-4 text-sm text-secondary">Not published in the current GIAS extract.</p>
      )}
    </section>
  );
}

export function SchoolDetailsSection({ school }: SchoolDetailsSectionProps): JSX.Element {
  const contactRows: (DetailRow | null)[] = [
    school.headName
      ? {
          label: "Headteacher",
          value: (
            <span>
              {school.headName}
              {school.headJobTitle ? (
                <span className="text-disabled">{` (${school.headJobTitle})`}</span>
              ) : null}
            </span>
          )
        }
      : null,
    school.website
      ? {
          label: "Website",
          value: (
            <a
              className="text-brand underline decoration-brand/30 underline-offset-4"
              href={school.website}
              rel="noreferrer"
              target="_blank"
            >
              {school.website}
            </a>
          )
        }
      : null,
    school.telephone ? { label: "Telephone", value: school.telephone } : null,
    school.lastChangedDate ? { label: "GIAS updated", value: school.lastChangedDate } : null
  ];

  const geographyRows: (DetailRow | null)[] = [
    school.addressLines.length > 0
      ? {
          label: "Address",
          value: (
            <span className="space-y-0.5">
              {school.addressLines.map((line) => (
                <span key={line} className="block">
                  {line}
                </span>
              ))}
            </span>
          )
        }
      : null,
    school.urbanRural ? { label: "Setting", value: school.urbanRural } : null,
    school.lsoaName
      ? {
          label: "LSOA",
          value: school.lsoaCode ? `${school.lsoaName} (${school.lsoaCode})` : school.lsoaName
        }
      : school.lsoaCode
        ? { label: "LSOA", value: school.lsoaCode }
        : null
  ];

  const characteristicsRows: (DetailRow | null)[] = [
    school.ageRangeLabel ? { label: "Age range", value: school.ageRangeLabel } : null,
    school.gender ? { label: "Gender intake", value: school.gender } : null,
    school.admissionsPolicy ? { label: "Admissions", value: school.admissionsPolicy } : null,
    school.sixthForm ? { label: "Sixth form", value: school.sixthForm } : null,
    school.nurseryProvision ? { label: "Nursery", value: school.nurseryProvision } : null,
    school.boarders ? { label: "Boarding", value: school.boarders } : null,
    school.religiousCharacter
      ? { label: "Religious character", value: school.religiousCharacter }
      : null,
    school.diocese ? { label: "Diocese", value: school.diocese } : null,
    school.giasFsmPct !== null
      ? { label: "GIAS FSM", value: formatPercent(school.giasFsmPct) ?? "n/a" }
      : null
  ];

  const governanceRows: (DetailRow | null)[] = [
    school.trustName ? { label: "Trust / group", value: school.trustName } : null,
    school.trustFlag ? { label: "Trust status", value: school.trustFlag } : null,
    school.federationName ? { label: "Federation", value: school.federationName } : null,
    school.federationFlag ? { label: "Federation status", value: school.federationFlag } : null,
    school.localAuthorityName
      ? {
          label: "Local authority",
          value: school.localAuthorityCode
            ? `${school.localAuthorityName} (${school.localAuthorityCode})`
            : school.localAuthorityName
        }
      : null,
    formatIntakeLabel(school)
      ? { label: "Published intake split", value: formatIntakeLabel(school) ?? "" }
      : null
  ];

  return (
    <section
      aria-labelledby="school-details-heading"
      className="panel-surface space-y-5 rounded-lg p-5 sm:p-6"
    >
      <div className="space-y-1">
        <h2
          id="school-details-heading"
          className="flex items-center gap-2 text-lg font-semibold text-primary sm:text-xl"
        >
          <span className="inline-block h-5 w-[3px] rounded-full bg-brand" aria-hidden />
          School Details
        </h2>
        <p className="text-sm text-secondary">
          Contact, admissions, governance and geography from the latest GIAS record.
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <DetailCard
          title="Contact and Leadership"
          description="School-reported contact details and lead contact fields."
          icon={<Phone className="h-4 w-4" aria-hidden />}
          rows={contactRows.filter(isDetailRow)}
        />
        <DetailCard
          title="Address and Geography"
          description="Location and statistical area context tied to the profile."
          icon={<MapPinned className="h-4 w-4" aria-hidden />}
          rows={geographyRows.filter(isDetailRow)}
        />
        <DetailCard
          title="Characteristics"
          description="Age range, admissions and published school-character data."
          icon={<Globe className="h-4 w-4" aria-hidden />}
          rows={characteristicsRows.filter(isDetailRow)}
        />
        <DetailCard
          title="Governance and Intake"
          description="Trust, local authority and published intake split fields."
          icon={<Landmark className="h-4 w-4" aria-hidden />}
          rows={governanceRows.filter(isDetailRow)}
        />
      </div>

      <div className="flex flex-wrap items-center gap-3 rounded-md border border-border-subtle/60 bg-surface/30 px-4 py-3 text-xs text-secondary">
        <span className="inline-flex items-center gap-2">
          <Building2 className="h-3.5 w-3.5 text-brand" aria-hidden />
          Source: Get Information About Schools (GIAS)
        </span>
        {formatIntakeLabel(school) ? (
          <span className="inline-flex items-center gap-2">
            <Users2 className="h-3.5 w-3.5 text-brand" aria-hidden />
            {formatIntakeLabel(school)}
          </span>
        ) : null}
      </div>
    </section>
  );
}
