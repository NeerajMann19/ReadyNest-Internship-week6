import React, { useState } from 'react';
import { useSession } from '../context/SessionContext';
import { apiClient } from '../api/client';
import type { Decision } from '../types';
import {
  Sliders,
  Play,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  TrendingUp,
  ShieldAlert,
  HelpCircle,
  Sparkles,
  ArrowRight,
} from 'lucide-react';

/**
 * Decision Center Page Component
 * Allows executive simulation of percentage price change scenarios.
 * Displays Recommendation, Expected Impact, Assumptions, and Counter Analysis.
 */
export const DecisionCenter: React.FC = () => {
  const { sessionId, dataset } = useSession();
  const [scenarioInput, setScenarioInput] = useState<string>('10');
  const [decision, setDecision] = useState<Decision | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);

  if (!dataset || !sessionId) {
    return (
      <div className="p-8 text-center border border-dashed border-border rounded-xl bg-surface space-y-2">
        <Sliders className="w-8 h-8 text-text-muted mx-auto" />
        <h2 className="text-xl font-semibold text-text-primary">No Dataset Uploaded</h2>
        <p className="text-text-secondary text-sm">
          No dataset uploaded — upload one from Overview to simulate business decisions.
        </p>
      </div>
    );
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setScenarioInput(val);
    setValidationError(null);

    if (val.trim() === '') return;
    const num = parseFloat(val);
    if (isNaN(num)) {
      setValidationError('Please enter a valid numeric value.');
    } else if (Math.abs(num) > 10000) {
      setValidationError('Input exceeds sanity limit of ±10,000%.');
    }
  };

  const runSimulation = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();

    const num = parseFloat(scenarioInput);
    if (isNaN(num)) {
      setValidationError('Please enter a valid numeric value.');
      return;
    }
    if (Math.abs(num) > 10000) {
      setValidationError('Input exceeds sanity limit of ±10,000%.');
      return;
    }

    setLoading(true);
    setError(null);
    setValidationError(null);

    try {
      const response = await apiClient.post<{ decision: Decision }>(`/dataset/${sessionId}/decision`, {
        scenario_input: num,
      });

      if (response.data && response.data.decision) {
        setDecision(response.data.decision);
      } else {
        throw new Error('Invalid response structure for decision simulation.');
      }
    } catch (err: any) {
      const msg = err.response?.data?.message || err.message || 'Failed to execute decision simulation.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-text-primary">Decision Center</h1>
          <p className="text-text-secondary text-sm">
            Active Dataset: <span className="font-mono text-text-primary">{dataset.filename}</span> ({dataset.rows.toLocaleString()} rows, {dataset.columns} columns)
          </p>
        </div>
      </div>

      {/* Scenario Control Panel */}
      <div className="bg-card border border-border rounded-xl p-6 space-y-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-primary/10 rounded-lg text-primary border border-primary/20">
            <Sliders className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-text-primary">Price Adjustment Simulator</h3>
            <p className="text-xs text-text-secondary">
              Simulate percentage price adjustments (+5% increase, -10% discount, etc.) to project demand impact and risk mitigations.
            </p>
          </div>
        </div>

        <form onSubmit={runSimulation} className="flex flex-col sm:flex-row items-start sm:items-center gap-4 pt-2">
          <div className="w-full sm:w-80 space-y-1">
            <label htmlFor="scenario-input" className="text-xs font-medium text-text-secondary block">
              Percentage Price Change (%)
            </label>
            <div className="relative">
              <input
                id="scenario-input"
                type="number"
                step="any"
                value={scenarioInput}
                onChange={handleInputChange}
                placeholder="e.g. 10 or -5"
                className={`w-full px-3.5 py-2.5 bg-surface border ${
                  validationError ? 'border-danger focus:ring-danger' : 'border-border focus:border-primary'
                } rounded-lg text-sm font-mono text-text-primary placeholder:text-text-muted focus:outline-none transition-colors`}
              />
              <span className="absolute right-3 top-2.5 text-xs font-mono text-text-muted">%</span>
            </div>
            {validationError && <p className="text-xs text-danger font-medium mt-1">{validationError}</p>}
          </div>

          <button
            type="submit"
            disabled={loading || !!validationError}
            className="sm:mt-5 px-5 py-2.5 bg-primary hover:bg-primary/90 text-white font-medium text-sm rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50 shrink-0"
          >
            {loading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Simulating...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-current" />
                <span>Run Simulation</span>
              </>
            )}
          </button>
        </form>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-6 bg-danger/10 border border-danger/30 rounded-xl space-y-3">
          <div className="flex items-center gap-3 text-danger">
            <AlertTriangle className="w-6 h-6 shrink-0" />
            <h3 className="text-lg font-semibold">Simulation Error</h3>
          </div>
          <p className="text-sm text-text-secondary">{error}</p>
          <button
            type="button"
            onClick={() => runSimulation()}
            className="px-4 py-2 text-xs font-medium text-white bg-danger hover:bg-danger/90 rounded-lg transition-colors inline-flex items-center gap-2"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Retry Simulation</span>
          </button>
        </div>
      )}

      {/* Loading Skeleton */}
      {loading && (
        <div className="space-y-6 animate-pulse">
          <div className="p-6 bg-card border border-border rounded-xl space-y-3">
            <div className="h-4 bg-elevated rounded w-1/4" />
            <div className="h-8 bg-elevated rounded w-3/4" />
            <div className="h-4 bg-elevated rounded w-1/2" />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-5 bg-card border border-border rounded-xl space-y-3">
              <div className="h-4 bg-elevated rounded w-1/3" />
              <div className="h-16 bg-surface rounded" />
            </div>
            <div className="p-5 bg-card border border-border rounded-xl space-y-3">
              <div className="h-4 bg-elevated rounded w-1/3" />
              <div className="h-16 bg-surface rounded" />
            </div>
          </div>
        </div>
      )}

      {/* Simulation Results Display */}
      {decision && !loading && (
        <div className="space-y-6">
          {/* Executive Recommendation Card */}
          <div className="p-6 bg-card border border-primary/40 rounded-xl space-y-4 shadow-sm">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div className="flex items-center gap-2 text-primary font-semibold text-sm">
                <Sparkles className="w-4 h-4" />
                <span>Executive Recommendation</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-xs font-mono bg-primary/10 text-primary px-2.5 py-1 rounded border border-primary/20">
                  {decision.scenario_name}
                </span>
                <span className="text-xs font-mono font-medium text-text-muted bg-surface px-2.5 py-1 rounded border border-border">
                  {(decision.confidence * 100).toFixed(0)}% Confidence
                </span>
              </div>
            </div>

            <p className="text-lg font-medium text-text-primary leading-snug">
              {decision.recommendation}
            </p>
          </div>

          {/* Expected Impact & Key Assumptions */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Expected Impact Card */}
            <div className="p-6 bg-card border border-border rounded-xl space-y-4">
              <div className="flex items-center gap-2 text-text-primary font-semibold text-base">
                <TrendingUp className="w-5 h-5 text-emerald-400" />
                <span>Projected Impact Metrics</span>
              </div>

              <div className="space-y-2 font-mono text-xs">
                {Object.entries(decision.expected_impact).map(([key, value]) => (
                  <div key={key} className="p-3 bg-surface border border-border rounded-lg flex items-center justify-between">
                    <span className="text-text-secondary capitalize">{key.replace(/_/g, ' ')}:</span>
                    <span className="font-semibold text-text-primary">
                      {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Key Business Assumptions Card */}
            <div className="p-6 bg-card border border-border rounded-xl space-y-4">
              <div className="flex items-center gap-2 text-text-primary font-semibold text-base">
                <HelpCircle className="w-5 h-5 text-indigo-400" />
                <span>Underlying Business Assumptions</span>
              </div>

              <ul className="space-y-2.5 text-xs text-text-secondary">
                {decision.assumptions.map((item, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <ArrowRight className="w-3.5 h-3.5 text-primary shrink-0 mt-0.5" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Counter Analysis Section (Visually Separated per UXD) */}
          <div className="p-6 bg-card border border-border/80 rounded-xl space-y-6 bg-gradient-to-b from-card to-surface/40">
            <div className="border-b border-border pb-3 flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-text-primary flex items-center gap-2">
                  <ShieldAlert className="w-5 h-5 text-warning" />
                  Counter Analysis & Risk Evaluation
                </h3>
                <p className="text-xs text-text-secondary">
                  Structured evaluation of business trade-offs, risks, alternative actions, and mitigations
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Identified Risks */}
              <div className="p-4 bg-surface/80 border border-border rounded-lg space-y-3">
                <h4 className="text-xs font-semibold text-danger uppercase tracking-wider flex items-center gap-1.5">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  Identified Risks
                </h4>
                <ul className="space-y-2 text-xs text-text-secondary">
                  {decision.counter_analysis.risks.map((risk, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-danger shrink-0 mt-1.5" />
                      <span>{risk}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Trade-offs */}
              <div className="p-4 bg-surface/80 border border-border rounded-lg space-y-3">
                <h4 className="text-xs font-semibold text-warning uppercase tracking-wider flex items-center gap-1.5">
                  <Sliders className="w-3.5 h-3.5" />
                  Business Trade-Offs
                </h4>
                <ul className="space-y-2 text-xs text-text-secondary">
                  {decision.counter_analysis.trade_offs.map((item, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-warning shrink-0 mt-1.5" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Alternative Scenarios */}
              <div className="p-4 bg-surface/80 border border-border rounded-lg space-y-3">
                <h4 className="text-xs font-semibold text-indigo-400 uppercase tracking-wider flex items-center gap-1.5">
                  <HelpCircle className="w-3.5 h-3.5" />
                  Alternative Scenarios
                </h4>
                <ul className="space-y-2 text-xs text-text-secondary">
                  {decision.counter_analysis.alternative_scenarios.map((alt, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 shrink-0 mt-1.5" />
                      <span>{alt}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Recommended Mitigations */}
              <div className="p-4 bg-surface/80 border border-border rounded-lg space-y-3">
                <h4 className="text-xs font-semibold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Recommended Mitigations
                </h4>
                <ul className="space-y-2 text-xs text-text-secondary">
                  {decision.counter_analysis.mitigations.map((mit, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0 mt-1.5" />
                      <span>{mit}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DecisionCenter;
