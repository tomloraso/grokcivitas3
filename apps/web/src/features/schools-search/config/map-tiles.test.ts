import { describe, expect, it } from "vitest";

import { resolveMapTileProviders } from "./map-tiles";

describe("map tile config", () => {
  it("uses cartodb dark matter as default primary provider", () => {
    const providers = resolveMapTileProviders("unknown-provider");

    expect(providers.primary.id).toBe("cartodb-dark-matter");
    expect(providers.fallback.id).not.toBe(providers.primary.id);
  });

  it("allows selecting a supported primary provider from config", () => {
    const providers = resolveMapTileProviders("cartodb-dark-nolabels");

    expect(providers.primary.id).toBe("cartodb-dark-nolabels");
  });
});
