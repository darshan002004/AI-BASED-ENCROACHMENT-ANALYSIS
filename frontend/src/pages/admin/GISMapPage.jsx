import React, { useState, useEffect } from 'react';
import {
  Filter,
  Search,
  MapPin,
  Eye,
  ExternalLink,
  Layers,
  Flame,
  Activity,
  CheckCircle2,
  AlertTriangle,
  X,
  ArrowRight,
  ShieldCheck,
  Clock,
  Compass,
  Info,
  RefreshCw,
  AlertOctagon
} from 'lucide-react';
import MapView from '../../components/MapView';
import { incidentsAPI, analyticsAPI } from '../../services/api';
import { useLanguage } from '../../context/LanguageContext';

const isValidCoord = (lat, lng) => {
  if (lat === null || lat === undefined || lng === null || lng === undefined) return false;
  const nLat = Number(lat);
  const nLng = Number(lng);
  if (isNaN(nLat) || isNaN(nLng)) return false;
  if (nLat < -90 || nLat > 90 || nLng < -180 || nLng > 180) return false;
  if (nLat === 0 && nLng === 0) return false;
  return true;
};

const matchesTime = (dateStr, filter) => {
  if (filter === 'All' || !dateStr) return true;
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return true;
    const now = new Date();
    const diffMs = now.getTime() - d.getTime();
    const diffHours = diffMs / (1000 * 60 * 60);
    if (filter === '24h') return diffHours <= 24;
    if (filter === '7d') return diffHours <= 24 * 7;
    if (filter === '30d') return diffHours <= 24 * 30;
  } catch (e) {
    return true;
  }
  return true;
};

export default function GISMapPage({ onSelectIncident, onNavigateToAreaComparison }) {
  const { t } = useLanguage();
  const [incidents, setIncidents] = useState([]);
  const [hotspots, setHotspots] = useState([]);
  const [areaHealth, setAreaHealth] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);

  // Feature 3: Toggleable Layers
  const [layers, setLayers] = useState({
    incidents: true,
    severity: true,
    hotspots: true,
    accessibility: true,
    assignments: true,
    areaHealth: true
  });

  // Feature 3: Multi-Filters including Time-based filters
  const [timeFilter, setTimeFilter] = useState('All'); // 'All' | '24h' | '7d' | '30d'
  const [severityFilter, setSeverityFilter] = useState('All');
  const [statusFilter, setStatusFilter] = useState('All');
  const [typeFilter, setTypeFilter] = useState('All');
  const [areaFilter, setAreaFilter] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');

  // UI Drawer states
  const [selectedArea, setSelectedArea] = useState(null);
  const [showLegend, setShowLegend] = useState(false);
  const [showUnmappedDrawer, setShowUnmappedDrawer] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const [incRes, hotRes, healthRes] = await Promise.allSettled([
        incidentsAPI.list({ limit: 200 }),
        analyticsAPI.getHotspots(),
        analyticsAPI.getLocationHealth()
      ]);

      if (incRes.status === 'fulfilled') {
        setIncidents(incRes.value.data || []);
      }
      if (hotRes.status === 'fulfilled') {
        setHotspots(hotRes.value.data || []);
      }
      if (healthRes.status === 'fulfilled') {
        setAreaHealth(healthRes.value.data || []);
      }
    } catch (err) {
      console.error('Failed to load GIS map data:', err);
      setLoadError('Failed to load map data. Please verify network connectivity.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Filter incidents locally based on active filters
  const filteredIncidents = incidents.filter((inc) => {
    // Time filter
    if (!matchesTime(inc.date_reported || inc.created_at, timeFilter)) {
      return false;
    }
    // Severity filter
    if (severityFilter !== 'All' && (inc.severity || '').toLowerCase() !== severityFilter.toLowerCase()) {
      return false;
    }
    // Status filter
    if (statusFilter !== 'All' && (inc.status || '').toLowerCase() !== statusFilter.toLowerCase()) {
      return false;
    }
    // Type filter
    if (typeFilter !== 'All') {
      const typeStr = (inc.primary_encroachment_type || '').toLowerCase();
      if (!typeStr.includes(typeFilter.toLowerCase())) return false;
    }
    // Area filter
    if (areaFilter !== 'All') {
      const locStr = (inc.location_name || '').toLowerCase();
      if (!locStr.includes(areaFilter.toLowerCase())) return false;
    }
    // Search query
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const match = (inc.location_name || '').toLowerCase().includes(q) ||
                    (inc.primary_encroachment_type || '').toLowerCase().includes(q) ||
                    (inc.title || '').toLowerCase().includes(q) ||
                    (inc.incident_number || '').toLowerCase().includes(q);
      if (!match) return false;
    }
    return true;
  });

  // Split into mapped and unmapped
  const mappedIncidents = filteredIncidents.filter(inc => isValidCoord(inc.latitude, inc.longitude));
  const unmappedIncidents = filteredIncidents.filter(inc => !isValidCoord(inc.latitude, inc.longitude));

  const toggleLayer = (layerKey) => {
    setLayers(prev => ({ ...prev, [layerKey]: !prev[layerKey] }));
  };

  const handleResetFilters = () => {
    setTimeFilter('All');
    setSeverityFilter('All');
    setStatusFilter('All');
    setTypeFilter('All');
    setAreaFilter('All');
    setSearchQuery('');
  };

  return (
    <div className="space-y-4 max-w-7xl mx-auto pb-12">
      {/* Top Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200/80 pb-3">
        <div>
          <h1 className="text-base font-bold text-slate-900 tracking-tight">{t('interactiveMap')}</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            {t('mapSubtitle')}
          </p>
        </div>

        {/* Top Right Controls: Search Box & Legend Toggle */}
        <div className="flex items-center gap-2 self-start sm:self-auto">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder={t('searchPlaceholder')}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-white border border-slate-200 text-xs pl-8 pr-3 py-1.5 rounded-lg text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 shadow-2xs w-48 sm:w-56"
            />
          </div>

          <button
            onClick={() => setShowLegend(!showLegend)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-colors flex items-center gap-1.5 ${
              showLegend
                ? 'bg-slate-900 text-white border-slate-900 shadow-2xs'
                : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
            }`}
          >
            <Info className="w-3.5 h-3.5" />
            <span>{t('mapLegend')}</span>
          </button>
        </div>
      </div>

      {/* Control Bar: Layer Toggles & Multi-Filters */}
      <div className="bg-white rounded-xl p-3.5 border border-slate-200/90 shadow-2xs space-y-3">
        {/* Row 1: Layer Toggles */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1 mr-1">
              <Layers className="w-3.5 h-3.5" />
              Layers:
            </span>

            {/* 1. Incidents */}
            <button
              onClick={() => toggleLayer('incidents')}
              className={`px-3 py-1 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
                layers.incidents
                  ? 'bg-blue-600 text-white shadow-xs'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              <span>{t('layerIncidents')}</span>
              <span className="text-[10px] opacity-80">({mappedIncidents.length})</span>
            </button>

            {/* 2. Severity & Risk */}
            <button
              onClick={() => toggleLayer('severity')}
              className={`px-3 py-1 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
                layers.severity
                  ? 'bg-red-600 text-white shadow-xs'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              <AlertTriangle className="w-3 h-3" />
              <span>{t('layerSeverity')}</span>
            </button>

            {/* 3. Hotspots */}
            <button
              onClick={() => toggleLayer('hotspots')}
              className={`px-3 py-1 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
                layers.hotspots
                  ? 'bg-amber-500 text-white shadow-xs'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              <Flame className="w-3 h-3" />
              <span>{t('layerHotspots')}</span>
            </button>

            {/* 4. Accessibility */}
            <button
              onClick={() => toggleLayer('accessibility')}
              className={`px-3 py-1 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
                layers.accessibility
                  ? 'bg-emerald-600 text-white shadow-xs'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              <Compass className="w-3 h-3" />
              <span>{t('layerAccessibility')}</span>
            </button>

            {/* 5. Officer Assignments */}
            <button
              onClick={() => toggleLayer('assignments')}
              className={`px-3 py-1 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
                layers.assignments
                  ? 'bg-purple-600 text-white shadow-xs'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              <ShieldCheck className="w-3 h-3" />
              <span>{t('layerAssignments')}</span>
            </button>
          </div>

          {/* Quick Stats Pill */}
          <div className="text-[11px] text-slate-500 font-semibold flex items-center gap-2">
            <span>Mapped: <strong>{mappedIncidents.length}</strong></span>
            {unmappedIncidents.length > 0 && (
              <button
                onClick={() => setShowUnmappedDrawer(true)}
                className="text-amber-700 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-lg font-bold hover:bg-amber-100 transition-colors"
              >
                {unmappedIncidents.length} Unmapped (No GPS)
              </button>
            )}
          </div>
        </div>

        {/* Row 2: Filters */}
        <div className="flex flex-wrap items-center gap-2.5 pt-2 border-t border-slate-100 text-xs">
          <span className="font-bold text-slate-600 text-xs flex items-center gap-1">
            <Filter className="w-3 h-3" />
            Filters:
          </span>

          {/* Timeframe Filter (Feature 3) */}
          <select
            value={timeFilter}
            onChange={(e) => setTimeFilter(e.target.value)}
            className="bg-slate-50 border border-slate-200 px-2.5 py-1 rounded-lg font-bold text-slate-700 focus:outline-none cursor-pointer"
          >
            <option value="All">{t('allTime')}</option>
            <option value="24h">{t('last24h')}</option>
            <option value="7d">{t('last7d')}</option>
            <option value="30d">{t('last30d')}</option>
          </select>

          {/* Severity Filter */}
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="bg-slate-50 border border-slate-200 px-2.5 py-1 rounded-lg font-bold text-slate-700 focus:outline-none cursor-pointer"
          >
            <option value="All">All Severities</option>
            <option value="High">{t('highSeverity')}</option>
            <option value="Medium">{t('mediumSeverity')}</option>
            <option value="Low">{t('lowSeverity')}</option>
          </select>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-50 border border-slate-200 px-2.5 py-1 rounded-lg font-bold text-slate-700 focus:outline-none cursor-pointer"
          >
            <option value="All">All Statuses</option>
            <option value="Pending">{t('pending')}</option>
            <option value="Verified">{t('verified')}</option>
            <option value="In Progress">{t('inProgress')}</option>
            <option value="Resolved">{t('resolved')}</option>
          </select>

          {/* Category Filter */}
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="bg-slate-50 border border-slate-200 px-2.5 py-1 rounded-lg font-bold text-slate-700 focus:outline-none cursor-pointer"
          >
            <option value="All">All Categories</option>
            <option value="Vendor">Street Vendors</option>
            <option value="Vehicle">Vehicles</option>
            <option value="Construction">Construction</option>
            <option value="Shop">Shop Extensions</option>
            <option value="Debris">Garbage &amp; Debris</option>
          </select>

          {/* Ward / Area Filter */}
          <select
            value={areaFilter}
            onChange={(e) => setAreaFilter(e.target.value)}
            className="bg-slate-50 border border-slate-200 px-2.5 py-1 rounded-lg font-bold text-slate-700 focus:outline-none cursor-pointer"
          >
            <option value="All">All Wards / Areas</option>
            <option value="MG Road">MG Road (Ward 112)</option>
            <option value="Indiranagar">Indiranagar (Ward 80)</option>
            <option value="BTM Layout">BTM Layout (Ward 176)</option>
            <option value="Koramangala">Koramangala (Ward 148)</option>
            <option value="JP Nagar">JP Nagar (Ward 178)</option>
            <option value="HSR Layout">HSR Layout (Ward 174)</option>
            <option value="Jayanagar">Jayanagar (Ward 168)</option>
          </select>

          {(timeFilter !== 'All' || severityFilter !== 'All' || statusFilter !== 'All' || typeFilter !== 'All' || areaFilter !== 'All' || searchQuery) && (
            <button
              onClick={handleResetFilters}
              className="text-blue-600 font-bold hover:underline flex items-center gap-1 ml-auto"
            >
              <X className="w-3.5 h-3.5" />
              <span>{t('clearFilters')}</span>
            </button>
          )}
        </div>
      </div>

      {/* Interactive Legend Box (Collapsible) */}
      {showLegend && (
        <div className="bg-white rounded-2xl p-4 border border-blue-200 shadow-sm space-y-3 animate-fade-in text-xs">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <span className="font-bold text-slate-800 flex items-center gap-1.5">
              <Compass className="w-4 h-4 text-blue-600" />
              <span>{t('mapLegend')}</span>
            </span>
            <button onClick={() => setShowLegend(false)} className="text-slate-400 hover:text-slate-700">
              <X className="w-4 h-4" />
            </button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
            <div className="space-y-1">
              <span className="font-bold text-slate-700 block">Incident Severity Pins:</span>
              <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-red-500" /> High Severity (Immediate Hazard)</div>
              <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-amber-500" /> Medium Severity (Partial Obstruction)</div>
              <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> Low Severity (Minor Obstacle)</div>
            </div>
            <div className="space-y-1">
              <span className="font-bold text-slate-700 block">Accessibility Zones:</span>
              <div className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full border border-emerald-500 bg-emerald-500/20" /> Good (Score &ge; 80)</div>
              <div className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full border border-amber-500 bg-amber-500/20" /> Moderately Affected (60–79)</div>
              <div className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full border border-red-500 bg-red-500/20" /> Severely Blocked (&lt; 40)</div>
            </div>
            <div className="space-y-1">
              <span className="font-bold text-slate-700 block">Verified Hotspots:</span>
              <div className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full border-2 border-dashed border-red-500" /> High Recurrence Area</div>
              <div className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full border-2 border-dashed border-amber-500" /> Medium Density Corridor</div>
              <span className="text-[10px] text-slate-400 block">Derived from verified municipal records</span>
            </div>
            <div className="space-y-1">
              <span className="font-bold text-slate-700 block">Officer Governance:</span>
              <div className="text-[11px] text-slate-600">
                Markers display assigned inspection personnel. Live GPS positioning is disabled per municipal privacy standard.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Map Container */}
      <div className="bg-white rounded-3xl border border-slate-200/90 shadow-sm p-2 sm:p-3 relative overflow-hidden min-h-[520px]">
        {loading ? (
          <div className="w-full h-[520px] rounded-2xl bg-slate-100 flex flex-col items-center justify-center gap-3">
            <RefreshCw className="w-7 h-7 text-blue-600 animate-spin" />
            <span className="text-xs font-bold text-slate-600">{t('loading')}</span>
          </div>
        ) : loadError ? (
          <div className="w-full h-[520px] rounded-2xl bg-red-50 border border-red-200 flex flex-col items-center justify-center p-6 text-center space-y-3">
            <AlertOctagon className="w-8 h-8 text-red-600" />
            <div className="text-sm font-bold text-red-800">{loadError}</div>
            <button
              onClick={fetchData}
              className="py-2 px-4 bg-red-600 hover:bg-red-700 text-white text-xs font-bold rounded-xl transition-colors shadow-xs"
            >
              {t('retry')}
            </button>
          </div>
        ) : mappedIncidents.length === 0 && !layers.hotspots && !layers.areaHealth ? (
          <div className="w-full h-[520px] rounded-2xl bg-slate-50 border border-slate-200 flex flex-col items-center justify-center p-6 text-center space-y-3">
            <MapPin className="w-8 h-8 text-slate-400" />
            <div className="text-sm font-bold text-slate-800">{t('noIncidentsMatch')}</div>
            <p className="text-xs text-slate-500 max-w-sm">
              Try adjusting the timeframe, severity, or category filters to view incidents.
            </p>
            <button
              onClick={handleResetFilters}
              className="py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-xl transition-colors shadow-xs"
            >
              {t('clearFilters')}
            </button>
          </div>
        ) : (
          <MapView
            incidents={mappedIncidents}
            hotspots={hotspots}
            areaHealth={areaHealth}
            layers={layers}
            onSelectIncident={onSelectIncident}
            onSelectArea={(spot) => setSelectedArea(spot)}
          />
        )}
      </div>

      {/* Unmapped Incidents Drawer / Modal */}
      {showUnmappedDrawer && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-xl w-full p-6 shadow-2xl border border-slate-100 space-y-4 max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-base font-black text-slate-900 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-500" />
                  <span>{t('unmappedIncidents')} ({unmappedIncidents.length})</span>
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  {t('missingGpsNotice')}
                </p>
              </div>
              <button
                onClick={() => setShowUnmappedDrawer(false)}
                className="p-1.5 rounded-xl hover:bg-slate-100 text-slate-500"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="overflow-y-auto divide-y divide-slate-100 flex-1 space-y-2">
              {unmappedIncidents.map((inc) => (
                <div key={inc.id || inc._id} className="pt-2 pb-2 flex items-center justify-between text-xs">
                  <div>
                    <div className="font-bold text-slate-800">{inc.title || inc.primary_encroachment_type}</div>
                    <div className="text-[11px] text-slate-500 flex items-center gap-2 mt-0.5">
                      <span>{inc.location_name || 'Unspecified Corridor'}</span>
                      <span>•</span>
                      <span className="font-mono text-slate-400">{inc.incident_number}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      inc.severity === 'High' ? 'bg-red-100 text-red-800' : 'bg-slate-100 text-slate-700'
                    }`}>
                      {inc.severity}
                    </span>
                    {onSelectIncident && (
                      <button
                        onClick={() => {
                          setShowUnmappedDrawer(false);
                          onSelectIncident(inc);
                        }}
                        className="py-1 px-2.5 rounded-lg bg-blue-50 text-blue-700 hover:bg-blue-100 font-bold text-[11px]"
                      >
                        {t('viewDetails')}
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>

            <div className="border-t border-slate-100 pt-3 flex justify-end">
              <button
                onClick={() => setShowUnmappedDrawer(false)}
                className="py-2 px-4 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold"
              >
                {t('close')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Selected Area Health Details Drawer */}
      {selectedArea && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl border border-slate-100 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-lg font-black text-slate-900">{selectedArea.area_name || selectedArea.area}</h3>
                <p className="text-xs text-slate-500">{selectedArea.ward}</p>
              </div>
              <button
                onClick={() => setSelectedArea(null)}
                className="p-1.5 rounded-xl hover:bg-slate-100 text-slate-500"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-2">
                <div className="p-3 bg-slate-50 rounded-xl">
                  <div className="text-[10px] text-slate-500 font-bold uppercase">{t('accessibilityScore')}</div>
                  <div className="text-xl font-black text-blue-600 mt-0.5">
                    {selectedArea.accessibility_score || selectedArea.avg_accessibility_score || 72}/100
                  </div>
                </div>
                <div className="p-3 bg-slate-50 rounded-xl">
                  <div className="text-[10px] text-slate-500 font-bold uppercase">Total Incidents</div>
                  <div className="text-xl font-black text-slate-900 mt-0.5">
                    {selectedArea.total_incidents || selectedArea.incidents || '—'}
                  </div>
                </div>
              </div>

              <div className="space-y-1.5 p-3 rounded-xl bg-slate-50 border border-slate-100">
                <div className="flex justify-between">
                  <span className="text-slate-600">Active Obstacles:</span>
                  <strong className="text-amber-600">{selectedArea.active !== undefined ? selectedArea.active : '—'}</strong>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-600">Resolution Rate:</span>
                  <strong className="text-emerald-600">{selectedArea.resolution_rate || selectedArea.resolution_rate_pct || '84%'}</strong>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-600">Primary Obstacle:</span>
                  <strong className="text-slate-900">{selectedArea.primary_cause || 'Street Vendors'}</strong>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2 pt-2">
              {onNavigateToAreaComparison && (
                <button
                  onClick={() => {
                    setSelectedArea(null);
                    onNavigateToAreaComparison();
                  }}
                  className="flex-1 py-2.5 px-4 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold flex items-center justify-center gap-1.5 shadow-xs transition-colors"
                >
                  <span>{t('areaComparison')}</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              )}
              <button
                onClick={() => setSelectedArea(null)}
                className="py-2.5 px-4 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold transition-colors"
              >
                {t('close')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
