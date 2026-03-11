import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { DataSourcesPage } from "./DataSourcesPage";
import { expectDocumentTitle } from "../test/head";
import { renderWithProviders } from "../test/render";

describe("DataSourcesPage", () => {
  it("renders the data source table and metadata", async () => {
    renderWithProviders(<DataSourcesPage />);

    expect(
      screen.getByRole("heading", { name: "Data Sources and Methodology" })
    ).toBeInTheDocument();
    expect(screen.getByText("Get Information About Schools (GIAS)")).toBeInTheDocument();
    expect(screen.getByText("Academies Accounts Return")).toBeInTheDocument();
    expect(screen.getByText("Key stage 4 destination measures")).toBeInTheDocument();
    expect(screen.getByText("16 to 18 destination measures")).toBeInTheDocument();
    await expectDocumentTitle("Data Sources and Methodology");
  });
});
