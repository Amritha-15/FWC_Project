import React, { useEffect, useState } from 'react';
import AIInterview from '../../candidate/AIInterview';
import { Loader2, AlertCircle, RefreshCw, User, Briefcase, Star, Calendar, CheckCircle, XCircle, Clock, Mic, CheckCircle2 } from 'lucide-react';
import api from '../../../utils/api';
import CandidateProfileModal from './CandidateProfileModal';

interface PipelineCandidate {
  application_id: number;
  candidate_id: number;
  candidate_name: string;
  candidate_email: string;
  job_id: number;
  job_title: string;
  application_status: string;
  resume_score: number | null;
  match_score: number | null;
  interview_score: number | null;
}

interface Stages {
  [stage: string]: PipelineCandidate[];
}

const STAGE_CONFIG: Record<string, { color: string; border: string; badge: string; icon: React.ReactNode; header: string }> = {
  'Shortlisted': {
    color: 'bg-amber-500/5',
    border: 'border-amber-500/30',
    badge: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    header: 'text-amber-400',
    icon: <Star size={15} className="text-amber-400" />,
  },
  'Interview Scheduled': {
    color: 'bg-blue-500/5',
    border: 'border-blue-500/30',
    badge: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    header: 'text-blue-400',
    icon: <Calendar size={15} className="text-blue-400" />,
  },
  'Interview In Progress': {
    color: 'bg-purple-500/5',
    border: 'border-purple-500/30',
    badge: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
    header: 'text-purple-400',
    icon: <Clock size={15} className="text-purple-400" />,
  },
  'Interview Completed': {
    color: 'bg-indigo-500/5',
    border: 'border-indigo-500/30',
    badge: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
    header: 'text-indigo-400',
    icon: <CheckCircle size={15} className="text-indigo-400" />,
  },
  'Selected': {
    color: 'bg-emerald-500/5',
    border: 'border-emerald-500/30',
    badge: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    header: 'text-emerald-400',
    icon: <CheckCircle size={15} className="text-emerald-400" />,
  },
  'Rejected': {
    color: 'bg-red-500/5',
    border: 'border-red-500/30',
    badge: 'bg-red-500/10 text-red-400 border-red-500/20',
    header: 'text-red-400',
    icon: <XCircle size={15} className="text-red-400" />,
  },
};

const ScorePill: React.FC<{ label: string; value: number | null; color: string }> = ({ label, value, color }) => (
  value !== null ? (
    <div className={`text-center px-2 py-1 rounded ${color}`}>
      <p className="text-[9px] font-bold uppercase opacity-70">{label}</p>
      <p className="text-xs font-black">{value.toFixed(1)}</p>
    </div>
  ) : null
);

const CandidatePipeline: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedAppId, setSelectedAppId] = useState<number | null>(null);
  const [stages, setStages] = useState<Stages>({});
  // Track which candidates have completed their interview
  const [completedInterviews, setCompletedInterviews] = useState<Set<number>>(new Set());
  const [interviewApp, setInterviewApp] = useState<{ id: number; jobTitle: string } | null>(null);
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [toast, setToast] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const fetchPipeline = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get('/api/hr/pipeline');
      setStages(res.data);
    } catch (err) {
      console.error('Pipeline fetch error', err);
      setError('Failed to load candidate pipeline.');
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = async (e: React.MouseEvent, appId: number) => {
    e.stopPropagation();
    setActionLoading(appId);
    try {
      await api.post(`/api/applications/${appId}/select`);
      setToast({ type: 'success', message: 'Candidate marked as Selected! They can now start the interview.' });
      fetchPipeline();
      setTimeout(() => setToast(null), 3000);
    } catch (err: any) {
      setToast({ type: 'error', message: err?.response?.data?.detail || 'Failed to select candidate' });
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async (e: React.MouseEvent, appId: number) => {
    e.stopPropagation();
    setActionLoading(appId);
    try {
      await api.post(`/api/applications/${appId}/reject`);
      setToast({ type: 'success', message: 'Candidate rejected.' });
      fetchPipeline();
      setTimeout(() => setToast(null), 3000);
    } catch (err: any) {
      setToast({ type: 'error', message: err?.response?.data?.detail || 'Failed to reject candidate' });
    } finally {
      setActionLoading(null);
    }
  };

  useEffect(() => {
    fetchPipeline();
  }, []);

  const totalCandidates = Object.values(stages).reduce((acc, arr) => acc + arr.length, 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Candidate Pipeline</h2>
          <p className="text-sm text-zinc-500 mt-1">{totalCandidates} candidates across all stages</p>
        </div>
        <button
          onClick={fetchPipeline}
          disabled={loading}
          className="glass-btn-secondary text-xs flex items-center gap-2 disabled:opacity-50"
        >
          <RefreshCw size={13} className={loading ? 'animate-spin' : ''} /> Refresh
        </button>
      </div>

      {/* Toast Notification */}
      {toast && (
        <div className={`fixed top-4 right-4 px-4 py-3 rounded-lg border flex items-center gap-2 text-sm font-semibold z-50 animate-fade-in ${toast.type === 'success'
            ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
            : 'bg-red-500/10 border-red-500/20 text-red-400'
          }`}>
          {toast.type === 'success' ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
          {toast.message}
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
          <AlertCircle size={16} /> {error}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex justify-center py-16 text-amber-500">
          <Loader2 size={32} className="animate-spin" />
        </div>
      )}

      {/* Kanban Board */}
      {!loading && !error && (
        <div className="flex gap-4 overflow-x-auto pb-4">
          {Object.entries(STAGE_CONFIG).map(([stage, cfg]) => {
            const candidates = stages[stage] || [];
            return (
              <div
                key={stage}
                className={`flex-shrink-0 w-72 rounded-xl border ${cfg.border} ${cfg.color} flex flex-col`}
              >
                {/* Column Header */}
                <div className={`flex items-center justify-between px-4 py-3 border-b ${cfg.border}`}>
                  <div className="flex items-center gap-2">
                    {cfg.icon}
                    <h3 className={`text-sm font-bold ${cfg.header}`}>{stage}</h3>
                  </div>
                  <span className={`text-xs font-black px-2 py-0.5 rounded-full border ${cfg.badge}`}>
                    {candidates.length}
                  </span>
                </div>

                {/* Cards */}
                <div className="flex flex-col gap-3 p-3 overflow-y-auto max-h-[calc(100vh-280px)]">
                  {candidates.length === 0 && (
                    <div className="text-center py-8 text-zinc-600 text-xs">No candidates here</div>
                  )}

                  {candidates.map((cand) => (
                    <div
                      key={cand.application_id}
                      className={`bg-zinc-900/60 border border-zinc-800 rounded-lg p-4 transition-all group ${cand.application_status?.toLowerCase() === 'shortlisted' ? '' : 'cursor-pointer hover:border-zinc-700'
                        }`}
                      onClick={() => cand.application_status?.toLowerCase() !== 'shortlisted' && setSelectedAppId(cand.application_id)}
                    >
                      {/* Avatar + Name */}
                      <div className="flex items-start gap-3 mb-3">
                        <div className="w-9 h-9 rounded-full bg-gradient-to-br from-zinc-700 to-zinc-800 border border-zinc-700 flex items-center justify-center text-sm font-bold text-amber-400 shrink-0">
                          {cand.candidate_name?.charAt(0).toUpperCase()}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-semibold text-white truncate group-hover:text-amber-400 transition-colors">
                            {cand.candidate_name}
                          </p>
                          <p className="text-[11px] text-zinc-500 truncate">{cand.candidate_email}</p>
                        </div>
                      </div>

                      {/* Job */}
                      <div className="flex items-center gap-1.5 mb-3">
                        <Briefcase size={11} className="text-zinc-500 shrink-0" />
                        <p className="text-xs text-zinc-400 truncate">{cand.job_title}</p>
                      </div>

                      {/* Score Pills */}
                      <div className="flex gap-2 flex-wrap">
                        <ScorePill label="Resume" value={cand.resume_score} color="bg-amber-500/10 text-amber-400" />
                        <ScorePill label="Match" value={cand.match_score} color="bg-blue-500/10 text-blue-400" />
                        {cand.interview_score !== null && (
                          <ScorePill label="Interview" value={cand.interview_score} color="bg-emerald-500/10 text-emerald-400" />
                        )}
                      </div>

                      {/* Action buttons for Shortlisted candidates */}
                      {cand.application_status?.toLowerCase() === 'shortlisted' && (
                        <div className="flex gap-2 mt-3 pt-3 border-t border-zinc-800">
                          <button
                            onClick={(e) => handleSelect(e, cand.application_id)}
                            disabled={actionLoading === cand.application_id}
                            className="flex-1 px-2 py-1.5 rounded text-[11px] font-bold flex items-center justify-center gap-1.5 transition-all
                              bg-emerald-500/10 text-emerald-400 border border-emerald-500/20
                              hover:bg-emerald-500/20 disabled:opacity-50"
                          >
                            {actionLoading === cand.application_id ? (
                              <Loader2 size={11} className="animate-spin" />
                            ) : (
                              <CheckCircle2 size={11} />
                            )}
                            Select
                          </button>
                          <button
                            onClick={(e) => handleReject(e, cand.application_id)}
                            disabled={actionLoading === cand.application_id}
                            className="flex-1 px-2 py-1.5 rounded text-[11px] font-bold flex items-center justify-center gap-1.5 transition-all
                              bg-red-500/10 text-red-400 border border-red-500/20
                              hover:bg-red-500/20 disabled:opacity-50"
                          >
                            {actionLoading === cand.application_id ? (
                              <Loader2 size={11} className="animate-spin" />
                            ) : (
                              <XCircle size={11} />
                            )}
                            Reject
                          </button>
                        </div>
                      )}
                      <p className="text-[10px] text-zinc-600 mt-3 group-hover:text-zinc-400 transition-colors">
                        Click to view full profile →
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* AI Interview Modal */}
      {interviewApp && (
        <AIInterview
          applicationId={interviewApp.id}
          candidateName={''}
          jobTitle={interviewApp.jobTitle}
          onClose={() => setInterviewApp(null)}
          onComplete={() => {
            setInterviewApp(null);
            setCompletedInterviews(prev => new Set(prev).add(interviewApp.id));
            fetchPipeline();
          }}
        />
      )}

      {/* Candidate Profile Modal */}
      <CandidateProfileModal
        key={selectedAppId ?? 'closed'}
        applicationId={selectedAppId}
        onClose={() => setSelectedAppId(null)}
        onStatusChange={() => fetchPipeline()}
      />
    </div>
  );
};

export default CandidatePipeline;