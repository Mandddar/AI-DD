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

export const finance = {
  uploadData: (projectId: string, file: File) => {
    const form = new FormData();
    form.append('file', file);
    return api.post<FinancialDataset>(`/projects/${projectId}/finance/upload`, form).then(r => r.data);
  },

  listDatasets: (projectId: string) =>
    api.get<FinancialDataset[]>(`/projects/${projectId}/finance/datasets`).then(r => r.data),

  getLineItems: (projectId: string, datasetId: string) =>
    api.get<LineItem[]>(`/projects/${projectId}/finance/datasets/${datasetId}/items`).then(r => r.data),

  getVarianceAnalyses: (projectId: string) =>
    api.get<VarianceAnalysis[]>(`/projects/${projectId}/finance/variance`).then(r => r.data),

  runVarianceAnalysis: (projectId: string, type: string = 'internal_historical') =>
    api.post<VarianceAnalysis>(`/projects/${projectId}/finance/variance/run?analysis_type=${type}`).then(r => r.data),
};
