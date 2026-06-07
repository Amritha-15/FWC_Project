import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Eye, EyeOff, ShieldAlert } from 'lucide-react';

export interface RegisterProps { onCancel?: () => void; }

export const Register: React.FC<RegisterProps> = ({ onCancel }) => {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Basic Validation
    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters long");
      return;
    }

    setLoading(true);

    try {
      await register(name, email, password);
      // Registration logs them in automatically, redirect to candidate portal
      navigate('/candidate');
    } catch (err: any) {
      console.error(err);
      setError(err.errorMessage || err.message || 'Registration failed. Email may already be in use.');
    } finally {
      setLoading(false);
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

      {/* Register Box */}
      <div className="w-full max-w-md glass-panel rounded-2xl p-8 shadow-card-shadow border-amber-500/10 backdrop-blur-2xl relative overflow-hidden animate-fade-in">
        {/* Glow overlay */}
        <div className="absolute -top-20 -right-20 w-40 h-40 bg-amber-500/5 rounded-full blur-3xl pointer-events-none"></div>
        <div className="absolute -bottom-20 -left-20 w-40 h-40 bg-amber-600/5 rounded-full blur-3xl pointer-events-none"></div>

        <h2 className="text-xl font-bold text-center text-zinc-100 mb-2">Candidate Signup</h2>
        <p className="text-center text-xs text-zinc-500 mb-6">Register to track and submit your applications</p>

        {/* Error Dialog */}
        {error && (
          <div className="mb-5 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-start gap-2.5 leading-normal">
            <ShieldAlert size={16} className="shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-1.5">Full Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="w-full glass-input"
              placeholder="Arjun Kumar"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-1.5">Email Address</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full glass-input"
              placeholder="arjun@example.com"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-1.5">Password</label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full glass-input pr-10"
                placeholder="Min. 8 characters"
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

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-1.5">Confirm Password</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              className="w-full glass-input"
              placeholder="Confirm your password"
            />
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full glass-btn-primary mt-6 relative flex items-center justify-center gap-2"
          >
            {loading ? (
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-black border-t-transparent"></div>
            ) : (
              'Create Applicant Profile'
            )}
          </button>
        </form>

        {/* Login Prompt */}
        <p className="text-center text-xs text-zinc-400 mt-6 leading-normal">
          Already have an account?{' '}
          <Link to="/login" className="text-amber-500 font-semibold hover:underline">
            Sign In
          </Link>
        </p>
      </div>
    </div>
  );
};

export default Register;
