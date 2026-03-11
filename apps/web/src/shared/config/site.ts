import {
  buildCanonicalUrlFromOrigin,
  resolveSiteConfig,
} from "../../../site.config";

export const siteConfig = resolveSiteConfig(
  import.meta.env as Record<string, string | undefined>
);

export function buildCanonicalUrl(path: string): string | null {
  return buildCanonicalUrlFromOrigin(siteConfig.publicUrl, path);
}

export function buildDocumentTitle(title: string): string {
  const trimmedTitle = title.trim();
  if (!trimmedTitle) {
    return siteConfig.productName;
  }

  return `${trimmedTitle} | ${siteConfig.productName}`;
}

export function buildSiteEmailHref(email: string): string {
  return `mailto:${email}`;
}
