import { lazy, Suspense } from "react";
import { createBrowserRouter, type RouteObject } from "react-router-dom";

import { PageContainer } from "../components/layout/PageContainer";
import { LoadingSkeleton } from "../components/ui/LoadingSkeleton";
import { SignInFeature } from "../features/auth/SignInFeature";
import { RootLayout } from "./RootLayout";
import { SchoolsSearchFeature } from "../features/schools-search/SchoolsSearchFeature";
import { AboutPage } from "../pages/AboutPage";
import { AccessibilityPage } from "../pages/AccessibilityPage";
import { ContactPage } from "../pages/ContactPage";
import { DataSourcesPage } from "../pages/DataSourcesPage";
import { NotFoundPage } from "../pages/NotFoundPage";
import { PrivacyPage } from "../pages/PrivacyPage";
import { TermsPage } from "../pages/TermsPage";

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

const FavouritesLibraryFeature = lazy(async () => {
  const module = await import("../features/favourites/FavouritesLibraryFeature");
  return { default: module.FavouritesLibraryFeature };
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
        path: "about",
        element: <AboutPage />
      },
      {
        path: "data-sources",
        element: <DataSourcesPage />
      },
      {
        path: "contact",
        element: <ContactPage />
      },
      {
        path: "privacy",
        element: <PrivacyPage />
      },
      {
        path: "terms",
        element: <TermsPage />
      },
      {
        path: "accessibility",
        element: <AccessibilityPage />
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
        path: "account/favourites",
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
            <FavouritesLibraryFeature />
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
