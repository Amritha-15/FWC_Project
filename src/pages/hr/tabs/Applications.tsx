import React, { useEffect, useState } from 'react';
import GlassCard from '../../../components/ui/GlassCard';
import api from '../../../utils/api';
import { RefreshCw, Check, AlertCircle } from 'lucide-react';
import CandidateProfileModal from './CandidateProfileModal';

interface CandidateItem {
  application_id: number;
  candidate_id: number;
  candidate_name: string;
  candidate_email: string;
  application_status: string;
  resume_score: number | null;
  match_score: number | null;
  ranking_position: number | null;
  hiring_confidence_score: number | null;
  candidate_skills: string;
  resume_quality_score: number | null;
  applied_at: string;
}

interface JobGroup {
  job_id: number;
  job_title: string;
  job_department: string;
  job_location: string;
  job_status: string;
  job_required_skills: string;
  candidates: CandidateItem[];
}

const Applications: React.FC = () => {
  const [jobs, setJobs] = useState<JobGroup[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [selectedAppId, setSelectedAppId] = useState<number | null>(null);
  const [screeningJobId, setScreeningJobId] = useState<number | 'all' | null>(null);

  const normalizeScores = (jobsData) => {
    return jobsData.map((job) => {
      const candidates = job.candidates.map((c) => ({
        ...c,
        resume_score: c.resume_score !== null ? Number(c.resume_score) : null,
        match_score: c.match_score !== null ? Number(c.match_score) : null,
        hiring_confidence_score: c.hiring_confidence_score !== null ? Number(c.hiring_confidence_score) : null,
      }));
      return { ...job, candidates };
    });
  };

  const fetchGrouped = async () => {
    try {
      const res = await api.get('/api/hr/applications-grouped');
      const normalized = normalizeScores(res.data);
      setJobs([...normalized]);
    } catch (err) {
      console.error('Applications load error', err);
      if (err?.response?.status === 401) {
        setError('Authentication required. Please log in.');
      } else {
        setError('Failed to load applications');
      }
    }
  };

  useEffect(() => {
    setLoading(true);
    fetchGrouped().finally(() => setLoading(false));
  }, []);

  const triggerScreenAll = async () => {
    setError(null);
    setSuccess(null);
    setScreeningJobId('all');
    try {
      const postRes = await api.post('/api/ai/screen-all');
      const data = postRes.data;
      const failedCount = data?.jobs_failed ? Object.keys(data.jobs_failed).length : 0;
      const res = await api.get('/api/hr/applications-grouped');
      const normalized = normalizeScores(res.data);
      setJobs([...normalized]);
      if (failedCount > 0) {
        setError(`Screening finished with ${failedCount} failed job(s). Check backend logs.`);
      } else {
        setSuccess(`AI Resume Screening completed. ${data?.jobs_processed ?? ''} job(s) processed.`);
      }
    } catch (err: any) {
      console.error(err);
      setError(err?.response?.data?.detail || 'Unable to start AI Screening');
    } finally {
      setScreeningJobId(null);
    }
  };

  const triggerScreenJob = async (jobId: number) => {
    setError(null);
    setSuccess(null);
    setScreeningJobId(jobId);
    try {
      await api.post(`/api/ai/screen-job/${jobId}`);
      const res = await api.get('/api/hr/applications-grouped');
      const normalized = normalizeScores(res.data);
      setJobs([...normalized]);
      setTimeout(fetchGrouped, 2000);
      setSuccess('Resume screening completed successfully.');
    } catch (err: any) {
      console.error(err);
      setError(err?.response?.data?.detail || 'Resume screening failed.');
    } finally {
      setScreeningJobId(null);
    }
  };

  return (
    <div className="space-y-5 animate-fade-in p-4 bg-zinc-900/50">
      {error && (
        <div className="p-3 rounded bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-center gap-2">
          <AlertCircle size={14} /> {error}
        </div>
      )}
      {success && (
        <div className="p-3 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs flex items-center gap-2">
          <Check size={14} /> {success}
        </div>
      )}

      <div className="flex justify-between items-center w-full mb-4">
        <h2 className="text-lg font-bold text-white">Active Applications (Job‑Centric)</h2>
        <button
          onClick={triggerScreenAll}
          disabled={screeningJobId !== null}
          className="glass-btn-primary text-xs flex items-center gap-1.5 disabled:opacity-50"
        >
          <RefreshCw size={14} className={screeningJobId === 'all' ? 'animate-spin' : ''} />
          Run AI Screen (All Jobs)
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <RefreshCw size={36} className="animate-spin text-amber-500" />
        </div>
      ) : (
        <div className="grid gap-6">
          {jobs.map((job) => (
            <GlassCard key={job.job_id} hoverable={false} className="border border-zinc-800">
              <div className="flex justify-between items-start p-4">
                <div>
                  <h3 className="text-xl font-bold text-white">{job.job_title}</h3>
                  <p className="text-xs text-zinc-500 mt-1 uppercase">{job.job_department} • {job.job_location}</p>
                </div>
                <button
                  onClick={() => triggerScreenJob(job.job_id)}
                  disabled={screeningJobId !== null}
                  className="glass-btn-secondary text-xs flex items-center gap-1.5 disabled:opacity-50"
                >
                  <RefreshCw size={12} className={screeningJobId === job.job_id ? 'animate-spin' : ''} />
                  Screen This Job
                </button>
              </div>
              <div className="px-4 pb-4">
                <p className="text-[10px] uppercase font-bold text-zinc-500 mb-2">Applicants ({job.candidates.length})</p>
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {job.candidates.map((cand) => (
                    <div key={cand.application_id} className="flex justify-between items-center bg-zinc-900/30 rounded p-2">
                      <div>
                        <p className="text-sm font-medium text-white">{cand.candidate_name}</p>
                        <p className="text-xs text-zinc-400">{cand.candidate_email}</p>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {cand.application_status && (
                            <span className={`px-1.5 py-0.5 text-[10px] rounded ${cand.application_status === 'Selected'
                              ? 'bg-emerald-500/10 text-emerald-400'
                              : cand.application_status === 'Shortlisted'
                                ? 'bg-amber-500/10 text-amber-400'
                                : 'bg-zinc-800/50 text-zinc-400'
                              }`}>
                              {cand.application_status}
                            </span>
                          )}
                          {cand.resume_score !== null && (
                            <span className="text-amber-400 text-xs">Resume: {Number(cand.resume_score).toFixed(1)}</span>
                          )}
                          {cand.match_score !== null && (
                            <span className="text-amber-300 text-xs">Match: {Number(cand.match_score).toFixed(1)}</span>
                          )}
                          {cand.ranking_position !== null && (
                            <span className="text-zinc-300 text-xs">Rank: #{cand.ranking_position}</span>
                          )}
                          {cand.hiring_confidence_score !== null && (
                            <span className="text-emerald-400 text-xs">Confidence: {Number(cand.hiring_confidence_score).toFixed(1)}</span>
                          )}
                        </div>
                      </div>
                      <div className="flex flex-col gap-1 items-end">
                        <button
                          className="glass-btn-secondary text-xs"
                          onClick={() => setSelectedAppId(cand.application_id)}
                        >
                          View
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </GlassCard>
          ))}
        </div>
      )}

      <CandidateProfileModal
        key={selectedAppId ?? 'closed'}
        applicationId={selectedAppId}
        onClose={() => setSelectedAppId(null)}
        onStatusChange={() => { fetchGrouped(); }}
      />
    </div>
  );
};

export default Applications;