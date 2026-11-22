import React, { useState, useEffect } from 'react';
import {
  Smartphone,
  CheckCircle2,
  Clock,
  AlertTriangle,
  MapPin,
  ChevronRight,
  Plus,
  ShieldCheck,
  FileText
} from 'lucide-react';
import { incidentsAPI } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import { StatusBadge, SeverityBadge } from '../../components/StatusBadge';

export default function CitizenDashboard({ onNewReport, onViewAllReports, onSelectIncident }) {
  const { user } = useAuth();
  const { t } = useLanguage();
  const [reports, setReports] = useState([]);
  const [stats, setStats] = useState({
    total: 0,
    inReview: 0,
    resolved: 0,
    pending: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    incidentsAPI.list({ my_reports: true, limit: 10 })
      .then((res) => {
        const data = res.data || [];
        setReports(data);

        // Compute dynamic counts from live citizen reports
        const total = data.length;
        const inReview = data.filter(r => ['AI Review', 'In Progress', 'Assigned'].includes(r.status)).length;
        const resolved = data.filter(r => r.status === 'Resolved').length;
        const pending = data.filter(r => ['Pending', 'Submitted'].includes(r.status)).length;

        setStats({ total, inReview, resolved, pending });
      })
      .catch((err) => {
        console.warn('Could not fetch citizen reports:', err);
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-5 max-w-6xl mx-auto pb-16">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200/80 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-semibold tracking-wider text-slate-500 uppercase">Citizen Service Portal</span>
            <span className="text-slate-300">•</span>
            <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200/80">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-600"></span>
              Live Telemetry
            </span>
          </div>
          <h1 className="text-lg font-bold text-slate-900 tracking-tight mt-1">
            {t('welcomeCitizen')}, {user?.full_name ? user.full_name.split(' ')[0] : 'Citizen'}
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            {t('citizenTagline')}
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <button
            onClick={onNewReport}
            className="px-3.5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs shadow-2xs flex items-center gap-1.5 transition-colors"
          >
            <Plus className="w-3.5 h-3.5 stroke-[2.5]" />
            <span>{t('newReport')}</span>
          </button>
        </div>
      </div>

      {/* 4 Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
        {/* Card 1: My Reports */}
        <div className="bg-white rounded-xl p-4 border border-slate-200/90 shadow-2xs flex items-center justify-between">
          <div>
            <div className="text-2xl font-bold text-slate-900 tracking-tight">{stats.total}</div>
            <div className="text-xs font-medium text-slate-500 mt-0.5">{t('myReports')}</div>
          </div>
          <div className="w-9 h-9 rounded-lg bg-blue-50 text-blue-700 flex items-center justify-center border border-blue-100">
            <FileText className="w-4 h-4" />
          </div>
        </div>

        {/* Card 2: In Review */}
        <div className="bg-white rounded-xl p-4 border border-slate-200/90 shadow-2xs flex items-center justify-between">
          <div>
            <div className="text-2xl font-bold text-slate-900 tracking-tight">{stats.inReview}</div>
            <div className="text-xs font-medium text-slate-500 mt-0.5">{t('inReview')}</div>
          </div>
          <div className="w-9 h-9 rounded-lg bg-amber-50 text-amber-700 flex items-center justify-center border border-amber-100">
            <Clock className="w-4 h-4" />
          </div>
        </div>

        {/* Card 3: Resolved */}
        <div className="bg-white rounded-xl p-4 border border-slate-200/90 shadow-2xs flex items-center justify-between">
          <div>
            <div className="text-2xl font-bold text-slate-900 tracking-tight">{stats.resolved}</div>
            <div className="text-xs font-medium text-slate-500 mt-0.5">{t('resolved')}</div>
          </div>
          <div className="w-9 h-9 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center border border-emerald-100">
            <CheckCircle2 className="w-4 h-4" />
          </div>
        </div>

        {/* Card 4: Pending */}
        <div className="bg-white rounded-xl p-4 border border-slate-200/90 shadow-2xs flex items-center justify-between">
          <div>
            <div className="text-2xl font-bold text-slate-900 tracking-tight">{stats.pending}</div>
            <div className="text-xs font-medium text-slate-500 mt-0.5">{t('pending')}</div>
          </div>
          <div className="w-9 h-9 rounded-lg bg-slate-100 text-slate-700 flex items-center justify-center border border-slate-200">
            <AlertTriangle className="w-4 h-4" />
          </div>
        </div>
      </div>

      {/* Corridor Reporting Notice Banner */}
      <div className="bg-white rounded-xl border border-slate-200/90 p-4 shadow-2xs flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center shrink-0 border border-emerald-100">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-slate-900">IRC:SP:102 Municipal Compliance Inspection</h3>
            <p className="text-[11px] text-slate-500 mt-0.5">
              Citizen reports are cryptographically hashed and inspected against clear-width urban pedestrian standards.
            </p>
          </div>
        </div>

        <button
          onClick={onNewReport}
          className="px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs shadow-2xs shrink-0 transition-colors"
        >
          Submit Encroachment Report
        </button>
      </div>

      {/* Recent Reports Section */}
      <div className="bg-white rounded-xl border border-slate-200/90 shadow-2xs p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h2 className="text-sm font-bold text-slate-900 tracking-tight">Recent Submissions</h2>
            <p className="text-xs text-slate-500 mt-0.5">Track the lifecycle of your reported corridor incidents</p>
          </div>
          <button
            onClick={onViewAllReports}
            className="text-xs font-semibold text-blue-600 hover:text-blue-800 flex items-center gap-1 transition-colors"
          >
            <span>{t('viewAllReports')}</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* List Cards */}
        {loading ? (
          <div className="p-12 text-center text-slate-500">
            <div className="animate-spin w-7 h-7 border-3 border-slate-700 border-t-transparent rounded-full mx-auto mb-3" />
            <p className="text-xs font-medium text-slate-600">{t('loading')}</p>
          </div>
        ) : reports.length > 0 ? (
          <div className="divide-y divide-slate-100">
            {reports.map((report) => {
              const statusStr = report.status || 'Pending';

              return (
                <div
                  key={report.id || report._id}
                  onClick={() => onSelectIncident && onSelectIncident(report)}
                  className="py-3 flex items-center justify-between gap-4 hover:bg-slate-50/80 p-2.5 rounded-lg transition-colors cursor-pointer group"
                >
                  <div className="flex items-center gap-3.5 min-w-0">
                    <img
                      src={report.privacy_image_url || report.image_url || '/uploads/original/clear_street.jpg'}
                      alt={report.title}
                      onError={(e) => { e.currentTarget.onerror = null; e.currentTarget.src = '/uploads/original/clear_street.jpg'; }}
                      className="w-12 h-12 rounded-lg object-cover border border-slate-200 shrink-0 bg-slate-100"
                    />

                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <h3 className="text-xs font-bold text-slate-900 group-hover:text-blue-600 transition-colors truncate">
                          {report.primary_encroachment_type || report.title}
                        </h3>
                        {report.incident_number && (
                          <span className="font-mono text-[10px] text-slate-400">
                            {report.incident_number}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2 text-[11px] text-slate-500 mt-0.5">
                        <span className="flex items-center gap-1 truncate">
                          <MapPin className="w-3 h-3 text-slate-400 shrink-0" />
                          {report.location_name || report.title || 'Bengaluru Corridor'}
                        </span>
                        <span>•</span>
                        <span className="shrink-0">{report.date_reported || 'Recently Reported'}</span>
                      </div>
                    </div>
                  </div>

                  {/* Status Badge */}
                  <div className="shrink-0 flex items-center gap-2">
                    <StatusBadge status={statusStr} />
                    <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-slate-600 transition-colors" />
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="p-12 text-center text-slate-400 text-xs">
            <CheckCircle2 className="w-8 h-8 text-slate-300 mx-auto mb-2" />
            <p className="font-semibold text-slate-700">No incidents have been reported yet.</p>
            <p className="text-slate-500 mt-1">When you report footpath obstructions or sidewalk encroachments, their verification and resolution progress will appear here.</p>
          </div>
        )}
      </div>
    </div>
  );
}
