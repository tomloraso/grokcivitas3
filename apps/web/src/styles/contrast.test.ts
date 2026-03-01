import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

type Rgb = { r: number; g: number; b: number };

function parseVariables(cssText: string): Record<string, string> {
  const variables: Record<string, string> = {};
  const variablePattern = /--([a-z0-9-]+)\s*:\s*([^;]+);/gi;
  let match: RegExpExecArray | null = variablePattern.exec(cssText);
  while (match) {
    variables[`--${match[1]}`] = match[2].trim();
    match = variablePattern.exec(cssText);
  }
  return variables;
}

function resolveToken(tokenName: string, variables: Record<string, string>, seen = new Set<string>()): string {
  const value = variables[tokenName];
  if (!value) {
    throw new Error(`Missing token value for ${tokenName}`);
  }

  const varMatch = value.match(/^var\((--[a-z0-9-]+)\)$/i);
  if (!varMatch) {
    return value;
  }

  const nextToken = varMatch[1];
  if (seen.has(nextToken)) {
    throw new Error(`Circular token reference at ${nextToken}`);
  }

  seen.add(nextToken);
  return resolveToken(nextToken, variables, seen);
}

function hexToRgb(hexColor: string): Rgb {
  const hex = hexColor.replace("#", "").trim();
  if (hex.length === 3) {
    return {
      r: Number.parseInt(hex[0] + hex[0], 16),
      g: Number.parseInt(hex[1] + hex[1], 16),
      b: Number.parseInt(hex[2] + hex[2], 16)
    };
  }

  if (hex.length === 6) {
    return {
      r: Number.parseInt(hex.slice(0, 2), 16),
      g: Number.parseInt(hex.slice(2, 4), 16),
      b: Number.parseInt(hex.slice(4, 6), 16)
    };
  }

  throw new Error(`Unsupported hex color format: ${hexColor}`);
}

function parseRgbFunction(rgbText: string): Rgb {
  const match = rgbText.match(
    /^rgba?\(\s*([0-9]{1,3})[\s,]+([0-9]{1,3})[\s,]+([0-9]{1,3})(?:[\s,/]+([0-9.]+))?\s*\)$/i
  );
  if (!match) {
    throw new Error(`Unsupported rgb format: ${rgbText}`);
  }
  return {
    r: Number.parseInt(match[1], 10),
    g: Number.parseInt(match[2], 10),
    b: Number.parseInt(match[3], 10)
  };
}

function parseColor(colorValue: string): Rgb {
  const normalized = colorValue.trim().toLowerCase();
  if (normalized.startsWith("#")) {
    return hexToRgb(normalized);
  }
  if (normalized.startsWith("rgb")) {
    return parseRgbFunction(normalized);
  }
  throw new Error(`Unsupported color format: ${colorValue}`);
}

function toLinear(component: number): number {
  const srgb = component / 255;
  if (srgb <= 0.04045) {
    return srgb / 12.92;
  }
  return ((srgb + 0.055) / 1.055) ** 2.4;
}

function relativeLuminance(color: Rgb): number {
  return 0.2126 * toLinear(color.r) + 0.7152 * toLinear(color.g) + 0.0722 * toLinear(color.b);
}

function contrastRatio(foreground: Rgb, background: Rgb): number {
  const foregroundLum = relativeLuminance(foreground);
  const backgroundLum = relativeLuminance(background);
  const lighter = Math.max(foregroundLum, backgroundLum);
  const darker = Math.min(foregroundLum, backgroundLum);
  return (lighter + 0.05) / (darker + 0.05);
}

const variables = parseVariables(readFileSync(path.resolve(process.cwd(), "src/styles/tokens.css"), "utf8"));

function expectContrast(foregroundToken: string, backgroundToken: string, minimumRatio: number): void {
  const foreground = parseColor(resolveToken(foregroundToken, variables));
  const background = parseColor(resolveToken(backgroundToken, variables));
  expect(contrastRatio(foreground, background)).toBeGreaterThanOrEqual(minimumRatio);
}

describe("theme contrast tokens", () => {
  it("meets WCAG AA contrast requirements for text and controls", () => {
    expectContrast("--color-text-primary", "--color-bg-canvas", 4.5);
    expectContrast("--color-text-primary", "--color-bg-surface", 4.5);
    expectContrast("--color-text-secondary", "--color-bg-surface", 4.5);
    expectContrast("--color-text-secondary", "--color-bg-canvas", 4.5);
    expectContrast("--color-action-primary", "--color-bg-surface", 3);

    const white = parseColor("#ffffff");
    const buttonBackground = parseColor(resolveToken("--color-action-primary-solid", variables));
    expect(contrastRatio(white, buttonBackground)).toBeGreaterThanOrEqual(4.5);
  });

  it("keeps semantic state colors legible on surfaces", () => {
    expectContrast("--color-state-success", "--color-bg-surface", 3);
    expectContrast("--color-state-warning", "--color-bg-surface", 3);
    expectContrast("--color-state-danger", "--color-bg-surface", 3);
    expectContrast("--color-state-info", "--color-bg-surface", 3);
  });
});
