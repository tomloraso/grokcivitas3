export const ANALYST_CAPABILITY_KEY = "premium_ai_analyst";
export const COMPARE_CAPABILITY_KEY = "premium_comparison";
export const NEIGHBOURHOOD_CAPABILITY_KEY = "premium_neighbourhood";

export type PremiumCapabilityKey =
  | typeof ANALYST_CAPABILITY_KEY
  | typeof COMPARE_CAPABILITY_KEY
  | typeof NEIGHBOURHOOD_CAPABILITY_KEY;

export type PremiumAccountAccessState =
  | "anonymous"
  | "free"
  | "pending"
  | "premium";

export type SectionAccessState = "available" | "locked" | "unavailable";

export interface SectionAccessVM {
  state: SectionAccessState;
  capabilityKey: string | null;
  reasonCode:
    | "free_baseline"
    | "premium_capability_missing"
    | "anonymous_user"
    | "artefact_not_published"
    | "artefact_not_supported"
    | "entitlement_expired"
    | "entitlement_revoked"
    | null;
  productCodes: string[];
  requiresAuth: boolean;
  requiresPurchase: boolean;
  schoolName: string | null;
}

export interface AccountEntitlementVM {
  id: string;
  productCode: string;
  productDisplayName: string;
  capabilityKeys: string[];
  status: "pending" | "active" | "expired" | "revoked";
  startsAt: string;
  endsAt: string | null;
  revokedAt: string | null;
  revokedReasonCode: string | null;
}

export interface AccountAccessVM {
  accountAccessState: PremiumAccountAccessState;
  capabilityKeys: string[];
  accessEpoch: string;
  entitlements: AccountEntitlementVM[];
}
