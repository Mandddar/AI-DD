/**
 * Role-based permission hook for the AI DD platform.
 *
 * Role hierarchy (from spec §4.1):
 *   Admin           → Full access to all features, projects, and settings
 *   Lead Advisor    → Creates projects, controls process, approves external communication
 *   Team Advisor    → Works on assigned workstreams within approved scope
 *   Seller          → Uploads documents, answers queries, views only their own areas
 *   Buyer/Investor  → Read-only access to approved documents and finalized reports
 */
import { useAuthStore } from "../store/auth";
import type { UserRole } from "../types";

/** Roles that can manage projects (trigger analysis, generate reports, approve plans) */
const ADVISOR_ROLES: UserRole[] = ["admin", "lead_advisor", "team_advisor"];

/** Roles that can contribute (upload docs, submit data) */
const CONTRIBUTOR_ROLES: UserRole[] = ["admin", "lead_advisor", "team_advisor", "seller"];

/** Roles that can create new projects */
const PROJECT_CREATOR_ROLES: UserRole[] = ["admin", "lead_advisor", "team_advisor"];

export interface Permissions {
  role: UserRole | null;

  /** Can create new projects/deals */
  canCreateProject: boolean;

  /** Can manage project settings, add members */
  canManageProject: boolean;

  /** Can upload documents */
  canUploadDocuments: boolean;

  /** Can delete documents */
  canDeleteDocuments: boolean;

  /** Can trigger AI analysis runs */
  canRunAnalysis: boolean;

  /** Can review/approve/reject findings */
  canReviewFindings: boolean;

  /** Can access planning module (submit data, advance phases, approve) */
  canManagePlanning: boolean;

  /** Can view planning data (read-only) */
  canViewPlanning: boolean;

  /** Can run financial variance analysis */
  canRunFinanceAnalysis: boolean;

  /** Can upload financial data */
  canUploadFinanceData: boolean;

  /** Can generate, edit, finalize reports */
  canManageReports: boolean;

  /** Can view reports (buyers only see finalized) */
  canViewReports: boolean;

  /** Whether this role can only see finalized reports */
  onlyFinalizedReports: boolean;

  /** Can view audit trail */
  canViewAudit: boolean;

  /** Can update request list items (answer queries) */
  canUpdateRequestList: boolean;

  /** Is an advisor role (admin, lead, team) */
  isAdvisor: boolean;

  /** Is a read-only role */
  isReadOnly: boolean;
}

export function usePermissions(): Permissions {
  const user = useAuthStore((s) => s.user);
  const role = user?.role ?? null;

  if (!role) {
    return {
      role: null,
      canCreateProject: false,
      canManageProject: false,
      canUploadDocuments: false,
      canDeleteDocuments: false,
      canRunAnalysis: false,
      canReviewFindings: false,
      canManagePlanning: false,
      canViewPlanning: false,
      canRunFinanceAnalysis: false,
      canUploadFinanceData: false,
      canManageReports: false,
      canViewReports: false,
      onlyFinalizedReports: false,
      canViewAudit: false,
      canUpdateRequestList: false,
      isAdvisor: false,
      isReadOnly: true,
    };
  }

  const isAdvisor = ADVISOR_ROLES.includes(role);
  const isContributor = CONTRIBUTOR_ROLES.includes(role);
  const isBuyer = role === "buyer";
  const isSeller = role === "seller";

  return {
    role,

    canCreateProject: PROJECT_CREATOR_ROLES.includes(role),
    canManageProject: isAdvisor,
    canUploadDocuments: isContributor,
    canDeleteDocuments: isAdvisor,
    canRunAnalysis: isAdvisor,
    canReviewFindings: isAdvisor,
    canManagePlanning: isAdvisor,
    canViewPlanning: !isBuyer,          // sellers can view planning (request list)
    canRunFinanceAnalysis: isAdvisor,
    canUploadFinanceData: isContributor,
    canManageReports: isAdvisor,
    canViewReports: true,               // all members can view (buyer restricted to finalized)
    onlyFinalizedReports: isBuyer,
    canViewAudit: isAdvisor,
    canUpdateRequestList: isContributor, // advisors + sellers can answer queries
    isAdvisor,
    isReadOnly: isBuyer,
  };
}
