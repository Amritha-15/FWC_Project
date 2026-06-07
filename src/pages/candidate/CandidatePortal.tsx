import React, { useState, useEffect, useRef } from 'react';

import DashboardLayout from '../../components/layout/DashboardLayout';
import GlassCard from '../../components/ui/GlassCard';
import api from '../../utils/api';
import { useAuth } from '../../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import AIInterview from './AIInterview';
import {
  Briefcase, FileText, Upload, Search, MapPin, DollarSign,
  Clock, CheckCircle2, XCircle, AlertCircle, RefreshCw, Send,
  User, Mail, Phone, Building2, ExternalLink, Bell, Mic
} from 'lucide-react';

/* ─── Types ─── */
interface Job {
  id: number;
  title: string;
  description: string;
  required_skills: string;
  experience_required: string;
  department: string;
  location: string;
  salary_range: string;
  status: string;
}

interface Application {
  id: number;
  job_id: number;
  job_title?: string;
  application_status: string;
  applied_at: string;
  resume_score: number | null;
  match_score: number | null;
  ranking_position: number | null;
  interview_score: number | null;
}

interface CandidateProfile {
  id: number;
  user_id: number;
  name: string;
  email: string;
  phone?: string;
  resume_url?: string;
  skills?: string;
  experience?: string;
  education?: string;
}

interface Notification {
  id: number;
  message: string;
  type: string;
  is_read: boolean;
  created_at: string;
}

/* ─── Status badge helper ─── */
const statusStyle = (s: string) => {
  const lower = s.toLowerCase();
  if (lower.includes('selected') || lower.includes('hired'))
    return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
  if (lower.includes('rejected'))
    return 'bg-red-500/10 text-red-400 border-red-500/20';
  if (lower.includes('interview'))
    return 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20';
  if (lower.includes('shortlisted'))
    return 'bg-amber-500/10 text-amber-500 border-amber-500/20';
  return 'bg-zinc-800 text-zinc-400 border-zinc-700/30';
};

/* ═══════════════════════════════════════════════════════
   Component
   ═══════════════════════════════════════════════════════ */
export const CandidatePortal: React.FC = () => {

  const { user } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('jobs');

  /* ─── Data ─── */
  const [jobs, setJobs] = useState<Job[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [profile, setProfile] = useState<CandidateProfile | null>(null);
  const [notifications, setNotifications] = useState<Notification[]>([]);

  /* ─── UI State ─── */
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [applyingId, setApplyingId] = useState<number | null>(null);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  /* ─── AI Interview state ─── */
  const [interviewApp, setInterviewApp] = useState<{
    id: number;
    jobTitle: string;
  } | null>(null);
  // Set of application_ids for which the AI interview has already been submitted
  const [completedInterviews, setCompletedInterviews] = useState<Set<number>>(new Set());

  /* ─── Data loaders ─── */
  const fetchJobs = async () => {
    try {
      const res = await api.get('/api/candidate/jobs');
      setJobs(res.data);
    } catch (err: any) {
      console.error('Failed to fetch jobs', err);
      setError(err?.response?.data?.detail || 'Failed to load jobs');
    }
  };

  const fetchApplications = async () => {
    try {
      const res = await api.get('/api/candidate/applications');
      setApplications(res.data);
      // For every application that is in a post-interview state, mark it completed
      // so the Start Interview button is disabled without an extra round-trip.
      // Also do a lightweight check via interview-results for 'selected' apps.
      const selectedApps: Application[] = (res.data as Application[]).filter(
        (a) => (a.application_status.toLowerCase() === 'selected' || a.application_status.toLowerCase() === 'shortlisted') && a.interview_score != null
      );
      if (selectedApps.length > 0) {
        setCompletedInterviews(new Set(selectedApps.map((a) => a.id)));
      }
    } catch (err: any) {
      console.error('Failed to fetch applications', err);
      setError(err?.response?.data?.detail || 'Failed to load applications');
    }
  };

  const fetchProfile = async () => {
    try {
      const res = await api.get('/api/candidate/profile');
      setProfile(res.data);
    } catch (err: any) {
      console.error('Failed to fetch profile', err);
      setError(err?.response?.data?.detail || 'Failed to load profile');
    }
  };

  const fetchNotifications = async () => {
    try {
      const res = await api.get('/api/candidate/notifications');
      setNotifications(res.data);
    } catch (err: any) {
      console.error('Failed to fetch notifications', err);
      setError(err?.response?.data?.detail || 'Failed to load notifications');
    }
  };

  const { loading: authLoading } = useAuth();
  useEffect(() => {
    if (authLoading) return;
    setError(null);
    setSuccess(null);
    setLoading(true);
    const load = async () => {
      await Promise.all([fetchJobs(), fetchApplications(), fetchProfile(), fetchNotifications()]);
      setLoading(false);
    };
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, authLoading]);

  /* ─── Actions ─── */
  const applyToJob = async (jobId: number) => {
    setError(null);
    setSuccess(null);
    setApplyingId(jobId);
    try {
      await api.post(`/api/candidate/jobs/${jobId}/apply`);
      setSuccess('Application submitted successfully!');
      await fetchApplications();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to apply. You may have already applied.');
    } finally {
      setApplyingId(null);
    }
  };

  const uploadResume = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    setSuccess(null);
    try {
      const formData = new FormData();
      formData.append('file', file);
      await api.post('/api/candidate/upload_resume', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setSuccess('Resume uploaded successfully!');
      await fetchProfile();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Resume upload failed');
    } finally {
      setUploading(false);
    }
  };

  /* ─── Derived data ─── */
  const appliedJobIds = new Set(applications.map((a) => a.job_id));
  const filteredJobs = jobs.filter(
    (j) =>
      j.status === 'Open' &&
      (j.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        j.department.toLowerCase().includes(searchQuery.toLowerCase()) ||
        j.required_skills.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  /* ═══════════════════════════════════════════════════════
     Render
     ═══════════════════════════════════════════════════════ */
  return (
    <DashboardLayout activeTab={activeTab} onTabChange={setActiveTab} title="Candidate Career Portal">
      {/* Alerts */}
      {error && (
        <div className="p-3.5 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-center gap-2.5 animate-fade-in">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}
      {success && (
        <div className="p-3.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs flex items-center gap-2.5 animate-fade-in">
          <CheckCircle2 size={16} />
          <span>{success}</span>
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-20">
          <RefreshCw size={36} className="animate-spin text-amber-500" />
        </div>
      ) : (
        <>
          {/* ──────────────── BROWSE JOBS ──────────────── */}
          {activeTab === 'jobs' && (
            <div className="space-y-6 animate-fade-in">
              {/* Header + Search */}
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div>
                  <h2 className="text-lg font-bold text-white">Open Positions</h2>
                  <p className="text-xs text-zinc-500">Discover roles that match your expertise</p>
                </div>
                <div className="relative w-full sm:w-72">
                  <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
                  <input
                    type="text"
                    placeholder="Search title, dept, skills…"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full glass-input pl-10"
                  />
                </div>
              </div>

              {/* Job Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                {filteredJobs.map((job) => {
                  const alreadyApplied = appliedJobIds.has(job.id);
                  return (
                    <GlassCard key={job.id} hoverable className="border border-zinc-800 flex flex-col justify-between group">
                      <div>
                        <div className="flex items-start justify-between">
                          <h3 className="font-bold text-md text-white leading-tight group-hover:text-amber-500 transition-colors">
                            {job.title}
                          </h3>
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shrink-0 ml-2">
                            Open
                          </span>
                        </div>

                        <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-[11px] text-zinc-500">
                          <span className="flex items-center gap-1"><Building2 size={12} />{job.department}</span>
                          <span className="flex items-center gap-1"><MapPin size={12} />{job.location}</span>
                          <span className="flex items-center gap-1"><DollarSign size={12} />{job.salary_range}</span>
                          <span className="flex items-center gap-1"><Clock size={12} />{job.experience_required}</span>
                        </div>

                        <p className="text-zinc-400 text-xs mt-3 line-clamp-3 leading-relaxed">{job.description}</p>

                        <div className="mt-3">
                          <p className="text-[10px] uppercase font-bold text-zinc-500 tracking-wider mb-1.5">Skills Required</p>
                          <div className="flex flex-wrap gap-1.5">
                            {job.required_skills ? (
                              job.required_skills.split(',').map((skill, i) => (
                                <span key={i} className="text-[10px] px-2 py-0.5 rounded bg-amber-500/5 text-amber-500 border border-amber-500/10">
                                  {skill.trim()}
                                </span>
                              ))
                            ) : (
                              <span className="text-xs text-zinc-500">No skills listed</span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Apply CTA */}
                      <div className="mt-5 pt-4 border-t border-zinc-900">
                        {alreadyApplied ? (
                          <div className="flex items-center gap-2 text-xs text-emerald-400 font-semibold">
                            <CheckCircle2 size={16} /> Already Applied
                          </div>
                        ) : (
                          <button
                            onClick={() => applyToJob(job.id)}
                            disabled={applyingId === job.id}
                            className="w-full glass-btn-primary text-xs flex items-center justify-center gap-2 disabled:opacity-50"
                          >
                            {applyingId === job.id ? (
                              <RefreshCw size={14} className="animate-spin" />
                            ) : (
                              <Send size={14} />
                            )}
                            {applyingId === job.id ? 'Submitting…' : 'Apply Now'}
                          </button>
                        )}
                      </div>
                    </GlassCard>
                  );
                })}
              </div>

              {filteredJobs.length === 0 && (
                <div className="text-center py-16">
                  <Briefcase size={48} className="mx-auto text-zinc-800 mb-4" />
                  <p className="text-zinc-500 text-sm">No positions match your search.</p>
                </div>
              )}
            </div>
          )}

          {/* ──────────────── MY APPLICATIONS ──────────────── */}
          {activeTab === 'applications' && (
            <div className="space-y-6 animate-fade-in">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-bold text-white">My Applications</h2>
              </div>

              {applications.length === 0 ? (
                <div className="text-center py-16">
                  <FileText size={48} className="mx-auto text-zinc-800 mb-4" />
                  <p className="text-zinc-500 text-sm">You haven't applied to any positions yet.</p>
                </div>
              ) : (
                <GlassCard hoverable={false} className="border border-zinc-800 overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="border-b border-zinc-800 text-xs font-bold uppercase tracking-wider text-zinc-500">
                          <th className="py-3 px-4">Position</th>
                          <th className="py-3 px-4">Applied</th>
                          <th className="py-3 px-4">AI Score</th>
                          <th className="py-3 px-4">Match</th>
                          <th className="py-3 px-4">Interview</th>
                          <th className="py-3 px-4">Rank</th>
                          <th className="py-3 px-4">Status</th>
                          <th className="py-3 px-4 text-right">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-zinc-900 text-sm">
                        {applications.map((app) => (
                          <tr key={app.id} className="hover:bg-zinc-900/20 transition-colors">
                            <td className="py-3 px-4 font-semibold text-zinc-200">
                              {app.job_title || `Job #${app.job_id}`}
                            </td>
                            <td className="py-3 px-4 text-zinc-400 text-xs">
                              {new Date(app.applied_at).toLocaleDateString()}
                            </td>
                            <td className="py-3 px-4 font-mono text-xs">
                              <span className="text-amber-500 font-bold">
                                {app.resume_score != null ? `${app.resume_score}%` : '—'}
                              </span>
                            </td>
                            <td className="py-3 px-4 font-mono text-xs">
                              <span className="text-amber-500 font-bold">
                                {app.match_score != null ? `${app.match_score}%` : '—'}
                              </span>
                            </td>
                            <td className="py-3 px-4 font-mono text-xs">
                              <span className="text-indigo-400 font-bold">
                                {app.interview_score != null ? `${Number(app.interview_score).toFixed(1)}` : '—'}
                              </span>
                            </td>
                            <td className="py-3 px-4 font-mono text-xs">
                              <span className="text-amber-600 font-bold">
                                {app.ranking_position != null ? `#${app.ranking_position}` : '—'}
                              </span>
                            </td>
                            <td className="py-3 px-4">
                              <span className={`inline-flex px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${statusStyle(app.application_status)}`}>
                                {app.application_status}
                              </span>
                              {app.application_status.toLowerCase() === 'hired' && (
                                <p className="text-[9px] text-emerald-400 mt-0.5 font-semibold">🎉 Offer incoming</p>
                              )}
                              {app.application_status.toLowerCase() === 'rejected' && (
                                <p className="text-[9px] text-zinc-500 mt-0.5">Not selected</p>
                              )}
                            </td>
                            <td className="py-3 px-4 text-right">
                              {/* AI Interview button — visible when Selected */}
                              {app.application_status.toLowerCase() === 'selected' && (
                                completedInterviews.has(app.id) ? (
                                  <div className="flex items-center gap-1.5 justify-end text-[11px] font-bold text-emerald-400">
                                    <CheckCircle2 size={13} /> Interview Submitted
                                  </div>
                                ) : (
                                  <button
                                    onClick={() => setInterviewApp({
                                      id: app.id,
                                      jobTitle: app.job_title || `Job #${app.job_id}`,
                                    })}
                                    className="px-3 py-1.5 rounded bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-[11px] font-bold flex items-center gap-1.5 ml-auto hover:bg-indigo-500/20 transition-all"
                                  >
                                    <Mic size={13} /> Start Interview
                                  </button>
                                )
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </GlassCard>
              )}
            </div>
          )}

          {/* ──────────────── PROFILE / RESUME ──────────────── */}
          {activeTab === 'profile' && (
            <div className="space-y-6 animate-fade-in">
              <div>
                <h2 className="text-lg font-bold text-white">My Resume & Profile</h2>
                <p className="text-xs text-zinc-500">Keep your profile polished for AI screening</p>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Profile card */}
                <GlassCard hoverable={false} className="lg:col-span-1 border border-zinc-800">
                  <div className="flex flex-col items-center text-center">
                    <div className="w-20 h-20 rounded-full bg-gradient-to-br from-amber-400/20 to-amber-600/20 border-2 border-amber-500/30 flex items-center justify-center text-3xl font-black text-amber-500 mb-4">
                      {user?.name?.charAt(0).toUpperCase() || 'C'}
                    </div>
                    <h3 className="text-lg font-bold text-white">{profile?.name || user?.name || 'Candidate'}</h3>
                    <p className="text-xs text-zinc-500 mt-1">{profile?.email || user?.email}</p>

                    {profile?.phone && (
                      <p className="text-xs text-zinc-500 flex items-center gap-1 mt-2"><Phone size={12} />{profile.phone}</p>
                    )}

                    <div className="w-full mt-6 pt-4 border-t border-zinc-900 space-y-3 text-left">
                      {profile?.experience && (
                        <div>
                          <p className="text-[10px] uppercase font-bold text-zinc-500 tracking-wider">Experience</p>
                          <p className="text-xs text-zinc-300 mt-0.5">{profile.experience}</p>
                        </div>
                      )}
                      {profile?.education && (
                        <div>
                          <p className="text-[10px] uppercase font-bold text-zinc-500 tracking-wider">Education</p>
                          <p className="text-xs text-zinc-300 mt-0.5">{profile.education}</p>
                        </div>
                      )}
                    </div>
                  </div>
                </GlassCard>

                {/* Resume Upload & Skills */}
                <GlassCard hoverable={false} className="lg:col-span-2 border border-zinc-800 space-y-6">
                  <div>
                    <p className="text-[10px] uppercase font-bold text-zinc-500 tracking-wider mb-3">Resume Document</p>
                    {profile?.resume_url ? (
                      <div className="flex items-center justify-between p-4 rounded-lg bg-emerald-500/5 border border-emerald-500/10">
                        <div className="flex items-center gap-3">
                          <FileText size={20} className="text-emerald-400" />
                          <div>
                            <p className="text-sm font-semibold text-emerald-400">Resume Uploaded</p>
                            <p className="text-[10px] text-zinc-500 mt-0.5 truncate max-w-[200px]">{profile.resume_url}</p>
                          </div>
                        </div>
                        <button onClick={() => fileInputRef.current?.click()} className="glass-btn-secondary text-xs">
                          Replace
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => fileInputRef.current?.click()}
                        disabled={uploading}
                        className="w-full py-10 rounded-lg border-2 border-dashed border-zinc-800 hover:border-amber-500/30 bg-zinc-950/50 text-center transition-all duration-300 group"
                      >
                        <Upload size={32} className="mx-auto text-zinc-600 group-hover:text-amber-500 transition-colors mb-3" />
                        <p className="text-sm text-zinc-400 group-hover:text-zinc-200 font-semibold transition-colors">
                          {uploading ? 'Uploading…' : 'Click to upload your resume'}
                        </p>
                        <p className="text-[10px] text-zinc-600 mt-1">PDF, DOCX, or TXT · Max 10 MB</p>
                      </button>
                    )}
                    <input
                      ref={fileInputRef}
                      type="file"
                      className="hidden"
                      accept=".pdf,.doc,.docx,.txt"
                      onChange={uploadResume}
                    />
                  </div>

                  {profile?.skills && (
                    <div>
                      <p className="text-[10px] uppercase font-bold text-zinc-500 tracking-wider mb-2">Skills Profile</p>
                      <div className="flex flex-wrap gap-2">
                        {profile.skills.split(',').map((skill, i) => (
                          <span key={i} className="text-xs px-3 py-1 rounded-full bg-amber-500/5 text-amber-500 border border-amber-500/10 font-medium">
                            {skill.trim()}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </GlassCard>
              </div>
            </div>
          )}

          {/* ──────────────── ONBOARDING INFO ──────────────── */}
          {activeTab === 'onboarding' && (
            <div className="space-y-6 animate-fade-in">
              <div>
                <h2 className="text-lg font-bold text-white">Onboarding Status</h2>
                <p className="text-xs text-zinc-500">Post-selection onboarding milestones and notifications</p>
              </div>

              {notifications.length === 0 ? (
                <div className="text-center py-16">
                  <Bell size={48} className="mx-auto text-zinc-800 mb-4" />
                  <p className="text-zinc-500 text-sm">No onboarding updates yet. You'll see notifications here once you're selected.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {notifications.map((notif) => (
                    <GlassCard key={notif.id} hoverable className="border border-zinc-800">
                      <div className="flex items-start gap-3">
                        <div className={`w-2 h-2 mt-1.5 rounded-full shrink-0 ${notif.is_read ? 'bg-zinc-700' : 'bg-amber-500 animate-pulse'}`} />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-zinc-200 font-medium">{notif.message}</p>
                          <p className="text-[10px] text-zinc-600 mt-1">
                            {new Date(notif.created_at).toLocaleString()} · <span className="uppercase font-bold tracking-wider">{notif.type}</span>
                          </p>
                        </div>
                      </div>
                    </GlassCard>
                  ))}
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* ── AI Interview Modal ── */}
      {interviewApp && (
        <AIInterview
          applicationId={interviewApp.id}
          candidateName={profile?.name || user?.name || 'Candidate'}
          jobTitle={interviewApp.jobTitle}
          interviewCompleted={completedInterviews.has(interviewApp.id)}
          onClose={() => setInterviewApp(null)}
          onComplete={() => {
            // Mark this application as completed so button disables immediately
            setCompletedInterviews(prev => new Set([...prev, interviewApp.id]));
            setInterviewApp(null);
            fetchApplications();
          }}
        />
      )}
    </DashboardLayout>
  );
};

export default CandidatePortal;