import type {
  CoLocationResponse,
  Equipment,
  Farm,
  FieldJob,
  LowFuelResponse,
  MaintenanceFlagsResponse,
  ReliabilityResponse,
  ReportingLinesResponse,
  User,
} from "../types";
import { api } from "./client";
import { swallowForbidden } from "./http";

const PAGE = { skip: 0, limit: 200 };

export async function listEquipment(): Promise<Equipment[]> {
  const { data } = await api.get<Equipment[]>("/equipment", { params: PAGE });
  return data;
}

export async function listFieldJobs(): Promise<FieldJob[]> {
  const { data } = await api.get<FieldJob[]>("/field-jobs", { params: PAGE });
  return data;
}

export async function listFarms(): Promise<Farm[]> {
  const { data } = await api.get<Farm[]>("/farms", { params: PAGE });
  return data;
}

export async function listUsers(): Promise<User[]> {
  const { data } = await api.get<User[]>("/users", { params: PAGE });
  return data;
}

export async function optionalLookups(): Promise<{ farms: Farm[]; users: User[] }> {
  const [farms, users] = await Promise.all([
    swallowForbidden(listFarms, []),
    swallowForbidden(listUsers, []),
  ]);
  return { farms, users };
}

export async function fetchLowFuel(): Promise<LowFuelResponse> {
  const { data } = await api.get<LowFuelResponse>("/analytics/low-fuel");
  return data;
}

export async function fetchCoLocation(): Promise<CoLocationResponse> {
  const { data } = await api.get<CoLocationResponse>("/analytics/co-location");
  return data;
}

export async function fetchReliability(): Promise<ReliabilityResponse> {
  const { data } = await api.get<ReliabilityResponse>("/analytics/reliability");
  return data;
}

export async function fetchMaintenanceFlags(): Promise<MaintenanceFlagsResponse> {
  const { data } = await api.get<MaintenanceFlagsResponse>("/analytics/maintenance-flags");
  return data;
}

export async function fetchReportingLines(supervisorId: string): Promise<ReportingLinesResponse> {
  const { data } = await api.get<ReportingLinesResponse>("/analytics/reporting-lines", {
    params: { supervisor_id: supervisorId },
  });
  return data;
}
