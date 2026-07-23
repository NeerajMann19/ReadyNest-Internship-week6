import React, { useState } from 'react';
import { useSession } from '../context/SessionContext';
import { apiClient } from '../api/client';
import type { Prediction } from '../types';
import { Play, RefreshCw, AlertTriangle, Cpu, Layers, ListChecks, CheckCircle2, BarChart2 } from 'lucide-react';

/**
 * Predictions Page Component
 * Allows user to select a target column and evaluate baseline ML models
 * (LinearRegression for regression, LogisticRegression for classification).
 */
export const Predictions: React.FC = () => {
  const { sessionId, dataset } = useSession();
  const [selectedTarget, setSelectedTarget] = useState<string>('');
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  if (!dataset || !sessionId) {
    return (
      <div className="p-8 text-center border border-dashed border-border rounded-xl bg-surface space-y-2">
        <h2 className="text-xl font-semibold text-text-primary">No Dataset Uploaded</h2>
        <p className="text-text-secondary text-sm">
          No dataset uploaded — upload one from Overview to run predictions.
        </p>
      </div>
    );
  }

  const handleRunPrediction = async () => {
    if (!selectedTarget) return;

    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.get<Prediction>(
        `/dataset/${sessionId}/prediction?target_column=${encodeURIComponent(selectedTarget)}`
      );
      setPrediction(response.data);
    } catch (err: any) {
      const msg = err.response?.data?.message || err.message || 'Failed to evaluate prediction model.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-text-primary">Predictions</h1>
        <p className="text-text-secondary text-sm">
          Evaluate baseline Machine Learning models for <span className="font-mono text-text-primary">{dataset.filename}</span>
        </p>
      </div>

      {/* Target Column Selector Card */}
      <div className="p-6 bg-card border border-border rounded-xl space-y-4">
        <div>
          <h3 className="text-base font-semibold text-text-primary">Select Target Column</h3>
          <p className="text-xs text-text-secondary">
            Choose the column you wish to predict. Task type (Regression vs Classification) is detected automatically.
          </p>
        </div>

        <div className="flex items-center gap-4 flex-wrap">
          <select
            value={selectedTarget}
            onChange={(e) => setSelectedTarget(e.target.value)}
            className="px-4 py-2 text-sm bg-surface border border-border rounded-lg text-text-primary font-mono focus:outline-none focus:border-primary min-w-[240px]"
          >
            <option value="">-- Select Target Column --</option>
            {dataset.schema.map((col) => (
              <option key={col.name} value={col.name}>
                {col.name} ({col.data_type})
              </option>
            ))}
          </select>

          <button
            type="button"
            disabled={!selectedTarget || loading}
            onClick={handleRunPrediction}
            className="flex items-center gap-2 px-5 py-2 text-sm font-medium text-white bg-primary hover:bg-primary/90 disabled:opacity-50 rounded-lg transition-colors shadow-sm"
          >
            {loading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Training Model...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-current" />
                <span>Run Prediction</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Dismissible / General Error Banner */}
      {error && (
        <div className="p-4 bg-danger/10 border border-danger/30 rounded-xl flex items-center gap-3 text-danger text-sm">
          <AlertTriangle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Unavailable Status Message */}
      {prediction && !prediction.available && (
        <div className="p-6 bg-amber-500/10 border border-amber-500/30 rounded-xl space-y-2 text-amber-400">
          <div className="flex items-center gap-2 font-semibold text-base">
            <AlertTriangle className="w-5 h-5 shrink-0" />
            <span>Prediction Unavailable</span>
          </div>
          <p className="text-xs text-text-secondary">{prediction.reason}</p>
        </div>
      )}

      {/* Prediction Results Display */}
      {prediction && prediction.available && (
        <div className="space-y-6">
          {/* Model Information & Metadata Card */}
          <div className="p-6 bg-card border border-border rounded-xl space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-4 flex-wrap gap-2">
              <div className="flex items-center gap-3">
                <Cpu className="w-6 h-6 text-primary" />
                <div>
                  <h3 className="text-lg font-bold text-text-primary">{prediction.model_type}</h3>
                  <p className="text-xs text-text-secondary uppercase tracking-wider font-mono">
                    Task Type: {prediction.problem_type}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2 text-xs font-mono">
                <span className="px-2.5 py-1 bg-elevated border border-border rounded text-text-secondary">
                  Target: <strong className="text-text-primary">{prediction.target_column}</strong>
                </span>
                {prediction.stratified !== null && (
                  <span
                    className={`px-2.5 py-1 rounded font-semibold ${
                      prediction.stratified
                        ? 'bg-success/20 text-success'
                        : 'bg-amber-500/20 text-amber-400'
                    }`}
                  >
                    {prediction.stratified ? 'Stratified Split' : 'Non-Stratified Fallback'}
                  </span>
                )}
              </div>
            </div>

            {/* Row Breakdown & Features */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="p-4 bg-surface border border-border rounded-lg space-y-2">
                <div className="flex items-center gap-2 font-semibold text-text-primary">
                  <Layers className="w-4 h-4 text-primary" />
                  <span>Dataset Split Breakdown</span>
                </div>
                <div className="grid grid-cols-3 gap-2 font-mono pt-1 text-center">
                  <div className="p-2 bg-elevated/50 rounded border border-border">
                    <span className="text-text-muted block text-[10px]">Total Cleaned</span>
                    <span className="text-text-primary font-bold">{prediction.row_counts?.total_cleaned ?? 0}</span>
                  </div>
                  <div className="p-2 bg-elevated/50 rounded border border-border">
                    <span className="text-text-muted block text-[10px]">Train (80%)</span>
                    <span className="text-text-primary font-bold">{prediction.row_counts?.train_count ?? 0}</span>
                  </div>
                  <div className="p-2 bg-elevated/50 rounded border border-border">
                    <span className="text-text-muted block text-[10px]">Test (20%)</span>
                    <span className="text-text-primary font-bold">{prediction.row_counts?.test_count ?? 0}</span>
                  </div>
                </div>
              </div>

              <div className="p-4 bg-surface border border-border rounded-lg space-y-2">
                <div className="flex items-center gap-2 font-semibold text-text-primary">
                  <ListChecks className="w-4 h-4 text-primary" />
                  <span>Features Used ({prediction.features_used.length})</span>
                </div>
                <div className="flex flex-wrap gap-1.5 pt-1 max-h-24 overflow-y-auto">
                  {prediction.features_used.map((feat) => (
                    <span
                      key={feat}
                      className="px-2 py-0.5 font-mono text-[10px] bg-elevated border border-border rounded text-text-secondary"
                    >
                      {feat}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Label Mapping (for Classification) */}
            {prediction.label_mapping && (
              <div className="p-3 bg-surface border border-border rounded-lg text-xs space-y-1">
                <span className="font-semibold text-text-primary">Target Label Class Mapping:</span>
                <div className="flex flex-wrap gap-3 font-mono text-text-secondary pt-0.5">
                  {Object.entries(prediction.label_mapping).map(([k, v]) => (
                    <span key={k} className="bg-elevated px-2 py-0.5 rounded border border-border">
                      {k} &rarr; <strong className="text-text-primary">{String(v)}</strong>
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Performance Metrics Cards Grid */}
          <div className="bg-card border border-border rounded-xl p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-semibold text-text-primary flex items-center gap-2">
                <BarChart2 className="w-5 h-5 text-primary" />
                <span>Model Evaluation Metrics</span>
              </h3>
              <span className="text-xs text-text-muted font-mono">Rounded to 4 decimal places</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {Object.entries(prediction.metrics).map(([metricKey, metricValue]) => (
                <div key={metricKey} className="p-4 bg-surface border border-border rounded-lg space-y-1">
                  <span className="text-xs font-mono uppercase text-text-muted">{metricKey}</span>
                  <p className="text-2xl font-bold font-mono text-text-primary">{metricValue.toFixed(4)}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Sample Predictions Table (First 10 rows) */}
          <div className="bg-card border border-border rounded-xl p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-semibold text-text-primary flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-success" />
                <span>Sample Test Predictions</span>
              </h3>
              <span className="text-xs text-text-muted font-mono">First {prediction.predictions.length} test rows</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="border-b border-border text-text-muted uppercase tracking-wider bg-surface">
                  <tr>
                    <th className="py-3 px-4 w-16">Sample #</th>
                    <th className="py-3 px-4">Actual Target</th>
                    <th className="py-3 px-4">Predicted Target</th>
                    <th className="py-3 px-4">Match Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {prediction.predictions.map((sample, idx) => {
                    const isMatch = String(sample.actual) === String(sample.predicted);
                    return (
                      <tr key={idx} className="hover:bg-elevated/40">
                        <td className="py-3 px-4 font-mono text-text-muted">#{idx + 1}</td>
                        <td className="py-3 px-4 font-mono font-medium text-text-primary">{String(sample.actual)}</td>
                        <td className="py-3 px-4 font-mono font-medium text-text-primary">{String(sample.predicted)}</td>
                        <td className="py-3 px-4">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold uppercase ${
                              isMatch ? 'bg-success/20 text-success' : 'bg-amber-500/20 text-amber-400'
                            }`}
                          >
                            {isMatch ? 'Exact Match' : 'Variance'}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Predictions;

