export type UserRole = "admin" | "lead_advisor" | "team_advisor" | "seller" | "buyer";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  disclaimer_accepted: boolean;
  totp_enabled: boolean;
  created_at: string;
}

export type DealType = "share_deal" | "asset_deal";
export type LegalForm = "GmbH" | "AG" | "KG" | "Other";
export type ProjectStatus = "active" | "on_hold" | "completed" | "archived";

export interface Project {
  id: string;
  name: string;
  company_name: string;
  legal_form: LegalForm;
  industry: string | null;
  employee_count: string | null;
  revenue_size: string | null;
  registered_office: string | null;
  deal_type: DealType;
  status: ProjectStatus;
  description: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
}
