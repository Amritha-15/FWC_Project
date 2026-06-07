import React, { useEffect, useState } from 'react';
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

interface DashboardSummary {
  total_users: number;
  total_candidates: number;
  total_jobs: number;
  total_applications: number;
  total_departments: number;
}

const HRAnalytics: React.FC = () => {
  console.log('HRAnalytics component mounted');
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        const resp = await fetch('http://127.0.0.1:8080/api/hr/dashboard/summary');
        console.log('HRAnalytics fetch response status:', resp.status);
        if (!resp.ok) {
          const text = await resp.text();
          console.error('Failed response body:', text);
          throw new Error(`Failed to load summary: ${resp.status}`);
        }
        const data = await resp.json();
        console.log('HRAnalytics summary data:', data);
        setSummary(data);
      } catch (e: any) {
        console.error('Failed to fetch HR summary:', e);
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };
    fetchSummary();
  }, []);

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      {loading ? (
        <div className="p-6">Loading analytics…</div>
      ) : error ? (
        <div className="p-6 text-red-500">Error: {error}</div>
      ) : !summary ? (
        <div className="p-6 text-zinc-400">No analytics data available.</div>
      ) : (
        <div className="p-6 space-y-6">
          <h2 className="text-2xl font-bold text-zinc-100">HR Dashboard Analytics</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-zinc-800/50 p-4 rounded border border-amber-500/20">
              <p className="text-xs text-amber-400 uppercase mb-1">Users</p>
              <p className="text-3xl font-bold text-zinc-100">{summary?.total_users ?? 0}</p>
            </div>
            <div className="bg-zinc-800/50 p-4 rounded border border-amber-500/20">
              <p className="text-xs text-amber-400 uppercase mb-1">Candidates</p>
              <p className="text-3xl font-bold text-zinc-100">{summary?.total_candidates ?? 0}</p>
            </div>
            <div className="bg-zinc-800/50 p-4 rounded border border-amber-500/20">
              <p className="text-xs text-amber-400 uppercase mb-1">Jobs</p>
              <p className="text-3xl font-bold text-zinc-100">{summary?.total_jobs ?? 0}</p>
            </div>
            <div className="bg-zinc-800/50 p-4 rounded border border-amber-500/20">
              <p className="text-xs text-amber-400 uppercase mb-1">Applications</p>
              <p className="text-3xl font-bold text-zinc-100">{summary?.total_applications ?? 0}</p>
            </div>
            <div className="bg-zinc-800/50 p-4 rounded border border-amber-500/20">
              <p className="text-xs text-amber-400 uppercase mb-1">Departments</p>
              <p className="text-3xl font-bold text-zinc-100">{summary?.total_departments ?? 0}</p>
            </div>
          </div>
          <div className="mt-6" style={{ height: '400px' }}>
            <Bar
              data={{
                labels: ['Users', 'Candidates', 'Jobs', 'Applications', 'Departments'],
                datasets: [
                  {
                    label: 'Count',
                    data: [
                      summary?.total_users ?? 0,
                      summary?.total_candidates ?? 0,
                      summary?.total_jobs ?? 0,
                      summary?.total_applications ?? 0,
                      summary?.total_departments ?? 0,
                    ],
                    backgroundColor: [
                      'rgba(255, 99, 132, 0.5)',
                      'rgba(54, 162, 235, 0.5)',
                      'rgba(255, 206, 86, 0.5)',
                      'rgba(75, 192, 192, 0.5)',
                      'rgba(153, 102, 255, 0.5)',
                    ],
                    borderWidth: 1,
                  },
                ],
              }}
              options={{ maintainAspectRatio: false }}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default HRAnalytics;
