import type { FormEvent } from "react";

import { Button } from "../../../components/ui/Button";
import { Field } from "../../../components/ui/Field";
import { Panel } from "../../../components/ui/Card";
import { Select } from "../../../components/ui/Select";
import { TextInput } from "../../../components/ui/TextInput";

const RADIUS_OPTIONS = [
  { value: "1", label: "1 mile" },
  { value: "3", label: "3 miles" },
  { value: "5", label: "5 miles" },
  { value: "10", label: "10 miles" },
  { value: "25", label: "25 miles" }
];

interface SearchFormProps {
  postcode: string;
  radius: string;
  postcodeError: string | null;
  isSubmitting: boolean;
  onPostcodeChange: (value: string) => void;
  onRadiusChange: (value: string) => void;
  onSubmit: () => Promise<void>;
}

export function SearchForm({
  postcode,
  radius,
  postcodeError,
  isSubmitting,
  onPostcodeChange,
  onRadiusChange,
  onSubmit
}: SearchFormProps): JSX.Element {
  const handleSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    await onSubmit();
  };

  return (
    <Panel>
      <form
        aria-label="Schools search form"
        className="grid gap-4 md:grid-cols-[minmax(0,1fr)_180px_auto] md:items-end"
        onSubmit={handleSubmit}
      >
        <Field
          label="Postcode"
          htmlFor="postcode"
          helperText="Use a full UK postcode format."
          errorText={postcodeError ?? undefined}
          required
        >
          <TextInput
            id="postcode"
            name="postcode"
            autoComplete="postal-code"
            value={postcode}
            onChange={(event) => onPostcodeChange(event.target.value)}
            aria-invalid={postcodeError ? "true" : "false"}
            aria-describedby={postcodeError ? "postcode-error" : "postcode-helper"}
            placeholder="SW1A 1AA"
          />
        </Field>
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
        <Button type="submit" className="w-full md:w-auto" disabled={isSubmitting}>
          {isSubmitting ? "Searching..." : "Search schools"}
        </Button>
      </form>
    </Panel>
  );
}
