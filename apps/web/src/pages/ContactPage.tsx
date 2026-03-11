import { Link } from "react-router-dom";

import { ContentPageLayout } from "../components/layout/ContentPageLayout";
import { buildSiteEmailHref, siteConfig } from "../shared/config/site";
import { paths } from "../shared/routing/paths";

export function ContactPage(): JSX.Element {
  return (
    <ContentPageLayout
      title="Contact and Feedback"
      metaDescription={`Get in touch about data issues, feature feedback, or general questions about ${siteConfig.productName}.`}
      canonicalPath="/contact"
      eyebrow="Contact"
      lede="Questions, corrections, and feedback are best sent by email so they stay tied to the exact source or workflow you are looking at."
    >
      <h2>General Enquiries</h2>
      <p>
        For product questions or feedback, email{" "}
        <a href={buildSiteEmailHref(siteConfig.supportEmail)}>{siteConfig.supportEmail}</a>.
      </p>

      <h2>Data Corrections</h2>
      <p>
        If something looks wrong, first check the original publisher source listed on the{" "}
        <Link to={paths.dataSources}>Data Sources and Methodology</Link> page. If the
        discrepancy still appears to be in {siteConfig.productName} rather than the source
        dataset, send the school, metric, and year in your message so it can be reviewed.
      </p>

      <h2>Feature Requests</h2>
      <p>
        Product feedback is useful when it is specific about the research task you are
        trying to complete. Short notes about what is missing, unclear, or hard to compare
        are more actionable than general suggestions.
      </p>

      <h2>Response Time</h2>
      <p>
        Every message is read, but response times vary depending on the issue and current
        workload.
      </p>
    </ContentPageLayout>
  );
}
