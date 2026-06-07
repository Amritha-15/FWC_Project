import React, { useState, useEffect } from 'react';
import DashboardLayout from '../../components/layout/DashboardLayout';
import GlassCard from '../../components/ui/GlassCard';
import api from '../../utils/api';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line
} from 'recharts';
import { 
  Clock, Calendar, User, Bell, LogIn, LogOut, Check, 
  AlertCircle, Key, UserCheck, ShieldAlert, Sparkles, RefreshCw, ChevronRight
} from 'lucide-react';

interface AttendanceItem {
  id: number;
  attendance_date: string;
  check_in: string | null;
  check_out: string | null;
  working_hours: number;
  status: string;
}

interface LeaveRequestItem {
  id: number;
  start_date: string;
  end_date: string;
  reason: string;
  status: string;
}

interface NotificationItem {
  id: number;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

export const EmployeeDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState('attendance');
  
  // Data States
  const [attendance, setAttendance] = useState<AttendanceItem[]>([]);
  const [leaves, setLeaves] = useState<LeaveRequestItem[]>([]);
  const [leaveBalance, setLeaveBalance] = useState<any>({ vacation: 14, sick: 7, personal: 5 });
  const [profile, setProfile] = useState<any>({
    employee_code: '', designation: '', salary: 0, joining_date: '',
    user: { name: '', email: '' }
  });
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  
  // Loadings & messages
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Check in/out states
  const [isCheckedIn, setIsCheckedIn] = useState(false);
  const [todayRecord, setTodayRecord] = useState<AttendanceItem | null>(null);

  // Leave Form State
  const [leaveStartDate, setLeaveStartDate] = useState('');
  const [leaveEndDate, setLeaveEndDate] = useState('');
  const [leaveReason, setLeaveReason] = useState('');

  // Profile Edit State
  const [profilePhone, setProfilePhone] = useState('');
  const [profileSkills, setProfileSkills] = useState('');
  
  // Password Change State
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // Load dashboard data
  const loadDashboardData = async () => {
    try {
      // 1. Fetch Profile
      const profileRes = await api.get('/employee/profile');
      setProfile(profileRes.data);
      setProfilePhone(profileRes.data.phone || '');
      setProfileSkills(profileRes.data.skills || '');

      // 2. Fetch Attendance
      const attRes = await api.get('/employee/attendance');
      setAttendance(attRes.data);
      
      // Determine if checked in today
      const todayStr = new Date().toISOString().split('T')[0];
      const todayRec = attRes.data.find((a: AttendanceItem) => a.attendance_date === todayStr);
      if (todayRec) {
        setTodayRecord(todayRec);
        setIsCheckedIn(todayRec.status === 'Present' && !todayRec.check_out);
      } else {
        setTodayRecord(null);
        setIsCheckedIn(false);
      }

      // 3. Fetch Leaves
      const leavesRes = await api.get('/employee/leave');
      setLeaves(leavesRes.data);

      // 4. Fetch Leave Balance
      try {
        const balRes = await api.get('/employee/leave/balance');
        setLeaveBalance(balRes.data);
      } catch {
        // Fallback standard balance
        setLeaveBalance({ vacation: 12, sick: 6, personal: 4 });
      }

      // 5. Fetch Notifications
      const notifRes = await api.get('/employee/notifications');
      setNotifications(notifRes.data);
    } catch (err: any) {
      console.error(err);
      setError(err.errorMessage || 'Failed to load employee metrics');
    }
  };

  useEffect(() => {
    setError(null);
    setSuccess(null);
    setLoading(true);
    const run = async () => {
      await loadDashboardData();
      setLoading(false);
    };
    run();
  }, [activeTab]);

  // Check in
  const handleCheckIn = async () => {
    setError(null);
    setSuccess(null);
    setActionLoading(true);
    try {
      await api.post('/employee/check-in');
      setSuccess('Checked in successfully. Have a productive day!');
      await loadDashboardData();
    } catch (err: any) {
      setError(err.errorMessage || 'Check-in failed');
    } finally {
      setActionLoading(false);
    }
  };

  // Check out
  const handleCheckOut = async () => {
    setError(null);
    setSuccess(null);
    setActionLoading(true);
    try {
      await api.post('/employee/check-out');
      setSuccess('Checked out successfully. Good work today!');
      await loadDashboardData();
    } catch (err: any) {
      setError(err.errorMessage || 'Check-out failed');
    } finally {
      setActionLoading(false);
    }
  };

  // Request Leave
  const handleApplyLeave = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setActionLoading(true);

    try {
      await api.post('/employee/leave', {
        start_date: leaveStartDate,
        end_date: leaveEndDate,
        reason: leaveReason,
      });
      setSuccess('Leave request submitted successfully for approval.');
      setLeaveStartDate('');
      setLeaveEndDate('');
      setLeaveReason('');
      await loadDashboardData();
    } catch (err: any) {
      setError(err.errorMessage || 'Failed to submit leave request');
    } finally {
      setActionLoading(false);
    }
  };

  // Update Profile Info
  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setActionLoading(true);

    try {
      await api.put('/employee/profile', {
        phone: profilePhone,
        skills: profileSkills,
      });
      setSuccess('Profile updated successfully.');
      await loadDashboardData();
    } catch (err: any) {
      setError(err.errorMessage || 'Failed to update profile');
    } finally {
      setActionLoading(false);
    }
  };

  // Change Password
  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (newPassword !== confirmPassword) {
      setError('New passwords do not match');
      return;
    }

    setActionLoading(true);
    try {
      await api.post('/employee/change-password', {
        old_password: oldPassword,
        new_password: newPassword,
      });
      setSuccess('Password changed successfully.');
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err: any) {
      setError(err.errorMessage || 'Failed to change password');
    } finally {
      setActionLoading(false);
    }
  };

  // Mark notification read
  const handleMarkRead = async (notifId: number) => {
    try {
      await api.post(`/employee/notifications/${notifId}/read`);
      setNotifications(prev => 
        prev.map(n => n.id === notifId ? { ...n, is_read: true } : n)
      );
    } catch (err) {
      console.error(err);
    }
  };

  // Process working hours chart
  const getHoursChartData = () => {
    return attendance
      .slice(0, 10)
      .reverse()
      .map(a => ({
        date: a.attendance_date.split('-').slice(1).join('/'),
        Hours: a.working_hours,
      }));
  };

  return (
    <DashboardLayout activeTab={activeTab} onTabChange={setActiveTab} title="Employee Dashboard Portal">
      {/* Alert overlays */}
      {error && (
        <div className="p-3.5 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-center gap-2.5">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}
      {success && (
        <div className="p-3.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs flex items-center gap-2.5">
          <Check size={16} />
          <span>{success}</span>
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-20">
          <RefreshCw size={36} className="animate-spin text-amber-500" />
        </div>
      ) : (
        <>
          {/* ATTENDANCE TAB */}
          {activeTab === 'attendance' && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start animate-fade-in">
              {/* Check in/out panel */}
              <GlassCard hoverable={false} className="lg:col-span-1 border border-zinc-800 text-center py-8 flex flex-col justify-center items-center">
                <div className="w-16 h-16 rounded-full bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-500 mb-4 animate-glow-pulse">
                  <Clock size={32} />
                </div>
                <h3 className="font-extrabold text-white text-lg leading-tight">Attendance Logger</h3>
                <p className="text-xs text-zinc-500 mt-1">Check-in at start of shifts and check-out on completion</p>

                <div className="my-6">
                  <p className="text-[10px] uppercase font-bold text-zinc-500 tracking-wider">Current Session Status</p>
                  <p className={`text-sm font-extrabold mt-1 uppercase ${isCheckedIn ? 'text-emerald-400' : 'text-zinc-400'}`}>
                    {isCheckedIn ? 'Checked-In' : 'Inactive / Checked-Out'}
                  </p>
                  {todayRecord && (
                    <div className="text-[10px] text-zinc-500 mt-2 space-y-0.5">
                      <p>In: {todayRecord.check_in || '--:--'}</p>
                      <p>Out: {todayRecord.check_out || '--:--'}</p>
                    </div>
                  )}
                </div>

                {isCheckedIn ? (
                  <button
                    onClick={handleCheckOut}
                    disabled={actionLoading}
                    className="glass-btn-secondary w-full max-w-xs flex items-center justify-center gap-2 border-red-500/30 hover:border-red-500/50 hover:bg-red-500/5 text-red-400 hover:text-red-300"
                  >
                    <LogOut size={16} /> End Shift (Check-Out)
                  </button>
                ) : (
                  <button
                    onClick={handleCheckIn}
                    disabled={actionLoading}
                    className="glass-btn-primary w-full max-w-xs flex items-center justify-center gap-2"
                  >
                    <LogIn size={16} /> Begin Shift (Check-In)
                  </button>
                )}
              </GlassCard>

              {/* Working Hours Chart & Logs */}
              <div className="lg:col-span-2 space-y-6">
                <GlassCard hoverable={false} title="Working Hours Progression" className="border border-zinc-800">
                  <div className="h-60 mt-4">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={getHoursChartData()}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                        <XAxis dataKey="date" tick={{ fill: '#a1a1aa', fontSize: 10 }} axisLine={false} />
                        <YAxis tick={{ fill: '#a1a1aa', fontSize: 10 }} axisLine={false} />
                        <Tooltip
                          contentStyle={{ backgroundColor: '#09090b', borderColor: 'rgba(245, 158, 11, 0.2)', color: '#fff' }}
                        />
                        <Bar dataKey="Hours" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </GlassCard>

                {/* Attendance Logs */}
                <GlassCard hoverable={false} title="Recent Session Logs" className="border border-zinc-800">
                  <div className="overflow-x-auto max-h-64 overflow-y-auto">
                    <table className="w-full text-left border-collapse text-xs">
                      <thead>
                        <tr className="border-b border-zinc-800 text-zinc-500 font-bold uppercase tracking-wider pb-2">
                          <th className="py-2.5 px-3">Date</th>
                          <th className="py-2.5 px-3">Checked-In</th>
                          <th className="py-2.5 px-3">Checked-Out</th>
                          <th className="py-2.5 px-3">Logged Hours</th>
                          <th className="py-2.5 px-3">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-zinc-900 text-zinc-300">
                        {attendance.map((a) => (
                          <tr key={a.id} className="hover:bg-zinc-900/20">
                            <td className="py-2.5 px-3 font-semibold">{a.attendance_date}</td>
                            <td className="py-2.5 px-3">{a.check_in || '--:--'}</td>
                            <td className="py-2.5 px-3">{a.check_out || '--:--'}</td>
                            <td className="py-2.5 px-3 font-mono">{a.working_hours} hrs</td>
                            <td className="py-2.5 px-3">
                              <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-bold uppercase ${
                                a.status === 'Present' 
                                  ? 'bg-emerald-500/10 text-emerald-400' 
                                  : (a.status === 'Late' ? 'bg-amber-500/10 text-amber-400' : 'bg-red-500/10 text-red-400')
                              }`}>
                                {a.status}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </GlassCard>
              </div>
            </div>
          )}

          {/* LEAVES TAB */}
          {activeTab === 'leaves' && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start animate-fade-in">
              {/* Leave Balance & Apply Form */}
              <div className="lg:col-span-1 space-y-6">
                <GlassCard hoverable={false} title="Leave Accrual Balances" className="border border-zinc-800">
                  <div className="grid grid-cols-3 gap-3 my-2 text-center">
                    <div className="p-3 bg-zinc-900/60 rounded-lg border border-zinc-800">
                      <p className="text-xl font-black text-amber-500">{leaveBalance.available ?? 0}</p>
                      <p className="text-[9px] text-zinc-400 uppercase font-semibold mt-1">Available</p>
                    </div>
                    <div className="p-3 bg-zinc-900/60 rounded-lg border border-zinc-800">
                      <p className="text-xl font-black text-amber-500">{leaveBalance.taken ?? 0}</p>
                      <p className="text-[9px] text-zinc-400 uppercase font-semibold mt-1">Used</p>
                    </div>
                    <div className="p-3 bg-zinc-900/60 rounded-lg border border-zinc-800">
                      <p className="text-xl font-black text-amber-500">{leaveBalance.entitlement ?? 0}</p>
                      <p className="text-[9px] text-zinc-400 uppercase font-semibold mt-1">Total</p>
                    </div>
                  </div>
                </GlassCard>

                {/* Apply Form */}
                <GlassCard hoverable={false} title="Apply for Leave" className="border border-zinc-800">
                  <form onSubmit={handleApplyLeave} className="space-y-4">
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-[10px] font-semibold uppercase tracking-wider text-zinc-400 mb-1">Start Date</label>
                        <input
                          type="date"
                          required
                          value={leaveStartDate}
                          onChange={(e) => setLeaveStartDate(e.target.value)}
                          className="w-full glass-input text-xs"
                        />
                      </div>
                      <div>
                        <label className="block text-[10px] font-semibold uppercase tracking-wider text-zinc-400 mb-1">End Date</label>
                        <input
                          type="date"
                          required
                          value={leaveEndDate}
                          onChange={(e) => setLeaveEndDate(e.target.value)}
                          className="w-full glass-input text-xs"
                        />
                      </div>
                    </div>
                    <div>
                      <label className="block text-[10px] font-semibold uppercase tracking-wider text-zinc-400 mb-1">Reason / Statement</label>
                      <textarea
                        required
                        rows={3}
                        value={leaveReason}
                        onChange={(e) => setLeaveReason(e.target.value)}
                        className="w-full glass-input text-xs resize-none"
                        placeholder="Personal reasons, family matter, sick leave details..."
                      />
                    </div>
                    <button
                      type="submit"
                      disabled={actionLoading}
                      className="glass-btn-primary w-full text-xs"
                    >
                      {actionLoading ? 'Submitting...' : 'Submit Leave Request'}
                    </button>
                  </form>
                </GlassCard>
              </div>

              {/* Leave Requests Log */}
              <GlassCard hoverable={false} title="Leave Application History" className="lg:col-span-2 border border-zinc-800">
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse text-xs">
                    <thead>
                      <tr className="border-b border-zinc-800 text-zinc-500 font-bold uppercase tracking-wider pb-2">
                        <th className="py-2.5 px-3">Duration</th>
                        <th className="py-2.5 px-3">Reason / Details</th>
                        <th className="py-2.5 px-3">Review Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-900 text-zinc-300">
                      {leaves.map((l) => (
                        <tr key={l.id} className="hover:bg-zinc-900/20">
                          <td className="py-3 px-3 font-semibold">
                            {l.start_date} <ChevronRight size={10} className="inline mx-1 text-zinc-500" /> {l.end_date}
                          </td>
                          <td className="py-3 px-3 text-zinc-400 leading-relaxed max-w-xs truncate">{l.reason}</td>
                          <td className="py-3 px-3">
                            <span className={`inline-flex items-center px-2 py-0.5 rounded text-[9px] font-bold uppercase ${
                              l.status === 'Approved' 
                                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' 
                                : (l.status === 'Rejected' ? 'bg-red-500/10 text-red-400 border border-red-500/20' : 'bg-amber-500/10 text-amber-400 border border-amber-500/20')
                            }`}>
                              {l.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                      {leaves.length === 0 && (
                        <tr>
                          <td colSpan={3} className="py-4 text-center text-zinc-500 italic">No leave applications registered.</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </GlassCard>
            </div>
          )}

          {/* PROFILE & SECURITY TAB */}
          {activeTab === 'profile' && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start animate-fade-in">
              {/* Profile Card Summary */}
              <GlassCard hoverable={false} className="lg:col-span-1 border border-zinc-800 text-center py-6">
                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-amber-400/20 to-amber-600/20 border border-amber-500/30 flex items-center justify-center font-bold text-lg text-amber-500 mx-auto mb-3">
                  {profile.user?.name ? profile.user.name.charAt(0).toUpperCase() : 'E'}
                </div>
                <h3 className="font-extrabold text-white text-md leading-tight">{profile.user?.name}</h3>
                <p className="text-xs text-amber-500/80 font-semibold mt-1 uppercase tracking-wider">{profile.designation}</p>

                <div className="mt-6 space-y-4 text-left text-xs border-t border-zinc-900 pt-4">
                  <div className="flex justify-between items-center">
                    <span className="text-zinc-500">Employee ID</span>
                    <span className="font-mono text-zinc-300 font-bold">{profile.employee_code}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-zinc-500">Corporate Email</span>
                    <span className="text-zinc-300 font-semibold truncate max-w-[150px]">{profile.user?.email}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-zinc-500">Joining Date</span>
                    <span className="text-zinc-300 font-semibold">{profile.joining_date}</span>
                  </div>
                </div>
              </GlassCard>

              {/* Adjust Profile Skills & Security Change */}
              <div className="lg:col-span-2 space-y-6">
                {/* Adjust Profile Skills */}
                <GlassCard hoverable={false} title="Modify Profile Details" className="border border-zinc-800">
                  <form onSubmit={handleUpdateProfile} className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-[10px] font-semibold uppercase tracking-wider text-zinc-400 mb-1.5">Contact Number</label>
                        <input
                          type="text"
                          value={profilePhone}
                          onChange={(e) => setProfilePhone(e.target.value)}
                          className="w-full glass-input text-xs"
                          placeholder="+91-9876543210"
                        />
                      </div>
                      <div>
                        <label className="block text-[10px] font-semibold uppercase tracking-wider text-zinc-400 mb-1.5">Skills Expertise (comma-separated)</label>
                        <input
                          type="text"
                          value={profileSkills}
                          onChange={(e) => setProfileSkills(e.target.value)}
                          className="w-full glass-input text-xs"
                          placeholder="React, TypeScript, Docker"
                        />
                      </div>
                    </div>
                    <button
                      type="submit"
                      disabled={actionLoading}
                      className="glass-btn-primary text-xs"
                    >
                      Save Profile Updates
                    </button>
                  </form>
                </GlassCard>

                {/* Password Change */}
                <GlassCard hoverable={false} title="Update Account Password" className="border border-zinc-800">
                  <form onSubmit={handleChangePassword} className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <label className="block text-[10px] font-semibold uppercase tracking-wider text-zinc-400 mb-1.5">Current Password</label>
                        <input
                          type="password"
                          required
                          value={oldPassword}
                          onChange={(e) => setOldPassword(e.target.value)}
                          className="w-full glass-input text-xs"
                          placeholder="••••••••"
                        />
                      </div>
                      <div>
                        <label className="block text-[10px] font-semibold uppercase tracking-wider text-zinc-400 mb-1.5">New Password</label>
                        <input
                          type="password"
                          required
                          value={newPassword}
                          onChange={(e) => setNewPassword(e.target.value)}
                          className="w-full glass-input text-xs"
                          placeholder="Min. 8 characters"
                        />
                      </div>
                      <div>
                        <label className="block text-[10px] font-semibold uppercase tracking-wider text-zinc-400 mb-1.5">Confirm New Password</label>
                        <input
                          type="password"
                          required
                          value={confirmPassword}
                          onChange={(e) => setConfirmPassword(e.target.value)}
                          className="w-full glass-input text-xs"
                          placeholder="Confirm new password"
                        />
                      </div>
                    </div>
                    <button
                      type="submit"
                      disabled={actionLoading}
                      className="glass-btn-primary text-xs"
                    >
                      Apply Password Update
                    </button>
                  </form>
                </GlassCard>
              </div>
            </div>
          )}

          {/* NOTIFICATIONS TAB */}
          {activeTab === 'notifications' && (
            <GlassCard hoverable={false} title="System Notifications Dashboard" className="border border-zinc-800 max-w-3xl mx-auto animate-fade-in">
              <div className="space-y-3 my-4">
                {notifications.map((n) => (
                  <div 
                    key={n.id}
                    onClick={() => !n.is_read && handleMarkRead(n.id)}
                    className={`
                      p-4 
                      rounded-lg 
                      border 
                      transition-all 
                      duration-200 
                      flex 
                      justify-between 
                      items-start 
                      gap-4
                      ${n.is_read 
                        ? 'bg-zinc-950/20 border-zinc-900 text-zinc-400' 
                        : 'bg-amber-500/[0.02] border-amber-500/10 text-zinc-100 cursor-pointer hover:bg-amber-500/[0.04]'
                      }
                    `}
                  >
                    <div>
                      <h4 className="text-xs font-bold flex items-center gap-1.5 leading-none">
                        {!n.is_read && <span className="w-1.5 h-1.5 bg-amber-500 rounded-full"></span>}
                        {n.title}
                      </h4>
                      <p className="text-xs text-zinc-400 mt-2 leading-relaxed">{n.message}</p>
                      <p className="text-[8px] text-zinc-500 mt-2">{new Date(n.created_at).toLocaleDateString()}</p>
                    </div>
                    {!n.is_read && (
                      <span className="text-[8px] font-bold text-amber-500 uppercase tracking-wider bg-amber-500/10 px-1.5 py-0.5 rounded shrink-0">
                        New
                      </span>
                    )}
                  </div>
                ))}
                {notifications.length === 0 && (
                  <div className="py-12 text-center text-zinc-500 italic text-xs">
                    No active notifications.
                  </div>
                )}
              </div>
            </GlassCard>
          )}
        </>
      )}
    </DashboardLayout>
  );
};

export default EmployeeDashboard;
