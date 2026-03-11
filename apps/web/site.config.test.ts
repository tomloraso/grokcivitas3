import { describe, expect, it } from "vitest";

import {
  STATIC_SITEMAP_PATHS,
  buildCanonicalUrlFromOrigin,
  buildRobotsTxt,
  buildSitemapXml,
  buildWebManifest,
  resolveSiteConfig,
} from "./site.config";

describe("site.config helpers", () => {
  it("resolves brand configuration and sanitizes the public origin", () => {
    const site = resolveSiteConfig({
      VITE_SITE_NAME: "Launch Atlas",
      VITE_SITE_SHORT_NAME: "Atlas",
      VITE_SITE_OPERATOR_NAME: "Launch Atlas Ltd",
      VITE_SITE_SUPPORT_EMAIL: "support@example.test",
      VITE_SITE_PRIVACY_EMAIL: "privacy@example.test",
      VITE_PUBLIC_URL: "https://schools.example.test/path?query=1#hash",
    });

    expect(site.productName).toBe("Launch Atlas");
    expect(site.shortName).toBe("Atlas");
    expect(site.operatorName).toBe("Launch Atlas Ltd");
    expect(site.supportEmail).toBe("support@example.test");
    expect(site.privacyEmail).toBe("privacy@example.test");
    expect(site.publicUrl).toBe("https://schools.example.test/path");
  });

  it("builds canonical URLs only when a public origin is configured", () => {
    expect(buildCanonicalUrlFromOrigin(null, "/about")).toBeNull();
    expect(
      buildCanonicalUrlFromOrigin("https://schools.example.test", "/about")
    ).toBe("https://schools.example.test/about");
    expect(buildCanonicalUrlFromOrigin("https://schools.example.test", "/")).toBe(
      "https://schools.example.test/"
    );
  });

  it("builds crawler assets for configured and unconfigured origins", () => {
    expect(buildRobotsTxt(null)).toBe("User-agent: *\nDisallow: /\n");
    expect(buildSitemapXml(null)).not.toContain("<loc>");

    const robotsTxt = buildRobotsTxt("https://schools.example.test");
    const sitemapXml = buildSitemapXml("https://schools.example.test");

    expect(robotsTxt).toContain("Allow: /");
    expect(robotsTxt).toContain("https://schools.example.test/sitemap.xml");
    expect(
      (sitemapXml.match(/<loc>/g) ?? []).length
    ).toBe(STATIC_SITEMAP_PATHS.length);
    expect(sitemapXml).toContain("https://schools.example.test/accessibility");
  });

  it("builds a manifest from the configured site identity", () => {
    const manifest = JSON.parse(
      buildWebManifest(
        resolveSiteConfig({
          VITE_SITE_NAME: "Launch Atlas",
          VITE_SITE_SHORT_NAME: "Atlas",
        })
      )
    );

    expect(manifest.name).toBe("Launch Atlas");
    expect(manifest.short_name).toBe("Atlas");
    expect(manifest.icons).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ src: "/favicon.svg" }),
        expect.objectContaining({ src: "/apple-touch-icon.png" }),
      ])
    );
  });
});
