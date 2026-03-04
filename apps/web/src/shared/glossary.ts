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
  disadvantaged: {
    short: "Disadvantaged",
    full: "Disadvantaged Pupils (DfE performance measure)",
    description:
      "A DfE comparison measure used in performance tables. It can differ from the direct free school meals eligibility percentage."
  },
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
    full: "Free School Meals (direct)",
    description:
      "The percentage of pupils currently known to be eligible for free school meals in that school year."
  },
  eal: {
    short: "EAL",
    full: "English as an Additional Language",
    description:
      "Children whose first language at home is not English."
  },
  first_language_english: {
    short: "First Language English",
    full: "First Language English",
    description:
      "Pupils whose first language is recorded as English in the school census. This is the language spoken at home, not a measure of proficiency."
  },
  first_language_unclassified: {
    short: "First Language Unclassified",
    full: "First Language Unclassified",
    description:
      "Pupils whose first language was not recorded or could not be classified in the school census. A high figure may indicate data-quality gaps."
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
  },
  section_5: {
    short: "Section 5",
    full: "Section 5 Inspection (Full Inspection)",
    description:
      "A full graded inspection under the Education Act 2005. Results in an overall effectiveness judgement of Outstanding, Good, Requires Improvement or Inadequate."
  },
  section_8: {
    short: "Section 8",
    full: "Section 8 Inspection (Short / Monitoring)",
    description:
      "A shorter, usually ungraded inspection. Often used to check whether a Good school remains Good, or to monitor progress at schools rated Requires Improvement or Inadequate."
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
