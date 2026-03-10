import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import {
  createBillingPortalSession,
  createCheckoutSession,
  getCheckoutSessionStatus,
  listBillingProducts,
} from "../../api/client";
import type { BillingProduct, CheckoutSessionStatusResponse } from "../../api/types";
import { Breadcrumbs } from "../../components/layout/Breadcrumbs";
import { PageContainer } from "../../components/layout/PageContainer";
import { Button } from "../../components/ui/Button";
import { Card, Panel } from "../../components/ui/Card";
import { ErrorState } from "../../components/ui/ErrorState";
import { LoadingSkeleton } from "../../components/ui/LoadingSkeleton";
import { useToast } from "../../components/ui/ToastContext";
import { paths } from "../../shared/routing/paths";
import { useAuth } from "../auth/useAuth";
import { getCapabilityDisplayLabel, getPremiumPaywallCopy } from "./copy";
import { useAccountAccess } from "./hooks/useAccountAccess";

type ProductsState =
  | {
      status: "loading";
      products: BillingProduct[];
      errorMessage: null;
    }
  | {
      status: "success";
      products: BillingProduct[];
      errorMessage: null;
    }
  | {
      status: "error";
      products: BillingProduct[];
      errorMessage: string;
    };

function formatInterval(product: BillingProduct): string {
  if (product.billing_interval === "monthly") {
    return "Monthly";
  }
  if (product.billing_interval === "annual") {
    return "Annual";
  }
  if (product.billing_interval === "one_time") {
    return "One-time";
  }
  return "Plan";
}

function checkoutStatusCopy(
  status: CheckoutSessionStatusResponse["status"]
): string {
  switch (status) {
    case "completed":
      return "Premium access is now active for this account.";
    case "processing_payment":
      return "Payment has returned from checkout. Civitas is waiting for provider reconciliation before unlocking access.";
    case "open":
      return "Checkout is still open. You can resume the hosted payment flow.";
    case "already_covered":
      return "This account already has the required Premium access.";
    case "canceled":
      return "Checkout was canceled before activation completed.";
    case "expired":
      return "Checkout expired before payment completed.";
    case "failed":
      return "Payment failed and Premium access was not activated.";
    default:
      return "Checkout status is updating.";
  }
}

export function UpgradeFeature(): JSX.Element {
  const { session, reloadSession } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { access, reload: reloadAccountAccess } = useAccountAccess();
  const [productsState, setProductsState] = useState<ProductsState>({
    status: "loading",
    products: [],
    errorMessage: null,
  });
  const [checkoutStatus, setCheckoutStatus] = useState<CheckoutSessionStatusResponse | null>(null);
  const [isStartingCheckout, setIsStartingCheckout] = useState(false);
  const [isOpeningPortal, setIsOpeningPortal] = useState(false);

  const requestedCapability = searchParams.get("capability");
  const requestedProduct = searchParams.get("product");
  const returnTo = searchParams.get("returnTo");
  const checkoutId = searchParams.get("checkout_id");

  const heroCopy = getPremiumPaywallCopy({
    capabilityKey: requestedCapability,
    schoolName: null,
    requiresAuth: session.state !== "authenticated",
  });

  useEffect(() => {
    let isCancelled = false;

    const loadProducts = async (): Promise<void> => {
      setProductsState({
        status: "loading",
        products: [],
        errorMessage: null,
      });

      try {
        const response = await listBillingProducts();
        if (isCancelled) {
          return;
        }
        setProductsState({
          status: "success",
          products: response.products,
          errorMessage: null,
        });
      } catch (error: unknown) {
        if (isCancelled) {
          return;
        }
        setProductsState({
          status: "error",
          products: [],
          errorMessage:
            error instanceof Error
              ? error.message
              : "Failed to load Premium plans.",
        });
      }
    };

    void loadProducts();

    return () => {
      isCancelled = true;
    };
  }, []);

  const selectedProduct = useMemo(() => {
    if (productsState.products.length === 0) {
      return null;
    }
    return (
      productsState.products.find((product) => product.code === requestedProduct) ??
      productsState.products[0]
    );
  }, [productsState.products, requestedProduct]);

  useEffect(() => {
    if (!checkoutId || session.state !== "authenticated") {
      setCheckoutStatus(null);
      return;
    }

    let isCancelled = false;
    let attempts = 0;
    let timer: ReturnType<typeof setTimeout> | null = null;

    const poll = async (): Promise<void> => {
      try {
        const status = await getCheckoutSessionStatus(checkoutId);
        if (isCancelled) {
          return;
        }

        setCheckoutStatus(status);

        if (status.status === "completed" || status.status === "already_covered") {
          await reloadSession();
          await reloadAccountAccess();
          return;
        }

        if (
          (status.status === "open" || status.status === "processing_payment") &&
          attempts < 15
        ) {
          attempts += 1;
          timer = setTimeout(() => {
            void poll();
          }, 2000);
        }
      } catch (error: unknown) {
        if (!isCancelled) {
          toast({
            title: "Checkout status unavailable",
            description:
              error instanceof Error
                ? error.message
                : "The latest checkout state could not be loaded.",
            variant: "warning",
          });
        }
      }
    };

    void poll();

    return () => {
      isCancelled = true;
      if (timer) {
        clearTimeout(timer);
      }
    };
  }, [checkoutId, reloadAccountAccess, reloadSession, session.state, toast]);

  async function handleStartCheckout(): Promise<void> {
    if (!selectedProduct || session.state !== "authenticated") {
      return;
    }

    setIsStartingCheckout(true);
    try {
      const upgradeReturnPath = paths.upgrade({
        capability: requestedCapability ?? undefined,
        product: selectedProduct.code,
        returnTo,
      });
      const result = await createCheckoutSession({
        product_code: selectedProduct.code,
        success_path: upgradeReturnPath,
        cancel_path: upgradeReturnPath,
      });

      if (result.status === "already_covered") {
        await reloadSession();
        await reloadAccountAccess();
        toast({
          title: "Premium already active",
          description: "This account already has the selected Premium access.",
        });
        return;
      }

      if (result.redirect_url) {
        globalThis.location.assign(result.redirect_url);
      }
    } catch (error: unknown) {
      toast({
        title: "Checkout unavailable",
        description:
          error instanceof Error
            ? error.message
            : "The hosted checkout session could not be started.",
        variant: "warning",
      });
    } finally {
      setIsStartingCheckout(false);
    }
  }

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

  return (
    <PageContainer className="space-y-8">
      <Breadcrumbs
        segments={[
          { label: "Account", href: paths.account },
          { label: "Upgrade" },
        ]}
      />

      <header className="space-y-3">
        <p className="eyebrow">Premium</p>
        <h1 className="text-3xl font-semibold text-primary sm:text-4xl">
          {heroCopy.title}
        </h1>
        <p className="max-w-3xl text-sm text-secondary sm:text-base">
          {heroCopy.description}
        </p>
      </header>

      {checkoutStatus ? (
        <Panel className="space-y-3 border-brand/30 bg-brand/5">
          <h2 className="text-lg font-semibold text-primary">Checkout status</h2>
          <p className="text-sm text-secondary">
            {checkoutStatusCopy(checkoutStatus.status)}
          </p>
          <div className="flex flex-wrap gap-3">
            {checkoutStatus.status === "open" && checkoutStatus.redirect_url ? (
              <Button asChild>
                <a href={checkoutStatus.redirect_url}>Resume checkout</a>
              </Button>
            ) : null}
            {checkoutStatus.status === "completed" && returnTo ? (
              <Button
                type="button"
                onClick={() => {
                  navigate(returnTo);
                }}
              >
                Continue
              </Button>
            ) : null}
            <Button asChild variant="secondary">
              <Link to={paths.account}>Open account</Link>
            </Button>
          </div>
        </Panel>
      ) : null}

      {productsState.status === "loading" ? (
        <div className="space-y-4">
          <LoadingSkeleton lines={4} />
          <LoadingSkeleton lines={6} />
        </div>
      ) : null}

      {productsState.status === "error" ? (
        <ErrorState
          title="Premium plans unavailable"
          description={productsState.errorMessage}
        />
      ) : null}

      {selectedProduct ? (
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_20rem]">
          <Panel className="space-y-5">
            <div className="space-y-2">
              <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-disabled">
                {selectedProduct.code}
              </p>
              <h2 className="text-2xl font-semibold text-primary">
                {selectedProduct.display_name}
              </h2>
              <p className="text-sm text-secondary">
                {selectedProduct.description ?? "Premium access to analyst views, neighbourhood context, and compare workflows."}
              </p>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <Card className="space-y-2">
                <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-disabled">
                  Billing
                </p>
                <p className="text-base font-semibold text-primary">
                  {formatInterval(selectedProduct)}
                </p>
              </Card>
              <Card className="space-y-2">
                <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-disabled">
                  Capabilities
                </p>
                <p className="text-base font-semibold text-primary">
                  {selectedProduct.capability_keys.length}
                </p>
              </Card>
            </div>

            <div className="space-y-3">
              <h3 className="text-lg font-semibold text-primary">Included in this plan</h3>
              <div className="grid gap-3 sm:grid-cols-2">
                {selectedProduct.capability_keys.map((capabilityKey) => (
                  <Card key={capabilityKey} className="border-brand/20 bg-brand/5">
                    <p className="text-sm font-medium text-primary">
                      {getCapabilityDisplayLabel(capabilityKey)}
                    </p>
                  </Card>
                ))}
              </div>
            </div>
          </Panel>

          <Panel className="space-y-4">
            <h2 className="text-xl font-semibold text-primary">Checkout</h2>

            {session.state !== "authenticated" ? (
              <>
                <p className="text-sm text-secondary">
                  Sign in first so Civitas can attach checkout and entitlement state to the correct account.
                </p>
                <Button asChild>
                  <Link
                    to={paths.signIn(
                      paths.upgrade({
                        capability: requestedCapability ?? undefined,
                        product: selectedProduct.code,
                        returnTo,
                      })
                    )}
                  >
                    Sign in to continue
                  </Link>
                </Button>
              </>
            ) : access?.accountAccessState === "premium" ? (
              <>
                <p className="text-sm text-secondary">
                  Premium is already active on this account. Use the billing portal for subscription changes or payment updates.
                </p>
                <div className="flex flex-wrap gap-3">
                  <Button type="button" onClick={() => void handleOpenBillingPortal()} disabled={isOpeningPortal}>
                    {isOpeningPortal ? "Opening billing portal..." : "Manage billing"}
                  </Button>
                  <Button asChild variant="secondary">
                    <Link to={returnTo ?? paths.account}>Continue</Link>
                  </Button>
                </div>
              </>
            ) : (
              <>
                <p className="text-sm text-secondary">
                  Checkout is hosted by the payment provider, but Civitas only unlocks Premium after backend reconciliation updates your entitlements.
                </p>
                <Button
                  type="button"
                  onClick={() => void handleStartCheckout()}
                  disabled={isStartingCheckout}
                >
                  {isStartingCheckout ? "Starting checkout..." : heroCopy.buttonLabel}
                </Button>
              </>
            )}
          </Panel>
        </div>
      ) : null}
    </PageContainer>
  );
}
