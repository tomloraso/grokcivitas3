import { siteConfig } from "../../shared/config/site";
import { paths } from "../../shared/routing/paths";
import type { SectionAccessVM } from "./types";
import {
  ANALYST_CAPABILITY_KEY,
  COMPARE_CAPABILITY_KEY,
  NEIGHBOURHOOD_CAPABILITY_KEY,
} from "./types";

interface PremiumPaywallCopy {
  title: string;
  description: string;
  buttonLabel: string;
}

function subjectLabel(
  capabilityKey: string | null,
  schoolName: string | null
): string {
  switch (capabilityKey) {
    case ANALYST_CAPABILITY_KEY:
      return schoolName ? `the full analyst view for ${schoolName}` : "the full analyst view";
    case NEIGHBOURHOOD_CAPABILITY_KEY:
      return schoolName
        ? `neighbourhood context for ${schoolName}`
        : "neighbourhood context";
    case COMPARE_CAPABILITY_KEY:
      return "side-by-side school comparison";
    default:
      return "this Premium feature";
  }
}

export function getPremiumPaywallCopy({
  capabilityKey,
  schoolName,
  requiresAuth,
}: {
  capabilityKey: string | null;
  schoolName: string | null;
  requiresAuth: boolean;
}): PremiumPaywallCopy {
  const subject = subjectLabel(capabilityKey, schoolName);

  if (requiresAuth) {
    return {
      title: `Sign in to unlock ${subject}`,
      description:
        `${siteConfig.productName} keeps Premium access on your account, then re-checks entitlement state from the backend before unlocking data.`,
      buttonLabel: "Sign in to continue",
    };
  }

  switch (capabilityKey) {
    case ANALYST_CAPABILITY_KEY:
      return {
        title: `Unlock ${subject}`,
        description:
          "See the full AI-generated read on the latest profile, trend, and context signals without the preview cut-off.",
        buttonLabel: "View Premium plans",
      };
    case NEIGHBOURHOOD_CAPABILITY_KEY:
      return {
        title: `Unlock ${subject}`,
        description:
          "Open the full deprivation, crime, and house-price context behind this school's postcode and local area.",
        buttonLabel: "View Premium plans",
      };
    case COMPARE_CAPABILITY_KEY:
      return {
        title: "Compare schools side by side with Premium",
        description:
          "Open the full compare matrix across inspection, demographics, attendance, behaviour, workforce, performance, and neighbourhood context.",
        buttonLabel: "View Premium plans",
      };
    default:
      return {
        title: `Unlock ${subject}`,
        description:
          "Premium adds deeper interpretation and workflow support on top of the free research baseline.",
        buttonLabel: "View Premium plans",
      };
  }
}

export function getCapabilityDisplayLabel(capabilityKey: string): string {
  switch (capabilityKey) {
    case ANALYST_CAPABILITY_KEY:
      return "AI analyst view";
    case NEIGHBOURHOOD_CAPABILITY_KEY:
      return "Neighbourhood context";
    case COMPARE_CAPABILITY_KEY:
      return "School comparison";
    default:
      return capabilityKey;
  }
}

export function buildAccessActionHref({
  access,
  returnTo,
}: {
  access: SectionAccessVM;
  returnTo: string;
}): string {
  const upgradeHref = paths.upgrade({
    capability: access.capabilityKey ?? undefined,
    product: access.productCodes[0],
    returnTo,
  });

  return access.requiresAuth ? paths.signIn(upgradeHref) : upgradeHref;
}
