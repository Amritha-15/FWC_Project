import React, { useState } from 'react';
import api from '../../../utils/api';
import { RefreshCw, AlertCircle, CheckCircle, ChevronDown, ChevronUp, Eye } from 'lucide-react';
import CandidateProfileModal from './CandidateProfileModal';

interface CandidateResult {
  application_id: number;
  candidate_name: string;
  candidate_email: string;
  application_status: string;
  resume_score: number | null;
  match_score: number | null;
  hiring_confidence_score: number | null;
  ranking_position: number | null;
  candidate_skills: string | null;
}

interface JobGroup {
  job_id: number;
  job_title: string;
  job_department: string;
  job_location: string;
  candidates: CandidateResult[];
}

interface ScreenAllResponse {
  success: boolean;
  message: string;
  jobs_processed: number;
  jobs_failed: Record<string, string>;
}

const ScoreBadge: React.FC<{ label: string; value: number | null; color: string }> = ({ label, value, color }) => (
  <div className="flex flex-col items-center bg-zinc-900/60 rounded-lg px-3 py-2 min-w-[72px]">
    <span className={`text-lg font-black ${color}`}>
      {value !== null && value !== undefined ? Number(value).toFixed(1) : '—'}
    </span>
    <span className="text-[10px] text-zinc-500 uppercase font-bold mt-0.5">{label}</span>
  </div>
);

interface JobResultCardProps {
  job: JobGroup;
  onViewCandidate: (appId: number) => void;
}

const JobResultCard: React.FC<JobResultCardProps> = ({ job, onViewCandidate }) => {
  const [expanded, setExpanded] = useState(true);

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900/40 overflow-hidden">
      {/* Job header */}
      <button
        onClick={() => setExpanded(e => !e)}
        className="w-full flex justify-between items-center px-4 py-3 hover:bg-zinc-800/30 transition-colors"
      >
        <div className="text-left">
          <p className="text-sm font-bold text-white">{job.job_title}</p>
          <p className="text-[10px] text-zinc-500 uppercase">{job.job_department} • {job.job_location}</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-zinc-400">{job.candidates.length} screened</span>
          {expanded ? <ChevronUp size={14} className="text-zinc-500" /> : <ChevronDown size={14} className="text-zinc-500" />}
        </div>
      </button>

      {/* Candidates */}
      {expanded && (
        <div className="divide-y divide-zinc-800/60">
          {job.candidates.length === 0 ? (
            <p className="text-xs text-zinc-500 px-4 py-3">No candidates were screened for this job.</p>
          ) : (
            job.candidates.map(cand => {
              const skills = cand.candidate_skills
                ? cand.candidate_skills.split(',').map(s => s.trim()).filter(Boolean)
                : [];

              return (
                <div key={cand.application_id} className="px-4 py-3">
                  {/* Name + status + View button */}
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex-1">
                      <p className="text-sm font-semibold text-white">{cand.candidate_name}</p>
                      <p className="text-xs text-zinc-500">{cand.candidate_email}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      {cand.ranking_position && (
                        <span className="text-[10px] font-bold text-zinc-300 bg-zinc-800 px-2 py-0.5 rounded">
                          Rank #{cand.ranking_position}
                        </span>
                      )}
                      <button
                        onClick={() => onViewCandidate(cand.application_id)}
                        className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 hover:bg-blue-500/20 transition-colors flex items-center gap-1"
                      >
                        <Eye size={12} /> View
                      </button>
                    </div>
                  </div>

                  {/* Score badges */}
                  <div className="flex gap-2 flex-wrap mb-2">
                    <ScoreBadge label="Resume" value={cand.resume_score} color="text-amber-400" />
                    <ScoreBadge label="Match" value={cand.match_score} color="text-amber-300" />
                    <ScoreBadge label="Confidence" value={cand.hiring_confidence_score} color="text-emerald-400" />
                  </div>

                  {/* Skills */}
                  {skills.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1">
                      {skills.map((skill, idx) => (
                        <span
                          key={idx}
                          className="px-1.5 py-0.5 text-[10px] rounded bg-zinc-800 text-zinc-300 border border-zinc-700"
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      )}
    </div>
  );
};

const AIScreening: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [screenedJobs, setScreenedJobs] = useState<JobGroup[]>([]);
  const [summary, setSummary] = useState<{ processed: number; failed: number } | null>(null);
  const [selectedAppId, setSelectedAppId] = useState<number | null>(null);

  const handleScreenAll = async () => {
    try {
      setLoading(true);
      setError('');
      setScreenedJobs([]);
      setSummary(null);

      // Run screening
      const res = await api.post('/api/ai/screen-all');
      const data: ScreenAllResponse = res.data;
      const failedCount = Object.keys(data.jobs_failed || {}).length;
      setSummary({ processed: data.jobs_processed, failed: failedCount });

      // Fetch fresh grouped results to show scores + skills
      const grouped = await api.get('/api/hr/applications-grouped');
      const jobs: JobGroup[] = (grouped.data || []).map((job: any) => ({
        job_id: job.job_id,
        job_title: job.job_title,
        job_department: job.job_department,
        job_location: job.job_location,
        // Only show candidates that have been screened (have a resume score)
        candidates: (job.candidates || []).filter((c: any) => c.resume_score !== null),
      })).filter((job: JobGroup) => job.candidates.length > 0);

      setScreenedJobs(jobs);

      if (failedCount > 0) {
        setError(`Screening finished with ${failedCount} failed job(s). Check backend logs for details.`);
      }
    } catch (e: any) {
      console.error(e);
      setError(e?.response?.data?.detail || 'Error triggering screening');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    try {
      const grouped = await api.get('/api/hr/applications-grouped');
      const jobs: JobGroup[] = (grouped.data || []).map((job: any) => ({
        job_id: job.job_id,
        job_title: job.job_title,
        job_department: job.job_department,
        job_location: job.job_location,
        candidates: (job.candidates || []).filter((c: any) => c.resume_score !== null),
      })).filter((job: JobGroup) => job.candidates.length > 0);

      setScreenedJobs(jobs);
    } catch (e: any) {
      setError('Failed to refresh results');
    }
  };

  return (
    <div className="p-6 max-w-4xl space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-white mb-1">AI Screening</h2>
        <p className="text-sm text-zinc-400">
          Screens only <span className="text-white font-medium">Applied</span> candidates across all open jobs.
          Click <span className="text-white font-medium">View</span> to review scores and make hiring decisions.
        </p>
      </div>

      {/* Run button */}
      <div className="flex gap-2">
        <button
          onClick={handleScreenAll}
          disabled={loading}
          className="glass-btn-primary px-5 py-2.5 rounded flex items-center gap-2 disabled:opacity-50"
        >
          <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
          {loading ? 'Running Screening…' : 'Run AI Screening (All Jobs)'}
        </button>
        {screenedJobs.length > 0 && (
          <button
            onClick={handleRefresh}
            className="glass-btn-secondary px-5 py-2.5 rounded flex items-center gap-2"
          >
            <RefreshCw size={15} />
            Refresh Results
          </button>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="p-3 rounded bg-red-900/30 border border-red-700 text-red-300 text-sm flex items-center gap-2">
          <AlertCircle size={14} /> {error}
        </div>
      )}

      {/* Summary */}
      {summary && !loading && (
        <div className="flex gap-3">
          <div className="flex-1 p-3 rounded bg-emerald-900/20 border border-emerald-800 text-center">
            <p className="text-2xl font-black text-emerald-400">{summary.processed}</p>
            <p className="text-[10px] text-zinc-400 uppercase mt-0.5">Jobs Processed</p>
          </div>
          <div className="flex-1 p-3 rounded bg-red-900/20 border border-red-800 text-center">
            <p className="text-2xl font-black text-red-400">{summary.failed}</p>
            <p className="text-[10px] text-zinc-400 uppercase mt-0.5">Jobs Failed</p>
          </div>
        </div>
      )}

      {/* Per-job results */}
      {screenedJobs.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <CheckCircle size={14} className="text-emerald-400" />
            <p className="text-sm font-semibold text-white">Screening Results</p>
          </div>
          {screenedJobs.map(job => (
            <JobResultCard
              key={job.job_id}
              job={job}
              onViewCandidate={setSelectedAppId}
            />
          ))}
          <p className="text-xs text-zinc-500 pt-1">
            Click <span className="text-zinc-300 font-medium">View</span> on any candidate to see full details, scores, and AI recommendation. Then decide to Select (Shortlisted) or Reject.
          </p>
        </div>
      )}

      {/* Loading skeleton */}
      {loading && (
        <div className="space-y-3">
          {[1, 2].map(i => (
            <div key={i} className="h-24 rounded-lg bg-zinc-800/40 animate-pulse" />
          ))}
        </div>
      )}

      {/* Modal */}
      <CandidateProfileModal
        key={selectedAppId ?? 'closed'}
        applicationId={selectedAppId}
        onClose={() => setSelectedAppId(null)}
        onSuccess={handleRefresh}
      />
    </div>
  );
};

export default AIScreening;