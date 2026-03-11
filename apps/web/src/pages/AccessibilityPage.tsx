import { ContentPageLayout } from "../components/layout/ContentPageLayout";
import { buildSiteEmailHref, siteConfig } from "../shared/config/site";

const LAST_REVIEWED_DATE = "11 March 2026";

export function AccessibilityPage(): JSX.Element {
  return (
    <ContentPageLayout
      title="Accessibility Statement"
      metaTitle="Accessibility Statement"
      metaDescription={`Accessibility commitment, known limitations, and contact details for reporting issues in ${siteConfig.productName}.`}
      canonicalPath="/accessibility"
      eyebrow="Accessibility"
      lede="The target baseline is WCAG 2.1 AA. This page describes the current accessibility approach, known issues, and how to report problems."
    >
      <h2>How Accessible This Service Is</h2>
      <p>
        {siteConfig.productName} aims to support keyboard navigation, clear semantic
        structure, readable contrast, and responsive layouts that work across common
        assistive technologies and screen sizes.
      </p>

      <h2>What We Do To Meet Accessibility Standards</h2>
      <p>
        The current target is WCAG 2.1 AA. The web app uses semantic HTML, visible focus
        states, responsive layouts, accessible names for controls, and text alternatives
        where the interface would otherwise rely on visual cues alone.
      </p>

      <h2>Known Limitations</h2>
      <ul>
        <li>
          Interactive map behaviour is not fully keyboard equivalent in every flow; postcode
          search and results lists remain the primary accessible alternative.
        </li>
        <li>
          Dense visualisations may require accompanying tables or surrounding explanatory
          text for the best screen-reader experience.
        </li>
      </ul>

      <h2>How To Report A Problem</h2>
      <p>
        Accessibility issues can be reported to{" "}
        <a href={buildSiteEmailHref(siteConfig.supportEmail)}>{siteConfig.supportEmail}</a>.
        Include the page, browser, device, and assistive technology where possible.
      </p>

      <h2>Enforcement Procedure</h2>
      <p>
        If you are not satisfied with the response, you can contact the{" "}
        <a href="https://www.equalityadvisoryservice.com/">
          Equality Advisory and Support Service (EASS)
        </a>{" "}
        for further advice.
      </p>

      <h2>Technical Information and Compatibility</h2>
      <p>
        The service is intended to work with current versions of major browsers and common
        assistive technologies. Accessibility should be reviewed as new product surfaces are
        added.
      </p>

      <h2>Preparation and Review</h2>
      <p>
        This statement was last reviewed on {LAST_REVIEWED_DATE}. It should be updated
        whenever significant UI changes are shipped or new accessibility issues are
        identified.
      </p>
    </ContentPageLayout>
  );
}
