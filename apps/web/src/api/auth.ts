import { api } from "./client";
import type { User } from "../types";

export const authApi = {
  register: (data: { email: string; password: string; full_name: string; role?: string }) =>
    api.post<User>("/auth/register", data).then((r) => r.data),

  login: (data: { email: string; password: string }) =>
    api.post<{ access_token: string; refresh_token: string; token_type: string }>("/auth/login", data).then((r) => r.data),

  me: () => api.get<User>("/auth/me").then((r) => r.data),

  acceptDisclaimer: () =>
    api.post<User>("/auth/disclaimer/accept", { accepted: true }).then((r) => r.data),
};
