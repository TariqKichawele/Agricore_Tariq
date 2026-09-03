import { Chip, type ChipProps } from "@mui/material";
import type { EquipmentStatus, JobPriority, JobStatus } from "../types";

const EQUIPMENT_COLOR: Record<EquipmentStatus, ChipProps["color"]> = {
  Idle: "default",
  "In-Use": "success",
  Maintenance: "warning",
  Retired: "default",
};

const JOB_COLOR: Record<JobStatus, ChipProps["color"]> = {
  Pending: "default",
  "In-Progress": "info",
  Completed: "success",
  Failed: "error",
};

const PRIORITY_COLOR: Record<JobPriority, ChipProps["color"]> = {
  Low: "default",
  Medium: "info",
  Critical: "error",
};

type StatusChipProps = {
  value: EquipmentStatus | JobStatus | JobPriority;
  kind: "equipment" | "job" | "priority";
};

export function StatusChip({ value, kind }: StatusChipProps) {
  const color =
    kind === "equipment"
      ? EQUIPMENT_COLOR[value as EquipmentStatus]
      : kind === "job"
        ? JOB_COLOR[value as JobStatus]
        : PRIORITY_COLOR[value as JobPriority];
  return <Chip size="small" label={value} color={color} variant={color === "default" ? "outlined" : "filled"} />;
}
