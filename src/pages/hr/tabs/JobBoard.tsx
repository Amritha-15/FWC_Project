import React, { useEffect, useState } from 'react';
import GlassCard from '../../../components/ui/GlassCard';
import api from '../../../utils/api';
import { AlertCircle, RefreshCw, Pencil, Plus } from 'lucide-react';
import JobFormModal from './JobFormModal';

interface Job {
  id: number;
  title: string;
  department: string;
  location: string;
  status: string;
}

const JobBoard: React.FC = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editJob, setEditJob] = useState<Job | null>(null);

  const fetchJobs = async () => {
    try {
      const res = await api.get('/api/hr/jobs');
      setJobs(res.data);
    } catch (err: any) {
      setError('Failed to load jobs');
    }
  };

  useEffect(() => {
    setLoading(true);
    fetchJobs().finally(() => setLoading(false));
  }, []);

  const openForm = (job?: Job) => {
    if (job) {
      setEditJob(job);
    } else {
      setEditJob(null);
    }
    setShowForm(true);
  };

  const closeForm = () => {
    setShowForm(false);
    setEditJob(null);
  };

  const handleSaved = () => {
    fetchJobs();
  };

  return (
    <div className="space-y-5 animate-fade-in">
      {error && (
        <div className="p-3 rounded bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-center gap-2">
          <AlertCircle size={14} /> {error}
        </div>
      )}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-white">Job Board</h2>
        <button onClick={() => openForm()} className="glass-btn-primary flex items-center gap-2">
          <Plus size={14} /> Add Job
        </button>
      </div>
      {loading ? (
        <div className="flex justify-center py-12">
          <RefreshCw size={36} className="animate-spin text-amber-500" />
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {jobs.map((job) => (
            <GlassCard
              key={job.id}
              hoverable
              className="border border-zinc-800 p-4 flex flex-col justify-between"
            >
              <div>
                <h3 className="text-lg font-bold text-white">{job.title}</h3>

                <p className="text-xs text-zinc-500 mt-1">
                  {job.department} • {job.location}
                </p>

                <p className="text-xs text-zinc-400 mt-2">
                  Status: {job.status}
                </p>

                {/* Job Description */}
                <p className="text-sm text-zinc-300 mt-3 line-clamp-3">
                  {job.description}
                </p>
              </div>

              <button
                onClick={() => openForm(job)}
                className="mt-3 self-start flex items-center text-amber-400 gap-1"
              >
                <Pencil size={14} />
                Edit
              </button>
            </GlassCard>
          ))}
        </div>
      )}

      <JobFormModal open={showForm} onClose={closeForm} onSaved={handleSaved} editJob={editJob ?? undefined} />
    </div>
  );
};

export default JobBoard;
