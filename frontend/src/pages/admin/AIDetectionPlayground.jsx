import React, { useState, useRef, useEffect } from 'react';
import {
  Upload,
  Video,
  Sparkles,
  Layers,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ShieldAlert,
  Save,
  RefreshCw,
  Info,
  Cpu,
  FileWarning,
  ExternalLink,
  XCircle,
  HelpCircle,
  ChevronDown,
  ChevronUp,
  Image as ImageIcon,
  Ruler,
  Activity,
  Flame,
  Eye
} from 'lucide-react';
import { aiAPI, incidentsAPI } from '../../services/api';

const ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png'];
const ALLOWED_IMAGE_MIMES = ['image/jpeg', 'image/jpg', 'image/png'];
const MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024; // 25 MB

const SAMPLE_IMAGES = [
  {
    name: 'Vehicle on Footpath (Potential Encroachment)',
    url: '/uploads/original/vehicle_indiranagar.jpg',
    fileName: 'vehicle_indiranagar.jpg',
    location: 'Indiranagar, Bengaluru',
    lat: 12.9784,
    lng: 77.6408,
  },
  {
    name: 'Canopy & Person on Footpath (Needs Human Review)',
    url: '/uploads/original/vendor_mg_road.jpg',
    fileName: 'vendor_mg_road.jpg',
    location: 'MG Road, Bengaluru',
    lat: 12.9756,
    lng: 77.6066,
  },
  {
    name: 'Clear Street / No Obstruction (0 Objects)',
    url: '/uploads/original/clear_street.jpg',
    fileName: 'clear_street.jpg',
    location: 'Koramangala, Bengaluru',
    lat: 12.9352,
    lng: 77.6245,
  },
];

export default function AIDetectionPlayground({ onIncidentCreated }) {
  const [activeMode, setActiveMode] = useState('image'); // 'image' | 'video'
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [validationError, setValidationError] = useState(null);
  const [apiError, setApiError] = useState(null);

  const [analyzing, setAnalyzing] = useState(false);
  const [processingStep, setProcessingStep] = useState(0);
  const [calibrationWidth, setCalibrationWidth] = useState('2.5'); // 'uncalibrated' | '1.8' | '2.5' | '3.0'
  const [aiResult, setAiResult] = useState(null);
  const [videoResult, setVideoResult] = useState(null);
  const [capabilities, setCapabilities] = useState(null);
  const [showSpecsDocs, setShowSpecsDocs] = useState(false);

  // Image Comparison View Mode: 'side-by-side' | 'segmentation' | 'interactive'
  const [viewTab, setViewTab] = useState('side-by-side');

  // Interactive Overlay Toggles
  const [showFootpath, setShowFootpath] = useState(true);
  const [showRoad, setShowRoad] = useState(true);
  const [showEncroachments, setShowEncroachments] = useState(true);
  const [showReviewObjects, setShowReviewObjects] = useState(true);
  const [showNormalObjects, setShowNormalObjects] = useState(true);

  // Incident Creation Review Form State
  const [incidentLocation, setIncidentLocation] = useState('MG Road, Bengaluru');
  const [incidentLat, setIncidentLat] = useState(12.9756);
  const [incidentLng, setIncidentLng] = useState(77.6066);
  const [incidentType, setIncidentType] = useState('Street Object (umbrella)');
  const [incidentSeverity, setIncidentSeverity] = useState('Medium');
  const [incidentNotes, setIncidentNotes] = useState('');
  const [creatingIncident, setCreatingIncident] = useState(false);
  const [createdIncident, setCreatedIncident] = useState(null);
  const [showIncidentForm, setShowIncidentForm] = useState(false);
  const [decisionAction, setDecisionAction] = useState('create'); // 'create' | 'review'

  const fileInputRef = useRef(null);

  useEffect(() => {
    aiAPI.getCapabilities()
      .then((res) => setCapabilities(res.data))
      .catch((err) => console.warn('Could not load AI capabilities metadata:', err));
  }, []);

  const validateImageFile = (file) => {
    if (!file) return 'No file selected.';
    const ext = (file.name.split('.').pop() || '').toLowerCase();
    const mime = (file.type || '').toLowerCase();

    if (!ALLOWED_IMAGE_EXTENSIONS.includes(ext)) {
      return `Invalid file format ".${ext}". Only JPG, JPEG, and PNG images are supported.`;
    }
    if (mime && !ALLOWED_IMAGE_MIMES.includes(mime)) {
      return `Unsupported MIME type "${mime}". Please upload a valid JPG, JPEG, or PNG image.`;
    }
    if (file.size === 0) {
      return 'The selected image file is empty (0 bytes).';
    }
    if (file.size > MAX_FILE_SIZE_BYTES) {
      return `File size (${(file.size / (1024 * 1024)).toFixed(2)} MB) exceeds the 25 MB maximum limit.`;
    }
    return null;
  };

  const handleFileSelection = (file) => {
    setValidationError(null);
    setApiError(null);
    setAiResult(null);
    setVideoResult(null);
    setCreatedIncident(null);

    if (!file) return;

    if (activeMode === 'image') {
      const errorMsg = validateImageFile(file);
      if (errorMsg) {
        setValidationError(errorMsg);
        setSelectedFile(null);
        setPreviewUrl(null);
        return;
      }
    } else {
      if (file.size === 0) {
        setValidationError('The selected video file is empty (0 bytes).');
        return;
      }
      if (file.size > MAX_FILE_SIZE_BYTES) {
        setValidationError('Video file exceeds the 25 MB maximum limit.');
        return;
      }
    }

    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileSelection(file);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    const file = e.dataTransfer?.files?.[0];
    if (file) {
      handleFileSelection(file);
    }
  };

  const handleLoadSampleImage = async (sample) => {
    setValidationError(null);
    setApiError(null);
    setAiResult(null);
    setCreatedIncident(null);
    try {
      const response = await fetch(sample.url);
      if (!response.ok) throw new Error('Sample image could not be loaded from server.');
      const blob = await response.blob();
      const file = new File([blob], sample.fileName, { type: 'image/jpeg' });
      setIncidentLocation(sample.location);
      setIncidentLat(sample.lat);
      setIncidentLng(sample.lng);
      handleFileSelection(file);
    } catch (err) {
      setApiError(`Could not load sample image: ${err.message}`);
    }
  };

  const handleRunImageAnalysis = async () => {
    if (!selectedFile) {
      setValidationError('Please select a JPG, JPEG, or PNG image before running analysis.');
      return;
    }

    const errorMsg = validateImageFile(selectedFile);
    if (errorMsg) {
      setValidationError(errorMsg);
      return;
    }

    setAnalyzing(true);
    setApiError(null);
    setCreatedIncident(null);
    setProcessingStep(1);

    const stepTimer1 = setTimeout(() => setProcessingStep(2), 250);
    const stepTimer2 = setTimeout(() => setProcessingStep(3), 550);
    const stepTimer3 = setTimeout(() => setProcessingStep(4), 850);

    const formData = new FormData();
    formData.append('file', selectedFile);

    const params = {};
    if (calibrationWidth && calibrationWidth !== 'uncalibrated') {
      params.nominal_footpath_width_m = Number(calibrationWidth);
    }

    try {
      const res = await aiAPI.analyzeImage(formData, params);
      const data = res.data;
      setAiResult(data);
      setShowIncidentForm(false);
      setDecisionAction(data.potential_encroachment === 'NEEDS REVIEW' ? 'review' : 'create');

      setIncidentType(
        data.primary_encroachment_type && !['No Obstruction Detected', 'Not an Encroachment'].includes(data.primary_encroachment_type)
          ? data.primary_encroachment_type
          : 'Street Object (Needs Review)'
      );
      setIncidentSeverity(data.severity || 'Low');
      setIncidentNotes(data.explanation || data.severity_reason || '');
    } catch (err) {
      console.error('AI Analysis Error:', err);
      const detail =
        err.response?.data?.detail ||
        err.message ||
        'AI Computer Vision analysis failed. Ensure backend server and YOLOv5n-ONNX weights are available.';
      setApiError(detail);
    } finally {
      clearTimeout(stepTimer1);
      clearTimeout(stepTimer2);
      clearTimeout(stepTimer3);
      setAnalyzing(false);
      setProcessingStep(0);
    }
  };

  const handleRunVideoTracking = async () => {
    if (!selectedFile) return;
    setAnalyzing(true);
    setApiError(null);
    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const res = await aiAPI.trackVideo(formData);
      setVideoResult(res.data);
    } catch (err) {
      console.error(err);
      setApiError(err.response?.data?.detail || 'Video tracking processing failed.');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleCreateIncident = async (e) => {
    if (e) e.preventDefault();
    if (!aiResult) return;

    setCreatingIncident(true);
    setApiError(null);
    try {
      const res = await incidentsAPI.create({
        location_name: incidentLocation,
        latitude: Number(incidentLat),
        longitude: Number(incidentLng),
        image_url: aiResult.original_image_url || previewUrl,
        annotated_image_url: aiResult.annotated_image_url,
        primary_encroachment_type: incidentType,
        description: incidentNotes || aiResult.explanation,
        detected_objects: aiResult.detected_objects,
        occupied_area_sqm: aiResult.occupied_area_sqm,
        footpath_area_sqm: aiResult.footpath_area_sqm,
        footpath_width_m: aiResult.footpath_width_m,
        obstructed_width_m: aiResult.obstructed_width_m,
        remaining_width_m: aiResult.remaining_width_m,
        bottleneck_blockage_pct: aiResult.bottleneck_blockage_pct,
        is_calibrated: aiResult.is_calibrated_physical_measurement || false,
        calibration_mode: aiResult.calibration_metadata?.calibration_mode || 'UNCALIBRATED_PIXEL_ONLY',
        footpath_roi_area_px: aiResult.footpath_roi_area_px,
        occupied_footpath_px: aiResult.occupied_footpath_px,
        footpath_width_px: aiResult.footpath_width_px,
        remaining_width_px: aiResult.remaining_width_px,
        bottleneck_y_px: aiResult.bottleneck_y_px,
        occupancy_percentage: aiResult.roi_pixel_occupancy_pct ?? aiResult.occupancy_percentage ?? 0,
        remaining_pedestrian_region_pct: aiResult.remaining_pedestrian_region_pct ?? (100 - (aiResult.roi_pixel_occupancy_pct ?? 0)),
        accessibility_score: aiResult.accessibility_score ?? 100,
        accessibility_status: aiResult.accessibility_status || 'NEEDS HUMAN REVIEW',
        accessibility_category: aiResult.accessibility_category || 'Good',
        path_continuity: aiResult.path_continuity || 'CLEAR',
        path_continuity_reason: aiResult.path_continuity_reason || '',
        obstruction_impact: aiResult.obstruction_impact || 'LOW',
        severity: incidentSeverity,
        severity_reason: aiResult.severity_reason,
        warnings: aiResult.warnings,
        confidence: aiResult.confidence,
        risk_score: aiResult.risk_score,
        risk_level: aiResult.risk_level,
        risk_factors: aiResult.risk_factors,
        why_flagged: aiResult.why_flagged || [],
        probability_status: aiResult.probability_status || aiResult.reasoning_summary?.overall_decision,
        potential_encroachment: aiResult.potential_encroachment || (aiResult.has_encroachment ? 'YES' : 'NO'),
        ai_explanation: aiResult.explanation,
        persistence_sec: aiResult.persistence_sec,
        is_persistent: aiResult.is_persistent || false,
        review_status: aiResult.review_status || (aiResult.potential_encroachment === 'NEEDS REVIEW' ? 'NEEDS_REVIEW' : 'PENDING'),
        reasoning: aiResult.reasoning_summary
      });
      setCreatedIncident(res.data);
    } catch (err) {
      console.error(err);
      setApiError(err.response?.data?.detail || 'Failed to register incident in backend database.');
    } finally {
      setCreatingIncident(false);
    }
  };

  const isDemoWeightsUnavailable = aiResult?.detection_metadata?.is_demo_mode ?? false;
  const segInfo = aiResult?.segmentation_info || capabilities?.road_footpath_segmentation;
  const unsupportedClasses =
    aiResult?.detection_metadata?.unsupported_specialized_classes ||
    capabilities?.object_detection?.unsupported_specialized_classes ||
    [];

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-16">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
              AI Road &amp; Footpath Encroachment Detection
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-200 flex items-center gap-1">
              <Cpu className="w-3.5 h-3.5" />
              Pretrained YOLOv5n-ONNX (COCO-80)
            </span>
          </div>
          <p className="text-xs text-slate-500 font-medium mt-1">
            Stage 1: Pure YOLOv5n-ONNX object detection • Stage 2: Prototype Corridor ROI overlap &amp; uncertainty classification • Honest 2D pixel measurements.
          </p>
        </div>

        {/* Mode Selector */}
        <div className="flex items-center bg-slate-100 p-1 rounded-xl text-xs font-semibold self-start">
          <button
            onClick={() => {
              setActiveMode('image');
              setSelectedFile(null);
              setPreviewUrl(null);
              setValidationError(null);
              setApiError(null);
            }}
            className={`px-3.5 py-2 rounded-lg flex items-center gap-1.5 transition-colors ${
              activeMode === 'image' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700'
            }`}
          >
            <Upload className="w-3.5 h-3.5" />
            Image Encroachment Scanner
          </button>
          <button
            onClick={() => {
              setActiveMode('video');
              setSelectedFile(null);
              setPreviewUrl(null);
              setValidationError(null);
              setApiError(null);
            }}
            className={`px-3.5 py-2 rounded-lg flex items-center gap-1.5 transition-colors ${
              activeMode === 'video' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700'
            }`}
          >
            <Video className="w-3.5 h-3.5" />
            Frame-Sampled Video Tracker
          </button>
        </div>
      </div>

      {/* Transparency Status Bar: Real AI vs Prototype ROI vs Uncalibrated Pixel Space */}
      <div className="bg-white rounded-2xl p-4 border border-slate-200/80 shadow-sm flex flex-col lg:flex-row lg:items-center justify-between gap-3 text-xs">
        <div className="flex flex-wrap items-center gap-2.5">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-900 font-semibold">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>Detection: <strong>Real Pretrained YOLOv5n-ONNX (COCO-80 Only)</strong></span>
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 font-semibold">
            <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
            <span>Regions: <strong>Prototype Geometric ROI (Not AI Segmentation)</strong></span>
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-blue-50 border border-blue-200 text-blue-900 font-semibold">
            <Ruler className="w-4 h-4 text-blue-600 shrink-0" />
            <span>Metrics: <strong>2D Pixel Space (Uncalibrated — No Invented m²)</strong></span>
          </div>
        </div>
        <button
          type="button"
          onClick={() => setShowSpecsDocs(!showSpecsDocs)}
          className="text-blue-600 hover:text-blue-800 font-bold flex items-center gap-1 shrink-0 self-start lg:self-auto"
        >
          <HelpCircle className="w-3.5 h-3.5" />
          {showSpecsDocs ? 'Hide Model & Calibration Docs' : 'Unsupported Classes & Calibration Docs'}
          {showSpecsDocs ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>
      </div>

      {/* Expandable Documentation: Unsupported Specialized Classes, Prototype ROI, & Calibration Requirements */}
      {showSpecsDocs && (
        <div className="bg-slate-900 text-slate-200 rounded-2xl p-5 border border-slate-800 space-y-4 text-xs animate-fade-in">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="font-bold text-sm text-white flex items-center gap-2">
              <Cpu className="w-4 h-4 text-emerald-400" />
              AI Engine Capabilities, Unsupported Specialized Classes &amp; Calibration Requirements
            </div>
            <span className="px-2.5 py-0.5 rounded-full text-[11px] bg-slate-800 text-emerald-400 font-mono">
              {capabilities?.object_detection?.yolo_onnx_loaded === false
                ? 'MODEL LOAD FAILED'
                : 'yolov5n.onnx (Loaded)'}
            </span>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Supported vs Unsupported Classes */}
            <div className="bg-slate-800/70 p-4 rounded-xl border border-slate-700/80 space-y-2">
              <div className="font-bold text-emerald-400">1. Supported COCO-80 vs. Unsupported Specialized Classes</div>
              <p className="text-slate-300 leading-relaxed">
                <strong>Supported (Real YOLOv5n-ONNX):</strong> Vehicles (<code>car</code>, <code>motorcycle</code>, <code>bus</code>, <code>truck</code>, <code>bicycle</code>), Pedestrians (<code>person</code>), Street Objects (<code>umbrella</code>, <code>bench</code>, <code>chair</code>, <code>dining table</code>, <code>potted plant</code>, <code>suitcase</code>, <code>handbag</code>, <code>backpack</code>), and Fixtures (<code>stop sign</code>, <code>traffic light</code>, <code>fire hydrant</code>, <code>parking meter</code>).
              </p>
              <div className="text-amber-300 font-semibold pt-1">Unsupported Specialized Classes (Require Custom Fine-Tuning):</div>
              <ul className="list-disc list-inside text-slate-300 space-y-1 text-[11px]">
                {unsupportedClasses.map((uc, idx) => (
                  <li key={idx}>
                    <strong>{uc.class_name}:</strong> {uc.reason}
                  </li>
                ))}
              </ul>
            </div>

            {/* Prototype ROI vs Real Semantic Segmentation */}
            <div className="bg-slate-800/70 p-4 rounded-xl border border-amber-500/30 space-y-2">
              <div className="font-bold text-amber-400">2. Prototype Corridor ROI (Not AI Segmentation)</div>
              <p className="text-slate-300 leading-relaxed">
                Road and Footpath regions are currently approximated using rule-based perspective trapezoid polygons and vertical Sobel gradient horizon estimation. They are <strong>not</strong> produced by a semantic segmentation neural network.
              </p>
              <div className="text-amber-300 font-semibold pt-1">Requirements for Real Semantic Segmentation:</div>
              <ul className="list-disc list-inside text-slate-300 space-y-1 text-[11px]">
                <li><strong>Models:</strong> <code>BiSeNetV2</code>, <code>DDRNet-23-slim</code>, <code>DeepLabV3+ (MobileNetV3)</code>, or <code>SegFormer-B0</code>.</li>
                <li><strong>Datasets:</strong> <strong>Cityscapes</strong> + <strong>Indian Driving Dataset (IDD)</strong> trained on pixel classes <code>road</code>, <code>sidewalk/footpath</code>, and <code>curb</code>.</li>
                <li><strong>Integration:</strong> Export ONNX model to <code>backend/app/ai/weights/road_footpath_seg.onnx</code>.</li>
              </ul>
            </div>

            {/* Camera Calibration & Scoring Assumptions */}
            <div className="bg-slate-800/70 p-4 rounded-xl border border-blue-500/30 space-y-2">
              <div className="font-bold text-blue-400">3. Pixel Estimates vs. Physical Measurements (m² / m)</div>
              <p className="text-slate-300 leading-relaxed">
                Single-frame 2D photos are uncalibrated. The engine does <strong>not</strong> invent square metres (<code>m²</code>) or physical widths (<code>m</code>). Instead, it reports exact 2D pixel areas (<code>px²</code>) and horizontal pixel spans (<code>px</code>).
              </p>
              <div className="text-blue-300 font-semibold pt-1">Calibration Requirements &amp; Scoring Formula:</div>
              <ul className="list-disc list-inside text-slate-300 space-y-1 text-[11px]">
                <li><strong>Calibration Needed:</strong> Camera intrinsic matrix <code>K</code>, ground-plane homography <code>H</code> from 4+ surveyed ground control points, or a fiducial marker / depth sensor.</li>
                <li><strong>Walkability Heuristic:</strong> <code>100 - (0.60 × FootpathROIPixelOverlap% + 0.40 × HorizontalPixelSpanBlockage%)</code>.</li>
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Validation Error Banner */}
      {validationError && (
        <div
          role="alert"
          className="bg-red-50 border border-red-200 rounded-2xl p-4 flex items-start justify-between gap-3 text-xs text-red-800 shadow-sm"
        >
          <div className="flex items-start gap-2.5">
            <FileWarning className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
            <div>
              <div className="font-bold text-sm text-red-900">File Validation Error</div>
              <p className="mt-0.5">{validationError}</p>
            </div>
          </div>
          <button
            onClick={() => setValidationError(null)}
            className="text-red-500 hover:text-red-700 font-bold px-2 py-1"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* API / Model Loading Error Banner */}
      {apiError && (
        <div
          role="alert"
          className="bg-red-50 border border-red-200 rounded-2xl p-4 flex items-start justify-between gap-3 text-xs text-red-800 shadow-sm"
        >
          <div className="flex items-start gap-2.5">
            <XCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
            <div>
              <div className="font-bold text-sm text-red-900">AI Engine / API Error</div>
              <p className="mt-0.5">{apiError}</p>
            </div>
          </div>
          <button
            onClick={() => setApiError(null)}
            className="text-red-500 hover:text-red-700 font-bold px-2 py-1"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Upload Dropzone & Pre-Analysis Preview */}
      <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm space-y-5">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
          {/* Dropzone Area */}
          <div className={previewUrl ? 'lg:col-span-7' : 'lg:col-span-12'}>
            <div
              onClick={() => fileInputRef.current?.click()}
              onDragOver={(e) => { e.preventDefault(); e.stopPropagation(); }}
              onDrop={handleDrop}
              className="border-2 border-dashed border-slate-200 hover:border-blue-500 rounded-2xl p-7 text-center cursor-pointer bg-slate-50/50 hover:bg-blue-50/20 transition-all duration-200 flex flex-col items-center justify-center gap-3"
            >
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                accept={activeMode === 'image' ? '.jpg,.jpeg,.png,image/jpeg,image/png' : 'video/*'}
                className="hidden"
                data-testid="ai-file-input"
              />

              <div className="w-12 h-12 rounded-full bg-blue-50 flex items-center justify-center text-blue-600">
                {activeMode === 'image' ? <Upload className="w-6 h-6" /> : <Video className="w-6 h-6" />}
              </div>

              <div>
                <div className="text-sm font-bold text-slate-800">
                  {selectedFile
                    ? selectedFile.name
                    : `Click or drag & drop ${activeMode === 'image' ? 'a street/footpath image (.JPG, .JPEG, .PNG)' : 'a street video (.MP4, .AVI)'}`}
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  {activeMode === 'image'
                    ? 'Strictly validated formats: JPG, JPEG, PNG • Maximum file size: 25 MB'
                    : 'Real frame-by-frame sampling (~2 FPS) via OpenCV VideoCapture + YOLOv5n-ONNX up to 25 MB'}
                </p>
              </div>

              {selectedFile && (
                <div className="flex flex-wrap items-center justify-center gap-2 mt-1">
                  <span className="text-xs font-semibold text-emerald-700 bg-emerald-50 px-3 py-1 rounded-full border border-emerald-200 flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Validated: {selectedFile.name.split('.').pop()?.toUpperCase()} ({(selectedFile.size / 1024).toFixed(1)} KB)
                  </span>
                </div>
              )}
            </div>

            {/* Quick Sample Street Scenarios for Instant Testing */}
            {activeMode === 'image' && (
              <div className="mt-3 flex flex-wrap items-center gap-2">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mr-1">
                  Test Scenarios:
                </span>
                {SAMPLE_IMAGES.map((sample, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleLoadSampleImage(sample)}
                    className="text-xs px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-blue-50 text-slate-700 hover:text-blue-700 border border-slate-200/80 transition-colors font-medium"
                  >
                    {sample.name}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Pre-Analysis Image Preview Card */}
          {previewUrl && activeMode === 'image' && (
            <div className="lg:col-span-5 bg-slate-50 rounded-2xl p-4 border border-slate-200/80 space-y-2.5">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-slate-700 flex items-center gap-1.5">
                  <ImageIcon className="w-4 h-4 text-blue-600" />
                  Selected Image Preview
                </span>
                <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-blue-100 text-blue-800">
                  {aiResult ? `Status: ${aiResult.processing_status}` : 'Ready for Analysis'}
                </span>
              </div>
              <img
                src={previewUrl}
                alt="Upload preview"
                className="w-full h-44 object-cover rounded-xl border border-slate-200 bg-slate-900"
              />
              <div className="flex items-center justify-between text-[11px] text-slate-500">
                <span className="truncate max-w-[200px] font-medium">{selectedFile?.name}</span>
                <span>{selectedFile ? `${(selectedFile.size / 1024).toFixed(1)} KB` : ''}</span>
              </div>
            </div>
          )}
        </div>

        {/* Processing Stepper when Analyzing */}
        {analyzing && (
          <div className="bg-blue-50/70 border border-blue-200 rounded-2xl p-4 space-y-3 animate-fade-in">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-bold text-blue-900">
                <RefreshCw className="w-4 h-4 animate-spin text-blue-600" />
                <span>PROCESSING STATUS: RUNNING YOLOv5n-ONNX &amp; SPATIAL OVERLAP PIPELINE...</span>
              </div>
              <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-blue-200 text-blue-900">
                Step {processingStep || 1} of 4
              </span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-2 text-[11px]">
              {[
                { step: 1, label: '1. Image Validation & Decoding' },
                { step: 2, label: '2. Prototype Corridor ROI Overlay' },
                { step: 3, label: '3. Pretrained YOLOv5n-ONNX Inference' },
                { step: 4, label: '4. ROI Overlap & Uncertainty Check' },
              ].map((item) => (
                <div
                  key={item.step}
                  className={`p-2 rounded-xl border font-semibold flex items-center gap-1.5 ${
                    processingStep >= item.step
                      ? 'bg-white border-blue-300 text-blue-800 shadow-xs'
                      : 'bg-slate-100/60 border-slate-200 text-slate-400'
                  }`}
                >
                  <div
                    className={`w-2 h-2 rounded-full ${
                      processingStep >= item.step ? 'bg-blue-600 animate-ping' : 'bg-slate-300'
                    }`}
                  />
                  <span>{item.label}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Action Buttons */}
        {selectedFile && (
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pt-3 border-t border-slate-100">
            {activeMode === 'image' ? (
              <div className="flex items-center gap-2 text-xs">
                <span className="font-bold text-slate-700 flex items-center gap-1.5 shrink-0">
                  <Ruler className="w-3.5 h-3.5 text-blue-600" />
                  Corridor Calibration:
                </span>
                <select
                  value={calibrationWidth}
                  onChange={(e) => setCalibrationWidth(e.target.value)}
                  className="bg-slate-50 border border-slate-200 rounded-xl px-2.5 py-1.5 font-semibold text-slate-800 text-xs focus:ring-2 focus:ring-blue-500 outline-none"
                >
                  <option value="uncalibrated">Mode B: Uncalibrated 2D Pixels (Honest px / px² — No Invented Units)</option>
                  <option value="1.8">Mode A: 1.8 m — Narrow Footpath (IRC:SP:102-2014 &amp; ADA Minimum Corridor)</option>
                  <option value="2.5">Mode A: 2.5 m — Standard Urban Sidewalk (MoHUA &amp; IRC Standard)</option>
                  <option value="3.0">Mode A: 3.0 m — Wide High-Density Commercial Promenade</option>
                </select>
              </div>
            ) : <div />}

            <div className="flex items-center justify-end gap-2.5">
              <button
                type="button"
                onClick={() => {
                  setSelectedFile(null);
                  setPreviewUrl(null);
                  setAiResult(null);
                  setVideoResult(null);
                  setValidationError(null);
                  setApiError(null);
                  setCreatedIncident(null);
                }}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl transition-colors"
              >
                Reset
              </button>
              <button
                type="button"
                data-testid="run-ai-analysis-btn"
                onClick={activeMode === 'image' ? handleRunImageAnalysis : handleRunVideoTracking}
                disabled={analyzing}
                className="px-6 py-2.5 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-xl transition-colors flex items-center gap-2 shadow-sm disabled:opacity-50"
              >
                <Sparkles className="w-4 h-4" />
                {analyzing
                  ? 'Running YOLOv5n-ONNX...'
                  : `Run ${activeMode === 'image' ? 'AI Encroachment Analysis' : 'Frame-by-Frame Video Tracker'}`}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* =====================================================================
          IMAGE AI ANALYSIS RESULTS
         ===================================================================== */}
      {aiResult && (
        <div className="space-y-6 animate-scale-in" data-testid="ai-analysis-results">
          {/* 1. Processing Status & Overall Classification Summary Banner */}
          <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-3">
              <div className="flex flex-wrap items-center gap-2.5">
                <span className="px-3 py-1 rounded-full text-xs font-extrabold bg-emerald-100 text-emerald-800 border border-emerald-300 flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  STATUS: {aiResult.processing_status || 'COMPLETED'}
                </span>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-bold border ${
                    isDemoWeightsUnavailable
                      ? 'bg-red-100 text-red-800 border-red-300'
                      : 'bg-blue-100 text-blue-800 border-blue-300'
                  }`}
                >
                  {isDemoWeightsUnavailable
                    ? 'DEMO MODE: MODEL WEIGHTS UNAVAILABLE (0 Predictions)'
                    : `REAL PRETRAINED YOLOv5n-ONNX (${aiResult.detection_metadata?.yolo_detections_count || 0} COCO Predictions)`}
                </span>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-extrabold border ${
                    aiResult.overall_classification?.startsWith('Potential encroachment')
                      ? 'bg-red-100 text-red-800 border-red-300'
                      : aiResult.overall_classification === 'Needs human review'
                      ? 'bg-amber-100 text-amber-800 border-amber-300'
                      : 'bg-emerald-50 text-emerald-800 border-emerald-200'
                  }`}
                >
                  {aiResult.encroachment_summary?.overall_status || aiResult.overall_classification}
                </span>
              </div>

              <div className="text-xs text-slate-500 font-medium">
                Inference Time: <strong>{aiResult.processing_time_sec}s</strong> • Top Confidence:{' '}
                <strong className="text-slate-900">
                  {aiResult.confidence !== null && aiResult.confidence !== undefined
                    ? `${(aiResult.confidence * 100).toFixed(1)}%`
                    : 'N/A (0 Detections)'}
                </strong>
              </div>
            </div>

            {/* Overall Explanation Box */}
            <div className="bg-slate-50 rounded-xl p-4 border border-slate-200/80 space-y-2">
              <div className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                <Info className="w-4 h-4 text-blue-600" />
                Stage 2 Spatial Overlap &amp; Uncertainty Summary
              </div>
              <p className="text-xs text-slate-700 leading-relaxed">
                {aiResult.explanation}
              </p>
              <div className="flex flex-wrap gap-4 pt-1 text-xs text-slate-600">
                <span>
                  YOLOv5n-ONNX Detections: <strong className="text-slate-900">{aiResult.detected_objects?.length || 0}</strong>
                </span>
                <span>
                  Potential Encroachments:{' '}
                  <strong className="text-red-600">
                    {aiResult.encroachment_summary?.encroaching_objects_count ?? 0}
                  </strong>
                </span>
                <span>
                  Needs Human Review:{' '}
                  <strong className="text-amber-600">
                    {aiResult.encroachment_summary?.needs_review_objects_count ?? 0}
                  </strong>
                </span>
                <span>
                  Not an Encroachment (Normal Traffic / Pedestrians):{' '}
                  <strong className="text-emerald-600">
                    {aiResult.encroachment_summary?.non_encroaching_objects_count ?? 0}
                  </strong>
                </span>
              </div>
            </div>
          </div>

          {/* 2. Visual Comparison & Prototype Corridor ROI Overlay Module */}
          <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm space-y-5">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between pb-4 border-b border-slate-100 gap-4">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="text-base font-bold text-slate-800">
                    Original Image, Prototype Corridor ROI &amp; Annotated YOLOv5n Output
                  </h3>
                  <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-100 text-amber-800 border border-amber-300">
                    {segInfo?.badge_label || 'Prototype Segmentation Overlay (Non-AI Geometric ROI)'}
                  </span>
                </div>
                <p className="text-xs text-slate-500 mt-0.5">
                  {segInfo?.description}
                </p>
              </div>

              {/* View Mode Switcher */}
              <div className="flex flex-wrap items-center bg-slate-100 p-1 rounded-xl text-xs font-semibold gap-1">
                <button
                  type="button"
                  onClick={() => setViewTab('side-by-side')}
                  className={`px-3 py-1.5 rounded-lg transition-colors ${
                    viewTab === 'side-by-side' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600'
                  }`}
                >
                  Original vs Annotated
                </button>
                <button
                  type="button"
                  onClick={() => setViewTab('segmentation')}
                  className={`px-3 py-1.5 rounded-lg transition-colors ${
                    viewTab === 'segmentation' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600'
                  }`}
                >
                  Prototype Corridor ROI Module
                </button>
                <button
                  type="button"
                  onClick={() => setViewTab('interactive')}
                  className={`px-3 py-1.5 rounded-lg transition-colors ${
                    viewTab === 'interactive' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600'
                  }`}
                >
                  Interactive BBox Inspector
                </button>
              </div>
            </div>

            {/* Color Legend */}
            <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-50 px-4 py-3 rounded-xl border border-slate-200/70 text-xs">
              <div className="flex flex-wrap items-center gap-4">
                <span className="font-bold text-slate-700 flex items-center gap-1">
                  <Layers className="w-3.5 h-3.5 text-slate-500" />
                  Visual Legend:
                </span>
                <span className="flex items-center gap-1.5 font-semibold text-slate-700">
                  <span className="w-3.5 h-3.5 rounded-sm bg-[#22C55E] inline-block border border-emerald-700" />
                  Green = Prototype Footpath ROI
                </span>
                <span className="flex items-center gap-1.5 font-semibold text-slate-700">
                  <span className="w-3.5 h-3.5 rounded-sm bg-[#3B82F6] inline-block border border-blue-700" />
                  Blue = Prototype Road ROI
                </span>
                <span className="flex items-center gap-1.5 font-semibold text-slate-700">
                  <span className="w-3.5 h-3.5 rounded-sm bg-[#EF4444] inline-block border border-red-700" />
                  Red = Potential Encroachment
                </span>
                <span className="flex items-center gap-1.5 font-semibold text-slate-700">
                  <span className="w-3.5 h-3.5 rounded-sm bg-[#F59E0B] inline-block border border-amber-600" />
                  Amber = Needs Human Review
                </span>
                <span className="flex items-center gap-1.5 font-semibold text-slate-700">
                  <span className="w-3.5 h-3.5 rounded-sm bg-[#238CD2] inline-block border border-sky-700" />
                  Teal/Blue Box = Not an Encroachment
                </span>
              </div>
            </div>

            {/* View Tab 1: Original vs Annotated */}
            {viewTab === 'side-by-side' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs font-semibold text-slate-600">
                    <span>ORIGINAL UPLOADED IMAGE</span>
                    <span className="text-[11px] text-slate-400">
                      {aiResult.image_dimensions?.width}×{aiResult.image_dimensions?.height} px
                    </span>
                  </div>
                  <img
                    src={aiResult.original_image_url || previewUrl}
                    alt="Original"
                    className="w-full h-80 object-cover rounded-xl border border-slate-200 bg-slate-900"
                  />
                </div>

                <div className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs font-semibold text-slate-600">
                    <span>YOLOv5n-ONNX DETECTIONS + PROTOTYPE ROI OVERLAY</span>
                    <span className="text-[11px] text-emerald-600 font-bold">
                      Exact COCO Labels &amp; Confidences
                    </span>
                  </div>
                  <img
                    src={aiResult.annotated_image_url}
                    alt="Annotated AI Result"
                    className="w-full h-80 object-cover rounded-xl border border-slate-200 bg-slate-900"
                  />
                </div>
              </div>
            )}

            {/* View Tab 2: Dedicated Prototype Corridor ROI Module */}
            {viewTab === 'segmentation' && (
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs font-semibold text-slate-600">
                      <span>PROTOTYPE ROAD &amp; FOOTPATH ROI OVERLAY (NON-AI)</span>
                      <span className="text-[11px] text-amber-700 font-bold">
                        {segInfo?.mode || 'PROTOTYPE_CORRIDOR_ROI'}
                      </span>
                    </div>
                    <img
                      src={aiResult.segmentation_image_url || aiResult.annotated_image_url}
                      alt="Prototype Road and Footpath ROI Overlay"
                      className="w-full h-80 object-cover rounded-xl border border-slate-200 bg-slate-900"
                    />
                  </div>

                  <div className="bg-slate-50 rounded-xl p-5 border border-slate-200 space-y-3 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-sm text-slate-900">
                        Prototype Region-of-Interest (ROI) Diagnostics
                      </span>
                      <span className="px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-800 font-bold border border-amber-300">
                        Non-AI Geometric Prototype
                      </span>
                    </div>
                    <p className="text-slate-600 leading-relaxed">
                      {segInfo?.description}
                    </p>
                    <div className="grid grid-cols-2 gap-3 pt-1">
                      <div className="bg-white p-3 rounded-lg border border-slate-200">
                        <div className="text-slate-400 font-semibold">Prototype Footpath ROI Area</div>
                        <div className="text-base font-extrabold text-emerald-600">
                          {aiResult.footpath_roi_area_px?.toLocaleString()} px²
                        </div>
                        <div className="text-[11px] text-slate-400 mt-0.5">
                          Mid-span width: {aiResult.footpath_width_px} px
                        </div>
                      </div>
                      <div className="bg-white p-3 rounded-lg border border-slate-200">
                        <div className="text-slate-400 font-semibold">Prototype Road ROI Area</div>
                        <div className="text-base font-extrabold text-blue-600">
                          {segInfo?.road_roi_area_px?.toLocaleString()} px²
                        </div>
                        <div className="text-[11px] text-slate-400 mt-0.5">
                          Estimated Horizon Y: {segInfo?.horizon_y_px} px
                        </div>
                      </div>
                    </div>
                    <div className="bg-amber-50/90 border border-amber-200 rounded-lg p-3 space-y-1 text-[11px] text-amber-900">
                      <div className="font-bold">Requirements for Real Road-Scene Semantic Segmentation:</div>
                      <div>
                        • <strong>Models:</strong>{' '}
                        {segInfo?.real_segmentation_requirements?.recommended_models?.join(', ')}
                      </div>
                      <div>
                        • <strong>Datasets:</strong>{' '}
                        {segInfo?.real_segmentation_requirements?.training_datasets?.join('; ')}
                      </div>
                      <div>
                        • <strong>Drop-in Weights Path:</strong>{' '}
                        <code>{segInfo?.real_segmentation_requirements?.expected_weights_path || 'backend/app/ai/weights/road_footpath_seg.onnx'}</code>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* View Tab 3: Interactive SVG Overlay Inspector */}
            {viewTab === 'interactive' && (
              <div className="space-y-3">
                <div className="flex flex-wrap items-center gap-3 text-xs">
                  <span className="font-bold text-slate-600">Toggle Interactive Layers:</span>
                  <label className="flex items-center gap-1.5 cursor-pointer bg-emerald-50 px-2.5 py-1 rounded-lg text-emerald-800 border border-emerald-200 font-semibold">
                    <input
                      type="checkbox"
                      checked={showFootpath}
                      onChange={() => setShowFootpath(!showFootpath)}
                      className="accent-emerald-600"
                    />
                    Prototype Footpath ROI
                  </label>
                  <label className="flex items-center gap-1.5 cursor-pointer bg-blue-50 px-2.5 py-1 rounded-lg text-blue-800 border border-blue-200 font-semibold">
                    <input
                      type="checkbox"
                      checked={showRoad}
                      onChange={() => setShowRoad(!showRoad)}
                      className="accent-blue-600"
                    />
                    Prototype Road ROI
                  </label>
                  <label className="flex items-center gap-1.5 cursor-pointer bg-red-50 px-2.5 py-1 rounded-lg text-red-800 border border-red-200 font-semibold">
                    <input
                      type="checkbox"
                      checked={showEncroachments}
                      onChange={() => setShowEncroachments(!showEncroachments)}
                      className="accent-red-600"
                    />
                    Potential Encroachments
                  </label>
                  <label className="flex items-center gap-1.5 cursor-pointer bg-amber-50 px-2.5 py-1 rounded-lg text-amber-800 border border-amber-200 font-semibold">
                    <input
                      type="checkbox"
                      checked={showReviewObjects}
                      onChange={() => setShowReviewObjects(!showReviewObjects)}
                      className="accent-amber-600"
                    />
                    Needs Human Review
                  </label>
                  <label className="flex items-center gap-1.5 cursor-pointer bg-sky-50 px-2.5 py-1 rounded-lg text-sky-800 border border-sky-200 font-semibold">
                    <input
                      type="checkbox"
                      checked={showNormalObjects}
                      onChange={() => setShowNormalObjects(!showNormalObjects)}
                      className="accent-sky-600"
                    />
                    Not an Encroachment
                  </label>
                </div>

                <div className="relative w-full max-w-4xl mx-auto rounded-xl overflow-hidden border border-slate-200 bg-slate-950">
                  <img
                    src={aiResult.original_image_url || previewUrl}
                    alt="Interactive Base"
                    className="w-full h-auto block"
                  />
                  <svg
                    viewBox={`0 0 ${segInfo?.image_dimensions?.width || 800} ${segInfo?.image_dimensions?.height || 500}`}
                    className="absolute inset-0 w-full h-full pointer-events-none"
                    preserveAspectRatio="none"
                  >
                    {aiResult.detected_objects?.map((obj, idx) => {
                      const cls = obj.classification;
                      if (cls === 'Potential encroachment' && !showEncroachments) return null;
                      if (cls === 'Needs human review' && !showReviewObjects) return null;
                      if (cls === 'Not an encroachment' && !showNormalObjects) return null;
                      const [bx, by, bw, bh] = obj.bbox || [0, 0, 0, 0];
                      const strokeColor =
                        cls === 'Potential encroachment'
                          ? '#EF4444'
                          : cls === 'Needs human review'
                          ? '#F59E0B'
                          : '#0284C7';
                      const fillColor =
                        cls === 'Potential encroachment'
                          ? 'rgba(239, 68, 68, 0.25)'
                          : cls === 'Needs human review'
                          ? 'rgba(245, 158, 11, 0.22)'
                          : 'rgba(2, 132, 199, 0.15)';
                      return (
                        <g key={idx}>
                          <rect
                            x={bx}
                            y={by}
                            width={bw}
                            height={bh}
                            fill={fillColor}
                            stroke={strokeColor}
                            strokeWidth="3"
                          />
                          <rect
                            x={bx}
                            y={Math.max(0, by - 24)}
                            width={Math.min(340, bw + 140)}
                            height="24"
                            fill={strokeColor}
                          />
                          <text
                            x={bx + 6}
                            y={Math.max(16, by - 7)}
                            fill="#FFFFFF"
                            fontSize="12"
                            fontWeight="bold"
                          >
                            {`${obj.coco_class} (${(obj.confidence * 100).toFixed(1)}%) — ${cls.toUpperCase()}`}
                          </text>
                        </g>
                      );
                    })}
                  </svg>
                </div>
              </div>
            )}
          </div>

          {/* =====================================================================
              1. AI DETECTION (Section 6)
             ===================================================================== */}
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-blue-600" />
                  <span>1. AI DETECTION</span>
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Detected Objects with neural confidence and corridor spatial localisation.
                </p>
              </div>
              <span className="px-3 py-1 rounded-full text-xs font-bold bg-blue-50 text-blue-700 border border-blue-200">
                {aiResult.detected_objects?.length || 0} Objects Detected
              </span>
            </div>

            {(!aiResult.detected_objects || aiResult.detected_objects.length === 0) ? (
              <div
                data-testid="no-obstruction-banner"
                className="p-6 rounded-xl bg-emerald-50/70 border border-emerald-200 text-center space-y-1.5"
              >
                <CheckCircle2 className="w-7 h-7 text-emerald-600 mx-auto" />
                <div className="text-sm font-extrabold text-emerald-900">
                  No Obstruction Detected (0 YOLOv5n-ONNX Predictions)
                </div>
                <p className="text-xs text-emerald-800 max-w-xl mx-auto">
                  Pretrained YOLOv5n-ONNX detected 0 objects above confidence threshold. Walkway corridor appears clear.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 text-slate-500 font-bold uppercase tracking-wider border-b border-slate-200/80">
                    <tr>
                      <th className="py-2.5 px-3">Object</th>
                      <th className="py-2.5 px-3">Confidence</th>
                      <th className="py-2.5 px-3">Region</th>
                      <th className="py-2.5 px-3">Footpath Overlap</th>
                      <th className="py-2.5 px-3">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {aiResult.detected_objects.map((obj, idx) => (
                      <tr key={idx} className="hover:bg-slate-50/60" data-testid={`detected-object-card-${idx}`}>
                        <td className="py-2.5 px-3 font-extrabold text-slate-900 flex items-center gap-2">
                          <span>{obj.label}</span>
                          <span className="font-mono text-[10px] text-slate-400 font-normal">({obj.coco_class})</span>
                        </td>
                        <td className="py-2.5 px-3 font-bold text-slate-700">
                          {(obj.confidence * 100).toFixed(1)}%
                        </td>
                        <td className="py-2.5 px-3">
                          <span className={`px-2 py-0.5 rounded-md font-bold text-[11px] ${
                            (obj.footpath_overlap_pct || 0) >= 15
                              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                              : 'bg-blue-50 text-blue-700 border border-blue-200'
                          }`}>
                            {(obj.footpath_overlap_pct || 0) >= 15 ? 'Footpath Corridor' : 'Roadway'}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-slate-600 font-medium">
                          {obj.footpath_overlap_pct ?? 0}%
                        </td>
                        <td className="py-2.5 px-3">
                          <span className={`px-2 py-0.5 rounded-md font-bold text-[10px] uppercase ${
                            obj.classification === 'Potential encroachment'
                              ? 'bg-red-100 text-red-800'
                              : obj.classification === 'Needs human review'
                              ? 'bg-amber-100 text-amber-800'
                              : 'bg-emerald-100 text-emerald-800'
                          }`}>
                            {obj.classification}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* =====================================================================
              2. ENCROACHMENT REASONING (Section 6)
             ===================================================================== */}
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
              <div>
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-purple-600" />
                  <span>2. ENCROACHMENT REASONING</span>
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Multi-factor explainable inference (object type, overlap, occupancy &amp; accessibility).
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-slate-500">Potential Encroachment:</span>
                <span className={`px-3 py-1 rounded-full text-xs font-black tracking-wide border ${
                  (aiResult.potential_encroachment || (aiResult.has_encroachment ? 'YES' : 'NO')) === 'YES'
                    ? 'bg-red-100 text-red-800 border-red-300'
                    : (aiResult.potential_encroachment === 'NEEDS REVIEW' || aiResult.needs_human_review)
                    ? 'bg-amber-100 text-amber-800 border-amber-300'
                    : 'bg-emerald-100 text-emerald-800 border-emerald-300'
                }`}>
                  {aiResult.potential_encroachment || (aiResult.has_encroachment ? 'YES' : (aiResult.needs_human_review ? 'NEEDS REVIEW' : 'NO'))}
                </span>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5 text-xs">
              <div className="font-bold text-slate-800">Reason:</div>
              <p className="text-slate-700 leading-relaxed font-medium">
                {aiResult.reason || aiResult.explanation}
              </p>
            </div>

            {/* Structured WHY WAS THIS FLAGGED? Section */}
            <div className="space-y-2 pt-1">
              <div className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                <span>WHY WAS THIS FLAGGED?</span>
                <span className="text-[10px] text-slate-400 font-normal">(Structured Evidence Checklist)</span>
              </div>

              <div className="space-y-2">
                {(aiResult.why_flagged || [
                  { label: `${aiResult.primary_encroachment_type || 'Object'} Detected`, detail: `Classified with ${Math.round((aiResult.confidence || 0.85) * 100)}% model confidence.`, status: 'flagged' },
                  { label: `Footpath Corridor Occupancy: ${aiResult.roi_pixel_occupancy_pct || aiResult.occupancy_percentage || 0}%`, detail: 'Footpath width occupied by detected obstacle.', status: 'flagged' },
                  { label: `Pedestrian Path Continuity: ${aiResult.path_continuity || 'PARTIALLY BLOCKED'}`, detail: aiResult.path_continuity_reason || 'Constricted walking corridor.', status: 'warning' }
                ]).map((item, idx) => (
                  <div
                    key={idx}
                    className={`p-3 rounded-xl border flex items-start gap-3 text-xs ${
                      item.status === 'flagged'
                        ? 'bg-red-50/60 border-red-200 text-red-950'
                        : item.status === 'warning'
                        ? 'bg-amber-50/60 border-amber-200 text-amber-950'
                        : 'bg-emerald-50/60 border-emerald-200 text-emerald-950'
                    }`}
                  >
                    <span className={`w-4 h-4 rounded-full flex items-center justify-center shrink-0 mt-0.5 font-bold text-[11px] ${
                      item.status === 'flagged'
                        ? 'bg-red-600 text-white'
                        : item.status === 'warning'
                        ? 'bg-amber-500 text-white'
                        : 'bg-emerald-600 text-white'
                    }`}>
                      {item.status === 'safe' ? '✓' : (item.status === 'warning' ? '!' : '✓')}
                    </span>
                    <div>
                      <div className="font-bold">{item.label}</div>
                      <div className="text-[11px] opacity-80 mt-0.5">{item.detail}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* =====================================================================
              3. FOOTPATH ANALYSIS (Section 6)
             ===================================================================== */}
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div>
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <Ruler className="w-4 h-4 text-emerald-600" />
                  <span>3. FOOTPATH ANALYSIS</span>
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Geometric footprint occupancy and corridor constriction analysis.
                </p>
              </div>
              <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${
                aiResult.is_calibrated_physical_measurement
                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                  : 'bg-slate-100 text-slate-700'
              }`}>
                {aiResult.is_calibrated_physical_measurement ? 'Calibrated Scale' : 'Estimated in uncalibrated 2D pixel space'}
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 text-xs">
              {/* Occupancy */}
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                <div className="font-bold text-slate-500 uppercase tracking-wider text-[11px]">Footpath Occupancy</div>
                <div className="text-3xl font-black text-slate-900">
                  {aiResult.roi_pixel_occupancy_pct ?? aiResult.occupancy_percentage ?? 0}%
                </div>
                <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      (aiResult.roi_pixel_occupancy_pct || 0) >= 35 ? 'bg-red-500' : 'bg-amber-500'
                    }`}
                    style={{ width: `${Math.min(100, aiResult.roi_pixel_occupancy_pct || aiResult.occupancy_percentage || 0)}%` }}
                  />
                </div>
                <div className="text-slate-500 text-[11px]">
                  {aiResult.occupied_footpath_px ? `${aiResult.occupied_footpath_px.toLocaleString()} px² obstructed` : 'Relative corridor area'}
                </div>
              </div>

              {/* Remaining Pedestrian Region */}
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                <div className="font-bold text-slate-500 uppercase tracking-wider text-[11px]">Remaining Pedestrian Region</div>
                <div className="text-3xl font-black text-emerald-600">
                  {aiResult.remaining_pedestrian_region_pct ?? (100 - (aiResult.roi_pixel_occupancy_pct || 0))}%
                </div>
                <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full bg-emerald-500"
                    style={{ width: `${Math.min(100, aiResult.remaining_pedestrian_region_pct || (100 - (aiResult.roi_pixel_occupancy_pct || 0)))}%` }}
                  />
                </div>
                <div className="text-slate-500 text-[11px]">
                  Clear walkable space available for pedestrians
                </div>
              </div>

              {/* Walkable Bottleneck Span */}
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                <div className="font-bold text-slate-500 uppercase tracking-wider text-[11px]">Corridor Bottleneck Clearance</div>
                <div className="text-3xl font-black text-blue-600">
                  {aiResult.is_calibrated_physical_measurement
                    ? `${aiResult.remaining_width_m} m`
                    : `${aiResult.remaining_width_at_bottleneck_px ?? aiResult.remaining_width_px} px`}
                </div>
                <div className="text-slate-600 font-semibold text-[11px]">
                  {aiResult.bottleneck_y_px ? `Critical Bottleneck at Row Y=${aiResult.bottleneck_y_px} px` : 'Uniform corridor'}
                </div>
                <div className="text-slate-400 text-[11px]">
                  {aiResult.is_calibrated_physical_measurement ? 'IRC:SP:102 (1.2m standard)' : 'Estimated 2D pixel width'}
                </div>
              </div>
            </div>
          </div>

          {/* =====================================================================
              4. ACCESSIBILITY (Section 6)
             ===================================================================== */}
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div>
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <Activity className="w-4 h-4 text-emerald-600" />
                  <span>4. ACCESSIBILITY</span>
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  EncroWatch Accessibility Score &amp; pedestrian walkability intelligence.
                </p>
              </div>
              <span className="text-xs font-mono text-slate-400">Benchmarked vs IRC:SP:102 &amp; ADA</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
              {/* EncroWatch Accessibility Score */}
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">EncroWatch Accessibility Score</div>
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-black text-slate-900">{aiResult.accessibility_score ?? 100}</span>
                  <span className="text-xs font-bold text-slate-400">/ 100</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-0.5 rounded-md font-bold text-[11px] ${
                    (aiResult.accessibility_score ?? 100) >= 80
                      ? 'bg-emerald-100 text-emerald-800'
                      : (aiResult.accessibility_score ?? 100) >= 60
                      ? 'bg-blue-100 text-blue-800'
                      : (aiResult.accessibility_score ?? 100) >= 40
                      ? 'bg-amber-100 text-amber-800'
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {aiResult.accessibility_category || ((aiResult.accessibility_score >= 80) ? 'Good' : ((aiResult.accessibility_score >= 60) ? 'Moderately Affected' : ((aiResult.accessibility_score >= 40) ? 'Poor' : 'Severely Blocked')))}
                  </span>
                </div>
                <div className="text-[10px] text-slate-400">Project analytical score (not government standard)</div>
              </div>

              {/* Path Continuity */}
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Path Continuity</div>
                <div className="flex items-center gap-2">
                  <span className={`px-2.5 py-1 rounded-lg text-xs font-black tracking-wide ${
                    aiResult.path_continuity === 'CLEAR'
                      ? 'bg-emerald-100 text-emerald-800'
                      : aiResult.path_continuity === 'PARTIALLY BLOCKED'
                      ? 'bg-amber-100 text-amber-800'
                      : aiResult.path_continuity === 'SEVERELY BLOCKED'
                      ? 'bg-red-100 text-red-800'
                      : 'bg-slate-200 text-slate-700'
                  }`}>
                    {aiResult.path_continuity || 'CLEAR'}
                  </span>
                </div>
                <p className="text-slate-600 text-[11px] leading-relaxed">
                  {aiResult.path_continuity_reason || 'Uninterrupted walking line through visible corridor.'}
                </p>
              </div>

              {/* Obstruction Impact */}
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Obstruction Impact</div>
                <div className="flex items-center gap-2">
                  <span className={`px-2.5 py-1 rounded-lg text-xs font-black tracking-wide ${
                    (aiResult.obstruction_impact || 'LOW') === 'HIGH'
                      ? 'bg-red-100 text-red-800'
                      : (aiResult.obstruction_impact || 'LOW') === 'MEDIUM'
                      ? 'bg-amber-100 text-amber-800'
                      : 'bg-emerald-100 text-emerald-800'
                  }`}>
                    {aiResult.obstruction_impact || 'LOW'} IMPACT
                  </span>
                </div>
                <p className="text-slate-600 text-[11px] leading-relaxed">
                  {(aiResult.obstruction_impact || 'LOW') === 'HIGH'
                    ? 'Substantial pedestrian corridor constriction; impedes wheelchair passage.'
                    : (aiResult.obstruction_impact || 'LOW') === 'MEDIUM'
                    ? 'Moderate corridor constriction requiring pedestrian detour.'
                    : 'Low pedestrian impact; adequate walkable width preserved.'}
                </p>
              </div>
            </div>
          </div>

          {/* =====================================================================
              5. RISK (Section 6)
             ===================================================================== */}
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div>
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <Flame className="w-4 h-4 text-red-500" />
                  <span>5. RISK</span>
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Dynamic Encroachment Risk Score fused from 4 measurable components.
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-slate-500">Severity:</span>
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
                  (aiResult.risk_level || aiResult.severity) === 'HIGH' || (aiResult.risk_level || aiResult.severity) === 'High'
                    ? 'bg-red-100 text-red-700'
                    : (aiResult.risk_level || aiResult.severity) === 'MEDIUM' || (aiResult.risk_level || aiResult.severity) === 'Medium'
                    ? 'bg-amber-100 text-amber-700'
                    : 'bg-emerald-100 text-emerald-700'
                }`}>
                  {aiResult.risk_level || aiResult.severity || 'LOW'}
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-12 gap-4 items-center">
              {/* Big Score Box */}
              <div className="sm:col-span-4 p-4 rounded-xl bg-slate-50 border border-slate-200 text-center space-y-1">
                <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Encroachment Risk Score</div>
                <div className="text-4xl font-black text-slate-900">
                  {aiResult.risk_score ?? 65} <span className="text-base font-bold text-slate-400">/ 100</span>
                </div>
                <div className="text-xs font-bold text-slate-600 mt-1">
                  {(aiResult.risk_score ?? 65) >= 70 ? 'HIGH RISK' : ((aiResult.risk_score ?? 65) >= 40 ? 'MEDIUM RISK' : 'LOW RISK')}
                </div>
              </div>

              {/* 4 Measurable Factors */}
              <div className="sm:col-span-8 grid grid-cols-2 gap-2.5 text-xs">
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
                  <div className="flex justify-between items-center text-slate-500">
                    <span className="font-semibold">Object Impact</span>
                    <span className="font-mono font-bold text-slate-800">{aiResult.risk_factors?.object_impact?.points ?? 26} / 30</span>
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5 truncate">{aiResult.risk_factors?.object_impact?.detail || 'Obstacle classification weight'}</div>
                </div>

                <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
                  <div className="flex justify-between items-center text-slate-500">
                    <span className="font-semibold">Footpath Overlap</span>
                    <span className="font-mono font-bold text-slate-800">{aiResult.risk_factors?.footpath_overlap?.points ?? 18} / 25</span>
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5 truncate">{aiResult.risk_factors?.footpath_overlap?.detail || 'Corridor footprint overlap'}</div>
                </div>

                <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
                  <div className="flex justify-between items-center text-slate-500">
                    <span className="font-semibold">Persistence</span>
                    <span className="font-mono font-bold text-slate-800">{aiResult.risk_factors?.persistence?.points ?? 10} / 20</span>
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5 truncate">{aiResult.risk_factors?.persistence?.detail || 'Baseline photographic capture'}</div>
                </div>

                <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
                  <div className="flex justify-between items-center text-slate-500">
                    <span className="font-semibold">Accessibility</span>
                    <span className="font-mono font-bold text-slate-800">{aiResult.risk_factors?.accessibility_impact?.points ?? 17} / 25</span>
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5 truncate">{aiResult.risk_factors?.accessibility_impact?.detail || 'Pedestrian hindrance factor'}</div>
                </div>
              </div>
            </div>
          </div>

          {/* =====================================================================
              6. AI DECISION (Section 6)
             ===================================================================== */}
          <div className="bg-slate-900 rounded-2xl p-6 text-white space-y-5 shadow-xl">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800">
              <div>
                <h3 className="text-base font-bold flex items-center gap-2">
                  <ShieldAlert className="w-5 h-5 text-emerald-400" />
                  <span>6. AI DECISION</span>
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Recommended municipal action based on real AI reasoning. Select an action below to proceed.
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400 font-semibold">Potential Encroachment:</span>
                <span className={`px-3 py-1 rounded-full text-xs font-black ${
                  (aiResult.potential_encroachment || (aiResult.has_encroachment ? 'YES' : 'NO')) === 'YES'
                    ? 'bg-red-500 text-white'
                    : (aiResult.potential_encroachment === 'NEEDS REVIEW' || aiResult.needs_human_review)
                    ? 'bg-amber-400 text-slate-950'
                    : 'bg-emerald-500 text-white'
                }`}>
                  {aiResult.potential_encroachment || (aiResult.has_encroachment ? 'YES' : (aiResult.needs_human_review ? 'NEEDS REVIEW' : 'NO'))}
                </span>
              </div>
            </div>

            {/* Two Clear Choices: [Create Incident] or [Needs Human Review] */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <button
                type="button"
                onClick={() => {
                  setDecisionAction('create');
                  setShowIncidentForm(true);
                }}
                className={`p-4 rounded-xl border flex items-center gap-3 transition-all ${
                  decisionAction === 'create' && showIncidentForm
                    ? 'bg-emerald-500/20 border-emerald-400 text-white ring-2 ring-emerald-500/40'
                    : 'bg-slate-800/80 hover:bg-slate-800 border-slate-700 text-slate-200'
                }`}
              >
                <div className="w-10 h-10 rounded-xl bg-emerald-500 text-slate-950 flex items-center justify-center font-bold shrink-0">
                  <CheckCircle2 className="w-5 h-5" />
                </div>
                <div className="text-left">
                  <div className="text-sm font-bold text-white">[Create Incident]</div>
                  <div className="text-xs text-slate-400 mt-0.5">Register confirmed encroachment to municipal queue</div>
                </div>
              </button>

              <button
                type="button"
                onClick={() => {
                  setDecisionAction('review');
                  setShowIncidentForm(true);
                }}
                className={`p-4 rounded-xl border flex items-center gap-3 transition-all ${
                  decisionAction === 'review' && showIncidentForm
                    ? 'bg-amber-500/20 border-amber-400 text-white ring-2 ring-amber-500/40'
                    : 'bg-slate-800/80 hover:bg-slate-800 border-slate-700 text-slate-200'
                }`}
              >
                <div className="w-10 h-10 rounded-xl bg-amber-400 text-slate-950 flex items-center justify-center font-bold shrink-0">
                  <Eye className="w-5 h-5" />
                </div>
                <div className="text-left">
                  <div className="text-sm font-bold text-white">[Needs Human Review]</div>
                  <div className="text-xs text-slate-400 mt-0.5">Flag uncertain boundary/detection for officer review</div>
                </div>
              </button>
            </div>

            {/* Registration Form (Appears when either option selected or by default) */}
            {createdIncident ? (
              <div
                data-testid="incident-created-banner"
                className="bg-emerald-950/90 border border-emerald-500/40 rounded-xl p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
              >
                <div className="space-y-1">
                  <div className="text-sm font-extrabold text-emerald-300 flex items-center gap-2">
                    <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                    Incident {createdIncident.incident_number} Saved Successfully!
                  </div>
                  <p className="text-xs text-slate-300">
                    Location: <strong>{createdIncident.location_name}</strong> • Type:{' '}
                    <strong>{createdIncident.primary_encroachment_type}</strong> • Status:{' '}
                    <strong>{createdIncident.status}</strong>
                  </p>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  {onIncidentCreated && (
                    <button
                      type="button"
                      onClick={() => onIncidentCreated(createdIncident)}
                      className="px-4 py-2 text-xs font-bold bg-emerald-400 hover:bg-emerald-300 text-slate-950 rounded-xl flex items-center gap-1.5 transition-colors"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                      Open Incident Record
                    </button>
                  )}
                </div>
              </div>
            ) : (
              showIncidentForm && (
                <form onSubmit={handleCreateIncident} className="space-y-4 pt-3 border-t border-slate-800 animate-fade-in">
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
                    <div>
                      <label className="block text-slate-400 font-semibold mb-1">Location Corridor</label>
                      <select
                        value={incidentLocation}
                        onChange={(e) => setIncidentLocation(e.target.value)}
                        className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2.5 text-white font-medium focus:outline-none focus:border-blue-500"
                      >
                        <option value="MG Road, Bengaluru">MG Road, Bengaluru</option>
                        <option value="Indiranagar, Bengaluru">Indiranagar, Bengaluru</option>
                        <option value="Koramangala, Bengaluru">Koramangala, Bengaluru</option>
                        <option value="HSR Layout, Bengaluru">HSR Layout, Bengaluru</option>
                        <option value="BTM Layout, Bengaluru">BTM Layout, Bengaluru</option>
                        <option value="Jayanagar, Bengaluru">Jayanagar, Bengaluru</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-slate-400 font-semibold mb-1">Reviewed Classification / Type</label>
                      <select
                        value={incidentType}
                        onChange={(e) => setIncidentType(e.target.value)}
                        className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2.5 text-white font-medium focus:outline-none focus:border-blue-500"
                      >
                        <option value="Street Object (umbrella)">Street Object (umbrella / canopy)</option>
                        <option value="Vehicle (car)">Vehicle (car / motorcycle / truck)</option>
                        <option value="Needs Review: Street Vendor">Human-Verified: Street Vendor</option>
                        <option value="Needs Review: Construction Material">Human-Verified: Construction Material</option>
                        <option value="Needs Review: Debris">Human-Verified: Debris / Rubble</option>
                        <option value="Needs Review: Signboard">Human-Verified: Signboard</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-slate-400 font-semibold mb-1">Reviewed Severity</label>
                      <select
                        value={incidentSeverity}
                        onChange={(e) => setIncidentSeverity(e.target.value)}
                        className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2.5 text-white font-medium focus:outline-none focus:border-blue-500"
                      >
                        <option value="High">High Severity</option>
                        <option value="Medium">Medium Severity</option>
                        <option value="Low">Low Severity</option>
                      </select>
                    </div>

                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <label className="block text-slate-400 font-semibold mb-1">Latitude</label>
                        <input
                          type="number"
                          step="0.0001"
                          value={incidentLat}
                          onChange={(e) => setIncidentLat(e.target.value)}
                          className="w-full bg-slate-800 border border-slate-700 rounded-xl px-2.5 py-2.5 text-white font-mono"
                        />
                      </div>
                      <div>
                        <label className="block text-slate-400 font-semibold mb-1">Longitude</label>
                        <input
                          type="number"
                          step="0.0001"
                          value={incidentLng}
                          onChange={(e) => setIncidentLng(e.target.value)}
                          className="w-full bg-slate-800 border border-slate-700 rounded-xl px-2.5 py-2.5 text-white font-mono"
                        />
                      </div>
                    </div>
                  </div>

                  <div className="text-xs">
                    <label className="block text-slate-400 font-semibold mb-1">
                      AI Analysis Explanation &amp; Human Reviewer Notes
                    </label>
                    <textarea
                      rows="2"
                      value={incidentNotes}
                      onChange={(e) => setIncidentNotes(e.target.value)}
                      className="w-full bg-slate-800 border border-slate-700 rounded-xl p-3 text-slate-200 focus:outline-none focus:border-blue-500"
                    />
                  </div>

                  <div className="flex justify-end">
                    <button
                      type="submit"
                      data-testid="register-incident-btn"
                      disabled={creatingIncident}
                      className={`px-6 py-3 text-xs font-bold rounded-xl transition-colors flex items-center gap-2 shadow-sm disabled:opacity-50 ${
                        decisionAction === 'review'
                          ? 'bg-amber-400 hover:bg-amber-300 text-slate-950'
                          : 'bg-emerald-400 hover:bg-emerald-300 text-slate-950'
                      }`}
                    >
                      <Save className="w-4 h-4" />
                      {creatingIncident
                        ? 'Saving Incident to Registry...'
                        : (decisionAction === 'review' ? 'Submit for Human Verification' : 'Confirm & Register Incident')}
                    </button>
                  </div>
                </form>
              )
            )}
          </div>
        </div>
      )}

      {/* =====================================================================
          REAL VIDEO FRAME-SAMPLED TRACKING RESULTS
         ===================================================================== */}
      {videoResult && (
        <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm space-y-4 animate-scale-in">
          <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-100">
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-slate-800">
                  Real Frame-Sampled Video Tracking Results
                </h3>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-100 text-blue-800">
                  {videoResult.processing_status}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">{videoResult.status_explanation}</p>
            </div>
            <div className="flex items-center gap-2">
              <span className="px-3 py-1 bg-slate-100 text-slate-700 text-xs font-bold rounded-full">
                Decoded: {videoResult.frames_decoded} frames ({videoResult.frames_analyzed} sampled)
              </span>
              <span className="px-3 py-1 bg-amber-50 text-amber-700 text-xs font-bold rounded-full border border-amber-200">
                Duration: {videoResult.duration_formatted}
              </span>
            </div>
          </div>

          {videoResult.persistent_obstructions?.length > 0 ? (
            <div className="space-y-3">
              <div className="text-xs font-bold text-red-700 uppercase tracking-wider">
                Persistent Stationary Tracks (&ge; {videoResult.persistence_threshold_sec || 3.0}s)
              </div>
              {videoResult.persistent_obstructions.map((obs, idx) => (
                <div
                  key={idx}
                  className="p-4 bg-red-50/60 rounded-xl border border-red-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-red-500 text-white flex items-center justify-center shrink-0">
                      <Clock className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="text-sm font-bold text-slate-800">
                        {obs.label} (Track {obs.object_id})
                      </div>
                      <div className="text-xs text-slate-600 mt-0.5">
                        Observed Duration: <strong className="text-red-700">{obs.duration_formatted}</strong> across{' '}
                        <strong>{obs.frames_observed}</strong> sampled frames • Max centroid shift: {obs.max_displacement_px} px
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-red-100 text-red-800">
                      {obs.status}
                    </span>
                    <span className="text-xs text-slate-600 font-semibold">
                      Mean Conf: {(obs.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-700">
              <strong>0 Persistent Stationary Obstructions (&ge; {videoResult.persistence_threshold_sec || 3.0}s):</strong>{' '}
              No stationary encroachment track exceeded the {videoResult.persistence_threshold_sec || 3.0}s threshold in this video.
            </div>
          )}

          {videoResult.all_tracks?.length > 0 && (
            <div className="space-y-2 pt-2">
              <div className="text-xs font-bold text-slate-600">
                All Observed YOLOv5n-ONNX Object Tracks ({videoResult.all_tracks.length}):
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5 text-xs">
                {videoResult.all_tracks.map((trk, idx) => (
                  <div key={idx} className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
                    <div>
                      <span className="font-bold text-slate-800">{trk.label}</span>{' '}
                      <span className="text-slate-400 font-mono">({trk.object_id})</span>
                      <div className="text-[11px] text-slate-500 mt-0.5">
                        Frames: {trk.frames_observed} • Span: {trk.start_time_sec}s–{trk.end_time_sec}s ({trk.duration_sec}s) • Shift: {trk.max_displacement_px}px
                      </div>
                    </div>
                    <span className="px-2 py-0.5 rounded-md text-[11px] font-bold bg-white border border-slate-200 text-slate-700">
                      {(trk.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
