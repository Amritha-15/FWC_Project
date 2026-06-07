import React, { useEffect, useState } from 'react';
import AIInterview from '../../candidate/AIInterview';
import api from '../../../utils/api';
import {
  X, User, Briefcase, FileText, Star, Brain, Mic,
  CheckCircle2, XCircle, Loader2, AlertCircle, TrendingUp,
  MessageSquare, Award, Zap, ThumbsUp, ThumbsDown
} from 'lucide-react';

// ─── Types ────────────────────────────────────────────────────────────────────

interface InterviewResult {
  id: number;
  overall_score: number | null;
  communication_score: number | null;
  technical_score: number | null;
  problem_solving_score: number | null;
  confidence_score: number | null;
  recommendation: string | null;
  ai_feedback: string | null;
  created_at: string;
}

interface ProfileData {
  application: {
    id: number;
    application_status: string;
    resume_score: number | null;
    match_score: number | null;
    interview_score: number | null;
    ranking_position: number | null;
    hiring_confidence_score: number | null;
    applied_at: string;
    candidate_name?: string;
    job_title?: string;
  };
  candidate: {
    candidate_id: number;
    name: string;
    email: string;
    phone?: string;
    skills?: string;
    experience?: string;
    education?: string;
    resume_summary?: string;
    resume_quality_score?: number | null;
    skill_strength_score?: number | null;
  };
  job: {
    job_id: number;
    title: string;
    required_skills?: string;
    department?: string;
  };
  interview_result: InterviewResult | null;
}

interface Props {
  applicationId: number | null;
  onClose: () => void;
  onStatusChange?: () => void;
}

// ─── Score Ring ───────────────────────────────────────────────────────────────

const ScoreRing: React.FC<{ score: number | null; label: string; color: string }> = ({ score, label, color }) => {
  const val = score ?? 0;
  const radius = 28;
  const circ = 2 * Math.PI * radius;
  const offset = circ - (val / 100) * circ;
  return (
    <div className="flex flex-col items-center gap-1">
      <svg width="72" height="72" className="-rotate-90">
        <circle cx="36" cy="36" r={radius} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="6" />
        <circle cx="36" cy="36" r={radius} fill="none" stroke={color} strokeWidth="6"
          strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 0.6s ease' }} />
      </svg>
      <div className="text-center -mt-12 mb-4">
        <p className="text-lg font-black text-white">{score != null ? `${val.toFixed(0)}` : '—'}</p>
      </div>
      <p className="text-[10px] text-zinc-400 text-center uppercase tracking-wider font-bold">{label}</p>
    </div>
  );
};

// ─── Component ────────────────────────────────────────────────────────────────

const CandidateProfileModal: React.FC<Props> = ({ applicationId, onClose, onStatusChange }) => {
  const [showInterview, setShowInterview] = useState(false);
  const [data, setData] = useState<ProfileData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<'hire' | 'reject' | 'select' | null>(null);
  const [actionDone, setActionDone] = useState<string | null>(null);

  useEffect(() => {
    if (!applicationId) return;
    setLoading(true);
    setError(null);
    setData(null);
    setActionDone(null);
    api.get(`/api/hr/candidates/${applicationId}/profile`)
      .then(res => setData(res.data))
      .catch(() => setError('Failed to load candidate profile'))
      .finally(() => setLoading(false));
  }, [applicationId]);

  if (!applicationId) return null;

  // ── Decision handlers ──────────────────────────────────────────────────────

  const handleSelectForInterview = async () => {
    setActionLoading('select');
    try {
      await api.post(`/api/hr/applications/${applicationId}/select`);
      setActionDone('Selected');
      if (data) setData({ ...data, application: { ...data.application, application_status: 'Selected' } });
      onStatusChange?.();
      setShowInterview(true);
    } catch {
      setError('Failed to update status. Please try again.');
    } finally {
      setActionLoading(null);
    }
  };

  const handleHire = async () => {
    setActionLoading('hire');
    try {
      await api.post(`/api/hr/applications/${applicationId}/hire`);
      setActionDone('Hired');
      if (data) setData({ ...data, application: { ...data.application, application_status: 'Hired' } });
      onStatusChange?.();
    } catch {
      setError('Failed to update status. Please try again.');
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async () => {
    setActionLoading('reject');
    try {
      await api.post(`/api/hr/applications/${applicationId}/reject-post-interview`);
      setActionDone('Rejected');
      if (data) setData({ ...data, application: { ...data.application, application_status: 'Rejected' } });
      onStatusChange?.();
    } catch {
      setError('Failed to update status. Please try again.');
    } finally {
      setActionLoading(null);
    }
  };

  const status = data?.application.application_status ?? '';
  const ir = data?.interview_result;
  const alreadyDecided = ['Hired', 'Rejected'].includes(status);

  const CandidateProfileModalContent = () => (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: 'rgba(0,0,0,0.80)', backdropFilter: 'blur(8px)' }}
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-3xl rounded-2xl overflow-hidden flex flex-col"
        style={{
          background: 'linear-gradient(145deg, #0f0f14 0%, #141420 100%)',
          border: '1px solid rgba(255,255,255,0.06)',
          maxHeight: '92vh',
          boxShadow: '0 25px 80px rgba(0,0,0,0.8)',
        }}
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/5 shrink-0">
          <div>
            <p className="text-xs text-indigo-400 font-bold uppercase tracking-widest mb-0.5">Candidate Profile</p>
            <h3 className="text-white font-bold text-base">
              {data?.candidate.name ?? 'Loading…'}
              {data?.job.title && <span className="text-zinc-400 font-normal"> · {data.job.title}</span>}
            </h3>
          </div>
          <button onClick={onClose} className="text-zinc-500 hover:text-white transition-colors p-1">
            <X size={18} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-6">
          {loading && (
            <div className="flex items-center justify-center py-20">
              <Loader2 size={32} className="animate-spin text-indigo-400" />
            </div>
          )}

          {error && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-center gap-2">
              <AlertCircle size={14} /> {error}
            </div>
          )}

          {data && (
            <>
              <div className="flex flex-wrap gap-2 items-center">
                <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase border ${status === 'Hired' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                  status === 'Rejected' ? 'bg-red-500/10 text-red-400 border-red-500/20' :
                    status === 'Selected' ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20' :
                      'bg-zinc-800 text-zinc-400 border-zinc-700'
                  }`}>{status}</span>
                {data.application.ranking_position && (
                  <span className="px-2 py-0.5 rounded text-[10px] bg-amber-500/10 text-amber-400 border border-amber-500/20 font-bold">
                    Rank #{data.application.ranking_position}
                  </span>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="bg-zinc-900/50 rounded-xl p-4 border border-zinc-800 space-y-2">
                  <p className="text-[10px] uppercase font-bold text-zinc-500 tracking-wider flex items-center gap-1.5">
                    <User size={11} /> Candidate
                  </p>
                  <p className="text-sm font-semibold text-white">{data.candidate.name}</p>
                  <p className="text-xs text-zinc-400">{data.candidate.email}</p>
                  {data.candidate.phone && <p className="text-xs text-zinc-500">{data.candidate.phone}</p>}
                  {data.candidate.education && <p className="text-xs text-zinc-400 mt-1">{data.candidate.education}</p>}
                </div>
                <div className="bg-zinc-900/50 rounded-xl p-4 border border-zinc-800 space-y-2">
                  <p className="text-[10px] uppercase font-bold text-zinc-500 tracking-wider flex items-center gap-1.5">
                    <Briefcase size={11} /> Scores
                  </p>
                  {[
                    ['Resume', data.application.resume_score, 'text-amber-400'],
                    ['Match', data.application.match_score, 'text-sky-400'],
                    ['Confidence', data.application.hiring_confidence_score, 'text-violet-400'],
                    ['Interview', data.application.interview_score, 'text-emerald-400'],
                  ].map(([label, val, cls]) => (
                    <div key={label as string} className="flex justify-between items-center">
                      <span className="text-xs text-zinc-500">{label as string}</span>
                      <span className={`text-xs font-bold ${cls as string}`}>
                        {val != null ? `${Number(val).toFixed(1)}` : '—'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {data.candidate.skills && (
                <div className="bg-zinc-900/50 rounded-xl p-4 border border-zinc-800">
                  <p className="text-[10px] uppercase font-bold text-zinc-500 tracking-wider mb-2 flex items-center gap-1.5">
                    <Zap size={11} /> Skills
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {data.candidate.skills.split(',').map((s, i) => (
                      <span key={i} className="text-[11px] px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/15">
                        {s.trim()}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {data.candidate.resume_summary && (
                <div className="bg-zinc-900/50 rounded-xl p-4 border border-zinc-800">
                  <p className="text-[10px] uppercase font-bold text-zinc-500 tracking-wider mb-2 flex items-center gap-1.5">
                    <FileText size={11} /> Resume Summary
                  </p>
                  <p className="text-xs text-zinc-300 leading-relaxed">{data.candidate.resume_summary}</p>
                </div>
              )}
              {!alreadyDecided && (
                <div className="bg-zinc-900/50 rounded-xl p-4 border border-zinc-800">
                  <p className="text-xs text-zinc-500 mb-3">
                    Resume screening decision
                  </p>

                  <div className="flex gap-3">
                    <button
                      onClick={handleSelectForInterview}
                      disabled={actionLoading !== null}
                      className="flex-1 py-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                    >
                      Select
                    </button>

                    <button
                      onClick={handleReject}
                      disabled={actionLoading !== null}
                      className="flex-1 py-2 rounded-lg bg-red-500/10 text-red-400 border border-red-500/20"
                    >
                      Reject
                    </button>
                  </div>
                </div>
              )}

              <div className="rounded-xl border overflow-hidden"
                style={{ borderColor: ir ? 'rgba(99,102,241,0.25)' : 'rgba(255,255,255,0.06)' }}>

                <div className="px-4 py-3 flex items-center gap-2"
                  style={{ background: ir ? 'rgba(99,102,241,0.08)' : 'rgba(255,255,255,0.02)' }}>
                  <Mic size={14} className={ir ? 'text-indigo-400' : 'text-zinc-600'} />
                  <p className="text-sm font-bold text-white">AI Interview Feedback</p>
                  {!ir && <span className="text-xs text-zinc-500 ml-auto">No interview taken yet</span>}
                </div>

                {ir ? (
                  <div className="p-5 space-y-5">
                    <div className="grid grid-cols-5 gap-2">
                      <ScoreRing score={ir.overall_score} label="Overall" color="#818cf8" />
                      <ScoreRing score={ir.communication_score} label="Communication" color="#34d399" />
                      <ScoreRing score={ir.technical_score} label="Technical" color="#f59e0b" />
                      <ScoreRing score={ir.problem_solving_score} label="Problem Solv." color="#38bdf8" />
                      <ScoreRing score={ir.confidence_score} label="Confidence" color="#a78bfa" />
                    </div>

                    {ir.recommendation && (
                      <div className="flex items-center gap-2">
                        <Award size={13} className="text-amber-400" />
                        <span className="text-xs text-zinc-400">AI Recommendation:</span>
                        <span className={`text-xs font-bold px-2 py-0.5 rounded-full border ${ir.recommendation.toLowerCase().includes('hire') || ir.recommendation.toLowerCase().includes('strong')
                          ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                          : ir.recommendation.toLowerCase().includes('reject')
                            ? 'bg-red-500/10 text-red-400 border-red-500/20'
                            : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                          }`}>
                          {ir.recommendation}
                        </span>
                      </div>
                    )}

                    {ir.ai_feedback && (
                      <div className="bg-zinc-950/60 rounded-lg p-4 border border-zinc-800">
                        <p className="text-[10px] uppercase font-bold text-zinc-500 tracking-wider mb-2 flex items-center gap-1.5">
                          <MessageSquare size={11} /> AI Feedback
                        </p>
                        <p className="text-xs text-zinc-300 leading-relaxed">{ir.ai_feedback}</p>
                      </div>
                    )}

                    <p className="text-[10px] text-zinc-600">
                      Evaluated {new Date(ir.created_at).toLocaleString()}
                    </p>

                    {!alreadyDecided && (
                      <div className="pt-2 border-t border-white/5">
                        <p className="text-xs text-zinc-500 mb-3">Make your hiring decision based on the AI interview results:</p>
                        <div className="flex gap-3">
                          <button
                            onClick={handleHire}
                            disabled={actionLoading !== null}
                            className="flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg font-bold text-sm transition-all
                              bg-emerald-500/10 text-emerald-400 border border-emerald-500/20
                              hover:bg-emerald-500/20 hover:border-emerald-500/40 disabled:opacity-50"
                          >
                            {actionLoading === 'hire'
                              ? <Loader2 size={15} className="animate-spin" />
                              : <ThumbsUp size={15} />}
                            Hire
                          </button>
                          <button
                            onClick={handleReject}
                            disabled={actionLoading !== null}
                            className="flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg font-bold text-sm transition-all
                              bg-red-500/10 text-red-400 border border-red-500/20
                              hover:bg-red-500/20 hover:border-red-500/40 disabled:opacity-50"
                          >
                            {actionLoading === 'reject'
                              ? <Loader2 size={15} className="animate-spin" />
                              : <ThumbsDown size={15} />}
                            Reject
                          </button>
                        </div>
                      </div>
                    )}

                    {alreadyDecided && (
                      <div className={`flex items-center gap-2 p-3 rounded-lg border ${status === 'Hired'
                        ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                        : 'bg-red-500/10 border-red-500/20 text-red-400'
                        }`}>
                        {status === 'Hired' ? <CheckCircle2 size={16} /> : <XCircle size={16} />}
                        <p className="text-sm font-bold">
                          Decision recorded: {status}
                          {actionDone && ' — Candidate notified by email.'}
                        </p>
                      </div>
                    )}

                  </div>
                ) : (
                  <div className="px-5 py-8 text-center">
                    <Brain size={32} className="mx-auto text-zinc-700 mb-3" />
                    <p className="text-sm text-zinc-500">The candidate hasn't completed their AI interview yet.</p>
                    <p className="text-xs text-zinc-600 mt-1">Once they do, scores and feedback will appear here.</p>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );

  const interviewModal = showInterview && (
    <AIInterview
      applicationId={applicationId}
      candidateName={data?.application.candidate_name || data?.candidate.name || ''}
      jobTitle={data?.application.job_title || data?.job.title || ''}
      onClose={() => setShowInterview(false)}
    />
  );

  return (
    <>
      {interviewModal}
      <CandidateProfileModalContent />
    </>
  );
};

export default CandidateProfileModal;