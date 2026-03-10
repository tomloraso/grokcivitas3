/**
 * @deprecated SHIM — this file re-exports from the canonical location.
 *
 * Import directly from `components/ui/stat-card` in new code:
 *
 *   import { StatCard } from "../../../components/ui/stat-card";
 *   import type { BenchmarkSlot } from "../../../components/ui/stat-card";
 *
 * This shim exists so that existing section components (AcademicPerformanceSection,
 * AttendanceBehaviourSection, DemographicsAndTrendsPanel, WorkforceLeadershipSection)
 * continue to work without modification. Do not add new code here.
 */
export { StatCard } from "../ui/stat-card";
export type { BenchmarkSlot } from "../ui/stat-card";
