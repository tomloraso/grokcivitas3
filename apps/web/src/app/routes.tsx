import { lazy, Suspense } from "react";
import { createBrowserRouter, type RouteObject } from "react-router-dom";

import { PageContainer } from "../components/layout/PageContainer";
import { LoadingSkeleton } from "../components/ui/LoadingSkeleton";
import { SignInFeature } from "../features/auth/SignInFeature";
import { RootLayout } from "./RootLayout";
import { SchoolsSearchFeature } from "../features/schools-search/SchoolsSearchFeature";
import { NotFoundPage } from "../pages/NotFoundPage";

const SchoolProfileFeature = lazy(async () => {
  const module = await import("../features/school-profile/SchoolProfileFeature");
  return { default: module.SchoolProfileFeature };
});

const SchoolCompareFeature = lazy(async () => {
  const module = await import("../features/school-compare/SchoolCompareFeature");
  return { default: module.SchoolCompareFeature };
});

const AccountFeature = lazy(async () => {
  const module = await import("../features/premium-access/AccountFeature");
  return { default: module.AccountFeature };
});

const UpgradeFeature = lazy(async () => {
  const module = await import("../features/premium-access/UpgradeFeature");
  return { default: module.UpgradeFeature };
});

const routes: RouteObject[] = [
  {
    element: <RootLayout />,
    children: [
      {
        index: true,
        element: <SchoolsSearchFeature />
      },
      {
        path: "sign-in",
        element: <SignInFeature />
      },
      {
        path: "account",
        element: (
          <Suspense
            fallback={
              <PageContainer>
                <div className="space-y-6">
                  <LoadingSkeleton lines={4} />
                  <LoadingSkeleton lines={6} />
                </div>
              </PageContainer>
            }
          >
            <AccountFeature />
          </Suspense>
        )
      },
      {
        path: "account/upgrade",
        element: (
          <Suspense
            fallback={
              <PageContainer>
                <div className="space-y-6">
                  <LoadingSkeleton lines={4} />
                  <LoadingSkeleton lines={6} />
                </div>
              </PageContainer>
            }
          >
            <UpgradeFeature />
          </Suspense>
        )
      },
      {
        path: "compare",
        element: (
          <Suspense
            fallback={
              <PageContainer>
                <div className="space-y-6">
                  <LoadingSkeleton lines={4} />
                  <LoadingSkeleton lines={6} />
                  <LoadingSkeleton lines={8} />
                </div>
              </PageContainer>
            }
          >
            <SchoolCompareFeature />
          </Suspense>
        )
      },
      {
        path: "schools/:urn",
        element: (
          <Suspense
            fallback={
              <PageContainer>
                <div className="space-y-6">
                  <LoadingSkeleton lines={4} />
                  <LoadingSkeleton lines={6} />
                  <LoadingSkeleton lines={4} />
                </div>
              </PageContainer>
            }
          >
            <SchoolProfileFeature />
          </Suspense>
        )
      },
      {
        path: "*",
        element: <NotFoundPage />
      }
    ]
  }
];

export const router = createBrowserRouter(routes);
