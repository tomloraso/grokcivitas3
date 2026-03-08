import type { FormEvent } from "react";

import { Button } from "../../../components/ui/Button";
import { Field } from "../../../components/ui/Field";
import { Panel } from "../../../components/ui/Card";
import { Select } from "../../../components/ui/Select";
import { TextInput } from "../../../components/ui/TextInput";
import type { SearchMode } from "../types";

const RADIUS_OPTIONS = [
  { value: "1", label: "1 mile" },
  { value: "3", label: "3 miles" },
  { value: "5", label: "5 miles" },
  { value: "10", label: "10 miles" }
];

interface SearchFormProps {
  searchText: string;
  radius: string;
  searchError: string | null;
  searchMode: SearchMode;
  isSubmitting: boolean;
  onSearchTextChange: (value: string) => void;
  onRadiusChange: (value: string) => void;
  onSubmit: () => Promise<void>;
}

export function SearchForm({
  searchText,
  radius,
  searchError,
  searchMode,
  isSubmitting,
  onSearchTextChange,
  onRadiusChange,
  onSubmit
}: SearchFormProps): JSX.Element {
  const handleSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    await onSubmit();
  };

  const isPostcode = searchMode === "postcode";
  const trimmed = searchText.trim();
  const helperText = isPostcode
    ? "Postcode search mode."
    : trimmed.length === 0
      ? "Use a full UK postcode or type a school name."
      : trimmed.length < 3
        ? "Type at least 3 characters for school name search."
        : "School name search mode.";

  return (
    <Panel>
      <form
        aria-label="Schools search form"
        className="flex flex-col gap-4"
        onSubmit={handleSubmit}
      >
        <Field
          label="Search"
          htmlFor="search-text"
          helperText={helperText}
          errorText={searchError ?? undefined}
          required
        >
          <TextInput
            id="search-text"
            name="search-text"
            autoComplete="off"
            value={searchText}
            onChange={(event) => onSearchTextChange(event.target.value)}
            aria-invalid={searchError ? "true" : "false"}
            aria-describedby={searchError ? "search-text-error" : "search-text-helper"}
            placeholder="Search by postcode or school name..."
          />
        </Field>
        <div className={`grid items-end gap-3 ${isPostcode ? "grid-cols-[1fr_auto]" : ""}`}>
          {isPostcode && (
            <Field label="Radius" htmlFor="radius-select">
              <Select
                id="radius-select"
                name="radius"
                ariaLabel="Search radius"
                value={radius}
                onValueChange={onRadiusChange}
                options={RADIUS_OPTIONS}
              />
            </Field>
          )}
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Searching..." : "Search schools"}
          </Button>
        </div>
      </form>
    </Panel>
  );
}
