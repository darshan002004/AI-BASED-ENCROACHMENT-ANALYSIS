import React, { useState } from 'react';
import { Settings, Sliders, Shield, Bell, Database, Save, Check } from 'lucide-react';

export default function SettingsPage() {
  const [minWidth, setMinWidth] = useState(1.5);
  const [confThreshold, setConfThreshold] = useState(50);
  const [persistentSec, setPersistentSec] = useState(3.0);
  const [dupRadius, setDupRadius] = useState(60);
  const [saved, setSaved] = useState(false);

  const handleSave = (e) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="space-y-5 max-w-4xl mx-auto pb-16">
      <div className="border-b border-slate-200/80 pb-3">
        <h1 className="text-base font-bold text-slate-900 tracking-tight">Platform Configuration & Thresholds</h1>
        <p className="text-xs text-slate-500 font-normal mt-0.5">
          Tune computer vision sensitivity, accessibility tolerance standards, and spatial duplicate clustering parameters
        </p>
      </div>

      <form onSubmit={handleSave} className="bg-white rounded-xl p-5 border border-slate-200/90 shadow-2xs space-y-5">
        {/* Computer Vision Thresholds */}
        <div className="space-y-3.5">
          <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
            <Sliders className="w-3.5 h-3.5 text-slate-700" />
            AI & Computer Vision Engine Parameters
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 text-xs">
            <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200 space-y-2">
              <label className="font-semibold text-slate-800 block">AI Detection Confidence Cutoff</label>
              <div className="flex items-center gap-3">
                <input
                  type="range"
                  min="30"
                  max="90"
                  value={confThreshold}
                  onChange={(e) => setConfThreshold(Number(e.target.value))}
                  className="w-full accent-slate-900"
                />
                <span className="font-bold text-slate-900 w-12 text-right">{confThreshold}%</span>
              </div>
              <p className="text-[11px] text-slate-500">Detections below this probability will be ignored as noise.</p>
            </div>

            <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200 space-y-2">
              <label className="font-semibold text-slate-800 block">Video Persistence Time Threshold</label>
              <div className="flex items-center gap-3">
                <input
                  type="range"
                  min="1"
                  max="15"
                  step="0.5"
                  value={persistentSec}
                  onChange={(e) => setPersistentSec(Number(e.target.value))}
                  className="w-full accent-slate-900"
                />
                <span className="font-bold text-slate-900 w-12 text-right">{persistentSec}s</span>
              </div>
              <p className="text-[11px] text-slate-500">Stationary obstacles must persist for this duration before incident triggers.</p>
            </div>
          </div>
        </div>

        {/* Walkability & Accessibility Tolerance Standards */}
        <div className="space-y-3.5 border-t border-slate-100 pt-4">
          <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
            <Shield className="w-3.5 h-3.5 text-slate-700" />
            Accessibility & Spatial Clustering Standards
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 text-xs">
            <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200 space-y-2">
              <label className="font-semibold text-slate-800 block">Minimum Safe Walkway Clearance (m)</label>
              <div className="flex items-center gap-3">
                <input
                  type="number"
                  step="0.1"
                  min="0.8"
                  max="3.0"
                  value={minWidth}
                  onChange={(e) => setMinWidth(Number(e.target.value))}
                  className="w-20 p-1.5 bg-white border border-slate-200 rounded-lg text-slate-800 font-bold focus:outline-none"
                />
                <span className="text-slate-500">Meters (IRC-103 ADA: 1.5m)</span>
              </div>
              <p className="text-[11px] text-slate-500">Clear width below this triggers High Severity warning.</p>
            </div>

            <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200 space-y-2">
              <label className="font-semibold text-slate-800 block">Duplicate Report GPS Radius (Meters)</label>
              <div className="flex items-center gap-3">
                <input
                  type="number"
                  step="5"
                  min="10"
                  max="200"
                  value={dupRadius}
                  onChange={(e) => setDupRadius(Number(e.target.value))}
                  className="w-20 p-1.5 bg-white border border-slate-200 rounded-lg text-slate-800 font-bold focus:outline-none"
                />
                <span className="text-slate-500">Meters spatial radius</span>
              </div>
              <p className="text-[11px] text-slate-500">Citizen reports within this distance will be merged under one master incident.</p>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between pt-3 border-t border-slate-100">
          {saved && (
            <span className="text-xs font-semibold text-emerald-700 flex items-center gap-1.5 animate-fade-in">
              <Check className="w-3.5 h-3.5" /> System parameters updated successfully!
            </span>
          )}
          <button
            type="submit"
            className="ml-auto px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-2xs transition-colors"
          >
            <Save className="w-3.5 h-3.5" />
            Save Configuration
          </button>
        </div>
      </form>
    </div>
  );
}
