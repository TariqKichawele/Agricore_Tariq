import type { Farm, User } from "./types";

export function farmName(farms: Farm[], id: string | null | undefined): string {
  if (!id) {
    return "—";
  }
  return farms.find((farm) => farm.id === id)?.name ?? id.slice(0, 8);
}

export function userName(users: User[], id: string | null | undefined): string {
  if (!id) {
    return "Unassigned";
  }
  return users.find((user) => user.id === id)?.full_name ?? id.slice(0, 8);
}

export function supervisorsFromFarms(farms: Farm[], users: User[]): User[] {
  const ids = [...new Set(farms.map((farm) => farm.supervisor_id).filter((id): id is string => Boolean(id)))];
  return ids.map((id) => users.find((user) => user.id === id) ?? null).filter((user): user is User => user !== null);
}
