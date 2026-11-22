import React, { useState } from 'react';
import {
  ArrowRight,
  Download,
  AlertTriangle,
  CheckCircle2,
  Activity,
  Layers,
  Sparkles,
  ExternalLink
} from 'lucide-react';

export default function AIDetectionPanel({ incident, onViewDetails }) {
  const [activeTab, setActiveTab] = useState('ai'); // 'original' | 'ai'

  if (!incident) {
    return (
      <div className="bg-white rounded-2xl p-12 border border-slate-200/80 shadow-xs text-center text-slate-400 space-y-3">
        <Sparkles className="w-10 h-10 text-slate-300 mx-auto" />
        <h3 className="font-bold text-slate-700 text-sm">No Incident Selected for AI Inspection</h3>
        <p className="text-xs text-slate-500 max-w-sm mx-auto">
          Select an incident from the Incident Queue or Map to inspect the computer vision detection results, spatial ROI segmentation, and accessibility analysis.
        </p>
      </div>
    );
  }

  const inc = incident;
  const detections = Array.isArray(inc.detections) ? inc.detections : [];
  const hasFootpath = inc.footpath_area_sqm != null;
  const hasOccupied = inc.occupied_area_sqm != null;
  const freeArea = (hasFootpath && hasOccupied) ? Math.max(0, inc.footpath_area_sqm - inc.occupied_area_sqm) : null;
  const hasScore = inc.accessibility_score != null;
  const scoreVal = hasScore ? Math.round(inc.accessibility_score) : null;

  return (
    <div className="space-y-6">
      {/* ======================================================== */}
      {/* 4. AI DETECTION RESULT matching Reference Panel 4 */}
      {/* ======================================================== */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs space-y-4">
        {/* Tab Controls: [Original Image] [AI Analysis Result] */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <h2 className="text-base font-bold text-slate-800">AI Detection Result</h2>

          <div className="flex items-center bg-slate-100 p-1 rounded-xl text-xs font-bold">
            <button
              onClick={() => setActiveTab('original')}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                activeTab === 'original'
                  ? 'bg-white text-slate-900 shadow-xs'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              Original Image
            </button>
            <button
              onClick={() => setActiveTab('ai')}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                activeTab === 'ai'
                  ? 'bg-[#0F172A] text-white shadow-xs'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              AI Analysis Result
            </button>
          </div>
        </div>

        {/* Visual Canvas */}
        <div className="relative rounded-2xl overflow-hidden bg-slate-900 border border-slate-200/80 aspect-video max-h-96 w-full flex items-center justify-center group">
          {activeTab === 'original' ? (
            inc.image_url ? (
              <img
                src={inc.image_url}
                alt="Original street photo"
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="text-slate-400 text-xs">No original image uploaded</div>
            )
          ) : (
            inc.annotated_image_url || inc.image_url ? (
              <img
                src={inc.annotated_image_url || inc.image_url}
                alt="AI Analysis Result Overlay"
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="text-slate-400 text-xs">No analysis visualization available</div>
            )
          )}
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center justify-between gap-4 pt-2 text-xs">
          <div className="flex flex-wrap items-center gap-4 sm:gap-6">
            <div className="flex items-center gap-2">
              <span className="w-3.5 h-3.5 rounded bg-emerald-500" />
              <span className="font-bold text-slate-700">Footpath ROI</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3.5 h-3.5 rounded bg-blue-500" />
              <span className="font-bold text-slate-700">Road Corridor</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3.5 h-3.5 rounded bg-red-500" />
              <span className="font-bold text-slate-700">Detected Obstruction</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3.5 h-3.5 rounded bg-amber-400" />
              <span className="font-bold text-slate-700">Uncertain Finding</span>
            </div>
          </div>

          <div className="text-[11px] font-semibold text-slate-400">
            YOLOv5n-ONNX • Geometric ROI Projection
          </div>
        </div>
      </div>

      {/* ======================================================== */}
      {/* 5. ANALYSIS DETAILS matching Reference Panel 5 */}
      {/* ======================================================== */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-bold text-slate-800">Analysis Details</h2>
          {onViewDetails && (
            <button
              onClick={() => onViewDetails(inc)}
              className="text-xs font-bold text-blue-600 hover:text-blue-700 flex items-center gap-1"
            >
              <span>Full Incident Dossier</span>
              <ExternalLink className="w-3 h-3" />
            </button>
          )}
        </div>

        {/* Top Row: Left Image Preview + Right Detected Objects Table */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-5 items-stretch">
          {/* Image Preview */}
          <div className="md:col-span-5 rounded-xl overflow-hidden border border-slate-200 bg-slate-900 max-h-52">
            {inc.image_url ? (
              <img
                src={inc.image_url}
                alt="Obstruction detail preview"
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-52 flex items-center justify-center text-slate-400 text-xs">
                No preview available
              </div>
            )}
          </div>

          {/* Detected Objects Table */}
          <div className="md:col-span-7 space-y-2">
            <div className="text-xs font-extrabold text-slate-700 uppercase tracking-wider mb-2">
              Detected Objects ({detections.length})
            </div>
            {detections.length > 0 ? (
              <div className="space-y-2 max-h-44 overflow-y-auto pr-1">
                {detections.map((d, idx) => {
                  const conf = typeof d.confidence === 'number'
                    ? (d.confidence <= 1 ? (d.confidence * 100).toFixed(0) + '%' : d.confidence.toFixed(0) + '%')
                    : 'N/A';
                  const isDanger = d.statusType === 'danger' || d.classification === 'Potential encroachment' || d.status === 'Potential Encroachment';
                  const label = d.label || d.category || d.raw_coco_class || 'Object';
                  const statusStr = d.status || d.classification || (isDanger ? 'Potential Encroachment' : 'On Road / Normal');

                  return (
                    <div
                      key={d.id || idx}
                      className="p-3 bg-slate-50/80 rounded-xl border border-slate-200/60 flex items-center justify-between text-xs gap-3"
                    >
                      <div className="flex items-center gap-3">
                        <span className="font-bold text-slate-800">{label}</span>
                        <span className="font-mono text-slate-500 font-semibold">{conf}</span>
                      </div>

                      <span
                        className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold ${
                          isDanger
                            ? 'bg-red-50 text-red-700 border border-red-200'
                            : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                        }`}
                      >
                        {statusStr}
                      </span>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="p-8 text-center text-slate-400 text-xs border border-dashed border-slate-200 rounded-xl">
                No objects detected by inference pipeline.
              </div>
            )}
          </div>
        </div>

        {/* Bottom Row: 3 Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
          {/* Footpath Analysis Card */}
          <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200/80 space-y-2">
            <div className="text-xs font-bold text-slate-700">Footpath Analysis</div>
            <div className="space-y-1.5 text-xs text-slate-600">
              <div className="flex justify-between">
                <span>Footpath Area:</span>
                <strong className="text-slate-800">
                  {hasFootpath ? `${inc.footpath_area_sqm} m²` : 'Uncalibrated / N/A'}
                </strong>
              </div>
              <div className="flex justify-between">
                <span>Occupied Area:</span>
                <strong className="text-slate-800">
                  {hasOccupied ? `${inc.occupied_area_sqm} m²` : 'Uncalibrated / N/A'}
                </strong>
              </div>
              <div className="flex justify-between">
                <span>Free Area:</span>
                <strong className="text-slate-800">
                  {freeArea != null ? `${freeArea} m²` : 'Uncalibrated / N/A'}
                </strong>
              </div>
              <div className="flex justify-between pt-1 border-t border-slate-200">
                <span className="font-bold">Occupancy:</span>
                <strong className="text-red-600 font-black">
                  {inc.occupancy_percentage != null ? `${inc.occupancy_percentage}%` : 'Uncalibrated'}
                </strong>
              </div>
            </div>
          </div>

          {/* Accessibility Score Card */}
          <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200/80 flex flex-col items-center justify-center text-center space-y-2">
            <div className="text-xs font-bold text-slate-700">Accessibility Score</div>

            {hasScore ? (
              <>
                <div className="relative w-20 h-20 flex items-center justify-center">
                  <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                    <path
                      className="text-slate-200"
                      strokeWidth="3.5"
                      stroke="currentColor"
                      fill="none"
                      d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    />
                    <path
                      className={scoreVal >= 70 ? 'text-emerald-500' : (scoreVal >= 40 ? 'text-amber-500' : 'text-red-500')}
                      strokeDasharray={`${scoreVal}, 100`}
                      strokeWidth="3.5"
                      strokeLinecap="round"
                      stroke="currentColor"
                      fill="none"
                      d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    />
                  </svg>
                  <div className="absolute font-black text-slate-900 text-base">
                    {scoreVal}%
                  </div>
                </div>

                <span className={`px-3 py-0.5 rounded-full text-[10px] font-bold ${
                  scoreVal >= 70
                    ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                    : (scoreVal >= 40
                      ? 'bg-amber-50 text-amber-800 border border-amber-200'
                      : 'bg-red-50 text-red-800 border border-red-200')
                }`}>
                  {scoreVal >= 70 ? 'Accessible' : (scoreVal >= 40 ? 'Partially Blocked' : 'Critical Obstruction')}
                </span>
              </>
            ) : (
              <div className="py-4 text-slate-400 text-xs">
                <span className="text-lg font-black block text-slate-500">N/A</span>
                <span className="text-[10px]">Uncalibrated Corridor</span>
              </div>
            )}
          </div>

          {/* Severity Card */}
          <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200/80 flex flex-col justify-between space-y-2">
            <div>
              <div className="text-xs font-bold text-slate-700">Severity</div>
              <div className="flex items-center gap-2 mt-2">
                <AlertTriangle className={`w-6 h-6 shrink-0 ${
                  inc.severity === 'High' ? 'text-red-600' : (inc.severity === 'Medium' ? 'text-amber-500' : 'text-slate-400')
                }`} />
                <span className={`text-2xl font-black tracking-tight ${
                  inc.severity === 'High' ? 'text-red-600' : (inc.severity === 'Medium' ? 'text-amber-600' : 'text-slate-700')
                }`}>
                  {inc.severity || 'Unassessed'}
                </span>
              </div>
            </div>

            <p className="text-[11px] text-slate-600 leading-snug">
              {inc.severity_reason || inc.reasoning || (inc.severity ? `${inc.severity} priority barrier assessed by municipal workflow.` : 'Pending field officer assessment.')}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
