import React, { useState } from 'react';
import {
  CheckCircle2,
  AlertTriangle,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  RefreshCw,
  Eye
} from 'lucide-react';

export default function BeforeAfterCompare({
  beforeUrl,
  afterUrl,
  comparisonUrl,
  verificationData,
  onRunVerification,
  isVerifying = false
}) {
  const isVerified = verificationData?.verified ?? true;
  const statusTitle = isVerified ? 'Resolution Verified' : 'Resolution Not Verified';
  const statusMessage = isVerified
    ? 'No obstruction detected in the latest image. AI analysis confirms the area is clear.'
    : 'Obstruction still detected in the inspection image. Area requires further field intervention.';

  return (
    <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-100 gap-3">
        <div>
          <h2 className="text-base font-bold text-slate-800">Before / After Verification</h2>
          <p className="text-xs text-slate-500 font-medium mt-0.5">
            Automated computer vision comparison between citizen evidence and officer clearance inspection
          </p>
        </div>

        {onRunVerification && (
          <button
            onClick={onRunVerification}
            disabled={isVerifying}
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold shadow-xs flex items-center gap-1.5 transition-all self-start sm:self-auto"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isVerifying ? 'animate-spin' : ''}`} />
            <span>{isVerifying ? 'Analyzing clearance...' : 'Run AI Verification'}</span>
          </button>
        )}
      </div>

      {/* Side-by-Side Images matching Reference Panel 10: Before (Reported) -> After (Inspection) */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Left: Before (Reported) */}
        <div className="flex-1 w-full space-y-2">
          <div className="rounded-2xl overflow-hidden border border-slate-200 bg-slate-900 shadow-xs aspect-video flex items-center justify-center relative">
            <img
              src={beforeUrl || '/uploads/original/vendor_mg_road.jpg'}
              alt="Before (Reported)"
              className="w-full h-full object-cover"
            />
            <div className="absolute top-3 left-3 bg-slate-900/80 backdrop-blur-xs text-white text-[10px] font-bold px-2.5 py-1 rounded-md">
              Before (Reported)
            </div>
          </div>
          <div className="text-center text-xs font-bold text-slate-700">
            Before (Reported)
          </div>
        </div>

        {/* Center Connecting Arrow matching Reference */}
        <div className="shrink-0 text-blue-600 my-2 md:my-0">
          <div className="w-10 h-10 rounded-full bg-blue-50 border border-blue-200 flex items-center justify-center">
            <ArrowRight className="w-5 h-5" />
          </div>
        </div>

        {/* Right: After (Inspection) */}
        <div className="flex-1 w-full space-y-2">
          <div className="rounded-2xl overflow-hidden border border-slate-200 bg-slate-900 shadow-xs aspect-video flex items-center justify-center relative">
            <img
              src={afterUrl || '/uploads/original/clear_street.jpg'}
              alt="After (Inspection)"
              className="w-full h-full object-cover"
            />
            <div className="absolute top-3 left-3 bg-slate-900/80 backdrop-blur-xs text-white text-[10px] font-bold px-2.5 py-1 rounded-md">
              After (Inspection)
            </div>
          </div>
          <div className="text-center text-xs font-bold text-slate-700">
            After (Inspection)
          </div>
        </div>
      </div>

      {/* Verification Banner matching Reference Panel 10 */}
      <div
        className={`p-4 rounded-2xl border flex items-start sm:items-center gap-3.5 transition-all ${
          isVerified
            ? 'bg-emerald-50/70 border-emerald-200/80 text-emerald-900'
            : 'bg-amber-50/70 border-amber-200/80 text-amber-900'
        }`}
      >
        <div
          className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
            isVerified ? 'bg-emerald-600 text-white shadow-xs' : 'bg-amber-500 text-white'
          }`}
        >
          {isVerified ? <CheckCircle2 className="w-6 h-6" /> : <AlertTriangle className="w-6 h-6" />}
        </div>

        <div className="space-y-0.5">
          <h3 className="text-sm font-black tracking-tight">{statusTitle}</h3>
          <p className="text-xs text-slate-600 leading-relaxed font-medium">
            {statusMessage}
          </p>
        </div>
      </div>
    </div>
  );
}
