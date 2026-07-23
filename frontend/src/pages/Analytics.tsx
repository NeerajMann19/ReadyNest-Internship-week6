import React, { useEffect, useState } from 'react';
import { useSession } from '../context/SessionContext';
import { apiClient } from '../api/client';
import type { Analytics as AnalyticsType } from '../types';
import { RefreshCw, AlertTriangle, Table, Grid, AlertCircle, HelpCircle, BarChart3, Lightbulb } from 'lucide-react';
import InsightsSection from '../components/analytics/InsightsSection';


/**
 * Analytics Page Component
 * Displays Numeric and Categorical Summary Statistics, Pairwise Pearson Correlation Matrix,
 * IQR Outlier Detection, and Missing Values Breakdown for the active dataset.
 */
export const Analytics: React.FC = () => {
  const { sessionId, dataset } = useSession();
  const [analytics, setAnalytics] = useState<AnalyticsType | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'summary' | 'correlation' | 'outliers' | 'missing' | 'insights'>('insights');


  useEffect(() => {
    if (!sessionId || !dataset) return;

    const fetchAnalytics = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await apiClient.get<AnalyticsType>(`/dataset/${sessionId}/analytics`);
        setAnalytics(response.data);
      } catch (err: any) {
        const msg = err.response?.data?.message || err.message || 'Failed to fetch dataset analytics.';
        setError(msg);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, [sessionId, dataset]);

  if (!dataset || !sessionId) {
    return (
      <div className="p-8 text-center border border-dashed border-border rounded-xl bg-surface space-y-2">
        <h2 className="text-xl font-semibold text-text-primary">No Dataset Uploaded</h2>
        <p className="text-text-secondary text-sm">
          No dataset uploaded — upload one from Overview to view analytics.
        </p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="p-12 border border-border rounded-xl bg-surface flex flex-col items-center justify-center space-y-3">
        <RefreshCw className="w-8 h-8 text-primary animate-spin" />
        <p className="text-sm font-medium text-text-primary">Computing Dataset Analytics...</p>
        <p className="text-xs text-text-muted">Analyzing numeric summaries, correlation matrix, and outliers</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-danger/10 border border-danger/30 rounded-xl space-y-3">
        <div className="flex items-center gap-3 text-danger">
          <AlertTriangle className="w-6 h-6 shrink-0" />
          <h3 className="text-lg font-semibold">Analytics Error</h3>
        </div>
        <p className="text-sm text-text-secondary">{error}</p>
        <button
          type="button"
          onClick={() => window.location.reload()}
          className="px-4 py-2 text-xs font-medium text-white bg-danger hover:bg-danger/90 rounded-lg transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  const numericSummary = analytics?.summary?.numeric_summary || {};
  const categoricalSummary = analytics?.summary?.categorical_summary || {};
  const missingSummary: Array<{ column: string; missing_count: number; missing_percentage: number }> =
    analytics?.summary?.missing_summary || [];
  const correlations = analytics?.correlations || { available: false, columns: [], matrix: {} };
  const outliers = analytics?.outliers || { available: false, columns: [] };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-text-primary">Analytics</h1>
          <p className="text-text-secondary text-sm">
            Active Dataset: <span className="font-mono text-text-primary">{dataset.filename}</span> ({dataset.rows.toLocaleString()} rows, {dataset.columns} columns)
          </p>
        </div>
      </div>

      {/* Analytics Tabs Header */}
      <div className="border-b border-border flex gap-4">
        <button
          type="button"
          onClick={() => setActiveTab('insights')}
          className={`pb-3 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === 'insights'
              ? 'border-primary text-primary font-semibold'
              : 'border-transparent text-text-secondary hover:text-text-primary'
          }`}
        >
          <Lightbulb className="w-4 h-4 text-primary" />
          <span>AI Business Insights</span>
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('summary')}
          className={`pb-3 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === 'summary'
              ? 'border-primary text-primary'
              : 'border-transparent text-text-secondary hover:text-text-primary'
          }`}
        >
          <Table className="w-4 h-4" />
          <span>Summary Statistics</span>
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('correlation')}
          className={`pb-3 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === 'correlation'
              ? 'border-primary text-primary'
              : 'border-transparent text-text-secondary hover:text-text-primary'
          }`}
        >
          <Grid className="w-4 h-4" />
          <span>Correlation Matrix</span>
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('outliers')}
          className={`pb-3 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === 'outliers'
              ? 'border-primary text-primary'
              : 'border-transparent text-text-secondary hover:text-text-primary'
          }`}
        >
          <AlertCircle className="w-4 h-4" />
          <span>Outlier Detection</span>
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('missing')}
          className={`pb-3 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === 'missing'
              ? 'border-primary text-primary'
              : 'border-transparent text-text-secondary hover:text-text-primary'
          }`}
        >
          <HelpCircle className="w-4 h-4" />
          <span>Missing Values</span>
        </button>
      </div>

      {/* Tab 0: AI Business Insights */}
      {activeTab === 'insights' && (
        <InsightsSection sessionId={sessionId} />
      )}


      {/* Tab 1: Summary Statistics */}
      {activeTab === 'summary' && (
        <div className="space-y-6">
          {/* Numeric Summary Table */}
          <div className="bg-card border border-border rounded-xl p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-text-primary">Numeric Summary Statistics</h3>
                <p className="text-xs text-text-secondary">
                  Calculated exclusively for schema-inferred numeric columns
                </p>
              </div>
            </div>

            {Object.keys(numericSummary).length === 0 ? (
              <p className="text-sm text-text-muted py-4">No numeric columns found in dataset.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="border-b border-border text-text-muted uppercase tracking-wider bg-surface">
                    <tr>
                      <th className="py-3 px-4">Column Name</th>
                      <th className="py-3 px-4 text-right">Mean</th>
                      <th className="py-3 px-4 text-right">Median</th>
                      <th className="py-3 px-4 text-right">Min</th>
                      <th className="py-3 px-4 text-right">Max</th>
                      <th className="py-3 px-4 text-right">Std Dev</th>
                      <th className="py-3 px-4 text-right">Variance</th>
                      <th className="py-3 px-4 text-right">Q1 (25%)</th>
                      <th className="py-3 px-4 text-right">Q3 (75%)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {Object.entries(numericSummary).map(([col, stats]: [string, any]) => (
                      <tr key={col} className="hover:bg-elevated/40">
                        <td className="py-3 px-4 font-mono font-medium text-text-primary">{col}</td>
                        <td className="py-3 px-4 text-right font-mono">{stats.mean ?? 'N/A'}</td>
                        <td className="py-3 px-4 text-right font-mono">{stats.median ?? 'N/A'}</td>
                        <td className="py-3 px-4 text-right font-mono">{stats.min ?? 'N/A'}</td>
                        <td className="py-3 px-4 text-right font-mono">{stats.max ?? 'N/A'}</td>
                        <td className="py-3 px-4 text-right font-mono">{stats.std_dev ?? 'N/A'}</td>
                        <td className="py-3 px-4 text-right font-mono">{stats.variance ?? 'N/A'}</td>
                        <td className="py-3 px-4 text-right font-mono">{stats.q1 ?? 'N/A'}</td>
                        <td className="py-3 px-4 text-right font-mono">{stats.q3 ?? 'N/A'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Categorical Summary Grid */}
          <div className="bg-card border border-border rounded-xl p-6 space-y-4">
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Categorical Column Summary</h3>
              <p className="text-xs text-text-secondary">
                Top 5 distinct value frequencies for string/categorical columns
              </p>
            </div>

            {Object.keys(categoricalSummary).length === 0 ? (
              <p className="text-sm text-text-muted py-4">No categorical columns found in dataset.</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {Object.entries(categoricalSummary).map(([col, data]: [string, any]) => (
                  <div key={col} className="p-4 bg-surface border border-border rounded-lg space-y-3">
                    <div className="flex items-center justify-between border-b border-border pb-2">
                      <span className="font-mono text-sm font-semibold text-text-primary">{col}</span>
                      <span className="text-[10px] font-mono bg-elevated px-2 py-0.5 rounded border border-border text-text-secondary">
                        {data.unique_count} unique
                      </span>
                    </div>

                    <div className="space-y-1.5 text-xs">
                      {data.top_values.length === 0 ? (
                        <p className="text-text-muted">No values available</p>
                      ) : (
                        data.top_values.map((tv: { value: string; count: number }, idx: number) => (
                          <div key={idx} className="flex items-center justify-between font-mono">
                            <span className="truncate max-w-[160px] text-text-secondary" title={tv.value}>
                              {tv.value}
                            </span>
                            <span className="text-text-primary font-medium">{tv.count.toLocaleString()}</span>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 2: Pearson Correlation Matrix */}
      {activeTab === 'correlation' && (
        <div className="bg-card border border-border rounded-xl p-6 space-y-4">
          <div>
            <h3 className="text-lg font-semibold text-text-primary">Pairwise Pearson Correlation Matrix</h3>
            <p className="text-xs text-text-secondary">
              Pairwise deletion (excludes missing values per pair). Column order strictly preserves original CSV schema order.
            </p>
          </div>

          {!correlations.available ? (
            <div className="p-6 bg-surface border border-border rounded-lg text-center space-y-2">
              <BarChart3 className="w-8 h-8 text-text-muted mx-auto" />
              <p className="text-sm font-medium text-text-primary">Correlation Unavailable</p>
              <p className="text-xs text-text-secondary">{correlations.reason || 'At least 2 numeric columns required.'}</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-center border-collapse">
                <thead>
                  <tr>
                    <th className="p-2 border border-border bg-surface font-mono font-medium text-text-secondary text-left">
                      Feature
                    </th>
                    {correlations.columns.map((colName: string) => (
                      <th
                        key={colName}
                        className="p-2 border border-border bg-surface font-mono font-medium text-text-primary max-w-[100px] truncate"
                        title={colName}
                      >
                        {colName}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {correlations.columns.map((rCol: string) => (
                    <tr key={rCol}>
                      <td className="p-2 border border-border bg-surface font-mono font-medium text-text-primary text-left truncate max-w-[140px]" title={rCol}>
                        {rCol}
                      </td>
                      {correlations.columns.map((cCol: string) => {
                        const val: number | null = correlations.matrix[rCol]?.[cCol];
                        let bgColor = 'bg-surface';
                        let textColor = 'text-text-primary';

                        if (val !== null && val !== undefined) {
                          if (rCol === cCol) {
                            bgColor = 'bg-primary/20';
                            textColor = 'text-primary font-bold';
                          } else if (val > 0.7) {
                            bgColor = 'bg-emerald-500/20';
                            textColor = 'text-emerald-400 font-semibold';
                          } else if (val > 0.3) {
                            bgColor = 'bg-emerald-500/10';
                            textColor = 'text-emerald-300';
                          } else if (val < -0.7) {
                            bgColor = 'bg-rose-500/20';
                            textColor = 'text-rose-400 font-semibold';
                          } else if (val < -0.3) {
                            bgColor = 'bg-rose-500/10';
                            textColor = 'text-rose-300';
                          }
                        }

                        return (
                          <td
                            key={cCol}
                            className={`p-3 border border-border font-mono transition-colors ${bgColor} ${textColor}`}
                          >
                            {val !== null && val !== undefined ? val.toFixed(3) : 'N/A'}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Outlier Detection (IQR Method) */}
      {activeTab === 'outliers' && (
        <div className="bg-card border border-border rounded-xl p-6 space-y-4">
          <div>
            <h3 className="text-lg font-semibold text-text-primary">IQR-based Outlier Detection</h3>
            <p className="text-xs text-text-secondary">
              Detected using 1.5 × IQR boundaries. Outlier indices represent 0-based positional row indices in the cleaned dataset.
            </p>
          </div>

          {!outliers.available ? (
            <div className="p-6 bg-surface border border-border rounded-lg text-center space-y-2">
              <AlertCircle className="w-8 h-8 text-text-muted mx-auto" />
              <p className="text-sm font-medium text-text-primary">Outlier Detection Unavailable</p>
              <p className="text-xs text-text-secondary">{outliers.reason || 'Insufficient dataset rows for outlier analysis.'}</p>
            </div>
          ) : (
            <div className="space-y-4">
              {outliers.columns.map((item: any) => (
                <div key={item.name} className="p-4 bg-surface border border-border rounded-lg space-y-3">
                  <div className="flex items-center justify-between flex-wrap gap-2">
                    <span className="font-mono text-sm font-semibold text-text-primary">{item.name}</span>
                    <div className="flex items-center gap-3 text-xs font-mono">
                      <span className="bg-elevated px-2 py-1 rounded border border-border text-text-secondary">
                        Lower Bound: {item.lower_bound ?? 'N/A'}
                      </span>
                      <span className="bg-elevated px-2 py-1 rounded border border-border text-text-secondary">
                        Upper Bound: {item.upper_bound ?? 'N/A'}
                      </span>
                      <span className={`px-2 py-1 rounded font-semibold ${item.outlier_indices.length > 0 ? 'bg-danger/20 text-danger' : 'bg-success/20 text-success'}`}>
                        {item.outlier_indices.length} outliers detected
                      </span>
                    </div>
                  </div>

                  {item.outlier_indices.length > 0 && (
                    <div className="text-xs space-y-1">
                      <span className="text-text-muted font-medium">Outlier Positional Indices (Row Pos in Cleaned Data):</span>
                      <p className="font-mono text-text-secondary bg-elevated/50 p-2 rounded border border-border break-all max-h-24 overflow-y-auto">
                        {item.outlier_indices.join(', ')}
                      </p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 4: Missing Values Breakdown */}
      {activeTab === 'missing' && (
        <div className="bg-card border border-border rounded-xl p-6 space-y-4">
          <div>
            <h3 className="text-lg font-semibold text-text-primary">Missing Values Summary</h3>
            <p className="text-xs text-text-secondary">
              Count and percentage of missing values for all columns across the dataset
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-border text-text-muted uppercase tracking-wider bg-surface">
                <tr>
                  <th className="py-3 px-4">Column Name</th>
                  <th className="py-3 px-4 text-right">Missing Count</th>
                  <th className="py-3 px-4 text-right">Missing Percentage</th>
                  <th className="py-3 px-4">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {missingSummary.map((item) => (
                  <tr key={item.column} className="hover:bg-elevated/40">
                    <td className="py-3 px-4 font-mono font-medium text-text-primary">{item.column}</td>
                    <td className="py-3 px-4 text-right font-mono text-text-secondary">{item.missing_count}</td>
                    <td className="py-3 px-4 text-right font-mono text-text-secondary">{item.missing_percentage}%</td>
                    <td className="py-3 px-4">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase ${
                          item.missing_count === 0
                            ? 'bg-success/20 text-success'
                            : item.missing_percentage > 20
                            ? 'bg-danger/20 text-danger'
                            : 'bg-warning/20 text-warning'
                        }`}
                      >
                        {item.missing_count === 0 ? 'Complete' : item.missing_percentage > 20 ? 'High Missing' : 'Partial Missing'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default Analytics;

