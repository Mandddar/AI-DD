import { api } from "./client";
import type { User } from "../types";

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  requires_2fa: boolean;
}

export interface TotpSetupResponse {
  secret: string;
  provisioning_uri: string;
}

export const authApi = {
  register: (data: { email: string; password: string; full_name: string; role?: string }) =>
    api.post<User>("/auth/register", data).then((r) => r.data),

  login: (data: { email: string; password: string; totp_code?: string }) =>
    api.post<TokenResponse>("/auth/login", data).then((r) => r.data),

  me: () => api.get<User>("/auth/me").then((r) => r.data),

  logout: () => api.post("/auth/logout").then((r) => r.data),

  acceptDisclaimer: () =>
    api.post<User>("/auth/disclaimer/accept", { accepted: true }).then((r) => r.data),

  // 2FA / TOTP
  setup2fa: () =>
    api.post<TotpSetupResponse>("/auth/2fa/setup").then((r) => r.data),

  verify2fa: (code: string) =>
    api.post<User>("/auth/2fa/verify", { code }).then((r) => r.data),

  disable2fa: (password: string) =>
    api.post<User>("/auth/2fa/disable", { password }).then((r) => r.data),

  // Password
  changePassword: (current_password: string, new_password: string) =>
    api.post("/auth/change-password", { current_password, new_password }).then((r) => r.data),

  requestPasswordReset: (email: string) =>
    api.post("/auth/password-reset/request", { email }).then((r) => r.data),

  confirmPasswordReset: (token: string, new_password: string) =>
    api.post("/auth/password-reset/confirm", { token, new_password }).then((r) => r.data),

  // Settings
  updateProfile: (data: { full_name?: string; email?: string }) =>
    api.patch<User>("/auth/settings", data).then((r) => r.data),

  // GDPR account deletion
  deleteAccount: (password: string) =>
    api.post("/auth/account/delete", { password, confirmation: "DELETE MY ACCOUNT" }).then((r) => r.data),
};
