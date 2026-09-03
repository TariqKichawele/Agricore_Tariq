import type { UserRole } from "./types";

export type NavItem = {
  to: string;
  label: string;
  roles: UserRole[];
};

export const NAV_ITEMS: NavItem[] = [
  { to: "/", label: "Dashboard", roles: ["admin", "field_hand", "auditor"] },
  { to: "/farms", label: "Farms", roles: ["admin", "auditor"] },
  { to: "/equipment", label: "Equipment", roles: ["admin", "field_hand", "auditor"] },
  { to: "/jobs", label: "Field Jobs", roles: ["admin", "field_hand", "auditor"] },
  { to: "/users", label: "Users", roles: ["admin", "auditor"] },
  { to: "/audit-logs", label: "Audit Logs", roles: ["admin", "auditor"] },
];

export function navForRole(role: UserRole): NavItem[] {
  return NAV_ITEMS.filter((item) => item.roles.includes(role));
}

export function canAccessPath(role: UserRole, pathname: string): boolean {
  const item = NAV_ITEMS.find((entry) =>
    entry.to === "/" ? pathname === "/" : pathname === entry.to || pathname.startsWith(`${entry.to}/`),
  );
  if (!item) {
    return true;
  }
  return item.roles.includes(role);
}

export const ROLE_LABEL: Record<UserRole, string> = {
  admin: "Farm Operations Admin",
  field_hand: "Field Hand",
  auditor: "Auditor",
};
