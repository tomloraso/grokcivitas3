import { ContentPageLayout } from "../components/layout/ContentPageLayout";
import { siteConfig } from "../shared/config/site";

const DATA_SOURCES = [
  {
    source: "Get Information About Schools (GIAS)",
    publisher: "Department for Education",
    href: "https://get-information-schools.service.gov.uk/",
    use: "School identity, location, phase, type, age range, and administrative details.",
    cadence: "Frequent refreshes from the canonical register.",
  },
  {
    source: "School Census / Characteristics",
    publisher: "Department for Education statistics",
    href: "https://explore-education-statistics.service.gov.uk/find-statistics/school-pupils-and-their-characteristics",
    use: "Pupil demographics including FSM, EAL, SEN, ethnicity, and numbers on roll.",
    cadence: "Annual release.",
  },
  {
    source: "Ofsted management information",
    publisher: "Ofsted",
    href: "https://www.gov.uk/government/statistical-data-sets/monthly-management-information-ofsteds-school-inspections-outcomes",
    use: "Latest inspection outcome, inspection date, and provider-page links.",
    cadence: "Monthly release.",
  },
  {
    source: "Ofsted inspection history",
    publisher: "Ofsted",
    href: "https://reports.ofsted.gov.uk/",
    use: "Inspection timelines and historical outcomes.",
    cadence: "Rolling updates.",
  },
  {
    source: "Key stage performance",
    publisher: "Department for Education statistics",
    href: "https://explore-education-statistics.service.gov.uk/find-statistics/key-stage-2-and-multi-academy-trust-performance",
    use: "KS2 and KS4 attainment and progress measures.",
    cadence: "Annual release.",
  },
  {
    source: "Attendance statistics",
    publisher: "Department for Education statistics",
    href: "https://explore-education-statistics.service.gov.uk/find-statistics/pupil-attendance-in-schools",
    use: "Overall attendance and persistent absence measures.",
    cadence: "Termly and annual publication.",
  },
  {
    source: "Suspensions and exclusions",
    publisher: "Department for Education statistics",
    href: "https://explore-education-statistics.service.gov.uk/find-statistics/suspensions-and-permanent-exclusions-in-england",
    use: "Suspension and permanent exclusion counts and rates.",
    cadence: "Annual release.",
  },
  {
    source: "School workforce census",
    publisher: "Department for Education statistics",
    href: "https://explore-education-statistics.service.gov.uk/find-statistics/school-workforce-in-england",
    use: "Teacher, support-staff, pay, absence, vacancy, and leadership measures.",
    cadence: "Annual release.",
  },
  {
    source: "Academies Accounts Return",
    publisher: "Department for Education",
    href: "https://www.gov.uk/government/collections/academies-accounts-direction",
    use: "Academy finance, income, expenditure, reserves, and per-pupil benchmark metrics.",
    cadence: "Annual release.",
  },
  {
    source: "School admissions data",
    publisher: "Department for Education",
    href: "https://www.gov.uk/government/statistics/secondary-and-primary-school-application-and-offers",
    use: "Places offered, applications, oversubscription, and offer-rate measures.",
    cadence: "Annual release.",
  },
  {
    source: "Key stage 4 destination measures",
    publisher: "Department for Education statistics",
    href: "https://explore-education-statistics.service.gov.uk/find-statistics/key-stage-4-destination-measures/2023-24",
    use: "School leaver destinations after key stage 4, including education, apprenticeships, employment, and sustained-destination measures.",
    cadence: "Annual release.",
  },
  {
    source: "16 to 18 destination measures",
    publisher: "Department for Education statistics",
    href: "https://explore-education-statistics.service.gov.uk/find-statistics/16-18-destination-measures/2023-24",
    use: "Leaver destinations after 16 to 18 study, including progression to education, apprenticeships, employment, and sustained-destination measures.",
    cadence: "Annual release.",
  },
  {
    source: "Indices of Multiple Deprivation (IMD / IDACI)",
    publisher: "Office for National Statistics and MHCLG releases",
    href: "https://www.gov.uk/government/statistics/english-indices-of-deprivation-2019",
    use: "Area deprivation context for the school neighbourhood.",
    cadence: "Periodic national release.",
  },
  {
    source: "Police UK street-level crime",
    publisher: "Police UK",
    href: "https://data.police.uk/",
    use: "Local crime counts and category breakdowns around the school area.",
    cadence: "Monthly publication.",
  },
  {
    source: "UK House Price Index",
    publisher: "HM Land Registry and ONS",
    href: "https://landregistry.data.gov.uk/app/ukhpi",
    use: "Area-level house price trends for neighbourhood context.",
    cadence: "Monthly publication.",
  },
] as const;

export function DataSourcesPage(): JSX.Element {
  return (
    <ContentPageLayout
      title="Data Sources and Methodology"
      metaDescription={`Every source used by ${siteConfig.productName}, what it is used for, and how published data is turned into search, profile, and compare views.`}
      canonicalPath="/data-sources"
      eyebrow="Methodology"
      lede="Every metric in the product should be traceable back to an official published source. This page summarises the current source set and the rules used to present it."
    >
      <h2>How Data Is Used</h2>
      <p>
        {siteConfig.productName} ingests official public datasets into a repeatable Bronze
        to Silver to Gold pipeline. The product then serves search, profile, and
        comparison views from those normalised datasets rather than reinterpreting the raw
        files in the browser.
      </p>

      <h2>Current Source Set</h2>
      <table>
        <thead>
          <tr>
            <th>Source</th>
            <th>Publisher</th>
            <th>What It Is Used For</th>
            <th>Update Cadence</th>
          </tr>
        </thead>
        <tbody>
          {DATA_SOURCES.map((entry) => (
            <tr key={entry.source}>
              <td data-label="Source">
                <a href={entry.href} target="_blank" rel="noreferrer">
                  {entry.source}
                </a>
              </td>
              <td data-label="Publisher">{entry.publisher}</td>
              <td data-label="What It Is Used For">{entry.use}</td>
              <td data-label="Update Cadence">{entry.cadence}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>Methodology Notes</h2>
      <ul>
        <li>Benchmarks are calculated from published data and are not editorial scores.</li>
        <li>Trend views are shown only when at least two valid data points are available.</li>
        <li>
          When a source does not publish a metric for a school or year, the product shows
          completeness messaging instead of hiding the gap.
        </li>
        <li>
          AI-generated school summaries, where present, are constrained by provenance and
          disclaimer rules and do not replace the underlying data.
        </li>
      </ul>

      <h2>Freshness and Verification</h2>
      <p>
        Pipeline runs track source freshness and failure state. The web product surfaces
        completeness and freshness cues where the source set is partial or not yet
        published for the latest year.
      </p>
    </ContentPageLayout>
  );
}
