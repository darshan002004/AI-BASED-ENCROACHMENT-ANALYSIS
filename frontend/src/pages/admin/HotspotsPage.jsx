import React, { useState, useEffect, useMemo } from 'react';
import {
  Flame,
  MapPin,
  TrendingUp,
  AlertTriangle,
  ShieldCheck,
  ChevronRight,
  Filter,
  Calendar,
  Layers,
  Clock,
  CheckCircle2,
  Info,
  Compass,
  Eye
} from 'lucide-react';
import { analyticsAPI } from '../../services/api';
import MapView from '../../components/MapView';

export default function HotspotsPage({ onSelectArea }) {
  const [hotspots, setHotspots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedHotspot, setSelectedHotspot] = useState(null);

  // Feature 3: Multi-Criteria Filter States
  const [dateRange, setDateRange] = useState('All');
  const [encroachmentType, setEncroachmentType] = useState('All');
  const [severity, setSeverity] = useState('All');

  const fetchHotspots = () => {
    setLoading(true);
    const params = {
      date_range: dateRange,
      encroachment_type: encroachmentType !== 'All' ? encroachmentType : undefined,
      severity: severity !== 'All' ? severity : undefined,
    };

    analyticsAPI.getHotspots(params)
      .then((res) => {
        const data = res.data || [];
        setHotspots(data);
        if (data.length > 0 && !selectedHotspot) {
          setSelectedHotspot(data[0]);
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchHotspots();
  }, [dateRange, encroachmentType, severity]);

  // Aggregate Metrics for Top Cards
  const totalClusters = hotspots.length;
  const criticalCount = hotspots.filter(h => h.status === 'Critical Hotspot').length;
  const avgOccupancy = hotspots.length > 0
    ? (hotspots.reduce((sum, h) => sum + (h.avg_occupancy_pct || 0), 0) / hotspots.length).toFixed(1)
    : '0.0';
  const avgResolutionTime = hotspots.length > 0
    ? (hotspots.reduce((sum, h) => sum + (h.avg_resolution_time_days || 0), 0) / hotspots.length).toFixed(1)
    : '0.0';
  const totalRepeatIncidents = hotspots.reduce((sum, h) => sum + (h.repeat_incidents || 0), 0);

  // Map markers & radial circles formatted for MapView
  const mapHotspots = useMemo(() => {
    return hotspots.map((h) => ({
      key: h.area.toLowerCase(),
      area_name: h.area,
      ward: h.ward,
      incidents: h.incidents,
      risk_level: h.status === 'Critical Hotspot' ? 'HIGH' : (h.status === 'High Density' ? 'MEDIUM' : 'LOW'),
      primary_cause: h.primary_cause,
      latitude: h.latitude,
      longitude: h.longitude,
      avg_occupancy: h.avg_occupancy_pct,
      repeat_count: h.repeat_incidents
    }));
  }, [hotspots]);

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-16">
      {/* Header & Subtitle */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200/80 pb-3">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-base font-bold text-slate-900 tracking-tight">Smart Hotspot Spatial Analytics</h1>
            <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-rose-50 text-rose-700 border border-rose-200/80 flex items-center gap-1">
              <Flame className="w-3 h-3 text-rose-600" />
              Live Spatial Density
            </span>
          </div>
          <p className="text-xs text-slate-500 font-normal mt-0.5">
            Spatial clustering engine grouping repeated encroachment corridors by urban administrative ward (≤ 50m radius).
          </p>
        </div>

        {/* Data Methodology Pill */}
        <div className="flex items-center gap-2 self-start sm:self-auto">
          <span className="px-2.5 py-1 rounded-lg bg-slate-100 border border-slate-200 text-slate-600 text-[11px] font-normal flex items-center gap-1.5 shadow-2xs">
            <Info className="w-3.5 h-3.5 text-blue-600" />
            <span>Verified Incident Cluster Aggregation</span>
          </span>
        </div>
      </div>

      {/* Feature 3: Multi-Criteria Filter Bar */}
      <div className="bg-white rounded-xl p-3.5 border border-slate-200/90 shadow-2xs flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-2 text-xs font-bold text-slate-700">
          <Filter className="w-4 h-4 text-blue-600" />
          <span>Filter Clusters:</span>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Date Range Filter */}
          <div className="flex items-center gap-1.5 text-xs">
            <Calendar className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={dateRange}
              onChange={(e) => setDateRange(e.target.value)}
              className="bg-slate-50 border border-slate-200 rounded-xl px-2.5 py-1.5 font-semibold text-slate-700 focus:outline-none"
            >
              <option value="All">All Timeframes</option>
              <option value="Today">Today Only</option>
              <option value="7 Days">Last 7 Days</option>
              <option value="30 Days">Last 30 Days</option>
              <option value="3 Months">Last 3 Months</option>
            </select>
          </div>

          {/* Encroachment Type Filter */}
          <div className="flex items-center gap-1.5 text-xs">
            <Layers className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={encroachmentType}
              onChange={(e) => setEncroachmentType(e.target.value)}
              className="bg-slate-50 border border-slate-200 rounded-xl px-2.5 py-1.5 font-semibold text-slate-700 focus:outline-none"
            >
              <option value="All">All Encroachment Types</option>
              <option value="Street Vendor">Street Vendor</option>
              <option value="Vehicle">Vehicle on Footpath</option>
              <option value="Construction Material">Construction Material</option>
              <option value="Shop Extension">Shop Counter Extension</option>
              <option value="Signboard">Commercial Signboard</option>
            </select>
          </div>

          {/* Severity Filter */}
          <div className="flex items-center gap-1.5 text-xs">
            <AlertTriangle className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={severity}
              onChange={(e) => setSeverity(e.target.value)}
              className="bg-slate-50 border border-slate-200 rounded-xl px-2.5 py-1.5 font-semibold text-slate-700 focus:outline-none"
            >
              <option value="All">All Severities</option>
              <option value="High">High Severity Only</option>
              <option value="Medium">Medium Severity</option>
              <option value="Low">Low Severity</option>
            </select>
          </div>

          {(dateRange !== 'All' || encroachmentType !== 'All' || severity !== 'All') && (
            <button
              onClick={() => {
                setDateRange('All');
                setEncroachmentType('All');
                setSeverity('All');
              }}
              className="text-xs text-blue-600 font-bold hover:underline"
            >
              Reset Filters
            </button>
          )}
        </div>
      </div>

      {/* Aggregate Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-xs">
          <span className="text-slate-400 text-xs font-semibold block">Tracked Hotspots</span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-2xl font-black text-slate-900">{totalClusters}</span>
            <span className="text-xs font-bold text-red-600">({criticalCount} Critical)</span>
          </div>
          <span className="text-[11px] text-slate-400 mt-0.5 block">50m corridor spatial clusters</span>
        </div>

        <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-xs">
          <span className="text-slate-400 text-xs font-semibold block">Repeat Obstructions</span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-2xl font-black text-amber-600">{totalRepeatIncidents}</span>
            <span className="text-xs font-bold text-slate-500">Recurrences</span>
          </div>
          <span className="text-[11px] text-slate-400 mt-0.5 block">Multiple citizen reports at same GPS</span>
        </div>

        <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-xs">
          <span className="text-slate-400 text-xs font-semibold block">Avg Corridor Occupancy</span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-2xl font-black text-blue-600">{avgOccupancy}%</span>
            <span className="text-xs font-bold text-slate-500">Corridor blocked</span>
          </div>
          <span className="text-[11px] text-slate-400 mt-0.5 block">YOLOv5n + ROI spatial measurement</span>
        </div>

        <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-xs">
          <span className="text-slate-400 text-xs font-semibold block">Avg Resolution Time</span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-2xl font-black text-emerald-600">{avgResolutionTime} Days</span>
            <span className="text-xs font-bold text-emerald-700">Municipal SLA</span>
          </div>
          <span className="text-[11px] text-slate-400 mt-0.5 block">Average officer clearance cycle</span>
        </div>
      </div>

      {/* Map/Heatmap Section + Selected Hotspot Detail */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
        {/* Interactive Map View */}
        <div className="lg:col-span-8 bg-white rounded-2xl p-4 border border-slate-200 shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Compass className="w-4 h-4 text-blue-600" />
              <h2 className="text-sm font-bold text-slate-900">Spatial Hotspot Heatmap &amp; Corridor Map</h2>
            </div>
            <span className="text-[11px] text-slate-400">Click a zone to focus</span>
          </div>

          <div className="h-[420px] rounded-xl overflow-hidden border border-slate-200">
            <MapView
              hotspots={mapHotspots}
              layers={{ incidents: false, hotspots: true, areaHealth: false }}
              center={[12.9550, 77.6100]}
              zoom={12}
              onSelectArea={(spot) => {
                const found = hotspots.find(h => h.area.toLowerCase() === spot.key?.toLowerCase());
                if (found) setSelectedHotspot(found);
              }}
            />
          </div>
        </div>

        {/* Selected Hotspot Intelligence Dossier */}
        <div className="lg:col-span-4 bg-white rounded-2xl p-5 border border-slate-200 shadow-xs space-y-4 flex flex-col justify-between">
          <div className="space-y-3">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Inspecting Cluster</span>
                <h3 className="text-base font-extrabold text-slate-900">
                  {selectedHotspot?.area || 'Select a Hotspot'}
                </h3>
                <span className="text-xs text-slate-400">{selectedHotspot?.ward}</span>
              </div>
              {selectedHotspot && (
                <span className={`px-2.5 py-1 rounded-full text-[11px] font-black ${
                  selectedHotspot.status === 'Critical Hotspot' ? 'bg-red-100 text-red-700' :
                  (selectedHotspot.status === 'High Density' ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700')
                }`}>
                  {selectedHotspot.status}
                </span>
              )}
            </div>

            {selectedHotspot ? (
              <div className="space-y-3 text-xs">
                <div className="p-3 bg-slate-50 rounded-xl space-y-1.5 border border-slate-100">
                  <div className="flex justify-between">
                    <span className="text-slate-500">GPS Coordinates:</span>
                    <strong className="font-mono text-slate-800">
                      {selectedHotspot.latitude?.toFixed(4)}, {selectedHotspot.longitude?.toFixed(4)}
                    </strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Total Encroachment Cases:</span>
                    <strong className="text-slate-900">{selectedHotspot.incidents}</strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Active Unresolved:</span>
                    <strong className="text-red-600">{selectedHotspot.active} active</strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Repeat Incidents:</span>
                    <strong className="text-amber-600">{selectedHotspot.repeat_incidents} recurrences</strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Avg Footpath Occupancy:</span>
                    <strong className="text-blue-600">{selectedHotspot.avg_occupancy_pct}%</strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Accessibility Score:</span>
                    <strong className="text-emerald-600">{selectedHotspot.avg_accessibility_score}/100</strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Resolution Rate:</span>
                    <strong className="text-emerald-700">{selectedHotspot.resolution_rate}</strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Avg Clearance SLA:</span>
                    <strong className="text-slate-800">{selectedHotspot.avg_resolution_time_days} days</strong>
                  </div>
                </div>

                <div className="p-3 bg-blue-50/70 border border-blue-200 rounded-xl space-y-1">
                  <span className="text-[10px] font-bold text-blue-700 block uppercase">Dominant Obstruction Factor</span>
                  <span className="text-xs font-bold text-blue-950 block">{selectedHotspot.primary_cause}</span>
                  <span className="text-[11px] text-blue-800/80 block">
                    Highest prevalence in this 50m sector. Field officers deployed for targeted enforcement.
                  </span>
                </div>
              </div>
            ) : (
              <div className="p-8 text-center text-slate-400 text-xs">
                Select a hotspot from the map or table below.
              </div>
            )}
          </div>

          <div className="pt-2 border-t border-slate-100">
            <span className="text-[10px] text-slate-400 italic block leading-relaxed">
              * Aggregation Method: {selectedHotspot?.aggregation_method || '50m spatial cluster grouping by urban administrative ward'}
            </span>
          </div>
        </div>
      </div>

      {/* Hotspots Ranking Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-900">
            Ranked Encroachment Corridors ({hotspots.length} Clusters)
          </h2>
          <span className="text-xs text-slate-400 font-medium">
            Sorted by Total Incident Density
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-100">
                <th className="py-3 px-4">Rank</th>
                <th className="py-3 px-4">Location &amp; Ward</th>
                <th className="py-3 px-4">Coordinates</th>
                <th className="py-3 px-4">Total / Active</th>
                <th className="py-3 px-4">Repeat Incidents</th>
                <th className="py-3 px-4">Corridor Occupancy</th>
                <th className="py-3 px-4">Accessibility</th>
                <th className="py-3 px-4">Resolution Rate</th>
                <th className="py-3 px-4">Primary Factor</th>
                <th className="py-3 px-4">Classification</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan="10" className="p-8 text-center text-slate-400">
                    Loading hotspot clusters...
                  </td>
                </tr>
              ) : hotspots.length === 0 ? (
                <tr>
                  <td colSpan="10" className="p-8 text-center text-slate-400">
                    No hotspots match the selected filter criteria.
                  </td>
                </tr>
              ) : (
                hotspots.map((h, idx) => {
                  const rank = idx + 1;
                  const isSelected = selectedHotspot?.area === h.area;
                  return (
                    <tr
                      key={h.area || idx}
                      onClick={() => setSelectedHotspot(h)}
                      className={`cursor-pointer transition-colors ${
                        isSelected ? 'bg-blue-50/70 font-semibold' : 'hover:bg-slate-50/80'
                      }`}
                    >
                      <td className="py-3.5 px-4 font-bold">
                        <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                          rank === 1 ? 'bg-red-500 text-white' : (rank === 2 ? 'bg-orange-500 text-white' : (rank === 3 ? 'bg-amber-500 text-white' : 'bg-slate-200 text-slate-700'))
                        }`}>
                          {rank}
                        </span>
                      </td>
                      <td className="py-3.5 px-4">
                        <div className="font-bold text-slate-900">{h.area}</div>
                        <div className="text-[11px] text-slate-400">{h.ward}</div>
                      </td>
                      <td className="py-3.5 px-4 font-mono text-[11px] text-slate-500">
                        {h.latitude?.toFixed(4)}, {h.longitude?.toFixed(4)}
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="font-extrabold text-slate-900 block">{h.incidents} cases</span>
                        <span className="text-[10px] text-amber-600 block">{h.active} active</span>
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="font-bold text-purple-700">{h.repeat_incidents} recurrences</span>
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="font-bold text-blue-600">{h.avg_occupancy_pct}%</span>
                        <span className="text-[10px] text-slate-400 block">corridor blocked</span>
                      </td>
                      <td className="py-3.5 px-4 font-semibold text-slate-700">
                        {h.avg_accessibility_score}/100
                      </td>
                      <td className="py-3.5 px-4 font-semibold text-emerald-600">
                        {h.resolution_rate}
                        <span className="text-[10px] text-slate-400 block">SLA: {h.avg_resolution_time_days}d</span>
                      </td>
                      <td className="py-3.5 px-4 font-medium text-slate-700">
                        {h.primary_cause}
                      </td>
                      <td className="py-3.5 px-4">
                        <span className={`px-2.5 py-1 rounded-full text-[11px] font-bold ${
                          h.status === 'Critical Hotspot' ? 'bg-red-100 text-red-700 border border-red-200' :
                          (h.status === 'High Density' ? 'bg-amber-100 text-amber-700 border border-amber-200' : 'bg-slate-100 text-slate-700')
                        }`}>
                          {h.status}
                        </span>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
