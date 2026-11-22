import React from 'react';
import {
  LayoutDashboard,
  AlertTriangle,
  MapPin,
  BarChart3,
  FileText,
  Users,
  Settings,
  ScanEye,
  ShieldCheck,
  Smartphone,
  CheckCircle2,
  LogOut,
  X,
  UserCheck,
  ArrowRightLeft,
  Cpu,
  Database,
  ClipboardList,
  Clock
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import EncroWatchLogo from './EncroWatchLogo';

export default function Sidebar({ activeTab, setActiveTab, mobileOpen = false, setMobileOpen, onLogout }) {
  const { role, user, logout } = useAuth();
  const { t } = useLanguage();

  const handleLogout = () => {
    logout();
    if (onLogout) onLogout();
  };

  // Citizen Navigation (strictly citizen-focused)
  const citizenNav = [
    { id: 'citizen-dashboard', key: 'dashboard', label: 'Citizen Dashboard', icon: LayoutDashboard },
    { id: 'citizen-report', key: 'reportEncroachment', label: 'Report Issue', icon: Smartphone },
    { id: 'my-reports', key: 'myReports', label: 'My Submissions', icon: CheckCircle2 },
    { id: 'public-transparency', key: 'publicTransparency', label: 'Public Transparency', icon: ShieldCheck },
    { id: 'map', key: 'map', label: 'City Accessibility Map', icon: MapPin },
  ];

  // Officer Navigation (field operations, assigned cases, AI review, clearance)
  const officerNav = [
    { id: 'officer-dashboard', key: 'officerDashboard', label: 'Field Operations', icon: LayoutDashboard },
    { id: 'incidents', key: 'assignedIncidents', label: 'Assigned Cases', icon: AlertTriangle },
    { id: 'ai-detection', key: 'aiDetection', label: 'Vision Inspection Review', icon: ScanEye },
    { id: 'map', key: 'map', label: 'Operational GIS Map', icon: MapPin },
    { id: 'public-transparency', key: 'publicTransparency', label: 'Public Transparency', icon: ShieldCheck },
    { id: 'reports', key: 'reports', label: 'Field Inspection Reports', icon: FileText },
  ];

  // Admin Navigation (comprehensive municipal administration)
  const adminNav = [
    { id: 'dashboard', key: 'dashboard', label: 'Operations Dashboard', icon: LayoutDashboard },
    { id: 'incidents', key: 'incidents', label: 'Incident Directory', icon: AlertTriangle },
    { id: 'ai-detection', key: 'aiDetection', label: 'AI Detection Engine', icon: ScanEye },
    { id: 'sla-management', key: 'slaManagement', label: 'SLA & Escalations', icon: Clock },
    { id: 'public-transparency', key: 'publicTransparency', label: 'Public Transparency', icon: ShieldCheck },
    { id: 'map', key: 'map', label: 'GIS Encroachment Map', icon: MapPin },
    { id: 'analytics', key: 'analytics', label: 'Spatial Analytics', icon: BarChart3 },
    { id: 'area-comparison', key: 'areaComparison', label: 'Ward Comparison', icon: ArrowRightLeft },
    { id: 'model-performance', key: 'modelPerformance', label: 'AI Model Benchmarks', icon: Cpu },
    { id: 'feedback-dataset', key: 'feedbackDataset', label: 'Model Feedback Dataset', icon: Database },
    { id: 'audit-logs', key: 'auditLogs', label: 'Audit Trail & Security', icon: ClipboardList },
    { id: 'reports', key: 'reports', label: 'Municipal Reports', icon: FileText },
    { id: 'users', key: 'users', label: 'User Directory', icon: Users },
    { id: 'officers', key: 'officers', label: 'Officer Roster', icon: UserCheck },
    { id: 'settings', key: 'settings', label: 'System Configuration', icon: Settings },
  ];

  const currentRole = role ? String(role).toLowerCase() : 'citizen';
  const navItems = currentRole === 'officer' ? officerNav : (currentRole === 'citizen' ? citizenNav : adminNav);

  const handleNavClick = (id) => {
    setActiveTab(id);
    if (setMobileOpen) setMobileOpen(false);
  };

  const getRoleBadge = () => {
    switch (currentRole) {
      case 'admin':
        return { label: 'Administrator', cls: 'bg-blue-500/15 text-blue-400 border-blue-500/30' };
      case 'officer':
        return { label: 'Field Officer', cls: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30' };
      case 'citizen':
      default:
        return { label: 'Citizen Reporter', cls: 'bg-purple-500/15 text-purple-400 border-purple-500/30' };
    }
  };

  const badge = getRoleBadge();

  return (
    <>
      {/* Mobile Backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs z-40 lg:hidden"
          onClick={() => setMobileOpen && setMobileOpen(false)}
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed lg:sticky top-0 left-0 z-50 h-screen w-64 bg-[#111827] text-slate-300 flex flex-col justify-between shrink-0 select-none shadow-xl transition-transform duration-200 ease-in-out border-r border-slate-800 ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        {/* Brand Header */}
        <div className="flex-1 overflow-y-auto">
          <div className="h-[64px] px-5 flex items-center justify-between border-b border-slate-800">
            <EncroWatchLogo size="sm" light={true} showSubtitle={true} />
            {setMobileOpen && (
              <button
                onClick={() => setMobileOpen(false)}
                className="lg:hidden p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                aria-label="Close menu"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* Role Navigation Group */}
          <div className="px-3 pt-4 pb-2">
            <span className="px-3 text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1.5">
              {currentRole === 'admin' ? 'Municipal Administration' : currentRole === 'officer' ? 'Field Operations' : 'Citizen Services'}
            </span>

            <nav className="space-y-0.5">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;

                return (
                  <button
                    key={item.id}
                    onClick={() => handleNavClick(item.id)}
                    className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
                      isActive
                        ? 'bg-slate-800 text-white font-semibold'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                    }`}
                  >
                    <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-emerald-400' : 'text-slate-500'}`} />
                    <span className="truncate">{t(item.key) || item.label}</span>
                  </button>
                );
              })}
            </nav>
          </div>
        </div>

        {/* User Identity Footer */}
        <div className="p-3.5 border-t border-slate-800 bg-[#0E1522] shrink-0 space-y-2.5">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-white text-xs shrink-0 overflow-hidden">
              {user?.avatar_url ? (
                <img src={user.avatar_url} alt="Avatar" className="w-full h-full object-cover" />
              ) : (
                <span>{(user?.full_name || user?.email || 'U').charAt(0).toUpperCase()}</span>
              )}
            </div>
            <div className="min-w-0 flex-1">
              <div className="text-xs font-semibold text-white truncate leading-tight">
                {user?.full_name || user?.email || 'Authenticated User'}
              </div>
              <div className="flex items-center gap-1.5 mt-0.5">
                <span className={`text-[10px] px-1.5 py-0.2 rounded font-semibold border ${badge.cls}`}>
                  {badge.label}
                </span>
                {user?.badge_id && (
                  <span className="text-[10px] text-slate-400 font-mono">
                    {user.badge_id}
                  </span>
                )}
              </div>
            </div>
          </div>

          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 py-1.5 px-3 text-xs font-medium text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>
    </>
  );
}
