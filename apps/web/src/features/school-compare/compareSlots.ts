import type { CompareSchoolColumnVM } from "./types";

export type CompareSlot = CompareSchoolColumnVM | null;

const TOTAL_SLOTS = 4;

export function padToSlots(
  schools: CompareSchoolColumnVM[],
  totalSlots: number = TOTAL_SLOTS
): CompareSlot[] {
  const slots: CompareSlot[] = [...schools];
  while (slots.length < totalSlots) {
    slots.push(null);
  }
  return slots.slice(0, totalSlots);
}
