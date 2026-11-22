import React, { useState } from 'react';
import { Shield, Lock, Mail, ArrowRight, ArrowLeft, UserCheck, Smartphone, Globe, Info, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { parseApiError } from '../utils/errorParser';
import EncroWatchLogo from '../components/EncroWatchLogo';

export default function Login({ onSwitchToRegister, onLoginSuccess, onBackToHome }) {
  const { login, demoSwitch } = useAuth();
  const { lang, changeLanguage, t } = useLanguage();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const userData = await login(email, password);
      const userRole = userData?.role ? String(userData.role).toLowerCase() : 'citizen';
      if (onLoginSuccess) onLoginSuccess(userRole);
    } catch (err) {
      setError(parseApiError(err, 'Invalid email or password'));
    } finally {
      setLoading(false);
    }
  };

  const handleQuickDemo = async (targetRole) => {
    setError('');
    setLoading(true);
    try {
      const userData = await demoSwitch(targetRole);
      const userRole = userData?.role ? String(userData.role).toLowerCase() : targetRole;
      if (onLoginSuccess) onLoginSuccess(userRole);
    } catch (err) {
      setError(parseApiError(err, 'Demo login failed'));
    } finally {
      setLoading(false);
    }
  };

  const fillCredentials = (demoEmail, demoPass) => {
    setEmail(demoEmail);
    setPassword(demoPass);
    setError('');
  };

  return (
    <div className="min-h-screen bg-[#F5F7FA] flex flex-col justify-center items-center p-4 sm:p-6 font-sans">
      <div className="max-w-md w-full bg-white rounded-2xl p-6 sm:p-8 border border-slate-200/90 shadow-2xs space-y-6">
        {/* Top Header: Back to home & Language selector */}
        <div className="flex justify-between items-center border-b border-slate-100 pb-3">
          {onBackToHome ? (
            <button
              onClick={onBackToHome}
              className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Home</span>
            </button>
          ) : (
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              RBAC Authentication
            </span>
          )}

          <div className="flex items-center bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1 text-xs">
            <Globe className="w-3.5 h-3.5 text-slate-500 mr-1.5 shrink-0" />
            <select
              value={lang}
              onChange={(e) => changeLanguage(e.target.value)}
              className="bg-transparent text-slate-700 font-semibold focus:outline-none cursor-pointer text-xs"
            >
              <option value="en">English (EN)</option>
              <option value="kn">ಕನ್ನಡ (KN)</option>
              <option value="hi">हिन्दी (HI)</option>
            </select>
          </div>
        </div>

        {/* Brand Header */}
        <div className="text-center space-y-1">
          <div className="flex justify-center mb-2">
            <EncroWatchLogo size="md" light={false} showSubtitle={false} />
          </div>
          <h2 className="text-lg font-bold text-slate-900 tracking-tight">{t('signInTitle')}</h2>
          <p className="text-xs text-slate-500">{t('tagline')}</p>
        </div>

        {/* Quick Demo Switcher Card with real registered personas */}
        <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200/90 space-y-2">
            <div className="flex items-center justify-between">
              <div className="text-[11px] font-bold text-slate-600 uppercase tracking-wider">
                {t('demoRoles') || 'Select Persona to Test'}
              </div>
              <span className="text-[10px] text-blue-600 font-medium">1-Click Sign In</span>
            </div>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                disabled={loading}
                onClick={() => handleQuickDemo('admin')}
                className="py-2 px-2 bg-white hover:bg-slate-100 border border-slate-200 hover:border-slate-300 rounded-lg text-xs font-bold text-slate-800 transition-colors shadow-2xs flex flex-col items-center gap-1 disabled:opacity-50"
              >
                <Shield className="w-4 h-4 text-blue-600" />
                <span>Admin</span>
                <span className="text-[9px] text-slate-400 font-normal">Full Control</span>
              </button>
              <button
                type="button"
                disabled={loading}
                onClick={() => handleQuickDemo('officer')}
                className="py-2 px-2 bg-white hover:bg-slate-100 border border-slate-200 hover:border-slate-300 rounded-lg text-xs font-bold text-slate-800 transition-colors shadow-2xs flex flex-col items-center gap-1 disabled:opacity-50"
              >
                <UserCheck className="w-4 h-4 text-emerald-600" />
                <span>Officer</span>
                <span className="text-[9px] text-slate-400 font-normal">Field Operations</span>
              </button>
              <button
                type="button"
                disabled={loading}
                onClick={() => handleQuickDemo('citizen')}
                className="py-2 px-2 bg-white hover:bg-slate-100 border border-slate-200 hover:border-slate-300 rounded-lg text-xs font-bold text-slate-800 transition-colors shadow-2xs flex flex-col items-center gap-1 disabled:opacity-50"
              >
                <Smartphone className="w-4 h-4 text-purple-600" />
                <span>Citizen</span>
                <span className="text-[9px] text-slate-400 font-normal">Public Reporting</span>
              </button>
            </div>
            <div className="pt-1 flex items-center justify-between text-[10px] text-slate-400 border-t border-slate-200/50">
              <span>Pre-fill form:</span>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => fillCredentials('admin@encrowatch.ai', 'admin123')}
                  className="hover:text-blue-600 underline font-medium"
                >
                  admin
                </button>
                <span>•</span>
                <button
                  type="button"
                  onClick={() => fillCredentials('officer@encrowatch.ai', 'officer123')}
                  className="hover:text-emerald-600 underline font-medium"
                >
                  officer
                </button>
                <span>•</span>
                <button
                  type="button"
                  onClick={() => fillCredentials('citizen@encrowatch.ai', 'citizen123')}
                  className="hover:text-purple-600 underline font-medium"
                >
                  citizen
                </button>
              </div>
            </div>
          </div>

        {error && (
          <div className="p-3 bg-rose-50 text-rose-700 text-xs font-medium rounded-lg border border-rose-200 flex items-start gap-2">
            <Info className="w-4 h-4 shrink-0 text-rose-600 mt-0.5" />
            <span className="leading-relaxed">
              {typeof error === 'string' ? error : (error?.message || error?.msg || String(error))}
            </span>
          </div>
        )}

        {/* Credentials Form */}
        <form onSubmit={handleSubmit} className="space-y-3.5">
          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-700">{t('emailAddress')}</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="user@encrowatch.ai"
                className="w-full bg-slate-50 border border-slate-200 text-xs pl-9 pr-3 py-2 rounded-lg focus:bg-white focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              />
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-700">{t('password')}</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-slate-50 border border-slate-200 text-xs pl-9 pr-3 py-2 rounded-lg focus:bg-white focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold shadow-2xs transition-colors flex items-center justify-center gap-2 disabled:opacity-50 mt-2"
          >
            {loading ? t('loading') : t('signIn')}
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        <div className="text-center text-xs text-slate-500 border-t border-slate-100 pt-3">
          <span>Need an account? </span>
          <button
            onClick={onSwitchToRegister}
            className="text-blue-600 font-semibold hover:underline"
          >
            Register as Citizen or Officer
          </button>
        </div>
      </div>
    </div>
  );
}
