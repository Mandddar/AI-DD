import { api } from "./client";
import type { User } from "../types";

export interface TOTPSetup {
  secret: string;
  otpauth_uri: string;
}

export const authApi = {
  register: (data: { email: string; password: string; full_name: string; role?: string }) =>
    api.post<User>("/auth/register", data).then((r) => r.data),

  login: (data: { email: string; password: string }) =>
    api.post<{ access_token: string; refresh_token: string; token_type: string }>("/auth/login", data).then((r) => r.data),

  me: () => api.get<User>("/auth/me").then((r) => r.data),

  acceptDisclaimer: () =>
    api.post<User>("/auth/disclaimer/accept", { accepted: true }).then((r) => r.data),

  logout: () => api.post("/auth/logout").catch(() => {}),

  changePassword: (data: { current_password: string; new_password: string }) =>
    api.patch("/auth/me/password", data),

  deleteAccount: () => api.delete("/auth/me"),

  // Password reset
  requestReset: (email: string) =>
    api.post("/auth/password-reset/request", { email }).then((r) => r.data),

  confirmReset: (data: { token: string; new_password: string }) =>
    api.post("/auth/password-reset/confirm", data),

  // 2FA
  setup2FA: () => api.post<TOTPSetup>("/auth/2fa/setup").then((r) => r.data),

  verify2FA: (code: string) =>
    api.post("/auth/2fa/verify", { code }).then((r) => r.data),

  disable2FA: () => api.delete("/auth/2fa"),
};
