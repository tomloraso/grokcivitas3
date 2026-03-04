import { createBrowserRouter, type RouteObject } from "react-router-dom";

import { RootLayout } from "./RootLayout";
import { SchoolsSearchFeature } from "../features/schools-search/SchoolsSearchFeature";
import { SchoolProfileFeature } from "../features/school-profile/SchoolProfileFeature";
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
        element: <SchoolProfileFeature />
      },
      {
        path: "*",
        element: <NotFoundPage />
      }
    ]
  }
];

export const router = createBrowserRouter(routes);
