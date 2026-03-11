export interface ResolvedSiteConfig {
  productName: string;
  shortName: string;
  operatorName: string;
  supportEmail: string;
  privacyEmail: string;
  publicUrl: string | null;
  defaultDescription: string;
  defaultOgImagePath: string;
}

export const STATIC_SITEMAP_PATHS = [
  "/",
  "/about",
  "/data-sources",
  "/contact",
  "/privacy",
  "/terms",
  "/accessibility",
] as const;

const DEFAULT_PRODUCT_NAME = "BRAND";
const DEFAULT_SHORT_NAME = "BRAND";
const DEFAULT_OPERATOR_NAME = "Civitas";
const DEFAULT_SUPPORT_EMAIL = "hello@example.invalid";
const DEFAULT_PRIVACY_EMAIL = "privacy@example.invalid";
const DEFAULT_DESCRIPTION =
  "Independent school research for England. Explore official data on demographics, trends, Ofsted, and local context.";
const DEFAULT_OG_IMAGE_PATH = "/og-default.png";

function readNonEmpty(value: string | undefined, fallback: string): string {
  const trimmed = value?.trim();
  return trimmed ? trimmed : fallback;
}

function sanitizePublicUrl(value: string | undefined): string | null {
  const trimmed = value?.trim();
  if (!trimmed) {
    return null;
  }

  try {
    const parsed = new URL(trimmed);
    if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
      return null;
    }
    parsed.hash = "";
    parsed.search = "";
    return parsed.toString().replace(/\/$/, "");
  } catch {
    return null;
  }
}

export function buildCanonicalUrlFromOrigin(
  publicUrl: string | null,
  path: string
): string | null {
  if (!publicUrl) {
    return null;
  }

  const normalizedPath = path === "/" ? "/" : `/${path.replace(/^\/+/, "")}`;
  return normalizedPath === "/"
    ? `${publicUrl}/`
    : `${publicUrl}${normalizedPath}`;
}

export function buildRobotsTxt(publicUrl: string | null): string {
  if (!publicUrl) {
    return "User-agent: *\nDisallow: /\n";
  }

  return `User-agent: *\nAllow: /\n\nSitemap: ${publicUrl}/sitemap.xml\n`;
}

export function buildSitemapXml(publicUrl: string | null): string {
  const lines = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
  ];

  if (publicUrl) {
    for (const path of STATIC_SITEMAP_PATHS) {
      const url = path === "/" ? `${publicUrl}/` : `${publicUrl}${path}`;
      lines.push(`  <url><loc>${url}</loc></url>`);
    }
  }

  lines.push("</urlset>");
  return `${lines.join("\n")}\n`;
}

export function buildWebManifest(site: ResolvedSiteConfig): string {
  return JSON.stringify(
    {
      name: site.productName,
      short_name: site.shortName,
      start_url: "/",
      display: "standalone",
      background_color: "#02060f",
      theme_color: "#0a1428",
      icons: [
        {
          src: "/favicon-32x32.png",
          sizes: "32x32",
          type: "image/png",
        },
        {
          src: "/apple-touch-icon.png",
          sizes: "180x180",
          type: "image/png",
        },
        {
          src: "/favicon.svg",
          sizes: "any",
          type: "image/svg+xml",
          purpose: "any",
        },
      ],
    },
    null,
    2
  );
}

export function resolveSiteConfig(
  env: Record<string, string | undefined>
): ResolvedSiteConfig {
  const productName = readNonEmpty(env.VITE_SITE_NAME, DEFAULT_PRODUCT_NAME);
  const shortName = readNonEmpty(env.VITE_SITE_SHORT_NAME, DEFAULT_SHORT_NAME);

  return {
    productName,
    shortName,
    operatorName: readNonEmpty(env.VITE_SITE_OPERATOR_NAME, DEFAULT_OPERATOR_NAME),
    supportEmail: readNonEmpty(env.VITE_SITE_SUPPORT_EMAIL, DEFAULT_SUPPORT_EMAIL),
    privacyEmail: readNonEmpty(env.VITE_SITE_PRIVACY_EMAIL, DEFAULT_PRIVACY_EMAIL),
    publicUrl: sanitizePublicUrl(env.VITE_PUBLIC_URL),
    defaultDescription: readNonEmpty(env.VITE_SITE_DESCRIPTION, DEFAULT_DESCRIPTION),
    defaultOgImagePath: DEFAULT_OG_IMAGE_PATH,
  };
}
