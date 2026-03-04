import { RouterProvider } from "react-router-dom";

import { ThemeProvider } from "./app/providers/ThemeProvider";
import { router } from "./app/routes";

export function App(): JSX.Element {
  return (
    <ThemeProvider>
      <RouterProvider router={router} />
    </ThemeProvider>
  );
}
