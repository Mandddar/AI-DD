import { api } from './client';

export interface FinancialDataset {
  id: string;
  project_id: string;
  name: string;
  source_filename: string;
  chart_of_accounts: string | null;
  period_from: string | null;
  period_to: string | null;
  created_at: string;
}

export interface LineItem {
  id: string;
  account_number: string | null;
  account_name: string;
  category: string | null;
  period: string;
  amount: number;
  currency: string;
}

export interface VarianceAnalysis {
  id: string;
  project_id: string;
  analysis_type: string;
  results: any[];
  generated_queries: any[] | null;
  created_at: string;
}

export interface FinancialKPI {
  name: string;
  value: number;
  unit: string;
  category: string;
}

export interface PeriodEntry {
  period: string;
  value: number;
  change_pct?: number;
}

export interface PeriodComparison {
  metric: string;
  periods: PeriodEntry[];
}

export interface ChartData {
  variance: { name: string; current: number; prior: number; variance_pct: number; flag: string }[];
  trends: PeriodComparison[];
}

export const finance = {
  uploadData: (projectId: string, file: File) => {
    const form = new FormData();
    form.append('file', file);
    return api.post<FinancialDataset>(`/projects/${projectId}/finance/upload`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(r => r.data);
  },

  listDatasets: (projectId: string) =>
    api.get<FinancialDataset[]>(`/projects/${projectId}/finance/datasets`).then(r => r.data),

  getLineItems: (projectId: string, datasetId: string) =>
    api.get<LineItem[]>(`/projects/${projectId}/finance/datasets/${datasetId}/items`).then(r => r.data),

  getVarianceAnalyses: (projectId: string) =>
    api.get<VarianceAnalysis[]>(`/projects/${projectId}/finance/variance`).then(r => r.data),

  runVarianceAnalysis: (projectId: string, type: string = 'internal_historical') =>
    api.post<VarianceAnalysis>(`/projects/${projectId}/finance/variance/run?analysis_type=${type}`).then(r => r.data),

  getKPIs: (projectId: string) =>
    api.get<FinancialKPI[]>(`/projects/${projectId}/finance/kpis`).then(r => r.data),

  getPeriodComparison: (projectId: string) =>
    api.get<PeriodComparison[]>(`/projects/${projectId}/finance/period-comparison`).then(r => r.data),

  getChartData: (projectId: string) =>
    api.get<ChartData>(`/projects/${projectId}/finance/chart-data`).then(r => r.data),
};
