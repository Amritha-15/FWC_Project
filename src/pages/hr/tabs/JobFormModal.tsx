import React, { useState, ChangeEvent, FormEvent } from 'react';
import { X } from 'lucide-react';
import api from '../../../utils/api';

type JobFormProps = {
  open: boolean;
  onClose: () => void;
  onSaved: () => void;
  editJob?: {
    id: number;
    title: string;
    department: string;
    location: string;
    status: string;
    description: string;
  };
};

const JobFormModal: React.FC<JobFormProps> = ({ open, onClose, onSaved, editJob }) => {
  const isEdit = !!editJob;
  const [formData, setFormData] = useState({
    title: editJob?.title || '',
    department: editJob?.department || '',
    location: editJob?.location || '',
    status: editJob?.status || 'Open',
    description: editJob?.description || '',
  });
  const [error, setError] = useState<string | null>(null);

  const handleChange = (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      if (isEdit && editJob) {
        await api.put(`/api/hr/jobs/${editJob.id}`, formData);
      } else {
        await api.post('/api/hr/jobs', formData);
      }
      onSaved();
      onClose();
    } catch (err: any) {
      console.error('Job save error', err);
      if (err?.response?.status === 401) {
        setError('Authentication required. Please log in.');
      } else {
        setError('Failed to save job');
      }
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center" onClick={onClose}>
      <div className="bg-zinc-900 p-6 rounded-lg w-96" onClick={e => e.stopPropagation()}>
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-white">{isEdit ? 'Edit Job' : 'Post New Job'}</h3>
          <button onClick={onClose} className="text-zinc-400 hover:text-white">
            <X size={20} />
          </button>
        </div>
        {error && (
          <div className="p-2 bg-red-500/10 text-red-400 rounded mb-2 text-sm">{error}</div>
        )}
        <form onSubmit={handleSubmit} className="space-y-3">
          <input
            required
            name="title"
            placeholder="Title"
            className="glass-input w-full"
            value={formData.title}
            onChange={handleChange}
          />
          <input
            required
            name="department"
            placeholder="Department"
            className="glass-input w-full"
            value={formData.department}
            onChange={handleChange}
          />
          <input
            required
            name="location"
            placeholder="Location"
            className="glass-input w-full"
            value={formData.location}
            onChange={handleChange}
          />
          <input
            required
            name="status"
            placeholder="Status"
            className="glass-input w-full"
            value={formData.status}
            onChange={handleChange}
          />
          <textarea
            name="description"
            placeholder="Job Description"
            className="glass-input w-full"
            rows={4}
            value={formData.description}
            onChange={handleChange}
          />
          <div className="flex justify-end space-x-2">
            <button type="button" onClick={onClose} className="glass-btn-secondary text-sm">
              Cancel
            </button>
            <button type="submit" className="glass-btn-primary text-sm">
              Save
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default JobFormModal;
