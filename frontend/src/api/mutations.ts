import type {
  AuditLog,
  Equipment,
  EquipmentStatus,
  Farm,
  FieldJob,
  JobPriority,
  JobStatus,
  ServiceReport,
  User,
  UserRole,
} from "../types";
import { api } from "./client";

const PAGE = { skip: 0, limit: 200 };

export async function createFarm(payload: {
  name: string;
  location_region: string;
  capacity: number;
  supervisor_id: string | null;
}): Promise<Farm> {
  const { data } = await api.post<Farm>("/farms", payload);
  return data;
}

export async function updateFarm(
  id: string,
  payload: Partial<{ name: string; location_region: string; capacity: number; supervisor_id: string | null }>,
): Promise<Farm> {
  const { data } = await api.patch<Farm>(`/farms/${id}`, payload);
  return data;
}

export async function deleteFarm(id: string): Promise<void> {
  await api.delete(`/farms/${id}`);
}

export async function createUser(payload: {
  email: string;
  password: string;
  full_name: string;
  role: UserRole;
  farm_id: string | null;
  is_active: boolean;
}): Promise<User> {
  const { data } = await api.post<User>("/users", payload);
  return data;
}

export async function updateUser(
  id: string,
  payload: {
    email?: string;
    password?: string;
    full_name?: string;
    role?: UserRole;
    farm_id?: string | null;
    is_active?: boolean;
  },
): Promise<User> {
  const { data } = await api.patch<User>(`/users/${id}`, payload);
  return data;
}

export async function deleteUser(id: string): Promise<void> {
  await api.delete(`/users/${id}`);
}

export async function createEquipment(payload: {
  serial_number: string;
  model: string;
  status: EquipmentStatus;
  fuel_level: number;
  facility_id: string;
  assigned_operator_id: string | null;
}): Promise<Equipment> {
  const { data } = await api.post<Equipment>("/equipment", payload);
  return data;
}

export async function updateEquipment(
  id: string,
  payload: Partial<{
    serial_number: string;
    model: string;
    status: EquipmentStatus;
    fuel_level: number;
    facility_id: string;
    assigned_operator_id: string | null;
  }>,
): Promise<Equipment> {
  const { data } = await api.patch<Equipment>(`/equipment/${id}`, payload);
  return data;
}

export async function deleteEquipment(id: string): Promise<void> {
  await api.delete(`/equipment/${id}`);
}

export async function createFieldJob(payload: {
  title: string;
  priority: JobPriority;
  status: JobStatus;
  equipment_id: string;
  operator_id: string;
}): Promise<FieldJob> {
  const { data } = await api.post<FieldJob>("/field-jobs", payload);
  return data;
}

export async function updateFieldJob(
  id: string,
  payload: Partial<{
    title: string;
    priority: JobPriority;
    status: JobStatus;
    equipment_id: string;
    operator_id: string;
  }>,
): Promise<FieldJob> {
  const { data } = await api.patch<FieldJob>(`/field-jobs/${id}`, payload);
  return data;
}

export async function deleteFieldJob(id: string): Promise<void> {
  await api.delete(`/field-jobs/${id}`);
}

export async function listReports(jobId: string): Promise<ServiceReport[]> {
  const { data } = await api.get<ServiceReport[]>(`/field-jobs/${jobId}/reports`, { params: PAGE });
  return data;
}

export async function uploadReport(jobId: string, file: File, notes: string): Promise<ServiceReport> {
  const body = new FormData();
  body.append("file", file);
  if (notes.trim()) {
    body.append("notes", notes.trim());
  }
  const { data } = await api.post<ServiceReport>(`/field-jobs/${jobId}/reports`, body);
  return data;
}

export async function listAuditLogs(q: string): Promise<AuditLog[]> {
  const { data } = await api.get<AuditLog[]>("/audit-logs", {
    params: { ...PAGE, ...(q.trim() ? { q: q.trim() } : {}) },
  });
  return data;
}
