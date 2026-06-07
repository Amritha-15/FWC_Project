import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { 
  Users, Building2, BarChart3, Briefcase, FileText, 
  Cpu, Clock, Calendar, User, Bell, LogOut, Menu, X, CheckSquare, Award
} from 'lucide-react';

interface SidebarItem {
  id: string;
  label: string;
  icon: React.ReactNode;
}

interface DashboardLayoutProps {
  children: React.ReactNode;
  activeTab: string;
  onTabChange: (tabId: string) => void;
  title: string;
}

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({
  children,
  activeTab,
  onTabChange,
  title,
}) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // Define sidebar navigation items based on user role
  const getSidebarItems = (): SidebarItem[] => {
    if (!user) return [];
    
    switch (user.role) {
      case 'admin':
        return [
          { id: 'users', label: 'User Management', icon: <Users size={20} /> },
          { id: 'departments', label: 'Departments', icon: <Building2 size={20} /> },
          { id: 'analytics', label: 'System Analytics', icon: <BarChart3 size={20} /> },
        ];
      case 'hr':
        return [
          { id: 'jobs', label: 'Job Board', icon: <Briefcase size={20} /> },
          { id: 'applications', label: 'Applications', icon: <FileText size={20} /> },
          { id: 'pipeline', label: 'Candidate Pipeline', icon: <Users size={20} /> },
          { id: 'feedback', label: 'Interview Feedback', icon: <Award size={20} /> },
          { id: 'analytics', label: 'HR Analytics', icon: <BarChart3 size={20} /> },
        ];
      case 'employee':
        return [
          { id: 'attendance', label: 'Attendance Check', icon: <Clock size={20} /> },
          { id: 'leaves', label: 'Leave Requests', icon: <Calendar size={20} /> },
          { id: 'profile', label: 'My Profile', icon: <User size={20} /> },
          { id: 'notifications', label: 'Notifications', icon: <Bell size={20} /> },
        ];
      case 'manager': // maps to Senior Manager
        return [
          { id: 'team', label: 'Team Directory', icon: <Users size={20} /> },
          { id: 'approvals', label: 'Leave Approvals', icon: <CheckSquare size={20} /> },
          { id: 'performance', label: 'Evaluations', icon: <Award size={20} /> },
          { id: 'analytics', label: 'Team Metrics', icon: <BarChart3 size={20} /> },
        ];
      case 'candidate':
        return [
          { id: 'jobs', label: 'Browse Jobs', icon: <Briefcase size={20} /> },
          { id: 'applications', label: 'My Applications', icon: <FileText size={20} /> },
          { id: 'profile', label: 'My Resume', icon: <User size={20} /> },
          { id: 'onboarding', label: 'Onboarding Info', icon: <Building2 size={20} /> },
        ];
      default:
        return [];
    }
  };

  const menuItems = getSidebarItems();

  const renderNavLinks = () => {
    return menuItems.map((item) => {
      const isActive = activeTab === item.id;
      return (
        <button
          key={item.id}
          onClick={() => {
            onTabChange(item.id);
            setMobileMenuOpen(false);
          }}
          className={`
            w-full 
            flex 
            items-center 
            gap-3 
            px-4 
            py-3 
            rounded-lg 
            text-sm 
            font-medium 
            transition-all 
            duration-200 
            mb-1.5
            ${isActive 
              ? 'bg-amber-500 text-black shadow-amber-glow font-bold' 
              : 'text-zinc-400 hover:text-zinc-100 hover:bg-zinc-900/60 border border-transparent hover:border-amber-500/10'
            }
          `}
        >
          <span className={isActive ? 'text-black' : 'text-amber-500/80'}>
            {item.icon}
          </span>
          {item.label}
        </button>
      );
    });
  };

  return (
    <div className="min-h-screen bg-black flex text-zinc-100 font-sans">
      {/* 1. Desktop Sidebar */}
      <aside className="hidden md:flex flex-col w-64 bg-[#0a0a0c] border-r border-amber-500/10 p-5 shrink-0">
        {/* Brand Header */}
        <div className="flex items-center gap-3 mb-8 px-2">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center text-black font-extrabold text-xl shadow-amber-glow">
            H
          </div>
          <div>
            <h2 className="font-bold text-md text-zinc-100 leading-tight">HRMS AI</h2>
            <p className="text-[10px] text-amber-500/80 font-semibold tracking-wider uppercase leading-none">Enterprise</p>
          </div>
        </div>

        {/* User Card */}
        {user && (
          <div className="glass-panel rounded-lg p-4 mb-6 border-amber-500/5 shadow-inner">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-zinc-800 to-zinc-900 border border-amber-500/20 flex items-center justify-center font-bold text-amber-500">
                {user.name.charAt(0).toUpperCase()}
              </div>
              <div className="overflow-hidden">
                <p className="text-sm font-semibold truncate leading-tight">{user.name}</p>
                <p className="text-[10px] text-zinc-500 uppercase font-bold tracking-wider leading-none mt-1">
                  {user.role === 'manager' ? 'Senior Manager' : user.role}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Sidebar Nav */}
        <nav className="flex-1">
          {renderNavLinks()}
        </nav>

        {/* Logout Button */}
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm text-zinc-400 hover:text-red-400 hover:bg-red-500/5 border border-transparent hover:border-red-500/10 transition-all duration-200 mt-auto"
        >
          <LogOut size={20} className="text-zinc-500 hover:text-red-400" />
          Sign Out
        </button>
      </aside>

      {/* 2. Main Content Frame */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="h-16 bg-[#070709] border-b border-amber-500/10 px-6 flex items-center justify-between z-10 shrink-0">
          <div className="flex items-center gap-4">
            {/* Mobile Menu Toggle */}
            <button 
              onClick={() => setMobileMenuOpen(true)}
              className="md:hidden text-zinc-400 hover:text-zinc-100"
            >
              <Menu size={24} />
            </button>
            <h1 className="text-xl font-bold tracking-tight text-zinc-100">
              {title}
            </h1>
          </div>

          <div className="flex items-center gap-4">
            {/* Notifications Dropdown Container */}
            <div className="relative">
              <button 
                onClick={() => setNotificationsOpen(!notificationsOpen)}
                className="w-9 h-9 rounded-lg bg-zinc-900/60 border border-zinc-800 hover:border-amber-500/30 flex items-center justify-center text-zinc-300 hover:text-amber-500 relative transition-all duration-200"
              >
                <Bell size={18} />
                <span className="absolute top-1 right-1 w-2.5 h-2.5 bg-amber-500 rounded-full border border-black animate-pulse"></span>
              </button>
              
              {notificationsOpen && (
                <div className="absolute right-0 mt-2 w-80 glass-panel rounded-lg shadow-card-shadow p-4 z-50 animate-fade-in border-amber-500/20">
                  <div className="flex items-center justify-between border-b border-amber-500/10 pb-2 mb-3">
                    <p className="text-xs font-bold text-zinc-300 uppercase tracking-wider">Alert Center</p>
                    <button 
                      onClick={() => setNotificationsOpen(false)}
                      className="text-[10px] text-amber-500 hover:underline"
                    >
                      Clear All
                    </button>
                  </div>
                  <div className="space-y-2.5 max-h-60 overflow-y-auto pr-1">
                    <div className="p-2.5 rounded bg-zinc-900/40 hover:bg-zinc-900/80 transition-colors border-l-2 border-amber-500">
                      <p className="text-xs font-semibold text-zinc-200">🤖 AI screening completed</p>
                      <p className="text-[10px] text-zinc-400 mt-1">Batch screening for React Developer is ready.</p>
                      <p className="text-[8px] text-zinc-500 mt-1">2 mins ago</p>
                    </div>
                    <div className="p-2.5 rounded bg-zinc-900/40 hover:bg-zinc-900/80 transition-colors border-l-2 border-amber-500">
                      <p className="text-xs font-semibold text-zinc-200">📅 Interview scheduled</p>
                      <p className="text-[10px] text-zinc-400 mt-1">Candidate John Doe interview is set for tomorrow.</p>
                      <p className="text-[8px] text-zinc-500 mt-1">1 hour ago</p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Quick Profile Icon */}
            <div className="hidden sm:flex items-center gap-2">
              <span className="text-xs font-semibold text-zinc-300">{user?.name}</span>
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-amber-400/20 to-amber-600/20 border border-amber-500/30 flex items-center justify-center font-bold text-xs text-amber-500">
                {user?.name.charAt(0).toUpperCase()}
              </div>
            </div>
          </div>
        </header>

        {/* Dashboard Work Area */}
        <main className="flex-1 overflow-y-auto bg-black p-6 md:p-8">
          <div className="max-w-7xl mx-auto space-y-8 animate-slide-up">
            {children}
          </div>
        </main>
      </div>

      {/* 3. Mobile Navigation Drawer Overlay */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex">
          <div className="w-64 bg-[#0a0a0c] border-r border-amber-500/10 p-5 flex flex-col animate-fade-in">
            <div className="flex items-center justify-between mb-8">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded bg-amber-500 flex items-center justify-center text-black font-bold text-lg">
                  H
                </div>
                <h2 className="font-bold text-zinc-100">HRMS AI</h2>
              </div>
              <button 
                onClick={() => setMobileMenuOpen(false)}
                className="text-zinc-400 hover:text-zinc-100"
              >
                <X size={20} />
              </button>
            </div>
            
            <nav className="flex-1">
              {renderNavLinks()}
            </nav>
            
            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm text-zinc-400 hover:text-red-400 hover:bg-red-500/5 transition-all duration-200 mt-auto"
            >
              <LogOut size={20} />
              Sign Out
            </button>
          </div>
          {/* Dismiss drawer click target */}
          <div className="flex-1" onClick={() => setMobileMenuOpen(false)}></div>
        </div>
      )}
    </div>
  );
};

export default DashboardLayout;
