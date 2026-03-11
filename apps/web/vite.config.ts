import { defineConfig, loadEnv, type Plugin } from "vite";
import react from "@vitejs/plugin-react";
import {
  buildRobotsTxt,
  buildSitemapXml,
  buildWebManifest,
  resolveSiteConfig,
} from "./site.config";

function phase13AssetsPlugin(mode: string): Plugin {
  const env = loadEnv(mode, process.cwd(), "");
  const site = resolveSiteConfig(env);
  const robotsTxt = buildRobotsTxt(site.publicUrl);
  const sitemapXml = buildSitemapXml(site.publicUrl);
  const webManifest = buildWebManifest(site);
  const ogImageUrl = site.publicUrl
    ? `${site.publicUrl}${site.defaultOgImagePath}`
    : site.defaultOgImagePath;

  return {
    name: "phase13-assets",
    transformIndexHtml(html) {
      return {
        html: html.replace(/<title>.*<\/title>/, `<title>${site.productName}</title>`),
        tags: [
          {
            tag: "meta",
            attrs: {
              name: "description",
              content: site.defaultDescription,
            },
            injectTo: "head",
          },
          {
            tag: "meta",
            attrs: {
              property: "og:title",
              content: site.productName,
            },
            injectTo: "head",
          },
          {
            tag: "meta",
            attrs: {
              property: "og:description",
              content: site.defaultDescription,
            },
            injectTo: "head",
          },
          {
            tag: "meta",
            attrs: {
              property: "og:type",
              content: "website",
            },
            injectTo: "head",
          },
          {
            tag: "meta",
            attrs: {
              property: "og:image",
              content: ogImageUrl,
            },
            injectTo: "head",
          },
          ...(site.publicUrl
            ? [
                {
                  tag: "meta",
                  attrs: {
                    property: "og:url",
                    content: `${site.publicUrl}/`,
                  },
                  injectTo: "head" as const,
                },
              ]
            : []),
          {
            tag: "meta",
            attrs: {
              name: "twitter:card",
              content: "summary_large_image",
            },
            injectTo: "head",
          },
          {
            tag: "link",
            attrs: {
              rel: "icon",
              type: "image/svg+xml",
              href: "/favicon.svg",
            },
            injectTo: "head",
          },
          {
            tag: "link",
            attrs: {
              rel: "icon",
              type: "image/png",
              sizes: "32x32",
              href: "/favicon-32x32.png",
            },
            injectTo: "head",
          },
          {
            tag: "link",
            attrs: {
              rel: "icon",
              type: "image/png",
              sizes: "16x16",
              href: "/favicon-16x16.png",
            },
            injectTo: "head",
          },
          {
            tag: "link",
            attrs: {
              rel: "apple-touch-icon",
              sizes: "180x180",
              href: "/apple-touch-icon.png",
            },
            injectTo: "head",
          },
          {
            tag: "link",
            attrs: {
              rel: "manifest",
              href: "/site.webmanifest",
            },
            injectTo: "head",
          },
        ],
      };
    },
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const pathname = req.url?.split("?")[0];
        if (pathname === "/robots.txt") {
          res.setHeader("Content-Type", "text/plain; charset=utf-8");
          res.end(robotsTxt);
          return;
        }
        if (pathname === "/sitemap.xml") {
          res.setHeader("Content-Type", "application/xml; charset=utf-8");
          res.end(sitemapXml);
          return;
        }
        if (pathname === "/site.webmanifest") {
          res.setHeader("Content-Type", "application/manifest+json; charset=utf-8");
          res.end(webManifest);
          return;
        }
        next();
      });
    },
    generateBundle() {
      this.emitFile({
        type: "asset",
        fileName: "robots.txt",
        source: robotsTxt,
      });
      this.emitFile({
        type: "asset",
        fileName: "sitemap.xml",
        source: sitemapXml,
      });
      this.emitFile({
        type: "asset",
        fileName: "site.webmanifest",
        source: webManifest,
      });
    },
  };
}

export default defineConfig(({ mode }) => ({
  plugins: [react(), phase13AssetsPlugin(mode)],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: false,
        headers: {
          host: "localhost:5173"
        }
      }
    }
  },
  test: {
    environment: "jsdom",
    setupFiles: "./src/test-setup.ts",
    globals: true,
    exclude: ["e2e/**", "node_modules/**"]
  }
}));
