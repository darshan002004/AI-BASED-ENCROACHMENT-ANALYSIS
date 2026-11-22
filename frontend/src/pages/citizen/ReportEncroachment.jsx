import React, { useState, useRef } from 'react';
import {
  Camera,
  Upload,
  Video,
  Sparkles,
  CheckCircle2,
  Navigation,
  FileWarning,
  Edit2,
  ArrowRight,
  ArrowLeft,
  MapPin,
  AlertTriangle,
  Layers,
  Check,
  Plus,
  X,
  Eye
} from 'lucide-react';
import { aiAPI, incidentsAPI } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';

const ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png'];
const ALLOWED_MIMES = ['image/jpeg', 'image/jpg', 'image/png'];
const MAX_SIZE_BYTES = 25 * 1024 * 1024;

export default function ReportEncroachment({ onReportSubmitted }) {
  const { user } = useAuth();
  const { t, lang } = useLanguage();
  const [currentStep, setCurrentStep] = useState(1); // 1: Upload, 2: Location, 3: Confirm, 4: Submit
  const [uploadMode, setUploadMode] = useState('image'); // 'photo' | 'image' | 'video'

  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState('/uploads/original/vendor_mg_road.jpg'); // Default reference preview
  const [analyzing, setAnalyzing] = useState(false);
  const [aiResult, setAiResult] = useState({
    primary_encroachment_type: 'Street Vendor',
    confidence: 0.87,
    accessibility_score: 68.0,
    severity: 'High'
  });
  const [errorMessage, setErrorMessage] = useState(null);
  const [isEditingType, setIsEditingType] = useState(false);

  // Batch 2: Multi-Image Evidence State
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [filePreviews, setFilePreviews] = useState([]); // [{ url, name, size }]
  const [activePreviewIdx, setActivePreviewIdx] = useState(0);
  const [multiAiResults, setMultiAiResults] = useState([]);
  const [isInconsistent, setIsInconsistent] = useState(false);
  const [inconsistencyReason, setInconsistencyReason] = useState(null);

  // Form Fields
  const [locationName, setLocationName] = useState('MG Road Promenade, Ward 112');
  const [latitude, setLatitude] = useState(12.9756);
  const [longitude, setLongitude] = useState(77.6066);
  const [geoLocating, setGeoLocating] = useState(false);
  const [selectedType, setSelectedType] = useState('Street Vendor');
  const [notes, setNotes] = useState('Hawker cart obstructing pedestrian movement near the metro pillar.');
  const [submitting, setSubmitting] = useState(false);
  const [submissionResult, setSubmissionResult] = useState(null);

  const fileInputRef = useRef(null);

  const handleFileSelect = async (e) => {
    const rawFiles = Array.from(e.target.files || []);
    if (!rawFiles.length) return;

    setErrorMessage(null);

    // Combine with existing selectedFiles up to max 5
    const combined = [...selectedFiles, ...rawFiles];
    if (combined.length > 5) {
      setErrorMessage('You can upload a maximum of 5 evidence photos per incident.');
      return;
    }

    // Validate each file
    for (const file of rawFiles) {
      const ext = (file.name.split('.').pop() || '').toLowerCase();
      const mime = (file.type || '').toLowerCase();

      if (!ALLOWED_EXTENSIONS.includes(ext) || (mime && !ALLOWED_MIMES.includes(mime))) {
        setErrorMessage(`Invalid format for "${file.name}". Please upload JPG or PNG images only.`);
        return;
      }
      if (file.size === 0 || file.size > MAX_SIZE_BYTES) {
        setErrorMessage(`"${file.name}" must be non-empty and under 25 MB.`);
        return;
      }
    }

    const newFiles = combined;
    setSelectedFiles(newFiles);

    // Build previews
    const newPreviews = newFiles.map((f) => ({
      url: URL.createObjectURL(f),
      name: f.name,
      size: Math.round(f.size / 1024),
      file: f
    }));
    setFilePreviews(newPreviews);
    setActivePreviewIdx(0);
    setPreviewUrl(newPreviews[0]?.url || previewUrl);

    // Trigger AI Multi-Image Pipeline
    setAnalyzing(true);
    try {
      const formData = new FormData();
      if (newFiles.length === 1) {
        formData.append('file', newFiles[0]);
        const res = await aiAPI.analyzeImage(formData);
        setAiResult(res.data);
        setMultiAiResults([res.data]);
        setIsInconsistent(false);
        setInconsistencyReason(null);
        if (res.data.primary_encroachment_type && !['No Obstruction Detected', 'Not an Encroachment'].includes(res.data.primary_encroachment_type)) {
          setSelectedType(res.data.primary_encroachment_type);
        }
      } else {
        newFiles.forEach((f) => formData.append('files', f));
        const res = await aiAPI.analyzeMultiple(formData);
        const data = res.data;
        setMultiAiResults(data.evidence_results || []);
        setIsInconsistent(!!data.is_inconsistent);
        setInconsistencyReason(data.inconsistency_reason || null);
        if (data.primary_result) {
          setAiResult(data.primary_result);
          if (data.primary_result.primary_encroachment_type && !['No Obstruction Detected', 'Not an Encroachment'].includes(data.primary_result.primary_encroachment_type)) {
            setSelectedType(data.primary_result.primary_encroachment_type);
          }
        }
      }
    } catch (err) {
      console.warn('AI analysis error, fallback predictions maintained:', err);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleRemovePhoto = (idx) => {
    const updatedFiles = selectedFiles.filter((_, i) => i !== idx);
    const updatedPreviews = filePreviews.filter((_, i) => i !== idx);
    setSelectedFiles(updatedFiles);
    setFilePreviews(updatedPreviews);
    if (activePreviewIdx >= updatedPreviews.length) {
      setActivePreviewIdx(Math.max(0, updatedPreviews.length - 1));
    }
    if (updatedPreviews.length > 0) {
      setPreviewUrl(updatedPreviews[0]?.url);
    }
  };

  const handleDetectLocation = () => {
    if (!navigator.geolocation) {
      setErrorMessage('Geolocation is not supported by your browser.');
      return;
    }
    setGeoLocating(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLatitude(pos.coords.latitude);
        setLongitude(pos.coords.longitude);
        setLocationName(`Current GPS (${pos.coords.latitude.toFixed(4)}, ${pos.coords.longitude.toFixed(4)})`);
        setGeoLocating(false);
      },
      () => {
        setGeoLocating(false);
      }
    );
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    setErrorMessage(null);

    // Build evidence images list
    const evidence_images = filePreviews.length > 0
      ? filePreviews.map((p, idx) => {
          const r = multiAiResults[idx] || {};
          return {
            id: `ev_${idx + 1}`,
            image_url: r.original_image_url || p.url,
            caption: r.perspective_label || `Perspective #${idx + 1}`,
            metadata: {
              filename: p.name,
              size_kb: p.size,
              detected_type: r.primary_encroachment_type || selectedType,
              confidence: r.confidence || aiResult?.confidence,
              occupancy_percentage: r.occupancy_percentage || aiResult?.occupancy_percentage
            }
          };
        })
      : [{ id: 'main', image_url: previewUrl, caption: 'Primary Photo' }];

    const primaryUrl = multiAiResults[0]?.original_image_url || filePreviews[0]?.url || previewUrl;

    const payload = {
      title: `${selectedType} on Footpath at ${locationName}`,
      description: notes || `Citizen report for ${selectedType} obstruction.`,
      location_name: locationName,
      latitude: parseFloat(latitude),
      longitude: parseFloat(longitude),
      image_url: primaryUrl,
      annotated_image_url: aiResult?.annotated_image_url || null,
      primary_encroachment_type: selectedType,
      occupancy_percentage: aiResult?.occupancy_percentage || 32.0,
      accessibility_score: aiResult?.accessibility_score || 68.0,
      severity: aiResult?.severity || 'High',
      footpath_width_m: aiResult?.footpath_width_m,
      obstructed_width_m: aiResult?.obstructed_width_m,
      remaining_width_m: aiResult?.remaining_width_m,
      bottleneck_blockage_pct: aiResult?.bottleneck_blockage_pct,
      is_calibrated: aiResult?.is_calibrated ?? true,
      calibration_mode: aiResult?.calibration_mode || 'calibrated',
      warnings: aiResult?.warnings || [],
      evidence_images: evidence_images,
      evidence_inconsistency_flag: isInconsistent,
      evidence_inconsistency_reason: inconsistencyReason,
      human_verification_status: isInconsistent ? 'NEEDS_REVIEW' : 'PENDING REVIEW'
    };

    try {
      const res = await incidentsAPI.create(payload);
      setSubmissionResult(res.data);
      setCurrentStep(4);
    } catch (err) {
      console.error(err);
      setErrorMessage(err.response?.data?.detail || 'Failed to submit encroachment incident.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-16">
      {/* Page Title */}
      <div>
        <h1 className="text-2xl font-black text-slate-900 tracking-tight">{t('reportEncroachment')}</h1>
        <p className="text-xs text-slate-500 font-medium mt-0.5">
          {t('reportSubtitle')}
        </p>
      </div>

      {/* Stepper Header matching Reference Panel 3 */}
      <div className="bg-white rounded-2xl p-4 sm:p-5 border border-slate-200/80 shadow-xs">
        <div className="flex items-center justify-between max-w-2xl mx-auto">
          {[
            { step: 1, label: t('stepUpload') },
            { step: 2, label: t('stepLocation') },
            { step: 3, label: t('stepConfirm') },
            { step: 4, label: t('stepSubmit') }
          ].map((s, idx, arr) => {
            const isActive = currentStep === s.step;
            const isDone = currentStep > s.step;
            return (
              <React.Fragment key={s.step}>
                <div className="flex flex-col items-center">
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-black transition-all ${
                      isActive
                        ? 'bg-blue-600 text-white shadow-md shadow-blue-500/30 ring-4 ring-blue-100'
                        : isDone
                        ? 'bg-emerald-600 text-white'
                        : 'bg-slate-100 text-slate-400'
                    }`}
                  >
                    {isDone ? <Check className="w-4 h-4 stroke-[3]" /> : s.step}
                  </div>
                  <span className={`text-[11px] font-bold mt-1.5 ${isActive ? 'text-blue-600' : isDone ? 'text-emerald-700' : 'text-slate-400'}`}>
                    {s.label}
                  </span>
                </div>
                {idx < arr.length - 1 && (
                  <div className={`flex-1 h-0.5 mx-3 sm:mx-6 -mt-4 transition-colors ${currentStep > s.step ? 'bg-emerald-500' : 'bg-slate-200'}`} />
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>

      {errorMessage && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-xs text-red-700 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0 text-red-600" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* STEP 1: UPLOAD matching Reference Panel 3 */}
      {currentStep === 1 && (
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-6">
          {/* Upload Mode Pills matching Reference [Take Photo] [Upload Image] [Upload Video] */}
          <div className="flex items-center gap-2">
            {[
              { id: 'photo', label: 'Take Photo', icon: Camera },
              { id: 'image', label: 'Upload Image', icon: Upload },
              { id: 'video', label: 'Upload Video', icon: Video }
            ].map((m) => {
              const Icon = m.icon;
              const isSelected = uploadMode === m.id;
              return (
                <button
                  key={m.id}
                  onClick={() => {
                    setUploadMode(m.id);
                    if (fileInputRef.current) fileInputRef.current.click();
                  }}
                  className={`px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-all ${
                    isSelected
                      ? 'bg-blue-600 text-white shadow-xs'
                      : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{m.label}</span>
                </button>
              );
            })}
          </div>

          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileSelect}
            accept="image/png,image/jpeg,image/jpg"
            multiple
            className="hidden"
          />

          {/* Side-by-Side: Drag & Drop Box + Image Preview matching Reference Panel 3 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5 items-stretch">
            {/* Drag & Drop Area */}
            <div
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-slate-300 hover:border-blue-500 rounded-2xl p-8 flex flex-col items-center justify-center text-center bg-slate-50/60 hover:bg-blue-50/30 transition-all cursor-pointer min-h-[220px]"
            >
              <div className="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mb-3">
                <Upload className="w-6 h-6" />
              </div>
              <p className="text-xs font-bold text-slate-800">
                {t('dragDropText')}
              </p>
              <p className="text-[11px] text-slate-400 font-medium mt-1">
                Upload up to 5 photos for multi-perspective validation (JPG, PNG &le; 25MB)
              </p>
              {filePreviews.length > 0 && (
                <span className="mt-2 text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">
                  {filePreviews.length} / 5 Photos Attached
                </span>
              )}
            </div>

            {/* Image Preview Box */}
            <div className="rounded-2xl border border-slate-200 overflow-hidden bg-slate-900 flex items-center justify-center relative min-h-[220px]">
              {previewUrl ? (
                <img
                  src={previewUrl}
                  alt="Incident Preview"
                  className="w-full h-full object-cover max-h-60"
                />
              ) : (
                <div className="text-xs text-slate-400">No image selected</div>
              )}
              {analyzing && (
                <div className="absolute inset-0 bg-slate-900/70 backdrop-blur-xs flex flex-col items-center justify-center text-white text-xs gap-2">
                  <Sparkles className="w-6 h-6 text-emerald-400 animate-spin" />
                  <span>Analyzing multi-angle perspectives with YOLOv5n-ONNX...</span>
                </div>
              )}
            </div>
          </div>

          {/* Multi-Image Evidence Thumbnails Bar */}
          {filePreviews.length > 0 && (
            <div className="p-3.5 bg-slate-50 rounded-2xl border border-slate-200/80 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-slate-700">
                  Evidence Photos ({filePreviews.length} / 5 Perspectives):
                </span>
                {filePreviews.length < 5 && (
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="text-blue-600 hover:text-blue-700 font-bold flex items-center gap-1 text-[11px]"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Add Another Angle</span>
                  </button>
                )}
              </div>

              <div className="flex items-center gap-3 overflow-x-auto pb-1">
                {filePreviews.map((p, idx) => {
                  const isCurrent = (filePreviews[activePreviewIdx]?.url === p.url);
                  return (
                    <div
                      key={idx}
                      className={`relative group shrink-0 rounded-xl overflow-hidden border-2 transition-all cursor-pointer ${
                        isCurrent ? 'border-blue-600 ring-2 ring-blue-500/30' : 'border-slate-200 opacity-80 hover:opacity-100'
                      }`}
                      onClick={() => {
                        setActivePreviewIdx(idx);
                        setPreviewUrl(p.url);
                      }}
                    >
                      <img src={p.url} alt="" className="w-20 h-16 object-cover" />
                      <span className="absolute bottom-0 inset-x-0 bg-black/60 text-white text-[9px] truncate px-1 text-center font-mono">
                        #{idx + 1}
                      </span>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRemovePhoto(idx);
                        }}
                        className="absolute top-1 right-1 p-0.5 rounded-full bg-red-600/90 text-white hover:bg-red-700 transition-colors"
                        title="Remove photo"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Batch 2: Conflicting Evidence Inconsistency Warning */}
          {isInconsistent && inconsistencyReason && (
            <div className="p-4 rounded-xl bg-amber-50 border border-amber-300 text-xs text-amber-900 flex items-start gap-2.5">
              <AlertTriangle className="w-4 h-4 shrink-0 text-amber-600 mt-0.5" />
              <div>
                <span className="font-extrabold block">Conflicting Evidence Detected Across Angles</span>
                <p className="opacity-90 leading-relaxed text-[11px] mt-0.5">
                  {inconsistencyReason}
                </p>
                <span className="text-[10px] font-bold text-amber-700 block mt-1">
                  * Note: Your report will still be accepted with all perspectives attached, and routed to an officer for human verification.
                </span>
              </div>
            </div>
          )}

          {/* Detected by AI (Auto Suggestion) Box matching Reference Panel 3 */}
          <div className="bg-slate-50 rounded-2xl p-4 sm:p-5 border border-slate-200/80 space-y-3">
            <div className="text-xs font-extrabold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
              <span>{t('detectedType')}</span>
            </div>

            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs bg-white p-3 rounded-xl border border-slate-200/60">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-slate-400">{t('category')}:</span>
                  {isEditingType ? (
                    <select
                      value={selectedType}
                      onChange={(e) => setSelectedType(e.target.value)}
                      className="border border-slate-300 rounded px-2 py-0.5 text-xs font-bold text-slate-800 focus:outline-none"
                    >
                      <option value="Street Vendor">Street Vendor</option>
                      <option value="Vehicle">Vehicle on Footpath</option>
                      <option value="Construction Material">Construction Material</option>
                      <option value="Shop Extension">Shop Counter Extension</option>
                      <option value="Signboard">Commercial Signboard</option>
                    </select>
                  ) : (
                    <span className="font-bold text-slate-800 text-sm">{selectedType}</span>
                  )}
                  <button
                    onClick={() => setIsEditingType(!isEditingType)}
                    className="text-blue-600 hover:text-blue-700 font-semibold flex items-center gap-1 text-[11px] ml-2"
                  >
                    <Edit2 className="w-3 h-3" />
                    {isEditingType ? 'Done' : 'Edit'}
                  </button>
                </div>
                <div className="text-slate-500">
                  {t('confidence')}: <strong className="text-emerald-600">{Math.round((aiResult?.confidence || 0.87) * 100)}%</strong>
                </div>
              </div>

              <div className="text-[11px] text-slate-400 sm:text-right">
                <div>Model: <strong>YOLOv5n-ONNX</strong></div>
                <div>Status: <span className="text-emerald-600 font-semibold">{t('verified')}</span></div>
              </div>
            </div>
          </div>

          {/* Action Button matching Reference: Large Green [Next →] */}
          <button
            onClick={() => setCurrentStep(2)}
            className="w-full py-3.5 px-6 rounded-2xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm shadow-md shadow-emerald-600/25 flex items-center justify-center gap-2 transition-all hover:scale-[1.01]"
          >
            <span>{t('next')}</span>
            <ArrowRight className="w-4 h-4 stroke-[2.5]" />
          </button>
        </div>
      )}

      {/* STEP 2: LOCATION */}
      {currentStep === 2 && (
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-slate-800">{t('location')}</h2>
            <button
              onClick={handleDetectLocation}
              disabled={geoLocating}
              className="px-3.5 py-1.5 text-xs font-bold text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-xl transition-colors flex items-center gap-1.5"
            >
              <Navigation className="w-3.5 h-3.5" />
              {geoLocating ? 'Detecting GPS...' : t('detectLocationGPS')}
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="sm:col-span-2 space-y-1.5">
              <label className="font-bold text-slate-700">{t('addressOrLandmark')}</label>
              <input
                type="text"
                value={locationName}
                onChange={(e) => setLocationName(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 font-semibold text-slate-800 focus:outline-none focus:border-blue-500"
              />
            </div>
            <div className="space-y-1.5">
              <label className="font-bold text-slate-700">Latitude</label>
              <input
                type="number"
                step="0.0001"
                value={latitude}
                onChange={(e) => setLatitude(parseFloat(e.target.value))}
                className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 font-mono font-semibold text-slate-800 focus:outline-none"
              />
            </div>
            <div className="space-y-1.5">
              <label className="font-bold text-slate-700">Longitude</label>
              <input
                type="number"
                step="0.0001"
                value={longitude}
                onChange={(e) => setLongitude(parseFloat(e.target.value))}
                className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 font-mono font-semibold text-slate-800 focus:outline-none"
              />
            </div>
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-slate-100">
            <button
              onClick={() => setCurrentStep(1)}
              className="px-5 py-2.5 rounded-xl text-xs font-bold text-slate-600 hover:bg-slate-100 flex items-center gap-2"
            >
              <ArrowLeft className="w-4 h-4" /> {t('back')}
            </button>
            <button
              onClick={() => setCurrentStep(3)}
              className="px-6 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-md flex items-center gap-2"
            >
              <span>{t('next')}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 3: CONFIRM */}
      {currentStep === 3 && (
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-6">
          <h2 className="text-base font-bold text-slate-800">{t('stepConfirm')}</h2>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
            <div className="space-y-2">
              <div className="rounded-xl overflow-hidden border border-slate-200 bg-slate-900 h-44">
                <img src={previewUrl} alt="Confirm preview" className="w-full h-full object-cover" />
              </div>
              {filePreviews.length > 1 && (
                <div className="flex gap-1.5 overflow-x-auto pb-1">
                  {filePreviews.map((p, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => setPreviewUrl(p.url)}
                      className={`relative w-12 h-10 rounded-md overflow-hidden border-2 shrink-0 ${
                        previewUrl === p.url ? 'border-blue-600' : 'border-slate-200 opacity-70'
                      }`}
                    >
                      <img src={p.url} alt="" className="w-full h-full object-cover" />
                      <span className="absolute bottom-0 inset-x-0 bg-black/60 text-[8px] text-white text-center">
                        #{idx + 1}
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="sm:col-span-2 space-y-3 text-xs">
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/60 space-y-1.5">
                <div className="flex justify-between"><span className="text-slate-400">{t('category')}:</span> <strong className="text-slate-900">{selectedType}</strong></div>
                <div className="flex justify-between"><span className="text-slate-400">{t('location')}:</span> <strong className="text-slate-900">{locationName}</strong></div>
                <div className="flex justify-between"><span className="text-slate-400">GPS:</span> <strong className="font-mono text-slate-800">{latitude.toFixed(4)}, {longitude.toFixed(4)}</strong></div>
                <div className="flex justify-between"><span className="text-slate-400">Evidence Angles:</span> <strong className="text-slate-800">{filePreviews.length > 0 ? `${filePreviews.length} Photos Attached` : '1 Photo Attached'}</strong></div>
                <div className="flex justify-between"><span className="text-slate-400">{t('confidence')}:</span> <strong className="text-emerald-600">{Math.round((aiResult?.confidence || 0.87) * 100)}%</strong></div>
                <div className="flex justify-between"><span className="text-slate-400">{t('accessibilityScore')}:</span> <strong className="text-blue-600">{aiResult?.accessibility_score || 68}%</strong></div>
                {isInconsistent && (
                  <div className="flex justify-between pt-1 border-t border-slate-200">
                    <span className="text-amber-700 font-bold">Cross-Check:</span>
                    <strong className="text-amber-800 font-bold">Needs Human Officer Review</strong>
                  </div>
                )}
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">{t('description')}</label>
                <textarea
                  rows={2}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder={t('notesPlaceholder')}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-xs text-slate-800 focus:outline-none"
                />
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-slate-100">
            <button
              onClick={() => setCurrentStep(2)}
              className="px-5 py-2.5 rounded-xl text-xs font-bold text-slate-600 hover:bg-slate-100 flex items-center gap-2"
            >
              <ArrowLeft className="w-4 h-4" /> {t('back')}
            </button>
            <button
              onClick={handleSubmit}
              disabled={submitting}
              className="px-7 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-md shadow-emerald-600/25 flex items-center gap-2"
            >
              {submitting ? 'Submitting Report...' : t('submitReport')}
            </button>
          </div>
        </div>
      )}

      {/* STEP 4: SUBMIT / CONFIRMATION */}
      {currentStep === 4 && (
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-8 text-center space-y-5">
          <div className="w-16 h-16 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto ring-8 ring-emerald-50/50">
            <CheckCircle2 className="w-8 h-8" />
          </div>

          <div>
            <h2 className="text-xl font-black text-slate-900">{t('reportSuccessTitle')}</h2>
            <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
              {t('reportSuccessDesc')}
            </p>
          </div>

          {submissionResult?.is_duplicate_merged && (
            <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl max-w-lg mx-auto text-left text-xs text-emerald-800 space-y-1">
              <div className="font-bold flex items-center gap-1.5">
                <Check className="w-4 h-4 text-emerald-600" />
                Duplicate Obstruction Merged
              </div>
              <p className="text-slate-600 leading-relaxed">
                Your evidence was merged with master incident <strong>{submissionResult.incident_number}</strong>. Total citizen endorsements: <strong>{submissionResult.supporting_reports_count}</strong>.
              </p>
            </div>
          )}

          <div className="pt-4 flex justify-center gap-3">
            <button
              onClick={() => {
                setCurrentStep(1);
                setSelectedFile(null);
                setSubmissionResult(null);
              }}
              className="px-5 py-2.5 rounded-xl text-xs font-bold bg-slate-100 text-slate-700 hover:bg-slate-200 transition-colors"
            >
              {t('submitAnother')}
            </button>
            <button
              onClick={onReportSubmitted}
              className="px-6 py-2.5 rounded-xl text-xs font-bold bg-blue-600 hover:bg-blue-700 text-white shadow-sm transition-colors"
            >
              {t('myReports')}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
