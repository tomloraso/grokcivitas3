import js from "@eslint/js";
import globals from "globals";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import tseslint from "typescript-eslint";

export default tseslint.config(
  {
    ignores: ["dist", "coverage", "playwright-report", "test-results"]
  },
  {
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    files: ["**/*.{ts,tsx}"],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser
    },
    plugins: {
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      "react-refresh/only-export-components": [
        "warn",
        { "allowConstantExport": true }
      ]
    }
  },
  {
    files: ["src/**/*.{ts,tsx}"],
    rules: {
      "no-restricted-globals": [
        "error",
        {
          name: "fetch",
          message: "Call backend APIs through typed modules under src/api/*."
        }
      ],
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            {
              group: ["**/api/openapi.json"],
              message: "openapi.json is only for generating TypeScript API contracts."
            },
            {
              group: ["**/generated-types", "**/generated-types.ts"],
              message: "Import API contract aliases from src/api/types.ts."
            }
          ]
        }
      ]
    }
  },
  {
    files: [
      "src/api/**/*.{ts,tsx}",
      "src/**/*.test.{ts,tsx}",
      "src/**/*.spec.{ts,tsx}",
      "src/test-setup.ts"
    ],
    rules: {
      "no-restricted-globals": "off"
    }
  },
  {
    files: ["src/api/types.ts"],
    rules: {
      "no-restricted-imports": "off"
    }
  }
);
