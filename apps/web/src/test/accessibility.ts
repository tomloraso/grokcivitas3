import { axe } from "vitest-axe";

export async function runA11yAudit(container: HTMLElement) {
  // JSDOM cannot evaluate color-contrast reliably; deterministic token contrast
  // budgets are enforced by src/styles/contrast.test.ts.
  return axe(container, {
    rules: {
      "color-contrast": { enabled: false }
    }
  });
}
