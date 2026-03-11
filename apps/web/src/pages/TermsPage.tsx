import { ContentPageLayout } from "../components/layout/ContentPageLayout";
import { buildSiteEmailHref, siteConfig } from "../shared/config/site";

export function TermsPage(): JSX.Element {
  return (
    <ContentPageLayout
      title="Terms of Use"
      metaTitle="Terms of Use"
      metaDescription={`Terms governing use of ${siteConfig.productName}, including data disclaimers, account expectations, and Premium access boundaries.`}
      canonicalPath="/terms"
      eyebrow="Legal"
      lede="These terms describe what the product provides, what it does not provide, and the basis on which account and billing features can be used."
    >
      <div className="content-callout">
        <p>
          This is a product-implementation baseline, not legal advice. Commercial and legal
          wording should be reviewed before production billing or public launch.
        </p>
      </div>

      <h2>Acceptance</h2>
      <p>
        By using {siteConfig.productName}, you agree to these terms. If you do not agree,
        you should stop using the service.
      </p>

      <h2>What The Product Provides</h2>
      <p>
        {siteConfig.productName} is a research tool built around official public school
        datasets. It is not advice, a ranking service, or a recommendation engine.
      </p>

      <h2>Data Accuracy And Availability</h2>
      <p>
        The product aggregates and displays published public data. Reasonable care is taken
        in ingestion and presentation, but completeness and accuracy cannot be guaranteed
        for every source, school, or reporting year. Important decisions should be checked
        against the original published source.
      </p>

      <h2>Acceptable Use</h2>
      <ul>
        <li>No abusive automated access or scraping beyond reasonable personal use.</li>
        <li>No redistribution of aggregated datasets without permission.</li>
        <li>No misuse of account or billing flows.</li>
      </ul>

      <h2>Accounts And Billing</h2>
      <p>
        Account holders are responsible for the use of their account. Premium access is
        controlled by backend entitlement state rather than browser-only state. Refund,
        cancellation, and subscription terms must be finalised before billing is used in
        production.
      </p>

      <h2>Intellectual Property</h2>
      <p>
        {siteConfig.operatorName} owns the product design, software, and presentation
        layer. Underlying public-sector data remains subject to the relevant publisher
        licences and attribution requirements.
      </p>

      <h2>Liability</h2>
      <p>
        To the extent permitted by law, {siteConfig.productName} is provided without
        guarantees as to uninterrupted availability, completeness, or fitness for a
        specific purpose.
      </p>

      <h2>Governing Law</h2>
      <p>
        These terms are governed by the laws of England and Wales unless a different
        legal requirement applies in the user's jurisdiction.
      </p>

      <h2>Changes To These Terms</h2>
      <p>
        Updated terms should be published on this page before the change takes effect.
        Material changes to account, billing, or acceptable-use rules should also be
        communicated through the product where appropriate.
      </p>

      <h2>Contact</h2>
      <p>
        Questions about these terms can be sent to{" "}
        <a href={buildSiteEmailHref(siteConfig.supportEmail)}>{siteConfig.supportEmail}</a>.
      </p>
    </ContentPageLayout>
  );
}
