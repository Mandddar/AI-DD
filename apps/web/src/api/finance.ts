import { api } from "./client";

export type DatasetStatus = "processing" | "completed" | "failed";
export type ChartOfAccounts = "skr03" | "skr04" | "custom";
export type VarianceSignificance = "normal" | "notable" | "significant" | "critical";
export type FinanceQueryStatus = "pending_review" | "approved" | "rejected";

export interface Dataset {
  id: string;
  project_id: string;
  chart_of_accounts: ChartOfAccounts;
  source_filename: string;
  imported_by: string;
  period_start: string | null;
  period_end: string | null;
  row_count: number;
  status: DatasetStatus;
  error_message: string | null;
  created_at: string;
}

export interface CategoryPeriodAmount {
  standardized_category: string;
  period: string;
  amount: number;
}

export interface PeriodSummary {
  period: string;
  total_revenue: number;
  total_costs: number;
  ebitda: number;
}

export interface FinancialSummary {
  periods: string[];
  categories: string[];
  data: CategoryPeriodAmount[];
  period_summaries: PeriodSummary[];
}

export interface VarianceResult {
  id: string;
  analysis_type: "mom" | "yoy" | "trend" | "benchmark";
  standardized_category: string | null;
  period: string;
  comparison_period: string | null;
  variance_pct: number | null;
  variance_abs: number | null;
  significance: VarianceSignificance;
  ai_commentary: string | null;
  created_at: string;
}

export interface TrendData {
  category: string;
  direction: "growing" | "declining" | "stable";
  avg_growth_rate: number | null;
  data_points: { period: string; amount: number }[];
}

export interface BenchmarkComparison {
  metric_name: string;
  company_value: number;
  industry_value: number;
  delta: number;
  source: string;
  year: number;
}

export interface FinanceQuery {
  id: string;
  project_id: string;
  variance_id: string | null;
  question: string;
  context: string | null;
  status: FinanceQueryStatus;
  approved_by: string | null;
  reviewed_at: string | null;
  created_at: string;
}

export const financeApi = {
  // Import
  importData: (projectId: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api.post<Dataset>(`/projects/${projectId}/finance/import`, form, {
      headers: { "Content-Type": "multipart/form-data" },
    }).then((r) => r.data);
  },

  appendData: (projectId: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api.post<Dataset>(`/projects/${projectId}/finance/append`, form, {
      headers: { "Content-Type": "multipart/form-data" },
    }).then((r) => r.data);
  },

  // Datasets
  listDatasets: (projectId: string) =>
    api.get<Dataset[]>(`/projects/${projectId}/finance/datasets`).then((r) => r.data),

  deleteDataset: (projectId: string, datasetId: string) =>
    api.delete(`/projects/${projectId}/finance/datasets/${datasetId}`),

  // Data
  getSummary: (projectId: string) =>
    api.get<FinancialSummary>(`/projects/${projectId}/finance/data/summary`).then((r) => r.data),

  getPeriods: (projectId: string) =>
    api.get<string[]>(`/projects/${projectId}/finance/data/periods`).then((r) => r.data),

  // Analysis
  runAnalysis: (projectId: string) =>
    api.post(`/projects/${projectId}/finance/analysis/run`).then((r) => r.data),

  getInternalVariance: (projectId: string, params?: { analysis_type?: string; category?: string }) =>
    api.get<VarianceResult[]>(`/projects/${projectId}/finance/analysis/internal`, { params }).then((r) => r.data),

  getExternalBenchmarks: (projectId: string) =>
    api.get<BenchmarkComparison[]>(`/projects/${projectId}/finance/analysis/external`).then((r) => r.data),

  getTrend: (projectId: string, category: string) =>
    api.get<TrendData>(`/projects/${projectId}/finance/analysis/trends/${category}`).then((r) => r.data),

  // Queries (HITL)
  listQueries: (projectId: string) =>
    api.get<FinanceQuery[]>(`/projects/${projectId}/finance/queries`).then((r) => r.data),

  reviewQuery: (projectId: string, queryId: string, status: "approved" | "rejected") =>
    api.patch<FinanceQuery>(`/projects/${projectId}/finance/queries/${queryId}`, { status }).then((r) => r.data),
};
