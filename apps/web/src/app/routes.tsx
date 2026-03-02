import { createBrowserRouter, type RouteObject } from "react-router-dom";

import { RootLayout } from "./RootLayout";
import { SchoolsSearchFeature } from "../features/schools-search/SchoolsSearchFeature";
import { NotFoundPage } from "../pages/NotFoundPage";

const routes: RouteObject[] = [
  {
    element: <RootLayout />,
    children: [
      {
        index: true,
        element: <SchoolsSearchFeature />
      },
      {
        path: "schools/:urn",
        /**
         * Placeholder for the school profile page (Phase 1G).
         * For now, renders a minimal profile shell so routes are wired.
         */
        lazy: async () => {
          const { SchoolProfilePlaceholder } = await import(
            "../features/school-profile/SchoolProfilePlaceholder"
          );
          return { Component: SchoolProfilePlaceholder };
        }
      },
      {
        path: "*",
        element: <NotFoundPage />
      }
    ]
  }
];

export const router = createBrowserRouter(routes);
