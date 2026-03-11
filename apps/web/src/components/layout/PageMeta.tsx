import { Helmet } from "react-helmet-async";

import {
  buildCanonicalUrl,
  buildDocumentTitle,
  siteConfig,
} from "../../shared/config/site";

interface PageMetaProps {
  title: string;
  description?: string;
  canonicalPath?: string;
  noIndex?: boolean;
}

export function PageMeta({
  title,
  description,
  canonicalPath,
  noIndex = false,
}: PageMetaProps): JSX.Element {
  const fullTitle = buildDocumentTitle(title);
  const metaDescription = description ?? siteConfig.defaultDescription;
  const canonicalUrl = canonicalPath ? buildCanonicalUrl(canonicalPath) : null;
  const ogImageUrl = siteConfig.publicUrl
    ? `${siteConfig.publicUrl}${siteConfig.defaultOgImagePath}`
    : siteConfig.defaultOgImagePath;

  return (
    <Helmet prioritizeSeoTags>
      <title>{fullTitle}</title>
      <meta name="description" content={metaDescription} />
      <meta property="og:title" content={fullTitle} />
      <meta property="og:description" content={metaDescription} />
      <meta property="og:type" content="website" />
      <meta property="og:image" content={ogImageUrl} />
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={fullTitle} />
      <meta name="twitter:description" content={metaDescription} />
      {canonicalUrl ? <link rel="canonical" href={canonicalUrl} /> : null}
      {canonicalUrl ? <meta property="og:url" content={canonicalUrl} /> : null}
      {noIndex ? <meta name="robots" content="noindex, nofollow" /> : null}
    </Helmet>
  );
}
