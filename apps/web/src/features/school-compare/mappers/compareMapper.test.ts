import { describe, expect, it } from "vitest";

import type { CompareSelectionItem } from "../../../shared/context/CompareSelectionContext";
import { mapCompareToVM } from "./compareMapper";
import { COMPARE_RESPONSE } from "../testData";

describe("mapCompareToVM", () => {
  it("maps school headers, profile return state, and benchmark labels", () => {
    const selectionByUrn = new Map<string, CompareSelectionItem>([
      [
        "100001",
        {
          urn: "100001",
          name: "Primary Example",
          phase: "Primary",
          type: "Community school",
          postcode: "SW1A 1AA",
          distanceMiles: 1.234,
          source: "search",
        },
      ],
    ]);

    const vm = mapCompareToVM(
      COMPARE_RESPONSE,
      selectionByUrn,
      "/compare?urns=100001,200002"
    );

    expect(vm.schools[0]).toMatchObject({
      urn: "100001",
      name: "Primary Example",
      distanceLabel: "1.23 mi",
      profileHref: "/schools/100001",
      profileState: {
        fromCompare: {
          href: "/compare?urns=100001,200002",
        },
      },
    });

    expect(vm.sections[1].rows[0].cells[0]).toMatchObject({
      displayValue: "20.1%",
      metaLabel: "2024/25",
      benchmarkLabel: "England 18.0% | Westminster 19.2%",
      availability: "available",
      isMuted: false,
    });
  });

  it("keeps unsupported and unavailable cells explicit", () => {
    const vm = mapCompareToVM(COMPARE_RESPONSE, new Map(), "/compare?urns=100001,200002");
    const unsupportedCell = vm.sections[1].rows[0].cells[1];
    const unavailableCell = vm.sections[2].rows[0].cells[1];
    const inspectionDateCell = vm.sections[0].rows[1].cells[0];

    expect(unsupportedCell.displayValue).toBe("Not applicable");
    expect(unsupportedCell.availability).toBe("unsupported");
    expect(unsupportedCell.isMuted).toBe(true);
    expect(unavailableCell.displayValue).toBe("Unavailable");
    expect(unavailableCell.detailLabel).toBe(
      "The source currently has limited coverage for this information."
    );
    expect(inspectionDateCell.displayValue).toBe("10 Oct 2025");
    expect(inspectionDateCell.metaLabel).toBeNull();
  });

  it("formats date rows from snapshot_date instead of reparsing value text", () => {
    const response = structuredClone(COMPARE_RESPONSE);
    response.sections[0].rows[1].cells[0].value_text = "10 Oct 2025";
    response.sections[0].rows[1].cells[0].snapshot_date = "2025-10-10";

    const vm = mapCompareToVM(response, new Map(), "/compare?urns=100001,200002");

    expect(vm.sections[0].rows[1].cells[0].displayValue).toBe("10 Oct 2025");
  });
});
