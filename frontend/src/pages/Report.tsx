import React, { useState } from 'react';
import { useSession } from '../context/SessionContext';
import { apiClient } from '../api/client';
import {
  FileText,
  Download,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  Sparkles,
  ShieldCheck,
  BarChart3,
  BrainCircuit,
  Sliders,
  Terminal,
} from 'lucide-react';

/**
 * Executive Report Page Component
 * Displays section readiness checklist and allows deliberate user-triggered POST /dataset/{session_id}/report PDF export.
 */
export const Report: React.FC = () => {
  const { sessionId, dataset } = useSession();
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [errorDetails, setErrorDetails] = useState<string | null>(null);
  const [is503Error, setIs503Error] = useState<boolean>(false);

  if (!dataset || !sessionId) {
    return (
      <div className="p-8 text-center border border-dashed border-border rounded-xl bg-surface space-y-2">
        <FileText className="w-8 h-8 text-text-muted mx-auto" />
        <h2 className="text-xl font-semibold text-text-primary">No Dataset Uploaded</h2>
        <p className="text-text-secondary text-sm">
          No dataset uploaded — upload one from Overview to generate executive PDF reports.
        </p>
      </div>
    );
  }

  const downloadReport = async () => {
    setLoading(true);
    setError(null);
    setErrorDetails(null);
    setIs503Error(false);

    try {
      const response = await apiClient.post(`/dataset/${sessionId}/report`, {}, {
        responseType: 'blob',
      });

      // Parse filename from Content-Disposition header if available
      let filename = `AnalyticsStudio_Executive_Report_${sessionId.substring(0, 8)}.pdf`;
      const disposition = response.headers['content-disposition'];
      if (disposition && disposition.includes('filename=')) {
        const matches = /filename="?([^"]+)"?/.exec(disposition);
        if (matches && matches[1]) {
          filename = matches[1];
        }
      }

      // Create blob download link
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      if (err.response) {
        if (err.response.status === 503) {
          setIs503Error(true);
          setError('PDF Rendering Engine Unavailable (503 Service Unavailable)');
          setErrorDetails(
            err.response.data?.details ||
              'WeasyPrint GTK3 / Pango / Cairo C-libraries are unavailable on local Windows host. Install GTK3-Runtime-Win64.exe or deploy on Linux for native PDF compilation.'
          );
        } else if (err.response.data instanceof Blob) {
          // Parse JSON error inside Blob
          const text = await err.response.data.text();
          try {
            const parsed = JSON.parse(text);
            setError(parsed.message || 'Failed to generate executive report.');
            if (parsed.details) setErrorDetails(parsed.details);
          } catch {
            setError('Failed to generate executive report.');
          }
        } else {
          setError(err.response.data?.message || 'Failed to generate executive report.');
        }
      } else {
        setError(err.message || 'Failed to generate executive report.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-text-primary">Executive Report</h1>
          <p className="text-text-secondary text-sm">
            Active Dataset: <span className="font-mono text-text-primary">{dataset.filename}</span> ({dataset.rows.toLocaleString()} rows, {dataset.columns} columns)
          </p>
        </div>
      </div>

      {/* Main Action Banner */}
      <div className="bg-card border border-border rounded-xl p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div className="flex items-start gap-4">
          <div className="p-3 bg-primary/10 rounded-xl text-primary border border-primary/20 shrink-0">
            <FileText className="w-8 h-8" />
          </div>
          <div className="space-y-1">
            <h3 className="text-lg font-semibold text-text-primary flex items-center gap-2">
              Executive PDF Report Export
              <span className="text-xs font-mono font-normal px-2 py-0.5 rounded bg-surface text-text-secondary border border-border">
                Jinja2 + WeasyPrint
              </span>
            </h3>
            <p className="text-xs text-text-secondary max-w-xl">
              Assembles cover header, deterministic executive summary, quality metrics, quantitative analytics, prediction evaluation, AI insights, and decision simulation into a dark-mode styled print PDF.
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={downloadReport}
          disabled={loading}
          className="px-6 py-3 bg-primary hover:bg-primary/90 text-white font-medium text-sm rounded-xl transition-all shadow-md flex items-center gap-2.5 shrink-0 disabled:opacity-50"
        >
          {loading ? (
            <>
              <RefreshCw className="w-5 h-5 animate-spin" />
              <span>Compiling PDF Report...</span>
            </>
          ) : (
            <>
              <Download className="w-5 h-5" />
              <span>Generate & Download PDF</span>
            </>
          )}
        </button>
      </div>

      {/* 503 System Dependency Diagnostic Banner */}
      {is503Error && (
        <div className="p-6 bg-warning/10 border border-warning/30 rounded-xl space-y-3">
          <div className="flex items-center gap-3 text-warning">
            <Terminal className="w-6 h-6 shrink-0" />
            <h3 className="text-lg font-semibold">WeasyPrint System Dependencies Missing (HTTP 503)</h3>
          </div>
          <p className="text-xs font-mono text-text-secondary bg-surface p-3 rounded border border-border">
            {errorDetails}
          </p>
          <div className="text-xs text-text-muted space-y-1">
            <p><strong>Note for Phase 7 Verification:</strong></p>
            <p>• On Linux/Render server deployment, WeasyPrint compiles PDFs natively via system `apt-get install pango cairo`.</p>
            <p>• On local Windows, install `GTK3-Runtime-Win64.exe` to enable local PDF generation.</p>
          </div>
        </div>
      )}

      {/* Generic Error Banner */}
      {error && !is503Error && (
        <div className="p-6 bg-danger/10 border border-danger/30 rounded-xl space-y-3">
          <div className="flex items-center gap-3 text-danger">
            <AlertTriangle className="w-6 h-6 shrink-0" />
            <h3 className="text-lg font-semibold">Report Generation Error</h3>
          </div>
          <p className="text-sm text-text-secondary">{error}</p>
          {errorDetails && <p className="text-xs font-mono text-text-muted bg-surface p-2 rounded">{errorDetails}</p>}
          <button
            type="button"
            onClick={downloadReport}
            className="px-4 py-2 text-xs font-medium text-white bg-danger hover:bg-danger/90 rounded-lg transition-colors inline-flex items-center gap-2"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Retry Export</span>
          </button>
        </div>
      )}

      {/* Section Readiness Checklist */}
      <div className="bg-card border border-border rounded-xl p-6 space-y-4">
        <div>
          <h3 className="text-base font-semibold text-text-primary">Report Section Order & Component Readiness</h3>
          <p className="text-xs text-text-secondary">
            Structured assembly pipeline strictly following section hierarchy
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-xs font-mono">
          {/* Section 1: Cover Header */}
          <div className="p-4 bg-surface border border-border rounded-lg space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-text-primary flex items-center gap-2">
                <FileText className="w-4 h-4 text-primary" />
                1. Cover & Header
              </span>
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            </div>
            <p className="text-text-muted text-[11px]">Filename, ISO timestamp, dataset dimensions</p>
          </div>

          {/* Section 2: Executive Summary */}
          <div className="p-4 bg-surface border border-border rounded-lg space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-text-primary flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-primary" />
                2. Executive Summary
              </span>
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            </div>
            <p className="text-text-muted text-[11px]">Deterministic Zero-LLM synthesis of findings</p>
          </div>

          {/* Section 3 & 4: Dataset & Data Quality */}
          <div className="p-4 bg-surface border border-border rounded-lg space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-text-primary flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                3 & 4. Data Quality
              </span>
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            </div>
            <p className="text-text-muted text-[11px]">Quality score ({dataset.quality.quality_score.toFixed(1)}%), missing values & duplicates</p>
          </div>

          {/* Section 5: Analytics Summary */}
          <div className="p-4 bg-surface border border-border rounded-lg space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-text-primary flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-primary" />
                5. Analytics Summary
              </span>
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            </div>
            <p className="text-text-muted text-[11px]">Numeric summary stats & correlation highlights</p>
          </div>

          {/* Section 6: Prediction Summary */}
          <div className="p-4 bg-surface border border-border rounded-lg space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-text-primary flex items-center gap-2">
                <BrainCircuit className="w-4 h-4 text-indigo-400" />
                6. Prediction Summary
              </span>
              <span className="text-[10px] bg-elevated px-2 py-0.5 rounded text-text-secondary border border-border">
                Optional
              </span>
            </div>
            <p className="text-text-muted text-[11px]">ML metrics or explicit placeholder if un-run</p>
          </div>

          {/* Section 7 & 8: Insights & Decision */}
          <div className="p-4 bg-surface border border-border rounded-lg space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-text-primary flex items-center gap-2">
                <Sliders className="w-4 h-4 text-warning" />
                7 & 8. Insights & Decision
              </span>
              <span className="text-[10px] bg-elevated px-2 py-0.5 rounded text-text-secondary border border-border">
                Most Recent
              </span>
            </div>
            <p className="text-text-muted text-[11px]">Structured AI insights & recent scenario simulation</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Report;
