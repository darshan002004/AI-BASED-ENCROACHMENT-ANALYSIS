import React, { useState, useEffect } from 'react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer
} from 'recharts';
import {
  Activity,
  Clock,
  CheckCircle2,
  Calendar,
  Download,
  Flame,
  AlertTriangle,
  TrendingUp,
  MapPin
} from 'lucide-react';
import { analyticsAPI, reportsAPI } from '../../services/api';

export default function AnalyticsPage() {
  const [dateRange, setDateRange] = useState('30 Days');
  const [topAreas, setTopAreas] = useState([]);

  const [metrics, setMetrics] = useState({
    avgAccessibility: 0,
    avgResolutionTime: '0.0 days',
    resolutionRate: '0%'
  });

  const [typesData, setTypesData] = useState([]);
  const [monthlyTrend, setMonthlyTrend] = useState([]);

  useEffect(() => {
    Promise.all([
      analyticsAPI.getTopAreas(),
      analyticsAPI.getTypes(),
      analyticsAPI.getMonthlyTrend(),
      analyticsAPI.getKPIs()
    ]).then(([areasRes, typesRes, trendRes, kpiRes]) => {
      if (areasRes.data) {
        setTopAreas(areasRes.data);
      }
      if (typesRes.data) setTypesData(typesRes.data);
      if (trendRes.data) setMonthlyTrend(trendRes.data);
      if (kpiRes.data) {
        const avgDays = kpiRes.data.avg_resolution_days !== undefined
          ? `${Number(kpiRes.data.avg_resolution_days).toFixed(1)} days`
          : '0.0 days';
        setMetrics({
          avgAccessibility: Math.round(kpiRes.data.avg_accessibility_score || 0),
          avgResolutionTime: avgDays,
          resolutionRate: `${Math.round(kpiRes.data.resolution_rate_pct || 0)}%`
        });
      }
    }).catch(console.warn);
  }, [dateRange]);

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-16">
      {/* Top Header & Range Filters */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200/80 pb-4">
        <div>
          <h1 className="text-base font-bold text-slate-900 tracking-tight">Analytics &amp; Spatial Intelligence</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Pedestrian accessibility metrics, recurring ward density hotspots, and resolution SLAs
          </p>
        </div>

        {/* Range Filters */}
        <div className="flex items-center bg-white p-1 rounded-lg border border-slate-200 text-xs font-semibold shadow-2xs">
          {['Today', '7 Days', '30 Days', '3 Months', 'Custom'].map((range) => (
            <button
              key={range}
              onClick={() => setDateRange(range)}
              className={`px-3 py-1 rounded-md transition-all ${
                dateRange === range
                  ? 'bg-slate-900 text-white shadow-2xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              {range}
            </button>
          ))}
        </div>
      </div>

      {/* Top 3 Summary Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Metric 1: Avg. Accessibility */}
        <div className="bg-white rounded-xl p-4 border border-slate-200/90 shadow-2xs flex items-center justify-between">
          <div>
            <div className="text-2xl font-bold text-slate-900 tracking-tight">{metrics.avgAccessibility}%</div>
            <div className="text-xs font-medium text-slate-700 mt-0.5">Avg. Accessibility</div>
            <div className="text-[11px] text-slate-400">Corridor Walkability Score</div>
          </div>
          <div className="w-10 h-10 rounded-lg bg-blue-50 text-blue-700 flex items-center justify-center border border-blue-100">
            <Activity className="w-5 h-5" />
          </div>
        </div>

        {/* Metric 2: Avg. Resolution */}
        <div className="bg-white rounded-xl p-4 border border-slate-200/90 shadow-2xs flex items-center justify-between">
          <div>
            <div className="text-2xl font-bold text-slate-900 tracking-tight">{metrics.avgResolutionTime}</div>
            <div className="text-xs font-medium text-slate-700 mt-0.5">Avg. Resolution SLA</div>
            <div className="text-[11px] text-slate-400">Field Officer Response Cycle</div>
          </div>
          <div className="w-10 h-10 rounded-lg bg-amber-50 text-amber-700 flex items-center justify-center border border-amber-100">
            <Clock className="w-5 h-5" />
          </div>
        </div>

        {/* Metric 3: Resolution Rate */}
        <div className="bg-white rounded-xl p-4 border border-slate-200/90 shadow-2xs flex items-center justify-between">
          <div>
            <div className="text-2xl font-bold text-slate-900 tracking-tight">{metrics.resolutionRate}</div>
            <div className="text-xs font-medium text-slate-700 mt-0.5">Resolution Rate</div>
            <div className="text-[11px] text-slate-400">Verified Cleared Corridors</div>
          </div>
          <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center border border-emerald-100">
            <CheckCircle2 className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Main Bar Chart: Top Affected Areas */}
      <div className="bg-white rounded-xl border border-slate-200/90 shadow-2xs p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h2 className="text-sm font-bold text-slate-900 tracking-tight">Top Affected Corridors &amp; Wards</h2>
            <p className="text-xs text-slate-500 mt-0.5">Encroachment concentration index by urban zone</p>
          </div>
          <span className="text-xs font-medium text-slate-500 px-2 py-0.5 bg-slate-100 rounded border border-slate-200">Incident Volume</span>
        </div>

        {/* Horizontal Bar Visual */}
        {topAreas.length > 0 ? (
          <div className="space-y-3 pt-1 max-w-4xl">
            {topAreas.map((area, idx) => {
              const maxVal = topAreas[0]?.incidents || 1;
              const pct = Math.min(100, Math.round((area.incidents / maxVal) * 100));

              return (
                <div key={idx} className="space-y-1 text-xs">
                  <div className="flex justify-between items-center">
                    <span className="font-semibold text-slate-800 text-xs">{area.area}</span>
                    <span className="font-mono font-bold text-slate-900 text-xs">{area.incidents} cases</span>
                  </div>
                  {/* Horizontal Progress Bar */}
                  <div className="h-2.5 bg-slate-100 rounded-full overflow-hidden flex">
                    <div
                      className="h-full rounded-full transition-all duration-500 bg-slate-800"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="py-10 text-center text-slate-400">
            <MapPin className="w-8 h-8 text-slate-300 mx-auto mb-2" />
            <p className="font-semibold text-slate-700 text-xs">No area statistics available yet.</p>
            <p className="mt-1 text-slate-500 text-[11px]">Top affected corridors will appear as incidents are cataloged across wards.</p>
          </div>
        )}
      </div>

      {/* Secondary Longitudinal Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Monthly Incident Progression */}
        <div className="bg-white rounded-xl border border-slate-200/90 shadow-2xs p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="text-sm font-bold text-slate-900 tracking-tight">Monthly Incident Frequency</h3>
            <span className="text-xs text-slate-500 font-medium">Timeline View</span>
          </div>

          <div className="h-56 w-full">
            {monthlyTrend.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={monthlyTrend} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <XAxis dataKey="month" stroke="#94A3B8" fontSize={11} tickLine={false} />
                  <YAxis stroke="#94A3B8" fontSize={11} tickLine={false} />
                  <Tooltip contentStyle={{ borderRadius: '8px', fontSize: '11px', border: '1px solid #E2E8F0', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }} />
                  <Line type="monotone" dataKey="incidents" stroke="#1E293B" strokeWidth={2} dot={{ r: 3 }} />
                  <Line type="monotone" dataKey="resolved" stroke="#059669" strokeWidth={2} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-slate-400 text-xs">
                <TrendingUp className="w-8 h-8 text-slate-300 mb-2" />
                <p className="font-semibold text-slate-700">Insufficient historical data for prediction.</p>
                <p className="mt-1 text-slate-500 text-[11px]">Monthly trends will plot once reports are logged across billing cycles.</p>
              </div>
            )}
          </div>
        </div>

        {/* Encroachment Categories Distribution */}
        <div className="bg-white rounded-xl border border-slate-200/90 shadow-2xs p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="text-sm font-bold text-slate-900 tracking-tight">Obstruction Categories</h3>
            <span className="text-xs text-slate-500 font-medium">Distribution %</span>
          </div>

          <div className="h-56 w-full">
            {typesData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={typesData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <XAxis dataKey="type" stroke="#94A3B8" fontSize={10} tickLine={false} />
                  <YAxis stroke="#94A3B8" fontSize={11} tickLine={false} />
                  <Tooltip contentStyle={{ borderRadius: '8px', fontSize: '11px', border: '1px solid #E2E8F0', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }} />
                  <Bar dataKey="percentage" fill="#059669" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-slate-400 text-xs">
                <Activity className="w-8 h-8 text-slate-300 mb-2" />
                <p className="font-semibold text-slate-700">No encroachment categories recorded.</p>
                <p className="mt-1 text-slate-500 text-[11px]">Category distributions will render as incidents are categorized.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
