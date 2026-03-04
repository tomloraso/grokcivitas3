/**
 * Domain glossary for education and area-context terms.
 * Used by GlossaryTerm to render inline tooltips that
 * explain acronyms and technical language for parents.
 */

export interface GlossaryEntry {
  /** Short display label (e.g. "EHCP") */
  short: string;
  /** Full expanded name */
  full: string;
  /** One-sentence plain-language explanation */
  description: string;
}

const GLOSSARY: Record<string, GlossaryEntry> = {
  ehcp: {
    short: "EHCP",
    full: "Education, Health and Care Plan",
    description:
      "A legal document for children with complex special educational needs, setting out the extra support they receive."
  },
  sen: {
    short: "SEN",
    full: "Special Educational Needs",
    description:
      "Children who need extra or different help with their learning compared to most children their age."
  },
  fsm: {
    short: "FSM",
    full: "Free School Meals",
    description:
      "Government-funded meals for children from families on lower incomes. Often used as an indicator of disadvantage."
  },
  eal: {
    short: "EAL",
    full: "English as an Additional Language",
    description:
      "Children whose first language at home is not English."
  },
  imd: {
    short: "IMD",
    full: "Index of Multiple Deprivation",
    description:
      "The official measure of relative deprivation in England, combining income, employment, health, education, crime, housing and environment factors."
  },
  idaci: {
    short: "IDACI",
    full: "Income Deprivation Affecting Children Index",
    description:
      "Measures the proportion of children in an area living in low-income households. A higher score means more children experience income deprivation."
  },
  lsoa: {
    short: "LSOA",
    full: "Lower Layer Super Output Area",
    description:
      "A small geographic area used for statistics, typically covering around 1,500 people."
  },
  ofsted: {
    short: "Ofsted",
    full: "Office for Standards in Education",
    description:
      "The government body that inspects schools and rates them Outstanding, Good, Requires Improvement or Inadequate."
  }
} as const;

/**
 * Look up a glossary entry by key. Returns undefined for unknown terms.
 */
export function getGlossaryEntry(term: string): GlossaryEntry | undefined {
  return GLOSSARY[term.toLowerCase()];
}

/**
 * All available glossary term keys.
 */
export type GlossaryTermKey = keyof typeof GLOSSARY;
