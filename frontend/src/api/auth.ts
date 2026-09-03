import type { LoginResponse, User } from "../types";
import { api } from "./client";

export async function loginRequest(email: string, password: string): Promise<LoginResponse> {
  const { data } = await api.post<LoginResponse>("/auth/login", { email, password });
  return data;
}

export async function fetchCurrentUser(): Promise<User> {
  const { data } = await api.get<User>("/auth/me");
  return data;
}
