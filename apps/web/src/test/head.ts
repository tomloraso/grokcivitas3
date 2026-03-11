import { waitFor } from "@testing-library/react";

import { buildDocumentTitle } from "../shared/config/site";

export async function expectDocumentTitle(title: string): Promise<void> {
  await waitFor(() => {
    expect(document.title).toBe(buildDocumentTitle(title));
  });
}

export async function expectHeadAttribute(
  selector: string,
  attribute: string,
  value: string
): Promise<void> {
  await waitFor(() => {
    expect(document.head.querySelector(selector)).toHaveAttribute(attribute, value);
  });
}
