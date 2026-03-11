import { useState } from "react";
import { Link } from "react-router-dom";

import { createBillingPortalSession } from "../../api/client";
import { Breadcrumbs } from "../../components/layout/Breadcrumbs";
import { PageContainer } from "../../components/layout/PageContainer";
import { PageMeta } from "../../components/layout/PageMeta";
import { Button } from "../../components/ui/Button";
import { Card, Panel } from "../../components/ui/Card";
import { ErrorState } from "../../components/ui/ErrorState";
import { LoadingSkeleton } from "../../components/ui/LoadingSkeleton";
import { useToast } from "../../components/ui/ToastContext";
import { siteConfig } from "../../shared/config/site";
import { paths } from "../../shared/routing/paths";
import { useAuth } from "../auth/useAuth";
import { getCapabilityDisplayLabel } from "./copy";
import { useAccountAccess } from "./hooks/useAccountAccess";

function formatDateTime(iso: string | null): string | null {
  if (!iso) {
    return null;
  }

  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return iso;
  }

  return date.toLocaleString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "UTC",
  });
}

function accessStateLabel(state: "anonymous" | "free" | "pending" | "premium"): string {
  switch (state) {
    case "premium":
      return "Premium active";
    case "pending":
      return "Payment processing";
    case "free":
      return "Free";
    case "anonymous":
    default:
      return "Signed out";
  }
}

export function AccountFeature(): JSX.Element {
  const { session } = useAuth();
  const { toast } = useToast();
  const { status, access, errorMessage, reload } = useAccountAccess();
  const [isOpeningPortal, setIsOpeningPortal] = useState(false);

  async function handleOpenBillingPortal(): Promise<void> {
    setIsOpeningPortal(true);
    try {
      const result = await createBillingPortalSession({
        return_path: paths.account,
      });
      globalThis.location.assign(result.redirect_url);
    } catch (error: unknown) {
      toast({
        title: "Billing portal unavailable",
        description:
          error instanceof Error
            ? error.message
            : "The billing portal could not be opened right now.",
        variant: "warning",
      });
    } finally {
      setIsOpeningPortal(false);
    }
  }

  if (session.state !== "authenticated") {
    return (
      <PageContainer className="space-y-8">
        <PageMeta
          title="Account"
          description={`Manage your ${siteConfig.productName} account, access state, and saved research.`}
          canonicalPath={paths.account}
          noIndex
        />
        <Breadcrumbs segments={[{ label: "Account" }]} />
        <Panel className="space-y-4">
          <h1 className="text-3xl font-semibold text-primary sm:text-4xl">Your account</h1>
          <p className="max-w-2xl text-sm text-secondary sm:text-base">
            Sign in to see your current access state, active entitlements, and billing recovery links.
          </p>
          <div className="flex flex-wrap gap-3">
            <Button asChild>
              <Link to={paths.signIn(paths.account)}>Sign in</Link>
            </Button>
            <Button asChild variant="secondary">
              <Link to={paths.upgrade({ returnTo: paths.account })}>View Premium plans</Link>
            </Button>
          </div>
        </Panel>
      </PageContainer>
    );
  }

  return (
    <PageContainer className="space-y-8">
      <PageMeta
        title="Account"
        description={`Manage your ${siteConfig.productName} account, access state, entitlements, and billing.`}
        canonicalPath={paths.account}
        noIndex
      />
      <Breadcrumbs segments={[{ label: "Account" }]} />

      <header className="space-y-3">
        <p className="eyebrow">Account</p>
        <h1 className="text-3xl font-semibold text-primary sm:text-4xl">
          Access and billing
        </h1>
        <p className="max-w-3xl text-sm text-secondary sm:text-base">
          {siteConfig.productName} resolves Premium access from backend entitlement state. This page shows the current account view rather than optimistic browser state.
        </p>
      </header>

      {status === "loading" && !access ? (
        <div className="space-y-4">
          <LoadingSkeleton lines={4} />
          <LoadingSkeleton lines={6} />
        </div>
      ) : null}

      {status === "error" ? (
        <ErrorState
          title="Account access unavailable"
          description={errorMessage ?? "The current access state could not be loaded."}
          onRetry={reload}
        />
      ) : null}

      {access ? (
        <>
          <div className="grid gap-4 md:grid-cols-3">
            <Card className="space-y-2">
              <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-disabled">
                Email
              </p>
              <p className="text-base font-semibold text-primary">{session.user?.email}</p>
            </Card>
            <Card className="space-y-2">
              <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-disabled">
                Access
              </p>
              <p className="text-base font-semibold text-primary">
                {accessStateLabel(access.accountAccessState)}
              </p>
            </Card>
            <Card className="space-y-2">
              <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-disabled">
                Capabilities
              </p>
              <p className="text-base font-semibold text-primary">
                {access.capabilityKeys.length}
              </p>
            </Card>
          </div>

          <Panel className="space-y-4">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div className="space-y-1">
                <h2 className="text-xl font-semibold text-primary">Saved schools</h2>
                <p className="text-sm text-secondary">
                  Open your saved research library to revisit schools you have shortlisted across search and profile pages.
                </p>
              </div>

              <Button asChild variant="secondary">
                <Link to={paths.accountFavourites}>Open saved schools</Link>
              </Button>
            </div>
          </Panel>

          <Panel className="space-y-4">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div className="space-y-1">
                <h2 className="text-xl font-semibold text-primary">Current entitlements</h2>
                <p className="text-sm text-secondary">
                  Active, pending, expired, and revoked grants are listed from the access slice.
                </p>
              </div>

              <div className="flex flex-wrap gap-3">
                <Button asChild variant="secondary">
                  <Link to={paths.upgrade({ returnTo: paths.account })}>View Premium plans</Link>
                </Button>
                {access.entitlements.length > 0 ? (
                  <Button
                    type="button"
                    variant="primary"
                    onClick={() => void handleOpenBillingPortal()}
                    disabled={isOpeningPortal}
                  >
                    {isOpeningPortal ? "Opening billing portal..." : "Manage billing"}
                  </Button>
                ) : null}
              </div>
            </div>

            {access.entitlements.length === 0 ? (
              <div className="rounded-lg border border-border-subtle/70 bg-surface/50 p-4">
                <p className="text-sm text-secondary">
                  This account does not have any recorded Premium entitlements yet.
                </p>
              </div>
            ) : (
              <div className="grid gap-4 lg:grid-cols-2">
                {access.entitlements.map((entitlement) => (
                  <Card key={entitlement.id} className="space-y-3 border-border-subtle/80 bg-surface/80">
                    <div className="space-y-1">
                      <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-disabled">
                        {entitlement.productCode}
                      </p>
                      <h3 className="text-lg font-semibold text-primary">
                        {entitlement.productDisplayName}
                      </h3>
                    </div>

                    <div className="grid gap-3 sm:grid-cols-2">
                      <div>
                        <p className="text-xs text-disabled">Status</p>
                        <p className="text-sm font-medium text-primary">{entitlement.status}</p>
                      </div>
                      <div>
                        <p className="text-xs text-disabled">Starts</p>
                        <p className="text-sm font-medium text-primary">
                          {formatDateTime(entitlement.startsAt)}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-disabled">Ends</p>
                        <p className="text-sm font-medium text-primary">
                          {formatDateTime(entitlement.endsAt) ?? "Open-ended"}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-disabled">Capabilities</p>
                        <p className="text-sm font-medium text-primary">
                          {entitlement.capabilityKeys.length > 0
                            ? entitlement.capabilityKeys
                                .map((capabilityKey) =>
                                  getCapabilityDisplayLabel(capabilityKey)
                                )
                                .join(", ")
                            : "None"}
                        </p>
                      </div>
                    </div>

                    {entitlement.revokedAt ? (
                      <p className="text-xs text-secondary">
                        Revoked {formatDateTime(entitlement.revokedAt)}
                        {entitlement.revokedReasonCode
                          ? ` (${entitlement.revokedReasonCode})`
                          : ""}
                      </p>
                    ) : null}
                  </Card>
                ))}
              </div>
            )}
          </Panel>
        </>
      ) : null}
    </PageContainer>
  );
}
