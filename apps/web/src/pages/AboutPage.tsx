import { ContentPageLayout } from "../components/layout/ContentPageLayout";
import { siteConfig } from "../shared/config/site";

export function AboutPage(): JSX.Element {
  return (
    <ContentPageLayout
      title={`About ${siteConfig.productName}`}
      metaTitle="About"
      metaDescription={`${siteConfig.productName} is an independent research tool for exploring English school data without editorial commentary.`}
      canonicalPath="/about"
      eyebrow="About"
      lede={`${siteConfig.productName} is built for people making serious, location-based decisions. It brings fragmented public school data into one clear research workflow.`}
    >
      <h2>What {siteConfig.productName} Is</h2>
      <p>
        {siteConfig.productName} is a free, independent research tool for exploring
        English school data. It is designed for parents, guardians, movers, renters,
        and researchers who want to assess schools using official published evidence.
      </p>

      <h2>What {siteConfig.productName} Is Not</h2>
      <p>
        {siteConfig.productName} does not rank schools, make recommendations, or tell
        users what they should choose. The product presents official public data with
        context, trends, and benchmark comparisons, but it does not add editorial
        scoring or opinion.
      </p>

      <h2>How It Works</h2>
      <p>
        Data is collected from government and public sources, normalised into a
        consistent model, and presented through postcode search, school profiles, and
        side-by-side comparison. Where enough history is published, trends show how a
        metric changes over time. Benchmark context compares a school with local or
        national baselines without implying judgement.
      </p>

      <h2>Who It Is For</h2>
      <ul>
        <li>Parents and guardians researching schools near a postcode.</li>
        <li>House movers and renters evaluating local school context before relocating.</li>
        <li>Education-focused professionals who need fast access to comparable evidence.</li>
      </ul>

      <h2>Open Data Commitment</h2>
      <p>
        The underlying data shown in {siteConfig.productName} comes from official public
        datasets. The product adds presentation, normalisation, freshness tracking,
        completeness signalling, and comparison workflows rather than proprietary source
        data.
      </p>

      <h2>Built By</h2>
      <p>
        {siteConfig.productName} is operated by {siteConfig.operatorName}. Product and
        legal contact details are published on the contact and privacy pages.
      </p>
    </ContentPageLayout>
  );
}
