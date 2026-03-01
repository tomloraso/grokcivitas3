import { useMemo, useState } from "react";

import { AppShell } from "./components/layout/AppShell";
import { PageContainer } from "./components/layout/PageContainer";
import { SplitPaneLayout } from "./components/layout/SplitPaneLayout";
import { MapPanel, type MapMarker } from "./components/maps/MapPanel";
import { Button } from "./components/ui/Button";
import { Panel } from "./components/ui/Card";
import { EmptyState } from "./components/ui/EmptyState";
import { ErrorState } from "./components/ui/ErrorState";
import { Field } from "./components/ui/Field";
import { LoadingSkeleton } from "./components/ui/LoadingSkeleton";
import { ResultCard } from "./components/ui/ResultCard";
import { Select } from "./components/ui/Select";
import { TextInput } from "./components/ui/TextInput";

type DemoState = "results" | "loading" | "empty" | "error";

interface DemoSchool {
  urn: string;
  name: string;
  type: string;
  phase: string;
  postcode: string;
  lat: number;
  lng: number;
  distanceMiles: number;
}

const demoResults: DemoSchool[] = [
  {
    urn: "100001",
    name: "Camden Bridge Primary School",
    type: "Community school",
    phase: "Primary",
    postcode: "NW1 8NH",
    lat: 51.5424,
    lng: -0.1418,
    distanceMiles: 0.52
  },
  {
    urn: "100002",
    name: "Alden Civic Academy",
    type: "Academy sponsor led",
    phase: "Secondary",
    postcode: "NW1 5TX",
    lat: 51.5357,
    lng: -0.1299,
    distanceMiles: 1.12
  },
  {
    urn: "100003",
    name: "Regent Square School",
    type: "Foundation school",
    phase: "All-through",
    postcode: "N1C 4AB",
    lat: 51.5335,
    lng: -0.1235,
    distanceMiles: 1.48
  }
];

export function App(): JSX.Element {
  const [postcode, setPostcode] = useState("NW1 6XE");
  const [radius, setRadius] = useState("5");
  const [state, setState] = useState<DemoState>("empty");

  const mapCenter = useMemo(
    () => ({
      lat: 51.5362,
      lng: -0.1357
    }),
    []
  );

  const markers = useMemo<MapMarker[]>(
    () =>
      demoResults.map((school) => ({
        id: school.urn,
        lat: school.lat,
        lng: school.lng,
        label: school.name,
        distanceMiles: school.distanceMiles
      })),
    []
  );

  return (
    <AppShell>
      <PageContainer className="space-y-6">
        <header className="panel-surface rounded-xl p-5 sm:p-7">
          <p className="font-mono text-xs uppercase tracking-[0.14em] text-secondary">
            Phase 0D1 Foundations
          </p>
          <h1 className="mt-2 text-3xl leading-tight sm:text-4xl">Civitas Schools Discovery</h1>
          <p className="mt-3 max-w-2xl text-sm text-secondary sm:text-base">
            Shared theme tokens, reusable primitives, and map-ready layout baseline for postcode
            search delivery.
          </p>
        </header>

        <Panel className="space-y-4">
          <div className="grid gap-4 md:grid-cols-[minmax(0,1fr)_180px_170px_auto] md:items-end">
            <Field label="Postcode" htmlFor="postcode" helperText="Use full UK postcode format">
              <TextInput
                id="postcode"
                name="postcode"
                value={postcode}
                autoComplete="postal-code"
                onChange={(event) => setPostcode(event.target.value)}
                aria-label="Postcode"
              />
            </Field>
            <Field label="Radius" htmlFor="radius-select">
              <Select
                id="radius-select"
                ariaLabel="Search radius"
                name="radius"
                value={radius}
                onValueChange={setRadius}
                options={[
                  { value: "1", label: "1 mile" },
                  { value: "3", label: "3 miles" },
                  { value: "5", label: "5 miles" },
                  { value: "10", label: "10 miles" },
                  { value: "25", label: "25 miles" }
                ]}
              />
            </Field>
            <Field label="Preview state">
              <Select
                ariaLabel="Preview state"
                value={state}
                onValueChange={(value) => setState(value as DemoState)}
                options={[
                  { value: "results", label: "Results" },
                  { value: "loading", label: "Loading" },
                  { value: "empty", label: "Empty" },
                  { value: "error", label: "Error" }
                ]}
              />
            </Field>
            <Button type="button" className="w-full md:w-auto">
              Search schools
            </Button>
          </div>
        </Panel>

        <SplitPaneLayout
          listPane={
            state === "loading" ? (
              <LoadingSkeleton lines={6} />
            ) : state === "empty" ? (
              <EmptyState
                title="No schools found"
                description="Try a wider radius or a nearby postcode to broaden the search area."
              />
            ) : state === "error" ? (
              <ErrorState
                title="Search temporarily unavailable"
                description="The postcode resolver did not respond. Retry once connectivity is restored."
                onRetry={() => setState("results")}
              />
            ) : (
              <>
                {demoResults.map((school) => (
                  <ResultCard
                    key={school.urn}
                    name={school.name}
                    type={school.type}
                    phase={school.phase}
                    postcode={school.postcode}
                    distanceMiles={school.distanceMiles}
                  />
                ))}
              </>
            )
          }
          mapPane={
            <MapPanel
              center={state === "results" ? mapCenter : null}
              markers={state === "results" ? markers : []}
              title="Nearby schools map"
            />
          }
        />
      </PageContainer>
    </AppShell>
  );
}
