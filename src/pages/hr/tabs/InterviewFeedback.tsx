import React, { useEffect, useState } from 'react';
import api from '../../../utils/api';
import {
  RefreshCw, AlertCircle, User, Briefcase, Star,
  MessageSquare, Cpu, Lightbulb, Zap, TrendingUp,
  ChevronDown, ChevronUp, CheckCircle, XCircle, Loader2
} from 'lucide-react';

// ── Types ─────────────────────────────────────────────────────────────────────

interface InterviewResult {
  result_id: number;
  application_id: number;
  overall_score: number | null;
  communication_score: number | null;
  technical_score: number | null;
  problem_solving_score: number | null;
  confidence_score: number | null;
  recommendation: string | null;
  ai_feedback: string | null;
  evaluated_at: string | null;
  application_status: string | null;
  candidate_name: string | null;
  candidate_email: string | null;
  job_title: string | null;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

const fmt = (v: number | null) =>
  v !== null && v !== undefined ? Number(v).toFixed(1) : '—';

const recommendationStyle = (rec: string | null) => {
  if (!rec) return { bg: 'bg-zinc-800/60', text: 'text-zinc-400', border: 'border-zinc-700' };
  const r = rec.toLowerCase();
  if (r.includes('strong hire')) return { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/30' };
  if (r.includes('hire')) return { bg: 'bg-amber-500/10', text: 'text-amber-400', border: 'border-amber-500/30' };
  if (r.includes('consider')) return { bg: 'bg-blue-500/10', text: 'text-blue-400', border: 'border-blue-500/30' };
  if (r.includes('reject')) return { bg: 'bg-red-500/10', text: 'text-red-400', border: 'border-red-500/30' };
  return { bg: 'bg-zinc-800/60', text: 'text-zinc-400', border: 'border-zinc-700' };
};

const scoreColor = (v: number | null) => {
  if (v === null || v === undefined) return 'text-zinc-500';
  if (v >= 75) return 'text-emerald-400';
  if (v >= 50) return 'text-amber-400';
  return 'text-red-400';
};

const statusBadge = (status: string | null) => {
  if (!status) return null;
  const s = status.toLowerCase();
  if (s === 'hired') return { label: 'Hired', cls: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30' };
  if (s === 'rejected') return { label: 'Rejected', cls: 'bg-red-500/15 text-red-400 border-red-500/30' };
  return null;
};

const ScoreBar: React.FC<{ value: number | null }> = ({ value }) => {
  const pct = value !== null && value !== undefined ? Math.min(Math.max(Number(value), 0), 100) : 0;
  const color = pct >= 75 ? '#34d399' : pct >= 50 ? '#f59e0b' : '#f87171';
  return (
    <div className="w-full h-1 rounded-full bg-zinc-800 overflow-hidden mt-1.5">
      <div className="h-full rounded-full transition-all duration-700" style={{ width: `${pct}%`, backgroundColor: color }} />
    </div>
  );
};

// ── Expandable Row ────────────────────────────────────────────────────────────

const ResultRow: React.FC<{
  item: InterviewResult;
  onStatusChange: (applicationId: number, newStatus: 'Hired' | 'Rejected') => void;
}> = ({ item, onStatusChange }) => {
  const [expanded, setExpanded] = useState(false);
  const [actionLoading, setActionLoading] = useState<'hire' | 'reject' | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const rec = recommendationStyle(item.recommendation);
  const badge = statusBadge(item.application_status);
  const isDone = item.application_status === 'Hired' || item.application_status === 'Rejected';

  const handleAction = async (action: 'hire' | 'reject') => {
    setActionError(null);
    setActionLoading(action);
    try {
      if (action === 'hire') {
        await api.post(`/api/hr/applications/${item.application_id}/hire`);
        onStatusChange(item.application_id, 'Hired');
      } else {
        await api.post(`/api/hr/applications/${item.application_id}/reject-post-interview`);
        onStatusChange(item.application_id, 'Rejected');
      }
    } catch (err: any) {
      setActionError(err?.response?.data?.detail ?? `Failed to ${action} candidate.`);
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 overflow-hidden transition-all duration-200 hover:border-zinc-700">

      {/* ── Collapsed row ── */}
      <div
        className="grid grid-cols-12 items-center gap-3 px-5 py-4 cursor-pointer select-none"
        onClick={() => setExpanded(e => !e)}
      >
        {/* Candidate */}
        <div className="col-span-3 flex items-center gap-3 min-w-0">
          <div className="w-8 h-8 rounded-full bg-amber-500/15 border border-amber-500/30 flex items-center justify-center flex-shrink-0">
            <User size={14} className="text-amber-400" />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-white truncate">{item.candidate_name ?? '—'}</p>
            <p className="text-[11px] text-zinc-500">App #{item.application_id}</p>
          </div>
        </div>

        {/* Job */}
        <div className="col-span-2 flex items-center gap-2 min-w-0">
          <Briefcase size={13} className="text-zinc-500 flex-shrink-0" />
          <span className="text-xs text-zinc-300 truncate">{item.job_title ?? '—'}</span>
        </div>

        {/* Overall */}
        <div className="col-span-2">
          <div className={`text-xl font-black tabular-nums ${scoreColor(item.overall_score)}`}>{fmt(item.overall_score)}</div>
          <ScoreBar value={item.overall_score} />
          <p className="text-[10px] text-zinc-600 mt-0.5 uppercase tracking-wide">Overall</p>
        </div>

        {/* Recommendation */}
        <div className="col-span-2">
          <span className={`inline-flex items-center px-2.5 py-1 rounded-md text-[11px] font-bold border ${rec.bg} ${rec.text} ${rec.border}`}>
            {item.recommendation ?? '—'}
          </span>
        </div>

        {/* Status badge or date */}
        <div className="col-span-2 flex items-center gap-2">
          {badge ? (
            <span className={`px-2.5 py-1 rounded-md text-[11px] font-bold border ${badge.cls}`}>{badge.label}</span>
          ) : (
            <span className="text-xs text-zinc-500">
              {item.evaluated_at
                ? new Date(item.evaluated_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
                : '—'}
            </span>
          )}
        </div>

        {/* Chevron */}
        <div className="col-span-1 flex justify-end">
          {expanded ? <ChevronUp size={15} className="text-zinc-500" /> : <ChevronDown size={15} className="text-zinc-500" />}
        </div>
      </div>

      {/* ── Expanded detail ── */}
      {expanded && (
        <div className="border-t border-zinc-800 px-5 py-4 bg-zinc-950/40 space-y-4">

          {/* Score breakdown */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { label: 'Communication', value: item.communication_score, icon: <MessageSquare size={13} /> },
              { label: 'Technical', value: item.technical_score, icon: <Cpu size={13} /> },
              { label: 'Problem Solving', value: item.problem_solving_score, icon: <Lightbulb size={13} /> },
              { label: 'Confidence', value: item.confidence_score, icon: <Zap size={13} /> },
            ].map(s => (
              <div key={s.label} className="rounded-lg bg-zinc-900 border border-zinc-800 p-3">
                <div className="flex items-center gap-1.5 text-zinc-500 mb-2">
                  {s.icon}
                  <span className="text-[10px] uppercase tracking-wider font-semibold">{s.label}</span>
                </div>
                <div className={`text-2xl font-black tabular-nums ${scoreColor(s.value)}`}>{fmt(s.value)}</div>
                <ScoreBar value={s.value} />
              </div>
            ))}
          </div>

          {/* AI Feedback */}
          {item.ai_feedback && (
            <div className="rounded-lg bg-amber-500/5 border border-amber-500/20 p-4">
              <p className="text-[10px] uppercase tracking-widest font-bold text-amber-500/70 mb-2">AI Feedback</p>
              <p className="text-sm text-zinc-300 leading-relaxed">{item.ai_feedback}</p>
            </div>
          )}

          {/* ── Hire / Reject action buttons ── */}
          {isDone ? (
            <div className={`flex items-center gap-2 px-4 py-3 rounded-lg border text-sm font-semibold
              ${item.application_status === 'Hired'
                ? 'bg-emerald-500/10 border-emerald-500/25 text-emerald-400'
                : 'bg-red-500/10 border-red-500/25 text-red-400'}`}>
              {item.application_status === 'Hired'
                ? <><CheckCircle size={15} /> Candidate has been hired</>
                : <><XCircle size={15} /> Candidate has been rejected</>}
            </div>
          ) : (
            <div className="flex flex-col gap-2">
              {actionError && (
                <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs">
                  <AlertCircle size={13} /> {actionError}
                </div>
              )}
              <div className="flex gap-3">
                <button
                  onClick={() => handleAction('hire')}
                  disabled={actionLoading !== null}
                  className="flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg
                             font-bold text-sm transition-all border
                             bg-emerald-500/10 border-emerald-500/30 text-emerald-400
                             hover:bg-emerald-500/20 hover:border-emerald-500/50
                             disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {actionLoading === 'hire'
                    ? <Loader2 size={15} className="animate-spin" />
                    : <CheckCircle size={15} />}
                  Hire Candidate
                </button>
                <button
                  onClick={() => handleAction('reject')}
                  disabled={actionLoading !== null}
                  className="flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg
                             font-bold text-sm transition-all border
                             bg-red-500/10 border-red-500/30 text-red-400
                             hover:bg-red-500/20 hover:border-red-500/50
                             disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {actionLoading === 'reject'
                    ? <Loader2 size={15} className="animate-spin" />
                    : <XCircle size={15} />}
                  Reject Candidate
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// ── Main Component ────────────────────────────────────────────────────────────

const InterviewFeedback: React.FC = () => {
  const [results, setResults] = useState<InterviewResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [recFilter, setRecFilter] = useState<string>('all');

  const fetchResults = async () => {
    setLoading(true);
    setError(null);
    try {
      // Use /interview-feedback — joins through Application so NULL FKs are never an issue
      const res = await api.get('/api/hr/interview-feedback');
      setResults(res.data ?? []);
    } catch (err: any) {
      console.error('InterviewFeedback fetch error:', err);
      setError(err?.response?.data?.detail ?? 'Failed to load interview results.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchResults(); }, []);

  // Optimistically update status in local state so UI reflects hire/reject immediately
  const handleStatusChange = (applicationId: number, newStatus: 'Hired' | 'Rejected') => {
    setResults(prev =>
      prev.map(r => r.application_id === applicationId ? { ...r, application_status: newStatus } : r)
    );
  };

  // ── Filter ──
  const filtered = results.filter(r => {
    const q = search.toLowerCase();
    const matchSearch =
      !q ||
      (r.candidate_name ?? '').toLowerCase().includes(q) ||
      (r.job_title ?? '').toLowerCase().includes(q);
    const matchRec =
      recFilter === 'all' ||
      (r.recommendation ?? '').toLowerCase().includes(recFilter.toLowerCase());
    return matchSearch && matchRec;
  });

  // ── Stats ──
  const avg = (key: keyof InterviewResult) => {
    const vals = results.map(r => r[key]).filter(v => v !== null && v !== undefined) as number[];
    if (!vals.length) return null;
    return vals.reduce((a, b) => a + Number(b), 0) / vals.length;
  };
  const hiredCount = results.filter(r => r.application_status === 'Hired').length;
  const rejectedCount = results.filter(r => r.application_status === 'Rejected').length;

  return (
    <div className="p-6 space-y-6 animate-fade-in bg-zinc-900/50 min-h-full">

      {/* ── Header ── */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Interview Feedback</h2>
          <p className="text-xs text-zinc-500 mt-0.5">AI-evaluated interview results — make hire/reject decisions below</p>
        </div>
        <button
          onClick={fetchResults}
          disabled={loading}
          className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold
                     bg-zinc-800 text-zinc-300 border border-zinc-700
                     hover:border-amber-500/40 hover:text-amber-400 transition-all disabled:opacity-50"
        >
          <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {/* ── Stats strip ── */}
      {!loading && results.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          {[
            { label: 'Total Evaluated', value: results.length, unit: '', icon: <TrendingUp size={14} />, color: 'text-amber-400' },
            { label: 'Avg Overall', value: avg('overall_score'), unit: '/100', icon: <Star size={14} />, color: 'text-emerald-400' },
            { label: 'Avg Technical', value: avg('technical_score'), unit: '/100', icon: <Cpu size={14} />, color: 'text-blue-400' },
            { label: 'Hired', value: hiredCount, unit: '', icon: <CheckCircle size={14} />, color: 'text-emerald-400' },
            { label: 'Rejected', value: rejectedCount, unit: '', icon: <XCircle size={14} />, color: 'text-red-400' },
          ].map(s => (
            <div key={s.label} className="rounded-xl bg-zinc-900 border border-zinc-800 px-4 py-3 flex items-center gap-3">
              <div className={`${s.color} opacity-70`}>{s.icon}</div>
              <div>
                <p className={`text-xl font-black tabular-nums ${s.color}`}>
                  {s.value !== null && s.value !== undefined
                    ? (typeof s.value === 'number' ? Number(s.value).toFixed(s.unit ? 1 : 0) : s.value)
                    : '—'}
                  <span className="text-xs font-normal text-zinc-500">{s.unit}</span>
                </p>
                <p className="text-[10px] text-zinc-500 uppercase tracking-wide">{s.label}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ── Filters ── */}
      <div className="flex flex-wrap gap-3 items-center">
        <input
          type="text"
          placeholder="Search candidate or job…"
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="flex-1 min-w-[200px] max-w-xs px-3 py-2 rounded-lg text-sm
                     bg-zinc-900 border border-zinc-700 text-white placeholder-zinc-600
                     focus:outline-none focus:border-amber-500/50"
        />
        <div className="flex gap-2 flex-wrap">
          {['all', 'strong hire', 'hire', 'consider', 'reject'].map(r => (
            <button
              key={r}
              onClick={() => setRecFilter(r)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all capitalize
                ${recFilter === r
                  ? 'bg-amber-500/15 border-amber-500/40 text-amber-400'
                  : 'bg-zinc-900 border-zinc-700 text-zinc-400 hover:border-zinc-500'}`}
            >
              {r === 'all' ? 'All' : r}
            </button>
          ))}
        </div>
      </div>

      {/* ── Error ── */}
      {error && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          <AlertCircle size={15} /> {error}
        </div>
      )}

      {/* ── Loading ── */}
      {loading && (
        <div className="flex justify-center py-20">
          <RefreshCw size={32} className="animate-spin text-amber-500" />
        </div>
      )}

      {/* ── Empty ── */}
      {!loading && !error && filtered.length === 0 && (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="w-14 h-14 rounded-full bg-zinc-800 border border-zinc-700 flex items-center justify-center mb-4">
            <MessageSquare size={22} className="text-zinc-600" />
          </div>
          <p className="text-white font-semibold text-lg">
            {results.length === 0 ? 'No interview results yet' : 'No results match your filter'}
          </p>
          <p className="text-zinc-500 text-sm mt-1 max-w-xs">
            {results.length === 0
              ? 'Once candidates complete AI interviews their evaluations will appear here.'
              : 'Try clearing the search or changing the recommendation filter.'}
          </p>
        </div>
      )}

      {/* ── Column headers ── */}
      {!loading && filtered.length > 0 && (
        <>
          <div className="grid grid-cols-12 gap-3 px-5 pb-1 text-[10px] uppercase tracking-widest text-zinc-600 font-bold">
            <div className="col-span-3">Candidate</div>
            <div className="col-span-2">Job</div>
            <div className="col-span-2">Overall</div>
            <div className="col-span-2">AI Recommendation</div>
            <div className="col-span-2">Status / Date</div>
            <div className="col-span-1" />
          </div>

          <div className="space-y-2">
            {filtered.map(item => (
              <ResultRow
                key={item.result_id}
                item={item}
                onStatusChange={handleStatusChange}
              />
            ))}
          </div>

          <p className="text-center text-xs text-zinc-700 pt-2">
            Showing {filtered.length} of {results.length} result{results.length !== 1 ? 's' : ''}
          </p>
        </>
      )}
    </div>
  );
};

export default InterviewFeedback;