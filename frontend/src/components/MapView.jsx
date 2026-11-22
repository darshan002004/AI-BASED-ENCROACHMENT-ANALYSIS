import React from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, CircleMarker } from 'react-leaflet';
import L from 'leaflet';
import { ExternalLink, AlertTriangle, ShieldCheck, Activity, User, Eye } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

// Custom SVG marker icons
const createSvgPin = (color, badgeText = null) => {
  return L.divIcon({
    className: 'custom-map-pin',
    html: `
      <div style="position: relative; width: 32px; height: 38px;">
        <svg viewBox="0 0 24 24" width="32" height="38" style="filter: drop-shadow(0 2px 4px rgba(0,0,0,0.35));">
          <path fill="${color}" stroke="#FFFFFF" stroke-width="1.5" d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
        </svg>
        ${badgeText ? `
          <div style="position: absolute; top: -4px; right: -4px; background: #0F172A; color: white; font-size: 8px; font-weight: 800; padding: 1px 4px; border-radius: 9999px; border: 1px solid white;">
            ${badgeText}
          </div>
        ` : ''}
      </div>
    `,
    iconSize: [32, 38],
    iconAnchor: [16, 38],
    popupAnchor: [0, -36],
  });
};

const redPin = createSvgPin('#EF4444');
const orangePin = createSvgPin('#F59E0B');
const greenPin = createSvgPin('#10B981');
const bluePin = createSvgPin('#3B82F6');
const neutralPin = createSvgPin('#64748B');

const WARD_COORDINATES = {
  'mg road': [12.9756, 77.6066],
  'indiranagar': [12.9784, 77.6408],
  'btm layout': [12.9166, 77.6101],
  'koramangala': [12.9352, 77.6245],
  'jp nagar': [12.9063, 77.5857],
  'hsr layout': [12.9121, 77.6446],
  'jayanagar': [12.9308, 77.5838],
};

const isValidCoord = (lat, lng) => {
  if (lat === null || lat === undefined || lng === null || lng === undefined) return false;
  const nLat = Number(lat);
  const nLng = Number(lng);
  if (isNaN(nLat) || isNaN(nLng)) return false;
  if (nLat < -90 || nLat > 90 || nLng < -180 || nLng > 180) return false;
  if (nLat === 0 && nLng === 0) return false;
  return true;
};

export default function MapView({
  incidents = [],
  hotspots = [],
  areaHealth = [],
  layers = {
    incidents: true,
    severity: true,
    hotspots: true,
    accessibility: true,
    assignments: true,
    areaHealth: true
  },
  center = [12.9550, 77.6100],
  zoom = 12,
  onSelectIncident,
  onSelectArea
}) {
  const { t } = useLanguage();

  const getPin = (inc) => {
    if (!layers.severity) {
      return neutralPin;
    }
    const s = (inc.severity || '').toLowerCase();
    if (s === 'high') return redPin;
    if (s === 'medium') return orangePin;
    if (s === 'low') return greenPin;
    return bluePin;
  };

  // Deduplicate incidents by unique incident ID to prevent duplicate markers
  const uniqueIncidents = [];
  const seenIds = new Set();
  for (const inc of incidents) {
    const id = inc.id || inc._id;
    if (!seenIds.has(id)) {
      seenIds.add(id);
      uniqueIncidents.push(inc);
    }
  }

  return (
    <div className="w-full h-full relative rounded-2xl overflow-hidden shadow-inner bg-slate-100">
      <MapContainer
        center={center}
        zoom={zoom}
        scrollWheelZoom={false}
        className="w-full h-full min-h-[480px]"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* LAYER 3: Historical / Verified Hotspots Radial Zones */}
        {layers.hotspots && hotspots.map((spot, idx) => {
          const lat = spot.latitude || (WARD_COORDINATES[spot.key?.toLowerCase()] ? WARD_COORDINATES[spot.key?.toLowerCase()][0] : (12.9716 + (idx * 0.015)));
          const lng = spot.longitude || (WARD_COORDINATES[spot.key?.toLowerCase()] ? WARD_COORDINATES[spot.key?.toLowerCase()][1] : (77.5946 + (idx * 0.015)));
          const coords = [lat, lng];

          const isHigh = (spot.status || spot.risk_level || spot.risk || '').toLowerCase().includes('critical') ||
                         (spot.status || spot.risk_level || spot.risk || '').toLowerCase() === 'high';
          const circleColor = isHigh ? '#EF4444' : '#F59E0B';

          return (
            <Circle
              key={`hotspot_${spot.area || spot.key || idx}`}
              center={coords}
              radius={450}
              pathOptions={{
                color: circleColor,
                fillColor: circleColor,
                fillOpacity: 0.16,
                weight: 2,
                dashArray: '6, 6'
              }}
            >
              <Popup className="custom-leaflet-popup">
                <div className="p-1 space-y-1.5 text-xs max-w-[220px]">
                  <div className="flex items-center gap-1.5 font-bold text-slate-900 text-sm">
                    <AlertTriangle className={`w-4 h-4 ${isHigh ? 'text-red-500' : 'text-amber-500'}`} />
                    <span>{spot.area || spot.area_name || spot.name || t('layerHotspots')}</span>
                  </div>
                  <div className="text-[11px] text-slate-600 space-y-1">
                    <div>{t('filterWard')}: <strong className="text-slate-800">{spot.ward || 'Bangalore Urban'}</strong></div>
                    <div>{t('filterStatus')}: <strong className={isHigh ? 'text-red-600' : 'text-amber-600'}>{spot.status || 'Verified Hotspot'}</strong></div>
                    <div>Total Incidents: <strong className="text-slate-800">{spot.incidents || '10+'}</strong></div>
                    <div>Active: <strong className="text-amber-600">{spot.active !== undefined ? spot.active : '—'}</strong></div>
                    <div>Top Cause: <strong className="text-slate-800">{spot.primary_cause || 'Obstruction'}</strong></div>
                  </div>
                  {onSelectArea && (
                    <button
                      onClick={() => onSelectArea(spot)}
                      className="w-full mt-2 py-1 px-2 text-[11px] font-bold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
                    >
                      {t('viewDetails')}
                    </button>
                  )}
                </div>
              </Popup>
            </Circle>
          );
        })}

        {/* LAYER 4: Accessibility Footpath Condition Overlays (Radial indicators) */}
        {layers.accessibility && uniqueIncidents.map((inc) => {
          if (!isValidCoord(inc.latitude, inc.longitude)) return null;
          const accScore = inc.accessibility_score !== undefined && inc.accessibility_score !== null ? Number(inc.accessibility_score) : 75;
          const accColor = accScore >= 80 ? '#10B981' : accScore >= 60 ? '#F59E0B' : accScore >= 40 ? '#F97316' : '#EF4444';

          return (
            <Circle
              key={`acc_ring_${inc.id || inc._id}`}
              center={[Number(inc.latitude), Number(inc.longitude)]}
              radius={80}
              pathOptions={{
                color: accColor,
                fillColor: accColor,
                fillOpacity: 0.12,
                weight: 1.5,
              }}
            />
          );
        })}

        {/* LAYER 5: Ward Health Circles */}
        {layers.areaHealth && areaHealth.map((ward, idx) => {
          const coords = WARD_COORDINATES[ward.key?.toLowerCase()] || [12.9716, 77.5946];
          const statusColor = ward.status === 'GREEN' ? '#10B981' : ward.status === 'YELLOW' ? '#F59E0B' : '#EF4444';

          return (
            <CircleMarker
              key={`ward_${ward.key || idx}`}
              center={coords}
              radius={14}
              pathOptions={{
                color: '#FFFFFF',
                fillColor: statusColor,
                fillOpacity: 0.9,
                weight: 2.5
              }}
            >
              <Popup className="custom-leaflet-popup">
                <div className="p-1.5 space-y-2 text-xs max-w-[220px]">
                  <div className="border-b border-slate-100 pb-1">
                    <div className="font-black text-slate-900 text-sm">{ward.area_name}</div>
                    <div className="text-[10px] text-slate-400">{ward.ward}</div>
                  </div>

                  <div className="space-y-1 text-[11px] text-slate-700">
                    <div className="flex justify-between">
                      <span>Area Health:</span>
                      <strong className={ward.status === 'GREEN' ? 'text-emerald-600' : ward.status === 'YELLOW' ? 'text-amber-600' : 'text-red-600'}>
                        {ward.status_label || ward.status}
                      </strong>
                    </div>
                    <div className="flex justify-between">
                      <span>{t('accessibilityScore')}:</span>
                      <strong className="text-blue-600">{ward.accessibility_score}/100</strong>
                    </div>
                    <div className="flex justify-between">
                      <span>Total Incidents:</span>
                      <strong className="text-slate-900">{ward.total_incidents}</strong>
                    </div>
                    <div className="flex justify-between">
                      <span>Resolution Rate:</span>
                      <strong className="text-emerald-600">{ward.resolution_rate_pct}%</strong>
                    </div>
                  </div>

                  {onSelectArea && (
                    <button
                      onClick={() => onSelectArea(ward)}
                      className="w-full py-1.5 text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors flex items-center justify-center gap-1 shadow-xs"
                    >
                      <Activity className="w-3.5 h-3.5" />
                      <span>{t('viewDetails')}</span>
                    </button>
                  )}
                </div>
              </Popup>
            </CircleMarker>
          );
        })}

        {/* LAYER 1: Incident Markers */}
        {layers.incidents && uniqueIncidents.map((inc) => {
          if (!isValidCoord(inc.latitude, inc.longitude)) return null;

          const sevStr = inc.severity || 'Medium';
          const statStr = inc.status || 'Verified';
          const occVal = inc.occupancy_percentage || 0;
          const assignedOfficer = inc.assigned_officer_name || null;

          return (
            <Marker
              key={inc.id || inc._id}
              position={[Number(inc.latitude), Number(inc.longitude)]}
              icon={getPin(inc)}
            >
              <Popup className="custom-leaflet-popup">
                <div className="p-1 max-w-[220px] space-y-2 text-xs">
                  {(inc.privacy_image_url || inc.image_url) && (
                    <img
                      src={inc.privacy_image_url || inc.image_url}
                      alt={inc.title}
                      className="w-full h-24 object-cover rounded-xl border border-slate-200"
                    />
                  )}

                  {/* Incident Number & Title */}
                  <div className="flex items-center justify-between gap-1">
                    <span className="font-mono text-[10px] font-bold text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded border border-blue-200">
                      {inc.incident_number || 'ENC-INC'}
                    </span>
                    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                      statStr === 'Resolved' ? 'bg-emerald-100 text-emerald-800' :
                      statStr === 'In Progress' ? 'bg-amber-100 text-amber-800' :
                      'bg-slate-100 text-slate-800'
                    }`}>
                      {t(statStr.toLowerCase().replace(' ', '')) || statStr}
                    </span>
                  </div>

                  <div className="font-bold text-slate-900 text-sm leading-tight">
                    {inc.location_name || 'Corridor Location'}
                  </div>

                  {/* Meta details */}
                  <div className="space-y-1 text-[11px] text-slate-600">
                    <div>{t('filterType')}: <strong className="text-slate-800">{inc.primary_encroachment_type || 'Street Vendor'}</strong></div>
                    
                    {layers.severity && (
                      <div>
                        {t('filterSeverity')}: <strong className={sevStr === 'High' ? 'text-red-600' : sevStr === 'Medium' ? 'text-amber-600' : 'text-emerald-600'}>
                          {sevStr} {inc.risk_score ? `(${inc.risk_score}/100)` : ''}
                        </strong>
                      </div>
                    )}

                    {layers.accessibility && (
                      <div>
                        {t('accessibilityScore')}: <strong className="text-blue-600">
                          {inc.accessibility_score !== undefined ? `${inc.accessibility_score}/100` : '—'}
                        </strong>
                        {inc.path_continuity && (
                          <span className="text-[10px] text-slate-500 block">
                            Path: {inc.path_continuity}
                          </span>
                        )}
                      </div>
                    )}

                    {layers.assignments && (
                      <div className="border-t border-slate-100 pt-1 text-[10px]">
                        {assignedOfficer ? (
                          <div className="flex items-center gap-1 text-emerald-700 font-semibold">
                            <ShieldCheck className="w-3 h-3 shrink-0" />
                            <span>Assigned: {assignedOfficer}</span>
                          </div>
                        ) : (
                          <div className="text-slate-500 italic">
                            Unassigned (Awaiting dispatch)
                          </div>
                        )}
                        <span className="text-[9px] text-slate-400 block mt-0.5">
                          {t('officerTrackingNote')}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* CTA Button */}
                  {onSelectIncident && (
                    <button
                      onClick={() => onSelectIncident(inc)}
                      className="w-full py-1.5 px-3 text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 rounded-lg flex items-center justify-center gap-1.5 transition-colors shadow-xs"
                    >
                      <span>{t('viewDetails')}</span>
                      <ExternalLink className="w-3 h-3" />
                    </button>
                  )}
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>
    </div>
  );
}
