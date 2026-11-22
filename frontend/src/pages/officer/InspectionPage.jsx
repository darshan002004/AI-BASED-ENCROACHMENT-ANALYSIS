import React, { useState, useRef } from 'react';
import {
  ArrowLeft,
  Camera,
  Upload,
  Sparkles,
  CheckCircle2,
  AlertOctagon,
  ShieldCheck,
  Send,
  RefreshCw
} from 'lucide-react';
import BeforeAfterCompare from '../../components/BeforeAfterCompare';
import { incidentsAPI } from '../../services/api';

export default function InspectionPage({ incident, onBack, onInspectionComplete }) {
  const [inspectionFile, setInspectionFile] = useState(null);
  const [inspectionPreview, setInspectionPreview] = useState(null);
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [verificationResult, setVerificationResult] = useState(incident?.ai_verification || null);
  const [isVerifying, setIsVerifying] = useState(false);

  const fileInputRef = useRef(null);

  if (!incident) {
    return (
      <div className="max-w-4xl mx-auto p-12 bg-white rounded-2xl border border-slate-200 text-center text-slate-400 space-y-3">
        <AlertOctagon className="w-10 h-10 text-slate-300 mx-auto" />
        <h3 className="font-bold text-slate-700 text-sm">No Incident Selected for Inspection</h3>
        <p className="text-xs text-slate-500">Please select an assigned incident from the Officer Patrol Queue to conduct a field inspection.</p>
        <button
          onClick={onBack}
          className="px-4 py-2 bg-blue-600 text-white rounded-xl text-xs font-bold hover:bg-blue-700 transition-colors"
        >
          Return to Queue
        </button>
      </div>
    );
  }

  const handlePhotoSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setInspectionFile(file);
      setInspectionPreview(URL.createObjectURL(file));
      setVerificationResult(null);
    }
  };

  const handleSubmitAndVerify = async (e) => {
    e.preventDefault();
    if (!inspectionPreview && !incident.inspection_image_url) {
      alert('Please capture or upload an on-site inspection photo.');
      return;
    }

    setIsVerifying(true);
    try {
      // 1. Submit inspection photo & notes
      const inspectRes = await incidentsAPI.submitInspection(incident.id, {
        inspection_image_url: inspectionPreview,
        inspection_notes: notes.trim() || 'Site cleared and inspected by field officer.'
      });

      // 2. Trigger automated Before/After AI Verification
      const verifyRes = await incidentsAPI.verifyResolution(incident.id);
      setVerificationResult(verifyRes.data.ai_verification);

      alert(`Inspection recorded! AI Verification: ${verifyRes.data.ai_verification?.status}`);
      if (onInspectionComplete) onInspectionComplete(verifyRes.data);
    } catch (err) {
      console.error(err);
      alert('Inspection submission or AI verification failed.');
    } finally {
      setIsVerifying(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-20">
      {/* Top Header */}
      <div className="flex items-center gap-3">
        <button
          onClick={onBack}
          className="p-2 rounded-xl bg-white border border-slate-200 text-slate-600 hover:bg-slate-50 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
        </button>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-extrabold text-slate-900 tracking-tight">
              Field Inspection & AI Verification
            </h1>
            <span className="font-mono text-xs font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-md border border-blue-200">
              {incident?.incident_number || `#${incident?.id?.slice(-6)}`}
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            {incident?.title || incident?.primary_encroachment_type} at {incident?.location_name || 'Corridor'}
          </p>
        </div>
      </div>

      {/* Side by side Before vs After Upload */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Left: Original Before Evidence */}
        <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm space-y-3">
          <div className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center justify-between">
            <span>BEFORE: Original Evidence</span>
            <span className="text-red-500 font-bold">
              {incident.occupancy_percentage != null ? `${incident.occupancy_percentage}% Blocked` : 'Occupancy Uncalibrated'}
            </span>
          </div>
          <div className="rounded-xl overflow-hidden border border-slate-200 bg-slate-900">
            {incident.image_url ? (
              <img
                src={incident.image_url}
                alt="Before evidence"
                className="w-full h-56 object-cover"
              />
            ) : (
              <div className="w-full h-56 flex items-center justify-center text-slate-400 text-xs">
                No initial image uploaded
              </div>
            )}
          </div>
          <div className="text-xs text-slate-500">
            Reported obstacle: <strong>{incident?.primary_encroachment_type || 'General Obstruction'}</strong>
          </div>
        </div>

        {/* Right: Upload Inspection Evidence */}
        <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm space-y-3">
          <div className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center justify-between">
            <span>AFTER: Clearance Photo</span>
            <span className="text-emerald-600 font-bold">Officer Evidence</span>
          </div>

          {!inspectionPreview && !incident?.inspection_image_url ? (
            <div
              onClick={() => fileInputRef.current?.click()}
              className="w-full h-56 border-2 border-dashed border-slate-200 hover:border-emerald-500 rounded-xl flex flex-col items-center justify-center gap-2 cursor-pointer bg-slate-50/60 hover:bg-emerald-50/20 transition-all text-center p-4"
            >
              <div className="w-10 h-10 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center">
                <Camera className="w-5 h-5" />
              </div>
              <span className="text-xs font-bold text-slate-800">Capture Inspection Photo</span>
              <span className="text-[10px] text-slate-400">Prove the obstacle has been cleared</span>
            </div>
          ) : (
            <div className="relative rounded-xl overflow-hidden border border-slate-200 bg-slate-900 group">
              <img
                src={inspectionPreview || incident?.inspection_image_url}
                alt="Inspection preview"
                className="w-full h-56 object-cover"
              />
              <button
                type="button"
                onClick={() => { setInspectionFile(null); setInspectionPreview(null); }}
                className="absolute top-2.5 right-2.5 bg-slate-900/80 text-white text-xs px-2.5 py-1 rounded-lg hover:bg-red-600 transition-colors"
              >
                Retake Photo
              </button>
            </div>
          )}

          <input
            type="file"
            ref={fileInputRef}
            onChange={handlePhotoSelect}
            accept="image/*"
            capture="environment"
            className="hidden"
          />

          <div className="text-xs text-slate-500">
            Upload post-clearance photo for automated AI comparison.
          </div>
        </div>
      </div>

      {/* Inspection Form Controls */}
      <form onSubmit={handleSubmitAndVerify} className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm space-y-4">
        <h2 className="text-sm font-bold text-slate-800">Officer Inspection Log & Action</h2>

        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-700">Inspection Observations & Resolution Notes</label>
          <textarea
            rows="2"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="w-full bg-slate-50 border border-slate-200 text-xs p-3 rounded-xl focus:outline-none focus:bg-white focus:border-blue-500 font-medium"
          />
        </div>

        <button
          type="submit"
          disabled={isVerifying}
          className="w-full py-3.5 px-4 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold flex items-center justify-center gap-2 shadow-md transition-colors disabled:opacity-50"
        >
          <Sparkles className="w-4 h-4" />
          {isVerifying ? 'Running Before/After AI Computer Vision Verification...' : 'Submit Evidence & Run AI Resolution Verification'}
        </button>
      </form>

      {/* Before/After Comparison Output Display */}
      {verificationResult && (
        <BeforeAfterCompare
          beforeUrl={incident?.image_url}
          afterUrl={inspectionPreview || incident?.inspection_image_url}
          comparisonUrl={verificationResult.comparison_image_url}
          verificationData={verificationResult}
        />
      )}
    </div>
  );
}
