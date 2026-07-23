/**
 * Canonical Domain Types for Analytics Studio Frontend
 * 
 * NOTE: Field names match backend/models.py exactly using snake_case.
 * Do not convert to camelCase — backend contracts must remain byte-identical.
 */

export interface ColumnSchema {
  name: string;
  data_type: string;
  missing_count: number;
  sample_values: any[];
}

export interface QualityReport {
  missing_values_count: number;
  duplicate_rows_count: number;
  quality_score: number;
  data_type_issues: string[];
}

export interface Dataset {
  id: string;
  filename: string;
  rows: number;
  columns: number;
  schema: ColumnSchema[];
  quality: QualityReport;
}

export interface Analytics {
  summary: Record<string, any>;
  correlations: Record<string, any>;
  charts: Array<Record<string, any>>;
  outliers: Record<string, any>;
}

export interface Prediction {
  available: boolean;
  reason?: string | null;
  target_column?: string | null;
  problem_type: string;
  model_type: string;
  metrics: Record<string, number>;
  stratified?: boolean | null;
  label_mapping?: Record<string, string> | null;
  features_used: string[];
  row_counts: {
    total_cleaned?: number;
    train_count?: number;
    test_count?: number;
  };
  predictions: Array<Record<string, any>>;
}

export interface Insight {
  id: string;
  title: string;
  description: string;
  severity: string;
  category: string;
  evidence: Record<string, any>;
  confidence: number;
}

export interface CounterAnalysis {
  risks: string[];
  trade_offs: string[];
  alternative_scenarios: string[];
  mitigations: string[];
}

export interface Decision {
  scenario_name: string;
  expected_impact: Record<string, any>;
  confidence: number;
  assumptions: string[];
  recommendation: string;
  counter_analysis: CounterAnalysis;
}

export interface Report {
  sections: Array<Record<string, any>>;
  generated_at: string;
  pdf_path: string;
}

export interface AdvisorResponse {
  explanation: string;
}

export interface SessionState {
  dataset?: Dataset | null;
  analytics?: Analytics | null;
  prediction?: Prediction | null;
  insights?: Insight[];
  decision?: Decision | null;
  report?: Report | null;
  cleaned_dataframe?: any | null;
}
