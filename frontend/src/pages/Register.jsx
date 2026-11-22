import React, { useState } from 'react';
import {
  User,
  Mail,
  Lock,
  Phone,
  ArrowRight,
  ArrowLeft,
  Globe,
  AlertCircle,
  Shield,
  Building2,
  Briefcase,
  MapPin,
  CheckCircle2,
  Info,
  BadgeCheck
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { parseApiError } from '../utils/errorParser';
import EncroWatchLogo from '../components/EncroWatchLogo';

export default function Register({ onSwitchToLogin, onRegisterSuccess, onBackToHome }) {
  const { register, registerOfficer } = useAuth();
  const { lang, changeLanguage, t } = useLanguage();
  
  // Registration Type: 'citizen' or 'officer'
  const [accountType, setAccountType] = useState('citizen');

  // Shared fields
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // Citizen-specific fields
  const [address, setAddress] = useState('');

  // Officer-specific fields
  const [employeeId, setEmployeeId] = useState('');
  const [department, setDepartment] = useState('Encroachment Removal Squad');
  const [designation, setDesignation] = useState('Ward Enforcement Officer');
  const [assignedArea, setAssignedArea] = useState('East Zone - Ward 84');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [officerSuccess, setOfficerSuccess] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Client-side validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email.trim())) {
      setError('Please enter a valid email address (e.g., name@example.com).');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match. Please re-enter your password.');
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters in length.');
      return;
    }

    if (accountType === 'officer') {
      if (phone.trim().length < 7) {
        setError('Official phone number must be at least 7 digits in length.');
        return;
      }
      if (!employeeId.trim()) {
        setError('Official Employee ID is required for municipal verification.');
        return;
      }
    }

    setLoading(true);

    try {
      if (accountType === 'citizen') {
        const citizenUser = await register({
          full_name: fullName.trim(),
          email: email.trim(),
          phone: phone.trim() || undefined,
          address: address.trim() || undefined,
          password
        });
        if (onRegisterSuccess) onRegisterSuccess('citizen');
      } else {
        const res = await registerOfficer({
          full_name: fullName.trim(),
          email: email.trim(),
          phone: phone.trim(),
          employee_id: employeeId.trim(),
          department: department.trim(),
          designation: designation.trim(),
          assigned_area: assignedArea.trim(),
          password
        });
        setOfficerSuccess(res);
      }
    } catch (err) {
      setError(parseApiError(err, 'Registration failed. Email or Employee ID may already be registered.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F5F7FA] flex flex-col justify-center items-center p-4 sm:p-6">
      <div className="max-w-xl w-full bg-white rounded-2xl p-6 sm:p-8 border border-slate-200/90 shadow-2xs space-y-6">
        {/* Top Bar with Logo, Back button & Language Selector */}
        <div className="flex items-center justify-between border-b border-slate-100 pb-3.5">
          <div className="flex items-center gap-3">
            {onBackToHome && (
              <button
                type="button"
                onClick={onBackToHome}
                className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 transition-colors pr-2 border-r border-slate-200"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Home</span>
              </button>
            )}
            <EncroWatchLogo size="small" />
          </div>
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

        {/* Title & Description */}
        <div>
          <h2 className="text-lg font-bold text-slate-900 tracking-tight">Create an Account</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Join the municipal urban accessibility monitoring network
          </p>
        </div>

        {/* Account Type Selector (Citizen vs Officer) */}
        <div className="grid grid-cols-2 gap-3">
          <button
            type="button"
            onClick={() => { setAccountType('citizen'); setError(''); }}
            className={`p-3.5 rounded-xl border text-left transition-all flex items-start gap-3 ${
              accountType === 'citizen'
                ? 'bg-emerald-50/50 border-emerald-500 ring-1 ring-emerald-500 text-slate-900 shadow-2xs'
                : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
            }`}
          >
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
              accountType === 'citizen' ? 'bg-emerald-600 text-white' : 'bg-slate-100 text-slate-500'
            }`}>
              <User className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-bold text-slate-900">Citizen Account</div>
              <div className="text-[11px] text-slate-500 mt-0.5 leading-snug">Report &amp; track corridor obstructions</div>
            </div>
          </button>

          <button
            type="button"
            onClick={() => { setAccountType('officer'); setError(''); }}
            className={`p-3.5 rounded-xl border text-left transition-all flex items-start gap-3 ${
              accountType === 'officer'
                ? 'bg-blue-50/50 border-blue-600 ring-1 ring-blue-600 text-slate-900 shadow-2xs'
                : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
            }`}
          >
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
              accountType === 'officer' ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-500'
            }`}>
              <Shield className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-bold text-slate-900">Municipal Officer</div>
              <div className="text-[11px] text-slate-500 mt-0.5 leading-snug">Field inspection &amp; clearance verification</div>
            </div>
          </button>
        </div>

        {/* Officer Successful Submission State */}
        {officerSuccess ? (
          <div className="p-5 bg-emerald-50/80 border border-emerald-200 rounded-xl space-y-3">
            <div className="flex items-center gap-2 text-emerald-800">
              <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
              <h3 className="text-xs font-bold uppercase tracking-wide">Officer Application Submitted</h3>
            </div>
            <p className="text-xs text-emerald-900 leading-relaxed">
              Your registration application for <strong>{officerSuccess.full_name}</strong> (Employee ID: <strong>{officerSuccess.employee_id}</strong>) has been submitted successfully.
            </p>
            <div className="text-[11px] text-emerald-800 bg-white/80 p-3 rounded-lg border border-emerald-200 space-y-1">
              <div className="font-semibold text-emerald-950">Administrative Verification Required</div>
              <div>Municipal policy requires an Administrator to review and approve your officer credentials before your account is activated.</div>
              <div className="text-emerald-700 mt-1 font-mono">Status: Awaiting Administrator Approval</div>
            </div>
            <button
              onClick={onSwitchToLogin}
              className="w-full py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold shadow-2xs flex items-center justify-center gap-1.5 transition-colors"
            >
              <span>Proceed to Sign In</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <>
            {/* Officer Registration Policy Notice */}
            {accountType === 'officer' && (
              <div className="p-3 bg-blue-50/70 border border-blue-200 rounded-lg text-xs text-blue-900 flex items-start gap-2.5">
                <Info className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
                <div className="leading-relaxed text-[11px]">
                  <strong>Government Verification Standard:</strong> Newly registered officers require administrator review and approval before field operations access is granted.
                </div>
              </div>
            )}

            {/* Error Message */}
            {error && (
              <div className="p-3 bg-rose-50 text-rose-700 text-xs font-medium rounded-lg border border-rose-200 flex items-start gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 text-rose-600 mt-0.5" />
                <span className="leading-relaxed">
                  {typeof error === 'string' ? error : (error?.message || error?.msg || String(error))}
                </span>
              </div>
            )}

            {/* Registration Form */}
            <form onSubmit={handleSubmit} className="space-y-3.5">
              {/* Full Name */}
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-700">
                  {accountType === 'officer' ? 'Official Full Name' : t('fullName')}
                </label>
                <div className="relative">
                  <User className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder={accountType === 'officer' ? 'Officer Rajesh Kumar' : 'Darshan Gowda'}
                    className="w-full bg-slate-50 border border-slate-200 text-xs pl-9 pr-3 py-2 rounded-lg focus:bg-white focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                  />
                </div>
              </div>

              {/* Email & Mobile Number Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700">
                    {accountType === 'officer' ? 'Official Email Address' : t('emailAddress')}
                  </label>
                  <div className="relative">
                    <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                    <input
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder={accountType === 'officer' ? 'officer.kumar@bbmp.gov.in' : 'darshan@example.com'}
                      className="w-full bg-slate-50 border border-slate-200 text-xs pl-9 pr-3 py-2 rounded-lg focus:bg-white focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                    />
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700">Mobile Number</label>
                  <div className="relative">
                    <Phone className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                    <input
                      type="tel"
                      required
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      placeholder="+91 98765 43210"
                      className="w-full bg-slate-50 border border-slate-200 text-xs pl-9 pr-3 py-2 rounded-lg focus:bg-white focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                    />
                  </div>
                </div>
              </div>

              {/* Citizen-Specific: Address */}
              {accountType === 'citizen' && (
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700">Residential Ward / Address (Optional)</label>
                  <div className="relative">
                    <MapPin className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                    <input
                      type="text"
                      value={address}
                      onChange={(e) => setAddress(e.target.value)}
                      placeholder="Indiranagar, Ward 84, Bengaluru"
                      className="w-full bg-slate-50 border border-slate-200 text-xs pl-9 pr-3 py-2 rounded-lg focus:bg-white focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                    />
                  </div>
                </div>
              )}

              {/* Officer-Specific: Employee ID & Department */}
              {accountType === 'officer' && (
                <>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-slate-700">Employee ID / Service #</label>
                      <div className="relative">
                        <BadgeCheck className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                        <input
                          type="text"
                          required
                          value={employeeId}
                          onChange={(e) => setEmployeeId(e.target.value)}
                          placeholder="MUNI-OFF-2026-089"
                          className="w-full bg-slate-50 border border-slate-200 text-xs pl-9 pr-3 py-2 rounded-lg focus:bg-white focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 font-mono"
                        />
                      </div>
                    </div>

                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-slate-700">Department</label>
                      <div className="relative">
                        <Building2 className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                        <select
                          value={department}
                          onChange={(e) => setDepartment(e.target.value)}
                          className="w-full bg-slate-50 border border-slate-200 text-xs pl-9 pr-3 py-2 rounded-lg focus:bg-white focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 cursor-pointer"
                        >
                          <option value="Encroachment Removal Squad">Encroachment Removal Squad</option>
                          <option value="Town Planning & Zoning">Town Planning &amp; Zoning</option>
                          <option value="Traffic Management & Mobility">Traffic Management &amp; Mobility</option>
                          <option value="Public Works Department">Public Works Department</option>
                          <option value="Revenue & Municipal Estate">Revenue &amp; Municipal Estate</option>
                        </select>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-slate-700">Designation</label>
                      <div className="relative">
                        <Briefcase className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                        <input
                          type="text"
                          required
                          value={designation}
                          onChange={(e) => setDesignation(e.target.value)}
                          placeholder="Ward Enforcement Officer"
                          className="w-full bg-slate-50 border border-slate-200 text-xs pl-9 pr-3 py-2 rounded-lg focus:bg-white focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                        />
                      </div>
                    </div>

                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-slate-700">Assigned Municipal Zone / Ward</label>
                      <div className="relative">
                        <MapPin className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                        <input
                          type="text"
                          required
                          value={assignedArea}
                          onChange={(e) => setAssignedArea(e.target.value)}
                          placeholder="East Zone - Ward 84"
                          className="w-full bg-slate-50 border border-slate-200 text-xs pl-9 pr-3 py-2 rounded-lg focus:bg-white focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                        />
                      </div>
                    </div>
                  </div>
                </>
              )}

              {/* Password & Confirm Password Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700">{t('password')}</label>
                  <div className="relative">
                    <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                    <input
                      type="password"
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Minimum 6 characters"
                      className="w-full bg-slate-50 border border-slate-200 text-xs pl-9 pr-3 py-2 rounded-lg focus:bg-white focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                    />
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700">Confirm Password</label>
                  <div className="relative">
                    <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                    <input
                      type="password"
                      required
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="Re-enter password"
                      className="w-full bg-slate-50 border border-slate-200 text-xs pl-9 pr-3 py-2 rounded-lg focus:bg-white focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                    />
                  </div>
                </div>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={loading}
                className={`w-full py-2.5 rounded-lg text-xs font-semibold text-white shadow-2xs transition-colors flex items-center justify-center gap-2 mt-4 disabled:opacity-50 ${
                  accountType === 'officer'
                    ? 'bg-slate-900 hover:bg-slate-800'
                    : 'bg-[#059669] hover:bg-[#047857]'
                }`}
              >
                {loading ? t('loading') : (
                  accountType === 'officer' ? 'Submit Officer Registration Application' : 'Create Citizen Account'
                )}
                <ArrowRight className="w-4 h-4" />
              </button>
            </form>
          </>
        )}

        {/* Switch to Login Link */}
        <div className="text-center text-xs text-slate-500 border-t border-slate-100 pt-3">
          <span>Already registered? </span>
          <button
            onClick={onSwitchToLogin}
            className="text-blue-600 font-semibold hover:underline"
          >
            Sign in to existing account
          </button>
        </div>
      </div>
    </div>
  );
}
