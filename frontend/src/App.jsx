import React, { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { NotificationProvider } from './context/NotificationContext';
import { LanguageProvider } from './context/LanguageContext';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import MobileBottomNav from './components/MobileBottomNav';
import { ErrorBoundary } from './components/ErrorBoundary';
import { ShieldAlert, ArrowLeft } from 'lucide-react';

// Pages
import LandingPage from './pages/LandingPage';
import Login from './pages/Login';
import Register from './pages/Register';
import AdminDashboard from './pages/admin/AdminDashboard';
import IncidentsPage from './pages/admin/IncidentsPage';
import IncidentDetailPage from './pages/admin/IncidentDetailPage';
import AIDetectionPlayground from './pages/admin/AIDetectionPlayground';
import GISMapPage from './pages/admin/GISMapPage';
import AnalyticsPage from './pages/admin/AnalyticsPage';
import HotspotsPage from './pages/admin/HotspotsPage';
import ReportsPage from './pages/admin/ReportsPage';
import UsersPage from './pages/admin/UsersPage';
import SettingsPage from './pages/admin/SettingsPage';
import AreaComparisonPage from './pages/admin/AreaComparisonPage';
import AIModelPerformancePage from './pages/admin/AIModelPerformancePage';
import AIFeedbackPage from './pages/admin/AIFeedbackPage';
import AuditLogPage from './pages/admin/AuditLogPage';
import CitizenDashboard from './pages/citizen/CitizenDashboard';
import ReportEncroachment from './pages/citizen/ReportEncroachment';
import MyReports from './pages/citizen/MyReports';
import OfficerDashboard from './pages/officer/OfficerDashboard';
import InspectionPage from './pages/officer/InspectionPage';
import PublicTransparencyPage from './pages/PublicTransparencyPage';
import SLAManagementPage from './pages/admin/SLAManagementPage';

// Role-Based Access Control Policy
const ROLE_PERMISSIONS = {
  admin: [
    'dashboard', 'incidents', 'incident-detail', 'ai-detection', 'sla-management',
    'public-transparency', 'map', 'analytics', 'area-comparison', 'model-performance',
    'feedback-dataset', 'audit-logs', 'reports', 'users', 'officers', 'settings',
    'inspection', 'hotspots', 'citizen-dashboard', 'citizen-report', 'my-reports',
    'officer-dashboard'
  ],
  officer: [
    'officer-dashboard', 'incidents', 'incident-detail', 'ai-detection',
    'map', 'public-transparency', 'reports', 'inspection'
  ],
  citizen: [
    'citizen-dashboard', 'citizen-report', 'my-reports', 'incident-detail',
    'public-transparency', 'map'
  ]
};

const DEFAULT_ROLE_DASHBOARD = {
  admin: 'dashboard',
  officer: 'officer-dashboard',
  citizen: 'citizen-dashboard'
};

function AppContent() {
  const { user, role, token, isAuthenticated, loading, logout } = useAuth();
  
  // Initialize view: unauthenticated visits show landing page; logged in users show app
  const [currentView, setCurrentView] = useState(() => {
    return localStorage.getItem('encrowatch_token') ? 'app' : 'landing';
  });
  
  const [activeTab, setActiveTab] = useState(() => {
    const savedUser = localStorage.getItem('encrowatch_user');
    if (savedUser) {
      try {
        const parsed = JSON.parse(savedUser);
        const savedRole = parsed?.role?.toLowerCase();
        return DEFAULT_ROLE_DASHBOARD[savedRole] || 'citizen-dashboard';
      } catch (e) {
        return 'citizen-dashboard';
      }
    }
    return 'citizen-dashboard';
  });

  const [selectedIncidentId, setSelectedIncidentId] = useState(null);
  const [inspectionIncident, setInspectionIncident] = useState(null);
  const [mobileOpen, setMobileOpen] = useState(false);

  // Synchronize dashboard tab whenever authenticated role changes
  useEffect(() => {
    if (role) {
      const allowed = ROLE_PERMISSIONS[role] || [];
      if (!allowed.includes(activeTab)) {
        setActiveTab(DEFAULT_ROLE_DASHBOARD[role] || 'citizen-dashboard');
      }
    }
  }, [role]);

  // Loading state while verifying credentials on refresh
  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex flex-col items-center justify-center text-white">
        <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-sm font-semibold text-slate-300">Verifying municipal authentication...</p>
      </div>
    );
  }

  // If unauthenticated and trying to view the protected app shell, redirect to login
  if (!isAuthenticated && currentView === 'app') {
    return (
      <Login
        onSwitchToRegister={() => setCurrentView('register')}
        onLoginSuccess={(newRole) => {
          const targetTab = DEFAULT_ROLE_DASHBOARD[newRole] || 'citizen-dashboard';
          setActiveTab(targetTab);
          setCurrentView('app');
        }}
      />
    );
  }

  // Landing page view
  if (currentView === 'landing') {
    return (
      <LandingPage
        onEnterApp={(target) => {
          if (target === 'login') {
            setCurrentView('login');
          } else if (target === 'register') {
            setCurrentView('register');
          } else if (target === 'public-transparency') {
            if (isAuthenticated) {
              setActiveTab('public-transparency');
              setCurrentView('app');
            } else {
              setCurrentView('public-transparency');
            }
          } else if (isAuthenticated) {
            if (target && (ROLE_PERMISSIONS[role] || []).includes(target)) {
              setActiveTab(target);
            } else {
              setActiveTab(DEFAULT_ROLE_DASHBOARD[role] || 'citizen-dashboard');
            }
            setCurrentView('app');
          } else {
            setCurrentView('login');
          }
        }}
      />
    );
  }

  // Standalone Public Transparency view for unauthenticated citizens
  if (currentView === 'public-transparency') {
    return (
      <div className="min-h-screen bg-[#F5F7FA] flex flex-col font-sans">
        <header className="h-[64px] bg-white border-b border-slate-200 px-6 sm:px-10 flex items-center justify-between sticky top-0 z-40 shadow-xs">
          <button
            onClick={() => setCurrentView('landing')}
            className="flex items-center gap-2 text-xs font-semibold text-slate-700 hover:text-slate-900 px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Home</span>
          </button>
          <div className="flex items-center gap-2.5">
            <button
              onClick={() => setCurrentView('login')}
              className="px-3.5 py-1.5 text-xs font-semibold text-slate-700 hover:text-slate-900 rounded-lg hover:bg-slate-100 transition-colors"
            >
              Login
            </button>
            <button
              onClick={() => setCurrentView('register')}
              className="px-3.5 py-1.5 text-xs font-semibold text-white bg-[#059669] hover:bg-[#047857] rounded-lg shadow-2xs transition-colors"
            >
              Sign Up
            </button>
          </div>
        </header>
        <main className="p-4 sm:p-6 flex-1 max-w-7xl mx-auto w-full">
          <PublicTransparencyPage />
        </main>
      </div>
    );
  }

  // Login view
  if (currentView === 'login') {
    return (
      <Login
        onSwitchToRegister={() => setCurrentView('register')}
        onBackToHome={() => setCurrentView('landing')}
        onLoginSuccess={(newRole) => {
          const targetTab = DEFAULT_ROLE_DASHBOARD[newRole] || 'citizen-dashboard';
          setActiveTab(targetTab);
          setCurrentView('app');
        }}
      />
    );
  }

  // Register view
  if (currentView === 'register') {
    return (
      <Register
        onSwitchToLogin={() => setCurrentView('login')}
        onBackToHome={() => setCurrentView('landing')}
        onRegisterSuccess={(registeredRole) => {
          if (registeredRole === 'officer') {
            setCurrentView('login');
          } else {
            setActiveTab('citizen-dashboard');
            setCurrentView('app');
          }
        }}
      />
    );
  }

  const handleSelectIncident = (inc) => {
    setSelectedIncidentId(inc.id || inc._id);
    setActiveTab('incident-detail');
  };

  const handleConductInspection = (inc) => {
    setInspectionIncident(inc);
    setActiveTab('inspection');
  };

  const handleLogout = () => {
    logout();
    setCurrentView('login');
    setSelectedIncidentId(null);
    setInspectionIncident(null);
  };

  // Check RBAC permission for the currently active tab
  const allowedTabs = ROLE_PERMISSIONS[role] || [];
  const hasTabPermission = allowedTabs.includes(activeTab);

  // Determine page title for top header
  const getPageTitle = () => {
    switch (activeTab) {
      case 'dashboard': return 'Admin Dashboard';
      case 'citizen-dashboard': return 'Citizen Portal';
      case 'officer-dashboard': return 'Officer Operations Dashboard';
      case 'citizen-report': return 'Report Encroachment';
      case 'my-reports': return 'My Submissions';
      case 'incidents': return 'Incident Management';
      case 'incident-detail': return 'Incident Dossier';
      case 'ai-detection': return 'AI Detection Engine';
      case 'map': return 'Interactive Map';
      case 'analytics': return 'Analytics & Reports';
      case 'area-comparison': return 'Ward & Area Comparison';
      case 'model-performance': return 'AI Model Performance';
      case 'feedback-dataset': return 'AI Feedback Dataset';
      case 'audit-logs': return 'Audit Trail & Governance Logs';
      case 'reports': return 'Report Generation';
      case 'users': return 'User Directory';
      case 'officers': return 'Field Officer Roster';
      case 'settings': return 'System Settings';
      case 'inspection': return 'Field Clearance Verification';
      case 'public-transparency': return 'Public Transparency Portal';
      case 'sla-management': return 'Municipal SLA & Escalation Engine';
      default: return 'EncroWatch AI';
    }
  };

  return (
    <div className="flex min-h-screen bg-[#F5F7FA]">
      {/* Sidebar navigation filtered strictly by user role */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={(tab) => {
          setActiveTab(tab);
          setSelectedIncidentId(null);
        }}
        mobileOpen={mobileOpen}
        setMobileOpen={setMobileOpen}
        onLogout={handleLogout}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-x-hidden">
        <Header
          pageTitle={getPageTitle()}
          onToggleMobileMenu={() => setMobileOpen(!mobileOpen)}
          onSearch={(query) => {
            if (query && activeTab !== 'incidents') {
              setActiveTab('incidents');
            }
          }}
          onSelectIncident={handleSelectIncident}
        />

        <main className="flex-1 p-4 sm:p-6 lg:p-7 pb-20 lg:pb-8">
          {/* RBAC Route Guard: Block unauthorized direct navigation */}
          {!hasTabPermission ? (
            <div className="max-w-md mx-auto my-12 p-6 bg-white rounded-xl border border-red-200 shadow-sm text-center space-y-3">
              <div className="w-12 h-12 bg-red-50 text-red-600 rounded-xl mx-auto flex items-center justify-center">
                <ShieldAlert className="w-6 h-6" />
              </div>
              <h2 className="text-lg font-bold text-slate-900">Access Restricted</h2>
              <p className="text-xs text-slate-600">
                Your account role (<strong className="capitalize text-slate-800">{role}</strong>) is not authorized to access <strong>{getPageTitle()}</strong>.
              </p>
              <div className="pt-2">
                <button
                  onClick={() => setActiveTab(DEFAULT_ROLE_DASHBOARD[role] || 'citizen-dashboard')}
                  className="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg text-xs transition-colors shadow-xs"
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                  Return to Dashboard
                </button>
              </div>
            </div>
          ) : (
            <>
              {/* Admin Views */}
              {activeTab === 'dashboard' && (
                <AdminDashboard
                  onNavigate={(tab) => setActiveTab(tab)}
                  onSelectIncident={handleSelectIncident}
                />
              )}

              {activeTab === 'incidents' && (
                <IncidentsPage
                  onSelectIncident={handleSelectIncident}
                  onNewIncident={() => setActiveTab('citizen-report')}
                />
              )}

              {activeTab === 'incident-detail' && (
                <IncidentDetailPage
                  incidentId={selectedIncidentId}
                  onBack={() => setActiveTab(DEFAULT_ROLE_DASHBOARD[role] || 'citizen-dashboard')}
                />
              )}

              {activeTab === 'ai-detection' && (
                <AIDetectionPlayground
                  onIncidentCreated={(newInc) => handleSelectIncident(newInc)}
                />
              )}

              {activeTab === 'map' && (
                <GISMapPage onSelectIncident={handleSelectIncident} />
              )}

              {activeTab === 'analytics' && (
                <AnalyticsPage />
              )}

              {activeTab === 'area-comparison' && (
                <AreaComparisonPage />
              )}

              {activeTab === 'model-performance' && (
                <AIModelPerformancePage />
              )}

              {activeTab === 'feedback-dataset' && (
                <AIFeedbackPage />
              )}

              {activeTab === 'audit-logs' && (
                <AuditLogPage />
              )}

              {activeTab === 'hotspots' && (
                <HotspotsPage onSelectArea={() => setActiveTab('map')} />
              )}

              {activeTab === 'reports' && (
                <ReportsPage />
              )}

              {activeTab === 'users' && (
                <UsersPage />
              )}

              {activeTab === 'officers' && (
                <UsersPage filterRole="officer" />
              )}

              {activeTab === 'settings' && (
                <SettingsPage />
              )}

              {activeTab === 'public-transparency' && (
                <PublicTransparencyPage />
              )}

              {activeTab === 'sla-management' && (
                <SLAManagementPage />
              )}

              {/* Citizen Views */}
              {activeTab === 'citizen-dashboard' && (
                <CitizenDashboard
                  onNewReport={() => setActiveTab('citizen-report')}
                  onViewAllReports={() => setActiveTab('my-reports')}
                  onSelectIncident={handleSelectIncident}
                />
              )}

              {activeTab === 'citizen-report' && (
                <ReportEncroachment
                  onReportSubmitted={() => setActiveTab('my-reports')}
                />
              )}

              {activeTab === 'my-reports' && (
                <MyReports
                  onSelectIncident={handleSelectIncident}
                  onNewReport={() => setActiveTab('citizen-report')}
                />
              )}

              {/* Officer Views */}
              {activeTab === 'officer-dashboard' && (
                <OfficerDashboard
                  onConductInspection={handleConductInspection}
                  onSelectIncident={handleSelectIncident}
                />
              )}

              {activeTab === 'inspection' && (
                <InspectionPage
                  incident={inspectionIncident}
                  onBack={() => setActiveTab(DEFAULT_ROLE_DASHBOARD[role] || 'officer-dashboard')}
                  onInspectionComplete={() => setActiveTab('incident-detail')}
                />
              )}
            </>
          )}
        </main>
      </div>

      {/* Mobile Bottom Navigation */}
      <MobileBottomNav activeTab={activeTab} setActiveTab={setActiveTab} />
    </div>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <NotificationProvider>
          <LanguageProvider>
            <AppContent />
          </LanguageProvider>
        </NotificationProvider>
      </AuthProvider>
    </ErrorBoundary>
  );
}
