import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Eye, EyeOff, ShieldAlert, Cpu } from 'lucide-react';

export const Login: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<'admin' | 'hr' | 'employee' | 'manager' | 'candidate'>('candidate');
  
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const loggedInUser = await login(email, password, role);
      
      // Redirect based on role
      switch (loggedInUser.role) {
        case 'admin':
          navigate('/admin');
          break;
        case 'hr':
          navigate('/hr');
          break;
        case 'employee':
          navigate('/employee');
          break;
        case 'manager':
          navigate('/manager');
          break;
        case 'candidate':
          navigate('/candidate');
          break;
        default:
          navigate('/login');
      }
    } catch (err: any) {
      console.error(err);
      setError(err.errorMessage || err.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleRoleChange = (selectedRole: 'admin' | 'hr' | 'employee' | 'manager' | 'candidate') => {
    setRole(selectedRole);
    setError(null);
    // Autofill seeded credentials for testing convenience
    if (selectedRole === 'admin') {
      setEmail('admin@example.com');
      setPassword('Password123');
    } else if (selectedRole === 'hr') {
      setEmail('amrithavarshini1510@gmail.com');
      setPassword('Password123');
    } else if (selectedRole === 'manager') {
      setEmail('manager@example.com');
      setPassword('Password123');
    } else if (selectedRole === 'employee') {
      setEmail('employee@example.com');
      setPassword('Password123');
    } else {
      setEmail('employee1@example.com');
      setPassword('Password123');
    }
  };

  return (
    <div className="min-h-screen bg-[#030303] bg-gradient-to-tr from-black via-zinc-950 to-amber-950/20 flex flex-col items-center justify-center p-4">
      {/* Brand Header */}
      <div className="flex items-center gap-3 mb-8">
        <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-amber-400 via-amber-500 to-amber-600 flex items-center justify-center text-black font-extrabold text-2xl shadow-amber-glow-strong">
          H
        </div>
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">HRMS AI Platform</h1>
          <p className="text-xs text-amber-500 font-semibold tracking-widest uppercase mt-0.5">Automated Talent Flow</p>
        </div>
      </div>

      {/* Login Box */}
      <div className="w-full max-w-md glass-panel rounded-2xl p-8 shadow-card-shadow border-amber-500/10 backdrop-blur-2xl relative overflow-hidden animate-fade-in">
        {/* Glow overlay */}
        <div className="absolute -top-20 -right-20 w-40 h-40 bg-amber-500/5 rounded-full blur-3xl pointer-events-none"></div>
        <div className="absolute -bottom-20 -left-20 w-40 h-40 bg-amber-600/5 rounded-full blur-3xl pointer-events-none"></div>

        <h2 className="text-xl font-bold text-center text-zinc-100 mb-6">Portal Authentication</h2>

        {/* Role Selector Grid */}
        <div className="grid grid-cols-5 gap-1 p-1 bg-zinc-950/80 rounded-xl border border-zinc-800/80 mb-6 text-[10px] sm:text-xs">
          {(['candidate', 'employee', 'manager', 'hr', 'admin'] as const).map((r) => (
            <button
              key={r}
              type="button"
              onClick={() => handleRoleChange(r)}
              className={`
                py-2 
                rounded-lg 
                font-bold 
                capitalize 
                transition-all 
                duration-200
                ${role === r 
                  ? 'bg-amber-500 text-black font-extrabold shadow-amber-glow' 
                  : 'text-zinc-500 hover:text-zinc-300'
                }
              `}
            >
              {r === 'manager' ? 'Manager' : r}
            </button>
          ))}
        </div>

        {/* Error Dialog */}
        {error && (
          <div className="mb-5 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-start gap-2.5 leading-normal">
            <ShieldAlert size={16} className="shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-1.5">Corporate Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full glass-input"
              placeholder="e.g. employee@company.com"
            />
          </div>

          <div>
            <div className="flex justify-between items-center mb-1.5">
              <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-400">Account Password</label>
              <a href="#" className="text-[10px] text-amber-500 hover:underline">Forgot password?</a>
            </div>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full glass-input pr-10"
                placeholder="••••••••"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300"
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {/* Sign In Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full glass-btn-primary mt-6 relative flex items-center justify-center gap-2"
          >
            {loading ? (
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-black border-t-transparent"></div>
            ) : (
              'Sign In securely'
            )}
          </button>
          {/* Sign Up Prompt for Candidates */}
          {role === 'candidate' && (
            <button
              type="button"
              onClick={() => navigate('/register')}
              className="w-full glass-btn-secondary mt-4 relative flex items-center justify-center gap-2"
            >
              Create Account
            </button>
          )}
        </form>

        {/* Google SSO Divider */}
        <div className="relative flex py-5 items-center">
          <div className="flex-grow border-t border-zinc-800"></div>
          <span className="flex-shrink mx-4 text-zinc-500 text-[10px] uppercase font-bold tracking-widest">or continue with</span>
          <div className="flex-grow border-t border-zinc-800"></div>
        </div>

        {/* Google SSO Button */}
        <button
          type="button"
          onClick={() => alert('Google authentication module active. Integrates OAuth credentials.')}
          className="w-full glass-btn-secondary flex items-center justify-center gap-2.5"
        >
          <svg className="w-4 h-4" viewBox="0 0 24 24">
            <path
              fill="currentColor"
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
            />
            <path
              fill="currentColor"
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
            />
            <path
              fill="currentColor"
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
            />
            <path
              fill="currentColor"
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
            />
          </svg>
          Google Cloud Identity
        </button>

        {/* Register Prompt */}
        {role === 'candidate' && (
          <p className="text-center text-xs text-zinc-400 mt-6 leading-normal">
            New applicant?{' '}
            <Link to="/register" className="text-amber-500 font-semibold hover:underline">
              Create an account
            </Link>
          </p>
        )}
      </div>
    </div>
  );
};

export default Login;
