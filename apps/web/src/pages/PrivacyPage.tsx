import { ContentPageLayout } from "../components/layout/ContentPageLayout";
import { buildSiteEmailHref, siteConfig } from "../shared/config/site";

export function PrivacyPage(): JSX.Element {
  return (
    <ContentPageLayout
      title="Privacy Policy"
      metaTitle="Privacy Policy"
      metaDescription={`How ${siteConfig.productName} handles account data, support enquiries, necessary cookies, and published school data.`}
      canonicalPath="/privacy"
      eyebrow="Legal"
      lede="This page explains what personal data the product handles, why it is handled, and how users can raise privacy questions."
    >
      <div className="content-callout">
        <p>
          This implementation provides the product structure for launch-readiness. Final
          legal wording should still be reviewed by a qualified legal professional before
          public launch.
        </p>
      </div>

      <h2>Who We Are</h2>
      <p>
        {siteConfig.productName} is operated by {siteConfig.operatorName}. Privacy
        questions can be sent to{" "}
        <a href={buildSiteEmailHref(siteConfig.privacyEmail)}>{siteConfig.privacyEmail}</a>.
      </p>

      <h2>What Data Is Collected</h2>
      <ul>
        <li>
          Standard request and infrastructure logs used for security, abuse prevention,
          and service operations.
        </li>
        <li>Email address and account identifiers when sign-in is enabled.</li>
        <li>Strictly necessary session cookies used to maintain authenticated sessions.</li>
        <li>Support and feedback emails that users choose to send.</li>
        <li>
          Payment-provider transaction records where Premium billing is enabled.{" "}
          {siteConfig.productName} does not store full card details.
        </li>
      </ul>

      <h2>Why Data Is Collected</h2>
      <table>
        <thead>
          <tr>
            <th>Category</th>
            <th>Why It Is Needed</th>
            <th>Typical Legal Basis</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td data-label="Category">Account identity</td>
            <td data-label="Why It Is Needed">
              To sign users in, maintain sessions, and apply account-level access.
            </td>
            <td data-label="Typical Legal Basis">Contract</td>
          </tr>
          <tr>
            <td data-label="Category">Operational logs</td>
            <td data-label="Why It Is Needed">
              To keep the service secure, diagnose incidents, and prevent abuse.
            </td>
            <td data-label="Typical Legal Basis">Legitimate interests</td>
          </tr>
          <tr>
            <td data-label="Category">Support enquiries</td>
            <td data-label="Why It Is Needed">
              To respond to messages, corrections, and privacy requests.
            </td>
            <td data-label="Typical Legal Basis">Legitimate interests</td>
          </tr>
          <tr>
            <td data-label="Category">Payment events</td>
            <td data-label="Why It Is Needed">
              To activate, reconcile, and support Premium billing where enabled.
            </td>
            <td data-label="Typical Legal Basis">Contract</td>
          </tr>
        </tbody>
      </table>

      <h2>How Long We Keep It</h2>
      <table>
        <thead>
          <tr>
            <th>Category</th>
            <th>Typical Retention</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td data-label="Category">Operational logs</td>
            <td data-label="Typical Retention">
              Retained for a limited operational window and then deleted or rotated out.
            </td>
          </tr>
          <tr>
            <td data-label="Category">Account records</td>
            <td data-label="Typical Retention">
              Kept while the account remains active and for a limited follow-up period
              needed for security, audit, or legal obligations.
            </td>
          </tr>
          <tr>
            <td data-label="Category">Support correspondence</td>
            <td data-label="Typical Retention">
              Kept only as long as needed to resolve the request and maintain an
              operational record.
            </td>
          </tr>
          <tr>
            <td data-label="Category">Payment records</td>
            <td data-label="Typical Retention">
              Retained for accounting, fraud-prevention, and legal compliance periods.
            </td>
          </tr>
        </tbody>
      </table>

      <h2>Cookies</h2>
      <p>
        The launch baseline uses only strictly necessary first-party cookies for
        authenticated session handling. If optional cookies are introduced later, a
        separate consent and preferences flow should ship in the same change set.
        {` `}
        {siteConfig.productName} does not use analytics or advertising cookies at
        launch.
      </p>
      <table>
        <thead>
          <tr>
            <th>Cookie Type</th>
            <th>Purpose</th>
            <th>Typical Lifetime</th>
            <th>Required</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td data-label="Cookie Type">Authentication session cookie</td>
            <td data-label="Purpose">
              Maintains a signed-in session and protects authenticated account actions.
            </td>
            <td data-label="Typical Lifetime">
              Session-limited or short-lived, depending on the configured identity flow.
            </td>
            <td data-label="Required">Yes</td>
          </tr>
        </tbody>
      </table>

      <h2>Sharing and Processors</h2>
      <ul>
        <li>Configured identity-provider services used to authenticate sign-in requests.</li>
        <li>Configured payment-provider services used for hosted checkout and billing.</li>
        <li>Infrastructure and email providers needed to host and support the service.</li>
        <li>{siteConfig.productName} does not sell personal data.</li>
      </ul>

      <h2>Your Rights</h2>
      <p>
        Depending on the applicable law, users may have rights to request access,
        correction, deletion, restriction, portability, or objection. Privacy requests can
        be sent to{" "}
        <a href={buildSiteEmailHref(siteConfig.privacyEmail)}>{siteConfig.privacyEmail}</a>.
      </p>

      <h2>Changes To This Policy</h2>
      <p>
        Material updates should be reflected on this page and, where appropriate, surfaced
        in the product before the change takes effect.
      </p>

      <h2>Contact</h2>
      <p>
        Privacy questions, data-subject requests, and concerns about this policy can be
        sent to{" "}
        <a href={buildSiteEmailHref(siteConfig.privacyEmail)}>{siteConfig.privacyEmail}</a>.
      </p>
    </ContentPageLayout>
  );
}
