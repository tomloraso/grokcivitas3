export interface CompareUrlState {
  hasExplicitUrns: boolean;
  urns: string[];
}

export function parseCompareUrns(rawValue: string | null | undefined): string[] {
  if (!rawValue) {
    return [];
  }

  const seen = new Set<string>();
  const urns: string[] = [];
  for (const token of rawValue.split(",")) {
    const urn = token.trim();
    if (!urn || seen.has(urn)) {
      continue;
    }
    seen.add(urn);
    urns.push(urn);
  }

  return urns;
}

export function serializeCompareUrns(urns: string[]): string {
  return urns.join(",");
}

export function readCompareUrlState(searchParams: URLSearchParams): CompareUrlState {
  return {
    hasExplicitUrns: searchParams.has("urns"),
    urns: parseCompareUrns(searchParams.get("urns"))
  };
}
