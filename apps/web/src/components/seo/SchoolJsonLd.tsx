import { buildCanonicalUrl } from "../../shared/config/site";

interface SchoolJsonLdProps {
  school: {
    urn: string;
    name: string;
    postcode: string;
    lat: number;
    lng: number;
    telephone: string | null;
    phase: string;
    type: string;
    addressLines: string[];
  };
  ofsted: {
    ratingLabel: string | null;
  } | null;
}

export function SchoolJsonLd({ school, ofsted }: SchoolJsonLdProps): JSX.Element {
  const canonicalUrl = buildCanonicalUrl(`/schools/${school.urn}`);
  const streetAddress = school.addressLines
    .filter((line) => line !== school.postcode)
    .join(", ");

  const payload = {
    "@context": "https://schema.org",
    "@type": "School",
    name: school.name,
    identifier: {
      "@type": "PropertyValue",
      propertyID: "URN",
      value: school.urn,
    },
    url: canonicalUrl ?? undefined,
    telephone: school.telephone ?? undefined,
    address: {
      "@type": "PostalAddress",
      streetAddress: streetAddress || undefined,
      postalCode: school.postcode !== "Unknown" ? school.postcode : undefined,
      addressCountry: "GB",
    },
    geo:
      Number.isFinite(school.lat) && Number.isFinite(school.lng)
        ? {
            "@type": "GeoCoordinates",
            latitude: school.lat,
            longitude: school.lng,
          }
        : undefined,
    additionalProperty: [
      school.phase
        ? {
            "@type": "PropertyValue",
            name: "Phase",
            value: school.phase,
          }
        : null,
      school.type
        ? {
            "@type": "PropertyValue",
            name: "Establishment type",
            value: school.type,
          }
        : null,
      ofsted?.ratingLabel
        ? {
            "@type": "PropertyValue",
            name: "Latest Ofsted rating",
            value: ofsted.ratingLabel,
          }
        : null,
    ].filter(Boolean),
  };

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(payload) }}
    />
  );
}
