import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  Eye,
  Calendar,
  CheckCircle2,
  Clock,
  AlertTriangle,
  BarChart3,
  MapPin,
  Search,
  Filter,
  Info,
  ExternalLink,
  ChevronRight,
  TrendingUp,
  FileText
} from 'lucide-react';
import { publicAPI } from '../services/api';
import { StatusBadge, SeverityBadge } from '../components/StatusBadge';
import { useLanguage } from '../context/LanguageContext';

export default function PublicTransparencyPage() {
  const { t } = useLanguage();
  const [stats, setStats] = useState(null);
  const [incidents, setIncidents] = useState([]);
  const [loadingStats, setLoadingStats] = useState(true);
  const [loadingIncidents, setLoadingIncidents] = useState(true);

  // Filters
  const [statusFilter, setStatusFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [daysFilter, setDaysFilter] = useState(30);
  const [selectedIncident, setSelectedIncident] = useState(null);

  useEffect(() => {
    fetchStatistics();
  }, [daysFilter]);

  useEffect(() => {
    fetchIncidents();
  }, [statusFilter, categoryFilter, daysFilter]);

  const fetchStatistics = async () => {
    try {
      setLoadingStats(true);
      const res = await publicAPI.getStatistics(daysFilter);
      setStats(res.data);
    } catch (err) {
      console.error('Failed to load public statistics:', err);
    } finally {
      setLoadingStats(false);
    }
  };

  const fetchIncidents = async () => {
    try {
      setLoadingIncidents(true);
      const params = { limit: 50 };
      if (statusFilter) params.status = statusFilter;
      if (categoryFilter) params.category = categoryFilter;
      if (daysFilter) params.days = daysFilter;

      const res = await publicAPI.getIncidents(params);
      const items = Array.isArray(res.data) ? res.data : (res.data?.items || []);
      setIncidents(items);
    } catch (err) {
      console.error('Failed to load public incidents:', err);
    } finally {
      setLoadingIncidents(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-5 pb-20">
      {/* Header Banner */}
      <div className="bg-[#111827] text-white rounded-xl p-6 sm:p-7 shadow-2xs relative overflow-hidden">
        <div className="relative z-10 max-w-3xl space-y-2.5">
          <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-md bg-slate-800 border border-slate-700 text-slate-300 text-[11px] font-semibold tracking-wide">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>MUNICIPAL PUBLIC TRANSPARENCY & CITIZEN OPEN DATA</span>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight">
            City Footpath Accessibility &amp; Encroachment Transparency Portal
          </h1>
          <p className="text-xs sm:text-xs text-slate-300 leading-relaxed font-normal">
            Real-time public audit of reported sidewalk obstructions, municipal enforcement actions, and verified clearances across urban corridors.
          </p>
          <div className="flex items-center gap-2 text-[11px] text-amber-300 bg-amber-950/40 border border-amber-500/30 px-2.5 py-1 rounded-md w-fit">
            <Info className="w-3.5 h-3.5 shrink-0" />
            <span>
              {t('anonymousDataNotice') || 'Privacy Protected: Location coordinates generalized (~1.1km) and faces/plates redacted.'}
            </span>
          </div>
        </div>
      </div>

      {/* Aggregate KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
        <div className="bg-white rounded-xl p-4 border border-slate-200/90 shadow-2xs">
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
            <span>Total Reported</span>
            <FileText className="w-4 h-4 text-slate-400" />
          </div>
          <div className="text-2xl font-bold text-slate-900 mt-1">
            {loadingStats ? '...' : (stats?.total_reports_received ?? stats?.total_reported ?? 0)}
          </div>
          <div className="text-[11px] text-slate-400 mt-0.5">In last {daysFilter} days</div>
        </div>

        <div className="bg-white rounded-xl p-4 border border-slate-200/90 shadow-2xs">
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
            <span>Verified Clearances</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-2xl font-bold text-emerald-600 mt-1">
            {loadingStats ? '...' : (stats?.verified_resolutions ?? stats?.verified_resolved ?? 0)}
          </div>
          <div className="text-[11px] text-emerald-700 font-medium mt-0.5">
            {loadingStats ? '' : `${stats?.resolution_rate_pct ?? stats?.verified_clearance_rate_pct ?? 0}% verified rate`}
          </div>
        </div>

        <div className="bg-white rounded-xl p-4 border border-slate-200/90 shadow-2xs">
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
            <span>Avg Resolution Time</span>
            <Clock className="w-4 h-4 text-slate-400" />
          </div>
          <div className="text-2xl font-bold text-slate-900 mt-1">
            {loadingStats ? '...' : `${stats?.average_resolution_days ?? stats?.avg_resolution_days ?? 0}d`}
          </div>
          <div className="text-[11px] text-slate-400 mt-0.5">From report to verification</div>
        </div>

        <div className="bg-white rounded-xl p-4 border border-slate-200/90 shadow-2xs">
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
            <span>Active Investigations</span>
            <AlertTriangle className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-2xl font-bold text-slate-900 mt-1">
            {loadingStats ? '...' : (stats?.open_cases ?? stats?.under_investigation ?? 0)}
          </div>
          <div className="text-[11px] text-slate-400 mt-0.5">Pending field resolution</div>
        </div>
      </div>

      {/* Filter and Control Bar */}
      <div className="bg-white rounded-xl p-3.5 border border-slate-200/90 shadow-2xs flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2 flex-wrap text-xs">
          <span className="font-semibold text-slate-700 flex items-center gap-1">
            <Filter className="w-3.5 h-3.5" /> Filters:
          </span>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-50 border border-slate-200 text-slate-700 rounded-lg px-2.5 py-1.5 focus:outline-none font-medium text-xs"
          >
            <option value="">All Statuses</option>
            <option value="Resolved - Verified">Resolved - Verified</option>
            <option value="Resolved - Pending Verification">Clearance Submitted</option>
            <option value="In Progress">In Progress</option>
            <option value="Under Investigation">Under Investigation</option>
            <option value="Reopened">Reopened</option>
          </select>

          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="bg-slate-50 border border-slate-200 text-slate-700 rounded-xl px-2.5 py-1.5 focus:outline-none font-medium"
          >
            <option value="">All Categories</option>
            <option value="Street Vendor">Street Vendor</option>
            <option value="Construction Material">Construction Material</option>
            <option value="Vehicle on Footpath">Vehicle on Footpath</option>
            <option value="Commercial Display">Commercial Display</option>
            <option value="Temporary Structure">Temporary Structure</option>
          </select>

          <select
            value={daysFilter}
            onChange={(e) => setDaysFilter(Number(e.target.value))}
            className="bg-slate-50 border border-slate-200 text-slate-700 rounded-xl px-2.5 py-1.5 focus:outline-none font-medium"
          >
            <option value={7}>Last 7 Days</option>
            <option value={30}>Last 30 Days</option>
            <option value={90}>Last 90 Days</option>
            <option value={365}>Last 1 Year</option>
          </select>
        </div>

        <div className="text-xs text-slate-400">
          Showing <strong>{incidents.length}</strong> public records
        </div>
      </div>

      {/* Incidents Table / Cards */}
      {loadingIncidents ? (
        <div className="bg-white rounded-2xl p-12 text-center text-slate-400 border border-slate-200/90 animate-pulse">
          Loading transparent incident records...
        </div>
      ) : incidents.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 text-center text-slate-400 border border-slate-200/90">
          No incidents found matching current filters.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {incidents.map((inc, idx) => (
            <div
              key={inc.id || inc._id || `${inc.incident_number || 'inc'}_${idx}`}
              onClick={() => setSelectedIncident(inc)}
              className="bg-white rounded-2xl border border-slate-200/90 shadow-xs hover:shadow-md transition-all p-4 flex flex-col justify-between cursor-pointer space-y-3 group"
            >
              <div className="space-y-3">
                {/* Image Preview (Strictly blurred) */}
                <div className="relative h-40 w-full rounded-xl overflow-hidden bg-slate-100 border border-slate-200">
                  <img
                    src={inc.privacy_image_url || inc.blurred_image_url || '/uploads/original/clear_street.jpg'}
                    alt={inc.category || 'Encroachment'}
                    onError={(e) => {
                      e.currentTarget.onerror = null;
                      e.currentTarget.src = '/uploads/original/clear_street.jpg';
                    }}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  />
                  <div className="absolute top-2 left-2 flex items-center gap-1 px-2 py-0.5 rounded-md bg-black/60 text-white text-[10px] font-bold backdrop-blur-xs">
                    <Eye className="w-3 h-3" /> Anonymized View
                  </div>
                  <div className="absolute top-2 right-2">
                    <StatusBadge status={inc.public_status || inc.status} />
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-mono font-bold text-blue-600">{inc.incident_number}</span>
                    <SeverityBadge severity={inc.severity || 'Medium'} />
                  </div>
                  <h3 className="font-bold text-slate-900 text-sm mt-1 group-hover:text-blue-600 transition-colors">
                    {inc.category}
                  </h3>
                  <div className="text-xs text-slate-500 flex items-center gap-1 mt-1">
                    <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <span className="truncate">{inc.generalized_location || inc.ward || 'Bengaluru Urban Corridor'}</span>
                  </div>
                </div>

                {/* Spatial Coarse Coordinates & Metrics */}
                <div className="p-2.5 rounded-xl bg-slate-50 text-[11px] text-slate-600 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Coarse Area:</span>
                    <span className="font-mono font-semibold">
                      {(inc.generalized_latitude || inc.coarse_latitude) && (inc.generalized_longitude || inc.coarse_longitude)
                        ? `${(inc.generalized_latitude || inc.coarse_latitude).toFixed(2)}°N, ${(inc.generalized_longitude || inc.coarse_longitude).toFixed(2)}°E (~1.1km grid)`
                        : 'Ward Aggregated'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Footpath Occupancy:</span>
                    <span className="font-bold text-slate-800">{inc.occupancy_percentage ?? 25}%</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Accessibility Index:</span>
                    <span className="font-bold text-blue-600">{inc.accessibility_score ?? 75}%</span>
                  </div>
                </div>
              </div>

              <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
                <span>Reported: {inc.date_reported}</span>
                <span className="text-blue-600 font-semibold group-hover:translate-x-0.5 transition-transform flex items-center gap-0.5">
                  Inspect Record <ChevronRight className="w-3 h-3" />
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Detail Modal */}
      {selectedIncident && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-xl w-full p-6 shadow-2xl border border-slate-100 space-y-5 animate-scale-in">
            <div className="flex items-start justify-between border-b border-slate-100 pb-3">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-mono font-bold text-xs text-blue-600">{selectedIncident.incident_number}</span>
                  <StatusBadge status={selectedIncident.public_status || selectedIncident.status} />
                  <SeverityBadge severity={selectedIncident.severity || 'Medium'} />
                </div>
                <h2 className="text-base font-bold text-slate-900 mt-1">{selectedIncident.category}</h2>
                <div className="text-xs text-slate-500">{selectedIncident.generalized_location || selectedIncident.ward || 'Bengaluru Corridor'}</div>
              </div>
              <button
                onClick={() => setSelectedIncident(null)}
                className="text-slate-400 hover:text-slate-700 text-xs font-bold px-2.5 py-1 bg-slate-100 rounded-lg"
              >
                Close
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <span className="text-xs font-bold text-slate-700 block mb-1">Blurred Original</span>
                <img
                  src={selectedIncident.privacy_image_url || selectedIncident.blurred_image_url || '/uploads/original/clear_street.jpg'}
                  alt="Anonymized Original"
                  onError={(e) => {
                    e.currentTarget.onerror = null;
                    e.currentTarget.src = '/uploads/original/clear_street.jpg';
                  }}
                  className="w-full h-36 rounded-xl object-cover border border-slate-200"
                />
              </div>

              {selectedIncident.after_image_url ? (
                <div>
                  <span className="text-xs font-bold text-emerald-700 block mb-1">Verified Clearance</span>
                  <img
                    src={selectedIncident.after_image_url}
                    alt="Verified Clearance"
                    onError={(e) => {
                      e.currentTarget.onerror = null;
                      e.currentTarget.src = '/uploads/original/clear_street.jpg';
                    }}
                    className="w-full h-36 rounded-xl object-cover border border-emerald-300"
                  />
                </div>
              ) : (
                <div className="h-36 rounded-xl bg-slate-50 border border-dashed border-slate-200 flex flex-col items-center justify-center text-slate-400 text-xs p-3 text-center">
                  <Clock className="w-5 h-5 mb-1" />
                  Clearance photo pending municipal verification
                </div>
              )}
            </div>

            <div className="bg-slate-50 p-3.5 rounded-xl text-xs space-y-1.5 text-slate-600">
              <div className="flex justify-between">
                <span>Generalized Coordinate:</span>
                <span className="font-mono font-bold text-slate-800">
                  {(selectedIncident.generalized_latitude || selectedIncident.coarse_latitude) && (selectedIncident.generalized_longitude || selectedIncident.coarse_longitude)
                    ? `${(selectedIncident.generalized_latitude || selectedIncident.coarse_latitude).toFixed(2)}°N, ${(selectedIncident.generalized_longitude || selectedIncident.coarse_longitude).toFixed(2)}°E`
                    : 'Ward Boundary'}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Accessibility Impact:</span>
                <span className="font-bold text-blue-600">{selectedIncident.accessibility_score ?? 75}% Path Score</span>
              </div>
              <div className="flex justify-between">
                <span>Footpath Occupancy:</span>
                <span className="font-bold text-slate-800">{selectedIncident.occupancy_percentage ?? 25}% Width Blocked</span>
              </div>
              {(selectedIncident.resolution_date || selectedIncident.resolution_verified_at) && (
                <div className="flex justify-between text-emerald-700 font-semibold">
                  <span>Verification Date:</span>
                  <span>{new Date(selectedIncident.resolution_date || selectedIncident.resolution_verified_at).toLocaleDateString()}</span>
                </div>
              )}
            </div>

            <div className="text-[11px] text-slate-400 bg-blue-50 p-3 rounded-xl border border-blue-100 text-blue-800">
              <strong>Data Governance Notice:</strong> Personal identifiable information (citizen contact, license plates, face recognition) is scrubbed in compliance with urban municipal data protection protocols.
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
