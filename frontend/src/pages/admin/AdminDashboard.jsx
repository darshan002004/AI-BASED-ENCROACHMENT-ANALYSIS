import React, { useState, useEffect } from 'react';
import {
  FileText,
  CheckCircle2,
  Clock,
  AlertTriangle,
  MapPin,
  ChevronRight,
  Activity,
  Flame,
  Percent,
  Video,
  Eye,
  Layers,
  ArrowUpRight,
  ShieldCheck,
  RefreshCw
} from 'lucide-react';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip
} from 'recharts';
import MapView from '../../components/MapView';
import { StatusBadge, SeverityBadge } from '../../components/StatusBadge';
import { analyticsAPI, incidentsAPI } from '../../services/api';
import { useLanguage } from '../../context/LanguageContext';

export default function AdminDashboard({ onNavigate, onSelectIncident }) {
  const { t } = useLanguage();
  const [kpis, setKpis] = useState({
    total_incidents: '0',
    verified: '0',
    pending: '0',
    high_severity: '0',
    avg_accessibility_score: '0%',
    avg_occupancy: '0%',
    high_risk_incidents: '0',
    persistent_obstructions: '0',
    needs_human_review: '0',
  });

  const [typesData, setTypesData] = useState([]);
  const [trendData, setTrendData] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [topHotspots, setTopHotspots] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    const token = localStorage.getItem('encrowatch_token');
    if (!token) {
      setLoading(false);
      return;
    }
    try {
      setLoading(true);
      const [kpiRes, typesRes, trendRes, incRes, hotRes] = await Promise.all([
        analyticsAPI.getKPIs(),
        analyticsAPI.getTypes(),
        analyticsAPI.getMonthlyTrend(),
        incidentsAPI.list({ limit: 10 }),
        analyticsAPI.getHotspots()
      ]);

      if (kpiRes.data) {
        setKpis({
          total_incidents: (kpiRes.data.total_incidents ?? 0).toLocaleString(),
          verified: (kpiRes.data.verified ?? 0).toLocaleString(),
          pending: (kpiRes.data.pending ?? 0).toLocaleString(),
          high_severity: (kpiRes.data.high_severity ?? 0).toLocaleString(),
          avg_accessibility_score: `${kpiRes.data.avg_accessibility_score ?? 0}%`,
          avg_occupancy: `${kpiRes.data.avg_occupancy ?? 0}%`,
          high_risk_incidents: (kpiRes.data.high_risk_incidents ?? 0).toLocaleString(),
          persistent_obstructions: (kpiRes.data.persistent_obstructions ?? 0).toLocaleString(),
          needs_human_review: (kpiRes.data.needs_human_review ?? 0).toLocaleString(),
        });
      }

      if (typesRes.data) {
        const colorMap = {
          'Vehicles': '#2563EB',
          'Street Vendors': '#059669',
          'Shop Extensions': '#D97706',
          'Construction': '#DC2626',
          'Garbage & Debris': '#7C3AED',
          'Garbage': '#7C3AED',
          'Street Objects': '#0891B2',
          'Others': '#64748B'
        };
        const formatted = (typesRes.data || []).map((item) => ({
          name: item.type || item.name,
          value: item.percentage || item.value,
          count: item.count || item.value,
          color: colorMap[item.type || item.name] || item.color || '#2563EB'
        }));
        setTypesData(formatted);
      }

      if (trendRes.data) {
        setTrendData(trendRes.data || []);
      }

      if (incRes.data) {
        setIncidents(incRes.data || []);
      }

      if (hotRes.data) {
        setTopHotspots(hotRes.data || []);
      }
    } catch (err) {
      console.warn('Dashboard data fetch note:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Page Title & Operational Status Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-[#172033] tracking-tight">Municipal Operations Dashboard</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Real-time urban encroachment telemetry, spatial walkability metrics, and field dispatch tracking
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <button
            onClick={fetchData}
            disabled={loading}
            className="p-1.5 border border-slate-200 rounded-lg hover:bg-white text-slate-600 transition-colors bg-white shadow-2xs"
            title="Refresh Live Telemetry"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <div className="flex items-center gap-2 px-3 py-1 bg-white border border-slate-200 rounded-lg shadow-2xs text-xs font-semibold text-slate-700">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>GIS Feed Active</span>
          </div>
        </div>
      </div>

      {/* Primary KPI Cards (Real Backend Metrics) */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Incidents */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs flex items-center justify-between">
          <div>
            <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">{t('totalReports')}</div>
            <div className="text-2xl font-extrabold text-[#172033] mt-1">{kpis.total_incidents}</div>
            <div className="text-[11px] text-slate-400 mt-0.5">Cataloged cases</div>
          </div>
          <div className="w-10 h-10 rounded-lg bg-slate-100 text-slate-700 flex items-center justify-center">
            <FileText className="w-5 h-5" />
          </div>
        </div>

        {/* Verified Clearances */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs flex items-center justify-between">
          <div>
            <div className="text-[11px] font-bold text-emerald-800 uppercase tracking-wider">{t('verified')}</div>
            <div className="text-2xl font-extrabold text-[#059669] mt-1">{kpis.verified}</div>
            <div className="text-[11px] text-emerald-700 mt-0.5">Physical clearances</div>
          </div>
          <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center border border-emerald-100">
            <CheckCircle2 className="w-5 h-5" />
          </div>
        </div>

        {/* Pending Investigation */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs flex items-center justify-between">
          <div>
            <div className="text-[11px] font-bold text-amber-800 uppercase tracking-wider">{t('pending')}</div>
            <div className="text-2xl font-extrabold text-[#D97706] mt-1">{kpis.pending}</div>
            <div className="text-[11px] text-amber-700 mt-0.5">In field review queue</div>
          </div>
          <div className="w-10 h-10 rounded-lg bg-amber-50 text-amber-700 flex items-center justify-center border border-amber-100">
            <Clock className="w-5 h-5" />
          </div>
        </div>

        {/* High Severity Alerts */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs flex items-center justify-between">
          <div>
            <div className="text-[11px] font-bold text-red-800 uppercase tracking-wider">{t('highSeverity')}</div>
            <div className="text-2xl font-extrabold text-[#DC2626] mt-1">{kpis.high_severity}</div>
            <div className="text-[11px] text-red-700 mt-0.5">Critical obstruction risk</div>
          </div>
          <div className="w-10 h-10 rounded-lg bg-red-50 text-red-700 flex items-center justify-center border border-red-100">
            <AlertTriangle className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Secondary Municipal Intelligence Row (Pedestrian Walkability & Risk) */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-2xs space-y-3">
        <div className="flex items-center justify-between pb-2 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-blue-600" />
            <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              Urban Walkability &amp; Risk Intelligence (IRC:SP:102 Standards)
            </h2>
          </div>
          <span className="text-[11px] text-slate-400 font-medium">Empirical Spatial Telemetry</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <div className="p-3 bg-[#F5F7FA] rounded-lg border border-slate-200/60">
            <div className="text-slate-500 font-medium">Avg. Accessibility Index</div>
            <div className="text-lg font-bold text-blue-700 mt-0.5">{kpis.avg_accessibility_score}</div>
            <div className="text-[10px] text-slate-400">Pedestrian corridor clear rating</div>
          </div>

          <div className="p-3 bg-[#F5F7FA] rounded-lg border border-slate-200/60">
            <div className="text-slate-500 font-medium">Avg. Footpath Occupancy</div>
            <div className="text-lg font-bold text-slate-800 mt-0.5">{kpis.avg_occupancy}</div>
            <div className="text-[10px] text-slate-400">Corridor width obstructed</div>
          </div>

          <div className="p-3 bg-[#F5F7FA] rounded-lg border border-slate-200/60">
            <div className="text-slate-500 font-medium">High Risk Corridors</div>
            <div className="text-lg font-bold text-red-700 mt-0.5">{kpis.high_risk_incidents}</div>
            <div className="text-[10px] text-slate-400">Bottlenecks &ge; 70/100</div>
          </div>

          <div className="p-3 bg-[#F5F7FA] rounded-lg border border-slate-200/60">
            <div className="text-slate-500 font-medium">Pending Human Review</div>
            <div className="text-lg font-bold text-amber-700 mt-0.5">{kpis.needs_human_review}</div>
            <div className="text-[10px] text-slate-400">HITL validation queue</div>
          </div>
        </div>
      </div>

      {/* Main Charts Row: Breakdown by Type & Clearance Trend */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-stretch">
        {/* Left: Donut Chart */}
        <div className="lg:col-span-6 bg-white rounded-xl border border-slate-200 shadow-2xs p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-100">
            <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wider">Incidents by Category</h2>
            <span className="text-[11px] text-slate-400 font-medium">Active Distribution</span>
          </div>

          {typesData.length === 0 ? (
            <div className="h-44 flex flex-col items-center justify-center text-center text-slate-400 text-xs">
              No categories cataloged yet.
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-12 gap-3 items-center">
              <div className="sm:col-span-6 relative h-44 flex items-center justify-center">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={typesData}
                      cx="50%"
                      cy="50%"
                      innerRadius={46}
                      outerRadius={70}
                      paddingAngle={2}
                      dataKey="value"
                    >
                      {typesData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(val, name, item) => [`${val}% (${item.payload.count || ''})`, name]}
                      contentStyle={{ borderRadius: '8px', fontSize: '11px', border: '1px solid #E2E8F0', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}
                    />
                  </PieChart>
                </ResponsiveContainer>
                <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                  <span className="text-lg font-bold text-slate-900">{kpis.total_incidents}</span>
                  <span className="text-[9px] text-slate-400 font-bold uppercase tracking-wider">Total</span>
                </div>
              </div>

              <div className="sm:col-span-6 space-y-1.5 text-xs">
                {typesData.map((t, idx) => (
                  <div key={idx} className="flex items-center justify-between">
                    <div className="flex items-center gap-2 min-w-0">
                      <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: t.color }} />
                      <span className="font-medium text-slate-700 truncate">{t.name}</span>
                    </div>
                    <span className="font-semibold text-slate-900 text-xs">{t.value}%</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right: Monthly Trend Line Chart */}
        <div className="lg:col-span-6 bg-white rounded-xl border border-slate-200 shadow-2xs p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-100">
            <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wider">Monthly Clearance Volume</h2>
            <span className="text-[11px] text-slate-400 font-medium">Historical Resolution Trend</span>
          </div>

          <div className="h-44 w-full">
            {trendData.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center text-slate-400 text-xs">
                Historical monthly data will chart automatically as incidents resolve.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trendData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <XAxis dataKey="month" stroke="#94A3B8" fontSize={10} tickLine={false} />
                  <YAxis stroke="#94A3B8" fontSize={10} tickLine={false} />
                  <Tooltip
                    formatter={(val) => [`${val} Cases`, 'Cleared']}
                    contentStyle={{ borderRadius: '8px', fontSize: '11px', border: '1px solid #E2E8F0', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}
                  />
                  <Line
                    type="monotone"
                    dataKey="incidents"
                    stroke="#059669"
                    strokeWidth={2}
                    dot={{ r: 3, fill: '#059669' }}
                    activeDot={{ r: 5 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>

      {/* GIS Spatial Overview and Recent Cases Table */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-stretch">
        {/* Left: Map Preview */}
        <div className="lg:col-span-6 bg-white rounded-xl border border-slate-200 shadow-2xs p-5 flex flex-col">
          <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <MapPin className="w-4 h-4 text-blue-600" />
              <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wider">Spatial Encroachment Map</h2>
            </div>
            <button
              onClick={() => onNavigate('map')}
              className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1"
            >
              <span>Full Screen GIS</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="h-64 rounded-lg overflow-hidden border border-slate-200 bg-slate-100 relative">
            <MapView
              incidents={incidents}
              zoom={12}
              onSelectIncident={onSelectIncident}
            />
          </div>
        </div>

        {/* Right: Recent Incidents List */}
        <div className="lg:col-span-6 bg-white rounded-xl border border-slate-200 shadow-2xs p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-100">
            <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wider">Recent Case Submissions</h2>
            <button
              onClick={() => onNavigate('incidents')}
              className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1"
            >
              <span>Directory</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="divide-y divide-slate-100 flex-1 overflow-y-auto max-h-64 pr-1">
            {incidents.length > 0 ? (
              incidents.slice(0, 5).map((inc) => (
                <div
                  key={inc.id || inc._id}
                  onClick={() => onSelectIncident && onSelectIncident(inc)}
                  className="py-2.5 flex items-center justify-between gap-3 hover:bg-slate-50 p-2 rounded-lg transition-colors cursor-pointer group text-xs"
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <img
                      src={inc.image_url || '/uploads/original/clear_street.jpg'}
                      alt=""
                      onError={(e) => {
                        e.currentTarget.onerror = null;
                        e.currentTarget.src = '/uploads/original/clear_street.jpg';
                      }}
                      className="w-9 h-9 rounded-md object-cover border border-slate-200 shrink-0"
                    />
                    <div className="min-w-0">
                      <div className="font-semibold text-slate-900 truncate group-hover:text-blue-600">
                        {inc.location_name || inc.title || 'Corridor Location'}
                      </div>
                      <div className="text-[11px] text-slate-400 font-mono truncate">
                        {inc.incident_number} &bull; {inc.primary_encroachment_type || 'Obstruction'}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-1.5 shrink-0">
                    <SeverityBadge severity={inc.severity} />
                    <StatusBadge status={inc.status} />
                  </div>
                </div>
              ))
            ) : (
              <div className="h-40 flex flex-col items-center justify-center text-center text-slate-400 text-xs">
                No recent incidents logged.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
