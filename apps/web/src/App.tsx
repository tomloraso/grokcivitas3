import { HelmetProvider } from "react-helmet-async";
import { RouterProvider } from "react-router-dom";

import { ThemeProvider } from "./app/providers/ThemeProvider";
import { router } from "./app/routes";
import { AuthProvider } from "./features/auth/AuthProvider";

export function App(): JSX.Element {
  return (
    <HelmetProvider>
      <ThemeProvider>
        <AuthProvider>
          <RouterProvider router={router} />
        </AuthProvider>
      </ThemeProvider>
    </HelmetProvider>
  );
}
