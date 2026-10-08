import React, { useState, useEffect } from 'react';
import {
  Activity,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Search,
  Copy,
  Check,
  RefreshCw,
  Globe,
  Database,
  ArrowRight,
} from 'lucide-react';

const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

interface DNSAnalysisResult {
  analysis_id: string;
  domain: string;
  status: 'HEALTHY' | 'DEGRADED' | 'UNRESOLVABLE' | 'INVALID' | string;
  created_at: string;
  dns_analysis: {
    domain: string;
    is_resolvable: boolean;
    status: string;
    records: {
      A: string[];
      AAAA: string[];
      MX: string[];
      NS: string[];
      TXT: string[];
      CNAME: string[];
      [key: string]: string[];
    };
    errors: Record<string, string>;
    response_time_ms: number;
  };
}

export default function App() {
  const [domainInput, setDomainInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<DNSAnalysisResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [apiStatus, setApiStatus] = useState<'online' | 'offline' | 'checking'>('checking');
  const [copiedId, setCopiedId] = useState(false);

  // Check backend health on mount and periodically
  const checkBackendHealth = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/health`);
      if (res.ok) {
        setApiStatus('online');
      } else {
        setApiStatus('offline');
      }
    } catch {
      setApiStatus('offline');
    }
  };

  useEffect(() => {
    checkBackendHealth();
    const interval = setInterval(checkBackendHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleAnalyze = async (e?: React.FormEvent, targetDomain?: string) => {
    if (e) e.preventDefault();
    const domainToAnalyze = (targetDomain || domainInput).trim();

    if (!domainToAnalyze) {
      setErrorMessage('Please enter a domain name to analyze.');
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      // 1. Initiate analysis POST /analysis
      const postRes = await fetch(`${API_BASE_URL}/analysis`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ domain: domainToAnalyze }),
      });

      const postData = await postRes.json();

      if (!postRes.ok) {
        throw new Error(postData.detail || 'Failed to start DNS analysis.');
      }

      const analysisId = postData.analysis_id;

      // 2. Fetch full result GET /analysis/{analysis_id}
      const getRes = await fetch(`${API_BASE_URL}/analysis/${analysisId}`);
      const getData = await getRes.json();

      if (!getRes.ok) {
        throw new Error(getData.detail || 'Failed to retrieve analysis report.');
      }

      setAnalysisResult(getData);
      setDomainInput(domainToAnalyze);
    } catch (err: any) {
      setErrorMessage(err.message || 'An unexpected error occurred during analysis.');
      setAnalysisResult(null);
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(true);
    setTimeout(() => setCopiedId(false), 2000);
  };

  const recordKeys = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'CNAME'] as const;

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col items-center py-8 px-4 sm:px-6 lg:px-8">
      {/* Main Container */}
      <div className="w-full max-w-4xl bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        
        {/* Top Header */}
        <header className="px-6 py-5 border-b border-slate-200 bg-white flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-50 border border-blue-100 rounded-lg text-blue-600">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl font-semibold tracking-tight text-slate-900">
                DNS Health Analyzer
              </h1>
              <p className="text-xs text-slate-500">
                Domain intelligence & DNS diagnostics
              </p>
            </div>
          </div>

          {/* Backend Status Badge */}
          <div className="flex items-center gap-2 self-start sm:self-auto">
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border bg-slate-50 border-slate-200">
              <span
                className={`w-2 h-2 rounded-full ${
                  apiStatus === 'online'
                    ? 'bg-emerald-500 animate-pulse'
                    : apiStatus === 'offline'
                    ? 'bg-rose-500'
                    : 'bg-amber-400'
                }`}
              />
              <span className="text-slate-600 capitalize">
                {apiStatus === 'online' ? 'API Online' : apiStatus === 'offline' ? 'API Offline' : 'Connecting...'}
              </span>
            </div>
            <button
              onClick={checkBackendHealth}
              title="Refresh API status"
              className="p-1 text-slate-400 hover:text-slate-600 transition"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>
        </header>

        {/* Search / Input Form Section */}
        <div className="p-6 bg-slate-50/50 border-b border-slate-200">
          <label htmlFor="domain-input" className="block text-sm font-medium text-slate-700 mb-2">
            Analyze a domain
          </label>
          <form onSubmit={handleAnalyze} className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                <Search className="w-4 h-4" />
              </div>
              <input
                id="domain-input"
                type="text"
                value={domainInput}
                onChange={(e) => setDomainInput(e.target.value)}
                placeholder="Enter domain e.g. google.com"
                disabled={isLoading}
                className="w-full pl-10 pr-4 py-2.5 bg-white border border-slate-300 rounded-lg text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition disabled:bg-slate-100"
              />
            </div>
            <button
              type="submit"
              disabled={isLoading || !domainInput.trim()}
              className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg shadow-sm transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 min-w-[110px]"
            >
              {isLoading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Analyzing...</span>
                </>
              ) : (
                <>
                  <span>Analyze</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Quick suggestions */}
          <div className="mt-3 flex items-center gap-2 flex-wrap text-xs text-slate-500">
            <span>Try sample domains:</span>
            {['google.com', 'github.com', 'cloudflare.com', 'openai.com'].map((sample) => (
              <button
                key={sample}
                type="button"
                onClick={() => {
                  setDomainInput(sample);
                  handleAnalyze(undefined, sample);
                }}
                className="px-2 py-0.5 bg-white border border-slate-200 hover:border-slate-300 rounded text-slate-600 hover:text-slate-900 transition"
              >
                {sample}
              </button>
            ))}
          </div>
        </div>

        {/* Error Alert Box */}
        {errorMessage && (
          <div className="p-4 m-6 mb-0 bg-rose-50 border border-rose-200 rounded-lg text-rose-800 text-sm flex items-start gap-3">
            <XCircle className="w-5 h-5 text-rose-500 shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="font-medium text-rose-900">Analysis Error</p>
              <p className="text-rose-700 text-xs mt-0.5">{errorMessage}</p>
            </div>
            <button
              onClick={() => setErrorMessage(null)}
              className="text-rose-400 hover:text-rose-600 text-xs font-semibold"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Empty State */}
        {!analysisResult && !isLoading && !errorMessage && (
          <div className="py-16 px-6 text-center">
            <div className="w-12 h-12 mx-auto mb-3 bg-slate-100 rounded-full flex items-center justify-center text-slate-400">
              <Globe className="w-6 h-6" />
            </div>
            <h3 className="text-base font-medium text-slate-800">No domain analyzed yet</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
              Enter a domain above and click Analyze to check DNS records, nameservers, and health diagnostics.
            </p>
          </div>
        )}

        {/* Loading State Skeleton */}
        {isLoading && (
          <div className="p-8 text-center space-y-4">
            <div className="inline-flex p-3 bg-blue-50 text-blue-600 rounded-full animate-bounce">
              <RefreshCw className="w-6 h-6 animate-spin" />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-800">Querying DNS Nameservers...</p>
              <p className="text-xs text-slate-500 mt-0.5">Resolving A, AAAA, MX, NS, TXT, and CNAME records</p>
            </div>
          </div>
        )}

        {/* Results Section */}
        {analysisResult && !isLoading && (
          <div className="p-6 space-y-6">
            
            {/* Health Status Banner Card */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-lg border bg-slate-50/70 border-slate-200">
              <div className="space-y-1">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  DNS Health Status
                </span>
                <div className="flex items-center gap-2">
                  <span
                    className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${
                      analysisResult.status === 'HEALTHY'
                        ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                        : analysisResult.status === 'DEGRADED'
                        ? 'bg-amber-50 text-amber-700 border-amber-200'
                        : 'bg-rose-50 text-rose-700 border-rose-200'
                    }`}
                  >
                    <span
                      className={`w-2 h-2 rounded-full ${
                        analysisResult.status === 'HEALTHY'
                          ? 'bg-emerald-500'
                          : analysisResult.status === 'DEGRADED'
                          ? 'bg-amber-500'
                          : 'bg-rose-500'
                      }`}
                    />
                    {analysisResult.status}
                  </span>
                </div>
              </div>

              {/* Meta information */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-2 text-xs">
                <div>
                  <span className="text-slate-400 block">Domain</span>
                  <span className="font-semibold text-slate-900 font-mono text-sm">
                    {analysisResult.domain}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block">Analysis ID</span>
                  <div className="flex items-center gap-1.5 font-mono text-slate-700">
                    <span>{analysisResult.analysis_id.slice(0, 8)}...</span>
                    <button
                      onClick={() => copyToClipboard(analysisResult.analysis_id)}
                      title="Copy full analysis ID"
                      className="text-slate-400 hover:text-slate-600 transition"
                    >
                      {copiedId ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                </div>
                <div>
                  <span className="text-slate-400 block">Response Time</span>
                  <span className="text-slate-700 font-medium">
                    {analysisResult.dns_analysis?.response_time_ms ?? 0} ms
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block">Timestamp</span>
                  <span className="text-slate-700">
                    {new Date(analysisResult.created_at).toLocaleTimeString()}
                  </span>
                </div>
              </div>
            </div>

            {/* Quick Record Grid Badges */}
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">
                Record Diagnostics Summary
              </h4>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2.5">
                {recordKeys.map((rtype) => {
                  const records = analysisResult.dns_analysis?.records?.[rtype] || [];
                  const hasRecords = records.length > 0;
                  const hasError = !!analysisResult.dns_analysis?.errors?.[rtype];

                  return (
                    <div
                      key={rtype}
                      className={`p-3 rounded-lg border text-center transition ${
                        hasRecords
                          ? 'bg-white border-slate-200'
                          : hasError
                          ? 'bg-rose-50/50 border-rose-200'
                          : 'bg-slate-50/50 border-slate-200 opacity-60'
                      }`}
                    >
                      <div className="font-mono font-semibold text-xs text-slate-700 mb-1">{rtype}</div>
                      <div className="flex items-center justify-center gap-1">
                        {hasRecords ? (
                          <span className="inline-flex items-center text-xs font-semibold text-emerald-600">
                            <CheckCircle2 className="w-3.5 h-3.5 mr-0.5" /> {records.length}
                          </span>
                        ) : hasError ? (
                          <span className="inline-flex items-center text-xs font-semibold text-rose-600">
                            <AlertTriangle className="w-3.5 h-3.5 mr-0.5" /> Err
                          </span>
                        ) : (
                          <span className="text-xs text-slate-400">—</span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Detailed DNS Records Table */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Detailed DNS Records
                </h4>
                <span className="text-xs text-slate-500 font-mono">
                  MongoDB Persisted
                </span>
              </div>

              <div className="border border-slate-200 rounded-lg overflow-hidden divide-y divide-slate-200">
                {recordKeys.map((rtype) => {
                  const records = analysisResult.dns_analysis?.records?.[rtype] || [];
                  const error = analysisResult.dns_analysis?.errors?.[rtype];

                  return (
                    <div key={rtype} className="p-4 bg-white hover:bg-slate-50/50 transition">
                      <div className="flex items-start gap-4">
                        <div className="w-16 font-mono text-xs font-semibold text-slate-500 uppercase pt-0.5">
                          {rtype}
                        </div>
                        <div className="flex-1 space-y-1">
                          {records.length > 0 ? (
                            records.map((rec, idx) => (
                              <div
                                key={idx}
                                className="font-mono text-xs text-slate-800 bg-slate-50 border border-slate-200 px-2.5 py-1 rounded select-all break-all"
                              >
                                {rec}
                              </div>
                            ))
                          ) : error ? (
                            <span className="text-xs text-rose-600 italic">{error}</span>
                          ) : (
                            <span className="text-xs text-slate-400 italic">No {rtype} records found</span>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

          </div>
        )}

        {/* Footer */}
        <footer className="px-6 py-4 border-t border-slate-200 bg-slate-50 flex items-center justify-between text-xs text-slate-500">
          <div className="flex items-center gap-2">
            <Database className="w-3.5 h-3.5 text-slate-400" />
            <span>MongoDB Document Database Connected</span>
          </div>
          <div>
            <span>FastAPI + dnspython Engine</span>
          </div>
        </footer>

      </div>
    </div>
  );
}
