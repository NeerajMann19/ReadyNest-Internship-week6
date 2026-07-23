import React, { useEffect, useState } from 'react';
import { apiClient } from '../../api/client';
import type { Insight, AdvisorResponse } from '../../types';
import {
  Lightbulb,
  AlertTriangle,
  TrendingUp,
  ShieldAlert,
  Sparkles,
  RefreshCw,
  CheckCircle2,
  BrainCircuit,
  X,
} from 'lucide-react';

interface InsightsSectionProps {
  sessionId: string | null;
}

export const InsightsSection: React.FC<InsightsSectionProps> = ({ sessionId }) => {
  const [insights, setInsights] = useState<Insight[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Executive Advisor explanation state per insightId
  const [explanations, setExplanations] = useState<
    Record<string, { loading: boolean; text?: string; error?: string }>
  >({});

  const fetchInsights = async () => {
    if (!sessionId) return;

    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.get<{ insights: Insight[] }>(`/dataset/${sessionId}/insights`);
      if (response.data && Array.isArray(response.data.insights)) {
        setInsights(response.data.insights);
      } else {
        throw new Error('Invalid response structure for insights.');
      }
    } catch (err: any) {
      const msg = err.response?.data?.message || err.message || 'Failed to generate AI insights.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleExplain = async (insightId: string) => {
    if (!sessionId) return;

    // Toggle off if already showing text
    if (explanations[insightId] && !explanations[insightId].loading && explanations[insightId].text) {
      setExplanations((prev) => {
        const copy = { ...prev };
        delete copy[insightId];
        return copy;
      });
      return;
    }

    setExplanations((prev) => ({
      ...prev,
      [insightId]: { loading: true },
    }));

    try {
      const response = await apiClient.post<AdvisorResponse>(`/dataset/${sessionId}/advisor`, {
        target_id: insightId,
      });
      setExplanations((prev) => ({
        ...prev,
        [insightId]: { loading: false, text: response.data.explanation },
      }));
    } catch (err: any) {
      const msg = err.response?.data?.message || err.message || 'Failed to fetch executive explanation.';
      setExplanations((prev) => ({
        ...prev,
        [insightId]: { loading: false, error: msg },
      }));
    }
  };

  const closeExplanation = (insightId: string) => {
    setExplanations((prev) => {
      const copy = { ...prev };
      delete copy[insightId];
      return copy;
    });
  };

  useEffect(() => {
    fetchInsights();
  }, [sessionId]);

  if (!sessionId) {
    return (
      <div className="p-8 text-center border border-dashed border-border rounded-xl bg-surface space-y-2">
        <Lightbulb className="w-8 h-8 text-text-muted mx-auto" />
        <h3 className="text-lg font-semibold text-text-primary">No Dataset Uploaded</h3>
        <p className="text-text-secondary text-sm">
          Upload a dataset from Overview to compute analytics and generate AI business insights.
        </p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="p-6 bg-card border border-border rounded-xl flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Sparkles className="w-5 h-5 text-primary animate-pulse" />
            <div>
              <h3 className="text-base font-semibold text-text-primary">Analyzing Dataset & Generating Insights...</h3>
              <p className="text-xs text-text-secondary">Evaluating quantitative analytics with Gemini AI engine</p>
            </div>
          </div>
          <RefreshCw className="w-5 h-5 text-primary animate-spin" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((idx) => (
            <div key={idx} className="p-5 bg-card border border-border rounded-xl space-y-4 animate-pulse">
              <div className="flex items-center justify-between">
                <div className="h-5 bg-elevated rounded w-1/3" />
                <div className="h-5 bg-elevated rounded w-1/4" />
              </div>
              <div className="h-4 bg-elevated rounded w-3/4" />
              <div className="h-12 bg-elevated rounded w-full" />
              <div className="h-16 bg-surface rounded p-3 space-y-2">
                <div className="h-3 bg-elevated rounded w-1/2" />
                <div className="h-3 bg-elevated rounded w-2/3" />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-danger/10 border border-danger/30 rounded-xl space-y-3">
        <div className="flex items-center gap-3 text-danger">
          <AlertTriangle className="w-6 h-6 shrink-0" />
          <h3 className="text-lg font-semibold">Insight Engine Error</h3>
        </div>
        <p className="text-sm text-text-secondary">{error}</p>
        <button
          type="button"
          onClick={fetchInsights}
          className="px-4 py-2 text-xs font-medium text-white bg-danger hover:bg-danger/90 rounded-lg transition-colors inline-flex items-center gap-2"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Retry Generation</span>
        </button>
      </div>
    );
  }

  const getSeverityBadgeClass = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'high':
        return 'bg-[#EF4444]/10 text-[#EF4444] border-[#EF4444]/30';
      case 'medium':
        return 'bg-[#F59E0B]/10 text-[#F59E0B] border-[#F59E0B]/30';
      case 'low':
      default:
        return 'bg-surface text-text-secondary border-border';
    }
  };

  const getCategoryBadgeClass = (category: string) => {
    switch (category) {
      case 'Opportunity':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      case 'Risk':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/30';
      case 'Trend':
      default:
        return 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30';
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'Opportunity':
        return <Sparkles className="w-3.5 h-3.5" />;
      case 'Risk':
        return <ShieldAlert className="w-3.5 h-3.5" />;
      case 'Trend':
      default:
        return <TrendingUp className="w-3.5 h-3.5" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex items-center justify-between p-4 bg-gradient-to-r from-card to-surface border border-border rounded-xl">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-primary/10 rounded-lg text-primary border border-primary/20">
            <Lightbulb className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-text-primary flex items-center gap-2">
              Automated Business Insights
              <span className="text-[10px] font-mono font-medium px-2 py-0.5 rounded bg-primary/20 text-primary border border-primary/30">
                {insights.length} Generated
              </span>
            </h3>
            <p className="text-xs text-text-secondary">
              Grounded empirical findings synthesized from dataset analytics and predictive modeling
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={fetchInsights}
          title="Refresh Insights"
          className="p-2 text-text-secondary hover:text-text-primary bg-surface hover:bg-elevated border border-border rounded-lg transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Insights Card Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {insights.map((insight) => (
          <div
            key={insight.id}
            className="p-5 bg-card border border-border rounded-xl space-y-4 hover:border-primary/40 transition-colors flex flex-col justify-between"
          >
            {/* Top Badges & Explain Action Button */}
            <div className="space-y-3">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <div className="flex items-center gap-2">
                  <span
                    className={`px-2.5 py-1 rounded-md text-xs font-semibold uppercase tracking-wider border flex items-center gap-1.5 ${getCategoryBadgeClass(
                      insight.category
                    )}`}
                  >
                    {getCategoryIcon(insight.category)}
                    {insight.category}
                  </span>
                  <span
                    className={`px-2.5 py-1 rounded-md text-xs font-medium uppercase tracking-wider border ${getSeverityBadgeClass(
                      insight.severity
                    )}`}
                  >
                    {insight.severity} Severity
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <span
                    className="text-[11px] font-mono font-medium text-text-muted bg-surface px-2 py-1 rounded border border-border"
                    title="Model confidence score"
                  >
                    {(insight.confidence * 100).toFixed(0)}% Confidence
                  </span>

                  <button
                    type="button"
                    onClick={() => handleExplain(insight.id)}
                    className="px-2.5 py-1 rounded-md bg-primary/10 hover:bg-primary/20 text-primary border border-primary/30 text-xs font-medium flex items-center gap-1.5 transition-colors"
                    title="Get executive business explanation from AI Advisor"
                  >
                    <BrainCircuit className="w-3.5 h-3.5" />
                    <span>Explain</span>
                  </button>
                </div>
              </div>

              {/* Title & Description */}
              <div>
                <h4 className="text-base font-semibold text-text-primary leading-tight mb-1.5">
                  {insight.title}
                </h4>
                <p className="text-xs text-text-secondary leading-relaxed">
                  {insight.description}
                </p>
              </div>
            </div>

            {/* Contextual Executive Advisor Brief Side/Bottom Box */}
            {explanations[insight.id] && (
              <div className="p-3.5 bg-surface/90 border border-primary/30 rounded-lg space-y-2 text-xs relative animate-fadeIn shadow-sm">
                <div className="flex items-center justify-between border-b border-border/40 pb-2">
                  <div className="flex items-center gap-1.5 font-semibold text-primary">
                    <BrainCircuit className="w-4 h-4" />
                    <span>Executive Advisor Brief</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => closeExplanation(insight.id)}
                    className="text-text-muted hover:text-text-primary p-0.5 rounded hover:bg-elevated transition-colors"
                    title="Close explanation"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>

                {explanations[insight.id].loading ? (
                  <div className="flex items-center gap-2 text-text-secondary py-2">
                    <RefreshCw className="w-3.5 h-3.5 animate-spin text-primary" />
                    <span>Synthesizing executive brief...</span>
                  </div>
                ) : explanations[insight.id].error ? (
                  <p className="text-danger py-1">{explanations[insight.id].error}</p>
                ) : (
                  <p className="text-text-primary leading-relaxed py-1 font-normal">
                    {explanations[insight.id].text}
                  </p>
                )}
              </div>
            )}

            {/* Grounded Evidence List */}
            {insight.evidence && Object.keys(insight.evidence).length > 0 && (
              <div className="p-3 bg-surface border border-border rounded-lg space-y-2">
                <div className="flex items-center gap-1.5 text-[11px] font-semibold text-text-muted uppercase tracking-wider">
                  <CheckCircle2 className="w-3.5 h-3.5 text-primary" />
                  <span>Supporting Evidence</span>
                </div>
                <div className="space-y-1 text-xs font-mono">
                  {Object.entries(insight.evidence).map(([key, val]) => (
                    <div key={key} className="flex items-start justify-between gap-2 border-b border-border/40 last:border-0 pb-1 last:pb-0">
                      <span className="text-text-muted capitalize">{key.replace(/_/g, ' ')}:</span>
                      <span className="text-text-primary font-medium text-right break-all">
                        {typeof val === 'object' ? JSON.stringify(val) : String(val)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default InsightsSection;
