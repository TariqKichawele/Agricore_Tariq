export type UserRole = "admin" | "field_hand" | "auditor";

export type User = {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  farm_id: string | null;
  is_active: boolean;
};

export type LoginResponse = {
  access_token: string;
  token_type: string;
  user: User;
};

export type EquipmentStatus = "Idle" | "In-Use" | "Maintenance" | "Retired";
export type JobStatus = "Pending" | "In-Progress" | "Completed" | "Failed";
export type JobPriority = "Low" | "Medium" | "Critical";

export type Farm = {
  id: string;
  name: string;
  location_region: string;
  capacity: number;
  supervisor_id: string | null;
  created_at: string;
};

export type Equipment = {
  id: string;
  serial_number: string;
  model: string;
  status: EquipmentStatus;
  fuel_level: number;
  facility_id: string;
  assigned_operator_id: string | null;
  created_at: string;
};

export type FieldJob = {
  id: string;
  title: string;
  priority: JobPriority;
  status: JobStatus;
  equipment_id: string;
  operator_id: string;
  created_at: string;
};

export type LowFuelResponse = {
  count: number;
  items: Equipment[];
};

export type CoLocationItem = {
  equipment_id: string;
  serial_number: string;
  model: string;
  facility_id: string;
  assigned_operator_id: string;
  operator_farm_id: string | null;
};

export type CoLocationResponse = {
  count: number;
  items: CoLocationItem[];
};

export type ReliabilityRow = {
  model: string;
  completed: number;
  failed: number;
};

export type ReliabilityResponse = {
  models: ReliabilityRow[];
};

export type MaintenanceFlagItem = {
  farm: Farm;
  unit_count: number;
  maintenance_count: number;
  maintenance_ratio: number;
};

export type MaintenanceFlagsResponse = {
  count: number;
  farms: MaintenanceFlagItem[];
};

export type ReportingLinesResponse = {
  count: number;
  field_hands: User[];
};

export type ServiceReport = {
  id: string;
  field_job_id: string;
  file_url: string;
  notes: string | null;
  created_at: string;
  download_expires_in: number;
};

export type AuditLog = {
  id: string;
  actor_id: string | null;
  action: string;
  entity_type: string;
  entity_id: string | null;
  details: Record<string, unknown> | null;
  created_at: string;
};

export const EQUIPMENT_STATUSES: EquipmentStatus[] = ["Idle", "In-Use", "Maintenance", "Retired"];
export const JOB_STATUSES: JobStatus[] = ["Pending", "In-Progress", "Completed", "Failed"];
export const JOB_PRIORITIES: JobPriority[] = ["Low", "Medium", "Critical"];
export const USER_ROLES: UserRole[] = ["admin", "field_hand", "auditor"];
