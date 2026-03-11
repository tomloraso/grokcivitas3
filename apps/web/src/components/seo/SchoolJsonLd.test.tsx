import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SchoolJsonLd } from "./SchoolJsonLd";

describe("SchoolJsonLd", () => {
  it("renders schema.org School JSON-LD with the URN identifier", () => {
    const { container } = render(
      <SchoolJsonLd
        school={{
          urn: "100001",
          name: "Camden Bridge Primary School",
          postcode: "NW1 1AA",
          lat: 51.535,
          lng: -0.125,
          telephone: "020 7000 0000",
          phase: "Primary",
          type: "Community school",
          addressLines: ["1 Example Road", "Camden", "NW1 1AA"],
        }}
        ofsted={{ ratingLabel: "Good" }}
      />
    );

    const script = container.querySelector(
      'script[type="application/ld+json"]'
    );
    expect(script).not.toBeNull();

    const payload = JSON.parse(script?.textContent ?? "{}");
    expect(payload["@context"]).toBe("https://schema.org");
    expect(payload["@type"]).toBe("School");
    expect(payload.identifier).toEqual({
      "@type": "PropertyValue",
      propertyID: "URN",
      value: "100001",
    });
    expect(payload.address).toEqual({
      "@type": "PostalAddress",
      streetAddress: "1 Example Road, Camden",
      postalCode: "NW1 1AA",
      addressCountry: "GB",
    });
    expect(payload.url).toBeUndefined();
  });
});
