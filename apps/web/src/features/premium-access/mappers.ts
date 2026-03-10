import type {
  AccountAccessResponse,
  SectionAccessResponse,
} from "../../api/types";
import type {
  AccountAccessVM,
  AccountEntitlementVM,
  SectionAccessVM,
} from "./types";

export function mapSectionAccess(
  access: SectionAccessResponse
): SectionAccessVM {
  return {
    state: access.state,
    capabilityKey: access.capability_key,
    reasonCode: access.reason_code,
    productCodes: [...(access.product_codes ?? [])],
    requiresAuth: access.requires_auth,
    requiresPurchase: access.requires_purchase,
    schoolName: access.school_name ?? null,
  };
}

function mapAccountEntitlement(
  entitlement: NonNullable<AccountAccessResponse["entitlements"]>[number]
): AccountEntitlementVM {
  return {
    id: entitlement.id,
    productCode: entitlement.product_code,
    productDisplayName: entitlement.product_display_name,
    capabilityKeys: [...(entitlement.capability_keys ?? [])],
    status: entitlement.status,
    startsAt: entitlement.starts_at,
    endsAt: entitlement.ends_at,
    revokedAt: entitlement.revoked_at,
    revokedReasonCode: entitlement.revoked_reason_code,
  };
}

export function mapAccountAccess(
  access: AccountAccessResponse
): AccountAccessVM {
  return {
    accountAccessState: access.account_access_state,
    capabilityKeys: [...(access.capability_keys ?? [])],
    accessEpoch: access.access_epoch,
    entitlements: (access.entitlements ?? []).map((entitlement) =>
      mapAccountEntitlement(entitlement)
    ),
  };
}
