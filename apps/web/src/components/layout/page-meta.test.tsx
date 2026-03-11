import { describe, expect, it } from "vitest";

import { PageMeta } from "./PageMeta";
import { expectDocumentTitle, expectHeadAttribute } from "../../test/head";
import { renderWithProviders } from "../../test/render";

describe("PageMeta", () => {
  it("sets the document title and description", async () => {
    renderWithProviders(
      <PageMeta title="Example page" description="Example description" canonicalPath="/" />
    );

    await expectDocumentTitle("Example page");
    await expectHeadAttribute(
      'meta[name="description"]',
      "content",
      "Example description"
    );
  });

  it("omits canonical links when no public URL is configured", () => {
    renderWithProviders(<PageMeta title="Example page" canonicalPath="/" />);

    expect(document.head.querySelector('link[rel="canonical"]')).toBeNull();
  });

  it("adds a noindex robots directive when requested", async () => {
    renderWithProviders(<PageMeta title="Hidden page" noIndex />);

    await expectHeadAttribute(
      'meta[name="robots"]',
      "content",
      "noindex, nofollow"
    );
  });
});
