import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Layers, ArrowRightLeft, ShieldCheck, AlertTriangle, CheckCircle2, TrendingUp, Navigation } from 'lucide-react';

const AVAILABLE_AREAS = [
  { key: 'mg road', label: 'MG Road (Shivajinagar)' },
  { key: 'indiranagar', label: 'Indiranagar (Hoysala Nagar)' },
  { key: 'koramangala', label: 'Koramangala (Ejipura)' },
  { key: 'btm layout', label: 'BTM Layout (Madivala)' },
  { key: 'jp nagar', label: 'JP Nagar (Sarakki)' },
  { key: 'hsr layout', label: 'HSR Layout' },
  { key: 'jayanagar', label: 'Jayanagar (Pattabhiram Nagar)' }
];

export default function AreaComparisonPage() {
  const [selectedAreas, setSelectedAreas] = useState(['mg road', 'indiranagar']);
  const [comparisonData, setComparisonData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchComparison();
  }, [selectedAreas]);

  const fetchComparison = async () => {
    setLoading(true);
    try {
      const areaParam = selectedAreas.join(',');
      const res = await axios.get(`/api/analytics/compare-areas?areas=${encodeURIComponent(areaParam)}`);
      setComparisonData(res.data.comparison || []);
    } catch (err) {
      console.error('Error fetching area comparison:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleArea = (key) => {
    if (selectedAreas.includes(key)) {
      if (selectedAreas.length > 2) {
        setSelectedAreas(selectedAreas.filter(k => k !== key));
      }
    } else {
      if (selectedAreas.length < 4) {
        setSelectedAreas([...selectedAreas, key]);
      }
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="p-1.5 rounded-lg bg-blue-50 text-blue-600">
              <ArrowRightLeft className="w-5 h-5" />
            </span>
            <h1 className="text-xl font-bold text-slate-900">Urban Ward & Area Comparison</h1>
          </div>
          <p className="text-sm text-slate-500">
            Side-by-side comparative analytics of pedestrian accessibility, encroachment density, and civic resolution rates.
          </p>
        </div>

        <div className="flex flex-wrap gap-1.5">
          {AVAILABLE_AREAS.map(a => {
            const isSelected = selectedAreas.includes(a.key);
            return (
              <button
                key={a.key}
                onClick={() => toggleArea(a.key)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all border ${
                  isSelected
                    ? 'bg-blue-600 text-white border-blue-600 shadow-sm'
                    : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
                }`}
              >
                {a.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Comparison Cards Grid */}
      {loading ? (
        <div className="bg-white rounded-2xl p-12 text-center text-slate-500 border border-slate-200">
          <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-3" />
          <p className="text-sm">Synthesizing ward GIS metrics...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {comparisonData.map((item, idx) => {
            const accScore = item.avg_accessibility;
            const healthColor = accScore >= 75 ? 'text-emerald-600 bg-emerald-50 border-emerald-200' : (accScore >= 50 ? 'text-amber-600 bg-amber-50 border-amber-200' : 'text-red-600 bg-red-50 border-red-200');

            return (
              <div key={idx} className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
                <div className="p-5 border-b border-slate-100 bg-gradient-to-br from-slate-50 to-white">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-semibold px-2 py-0.5 rounded-md bg-slate-200 text-slate-700">
                      Ward {idx + 1}
                    </span>
                    <span className={`text-xs font-bold px-2 py-0.5 rounded-full border ${healthColor}`}>
                      {accScore >= 75 ? 'Healthy Corridor' : (accScore >= 50 ? 'Needs Attention' : 'Critical Corridor')}
                    </span>
                  </div>
                  <h3 className="text-lg font-bold text-slate-900">{item.area_name}</h3>
                  <p className="text-xs text-slate-500">{item.ward}</p>
                </div>

                <div className="p-5 space-y-4 flex-1">
                  {/* Accessibility Meter */}
                  <div>
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="font-semibold text-slate-600">Walkway Accessibility</span>
                      <span className="font-bold text-slate-900">{item.avg_accessibility}/100</span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
                      <div
                        className={`h-full rounded-full ${
                          accScore >= 75 ? 'bg-emerald-500' : (accScore >= 50 ? 'bg-amber-500' : 'bg-red-500')
                        }`}
                        style={{ width: `${accScore}%` }}
                      />
                    </div>
                  </div>

                  {/* Occupancy Meter */}
                  <div>
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="font-semibold text-slate-600">Footpath Area Occupied</span>
                      <span className="font-bold text-slate-900">{item.avg_occupancy_pct}%</span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
                      <div
                        className="h-full bg-blue-500 rounded-full"
                        style={{ width: `${Math.min(100, item.avg_occupancy_pct)}%` }}
                      />
                    </div>
                  </div>

                  {/* Key Stats Grid */}
                  <div className="grid grid-cols-2 gap-3 pt-2">
                    <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                      <span className="text-[11px] font-medium text-slate-500 block">Total Incidents</span>
                      <span className="text-base font-bold text-slate-900">{item.total_incidents}</span>
                    </div>
                    <div className="p-3 bg-red-50/60 rounded-xl border border-red-100">
                      <span className="text-[11px] font-medium text-red-600 block">High Severity</span>
                      <span className="text-base font-bold text-red-700">{item.high_severity_count}</span>
                    </div>
                    <div className="p-3 bg-emerald-50/60 rounded-xl border border-emerald-100">
                      <span className="text-[11px] font-medium text-emerald-600 block">Resolution Rate</span>
                      <span className="text-base font-bold text-emerald-700">{item.resolution_rate_pct}%</span>
                    </div>
                    <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                      <span className="text-[11px] font-medium text-slate-500 block">Active Cases</span>
                      <span className="text-base font-bold text-slate-900">{item.active_incidents}</span>
                    </div>
                  </div>

                  {/* Primary Root Cause */}
                  <div className="pt-2 border-t border-slate-100">
                    <span className="text-xs text-slate-400 block mb-0.5">Primary Encroachment Driver</span>
                    <span className="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                      {item.primary_cause}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Comparative Data Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-5 border-b border-slate-100">
          <h2 className="text-base font-bold text-slate-900">Ward Metrics Cross-Comparison Table</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-600">
            <thead className="bg-slate-50 text-slate-700 font-semibold text-xs border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">Ward / Area</th>
                <th className="py-3 px-4">Total Cases</th>
                <th className="py-3 px-4">Active</th>
                <th className="py-3 px-4">High Severity</th>
                <th className="py-3 px-4">Avg Accessibility</th>
                <th className="py-3 px-4">Avg Occupancy</th>
                <th className="py-3 px-4">Resolution Rate</th>
                <th className="py-3 px-4">Dominant Cause</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {comparisonData.map((row, idx) => (
                <tr key={idx} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-3.5 px-4 font-bold text-slate-900">{row.area_name}</td>
                  <td className="py-3.5 px-4">{row.total_incidents}</td>
                  <td className="py-3.5 px-4 font-semibold text-slate-800">{row.active_incidents}</td>
                  <td className="py-3.5 px-4">
                    <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-red-100 text-red-700">
                      {row.high_severity_count}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 font-bold text-slate-800">{row.avg_accessibility}/100</td>
                  <td className="py-3.5 px-4">{row.avg_occupancy_pct}%</td>
                  <td className="py-3.5 px-4 font-bold text-emerald-600">{row.resolution_rate_pct}%</td>
                  <td className="py-3.5 px-4 text-xs font-medium text-slate-700">{row.primary_cause}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
