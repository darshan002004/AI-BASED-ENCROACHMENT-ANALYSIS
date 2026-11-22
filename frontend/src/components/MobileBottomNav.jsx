import React from 'react';
import { LayoutDashboard, Smartphone, MapPin, CheckCircle2, ShieldCheck, AlertTriangle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';

export default function MobileBottomNav({ activeTab, setActiveTab }) {
  const { role } = useAuth();
  const { t } = useLanguage();

  const citizenTabs = [
    { id: 'citizen-dashboard', key: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'citizen-report', key: 'reportEncroachment', label: 'Report', icon: Smartphone, highlight: true },
    { id: 'my-reports', key: 'myReports', label: 'My Reports', icon: CheckCircle2 },
    { id: 'map', key: 'map', label: 'Map', icon: MapPin },
  ];

  const officerTabs = [
    { id: 'officer-dashboard', key: 'officerDashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'incidents', key: 'assignedIncidents', label: 'Assigned', icon: ShieldCheck, highlight: true },
    { id: 'map', key: 'map', label: 'Map', icon: MapPin },
  ];

  const adminTabs = [
    { id: 'dashboard', key: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'incidents', key: 'incidents', label: 'Incidents', icon: AlertTriangle },
    { id: 'map', key: 'map', label: 'Map', icon: MapPin },
    { id: 'analytics', key: 'analytics', label: 'Analytics', icon: LayoutDashboard },
  ];

  const tabs = role === 'officer' ? officerTabs : (role === 'citizen' ? citizenTabs : adminTabs);

  return (
    <div className="lg:hidden fixed bottom-0 left-0 right-0 z-40 bg-white border-t border-slate-200 shadow-lg px-2 py-1.5 flex items-center justify-around select-none">
      {tabs.map((tab) => {
        const Icon = tab.icon;
        const isActive = activeTab === tab.id;

        if (tab.highlight) {
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className="flex flex-col items-center justify-center -mt-5"
            >
              <div className="w-12 h-12 rounded-full bg-emerald-600 text-white flex items-center justify-center shadow-lg shadow-emerald-600/30 ring-4 ring-white">
                <Icon className="w-5 h-5" />
              </div>
              <span className="text-[10px] font-bold text-emerald-700 mt-1">{t(tab.key) || tab.label}</span>
            </button>
          );
        }

        return (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex flex-col items-center justify-center py-1 px-3 rounded-xl transition-colors ${
              isActive ? 'text-blue-600 font-bold' : 'text-slate-400 hover:text-slate-700'
            }`}
          >
            <Icon className="w-5 h-5" />
            <span className="text-[10px] mt-0.5">{t(tab.key) || tab.label}</span>
          </button>
        );
      })}
    </div>
  );
}
