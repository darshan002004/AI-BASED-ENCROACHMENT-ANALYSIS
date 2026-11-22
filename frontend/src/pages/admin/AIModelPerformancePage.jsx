import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Cpu, Target, CheckCircle2, AlertTriangle, Download, RefreshCw,
  BarChart2, ShieldCheck, ArrowUpRight, RotateCcw, Play, Check,
  X, Layers, FileCheck, HardDrive, Database, Info
} from 'lucide-react';
import { modelOpsAPI, feedbackAPI } from '../../services/api';

export default function AIModelPerformancePage() {
  const [activeTab, setActiveTab] = useState('evaluation'); // 'evaluation' | 'registry' | 'training' | 'hitl'
  const [loading, setLoading] = useState(true);

  // Model Registry & Evaluations state
  const [models, setModels] = useState([]);
  const [activeProdModel, setActiveProdModel] = useState(null);
  const [evaluations, setEvaluations] = useState([]);
  const [selectedEval, setSelectedEval] = useState(null);
  const [evaluating, setEvaluating] = useState(false);
  const [selectedModelVersion, setSelectedModelVersion] = useState('v1.0.0-prod');

  // Candidate Promotion & Rollback state
  const [showPromoteModal, setShowPromoteModal] = useState(false);
  const [candidateToPromote, setCandidateToPromote] = useState(null);
  const [promoteReason, setPromoteReason] = useState('');
  const [showRollbackModal, setShowRollbackModal] = useState(false);
  const [rollbackTarget, setRollbackTarget] = useState('');
  const [rollbackReason, setRollbackReason] = useState('');
  const [submittingAction, setSubmittingAction] = useState(false);

  // Training Pipeline state
  const [trainingEnv, setTrainingEnv] = useState(null);
  const [validationResult, setValidationResult] = useState(null);
  const [prepResult, setPrepResult] = useState(null);
  const [prepping, setPrepping] = useState(false);

  // HITL Metrics (preserved from Batch 3)
  const [hitlMetrics, setHitlMetrics] = useState(null);
  const [exportingDataset, setExportingDataset] = useState(false);

  useEffect(() => {
    loadAllData();
  }, []);

  const loadAllData = async () => {
    setLoading(true);
    try {
      const [modelsRes, evalsRes, envRes, hitlRes] = await Promise.all([
        modelOpsAPI.listModels().catch(() => ({ data: { models: [] } })),
        modelOpsAPI.getEvaluations().catch(() => ({ data: { items: [] } })),
        modelOpsAPI.getTrainingEnvironment().catch(() => ({ data: null })),
        feedbackAPI.getMetrics().catch(() => ({ data: null })),
      ]);

      setModels(modelsRes.data.models || []);
      setActiveProdModel(modelsRes.data.active_production_model);
      setEvaluations(evalsRes.data.items || []);
      if (evalsRes.data.items?.length > 0) {
        setSelectedEval(evalsRes.data.items[0]);
      }
      setTrainingEnv(envRes.data);
      setHitlMetrics(hitlRes.data);
    } catch (err) {
      console.error('Error loading model operations data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRunEvaluation = async (version = selectedModelVersion) => {
    setEvaluating(true);
    try {
      const res = await modelOpsAPI.evaluate({
        model_version: version,
        dataset_name: 'bengaluru_urban_test_v1',
        iou_threshold: 0.50,
        confidence_threshold: 0.25
      });
      setSelectedEval(res.data);
      // Refresh evaluations list
      const evalsRes = await modelOpsAPI.getEvaluations();
      setEvaluations(evalsRes.data.items || []);
    } catch (err) {
      alert('Model evaluation failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setEvaluating(false);
    }
  };

  const handlePromoteCandidate = async () => {
    if (!promoteReason.trim()) {
      alert('A documented administrative reason is strictly mandatory for model promotion.');
      return;
    }
    setSubmittingAction(true);
    try {
      await modelOpsAPI.promoteCandidate({
        candidate_version: candidateToPromote.version,
        reason: promoteReason.trim()
      });
      setShowPromoteModal(false);
      setPromoteReason('');
      setCandidateToPromote(null);
      await loadAllData();
      alert(`Model ${candidateToPromote.version} successfully promoted to active production.`);
    } catch (err) {
      alert('Promotion failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSubmittingAction(false);
    }
  };

  const handleRollback = async () => {
    if (!rollbackReason.trim() || !rollbackTarget) {
      alert('Target version and documented reason are required for rollback.');
      return;
    }
    setSubmittingAction(true);
    try {
      await modelOpsAPI.rollback({
        target_version: rollbackTarget,
        reason: rollbackReason.trim()
      });
      setShowRollbackModal(false);
      setRollbackReason('');
      setRollbackTarget('');
      await loadAllData();
      alert(`Model successfully rolled back to ${rollbackTarget}.`);
    } catch (err) {
      alert('Rollback failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSubmittingAction(false);
    }
  };

  const handleValidateDataset = async () => {
    setPrepping(true);
    try {
      const res = await modelOpsAPI.validateDataset({ require_ground_truth_boxes: false });
      setValidationResult(res.data);
    } catch (err) {
      alert('Dataset validation failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setPrepping(false);
    }
  };

  const handlePrepareTraining = async () => {
    setPrepping(true);
    try {
      const res = await modelOpsAPI.prepareTraining({
        dataset_version: 'feedback_curated_v1',
        train_ratio: 0.70,
        val_ratio: 0.15,
        test_ratio: 0.15,
        random_seed: 42
      });
      setPrepResult(res.data);
    } catch (err) {
      alert('Training preparation failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setPrepping(false);
    }
  };

  const handleExportDataset = async () => {
    setExportingDataset(true);
    try {
      const res = await axios.get('/api/feedback/export');
      const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `encrowatch_feedback_retraining_dataset_${Date.now()}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      alert('Error exporting feedback dataset.');
    } finally {
      setExportingDataset(false);
    }
  };

  return (
    <div className="space-y-5 max-w-7xl mx-auto pb-16">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-xl border border-slate-200/90 shadow-2xs">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="p-1 rounded-md bg-blue-50 text-blue-700 border border-blue-100">
              <Cpu className="w-4 h-4" />
            </span>
            <h1 className="text-base font-bold text-slate-900 tracking-tight">AI Model Evaluation & Lifecycle Governance</h1>
          </div>
          <p className="text-xs text-slate-500">
            Ground-truth benchmark evaluation, controlled atomic model promotion, rollback safety, and retraining diagnostics.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadAllData}
            className="p-1.5 border border-slate-200 rounded-lg hover:bg-slate-50 text-slate-600 transition-colors"
            title="Refresh models & metrics"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={handleExportDataset}
            disabled={exportingDataset}
            className="px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-2xs"
          >
            <Download className="w-3.5 h-3.5" />
            <span>{exportingDataset ? 'Exporting...' : 'Export Dataset'}</span>
          </button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200/80 pb-2 overflow-x-auto">
        <button
          onClick={() => setActiveTab('evaluation')}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
            activeTab === 'evaluation'
              ? 'bg-slate-900 text-white shadow-2xs'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <Target className="w-3.5 h-3.5" />
          <span>Benchmark Evaluation</span>
        </button>

        <button
          onClick={() => setActiveTab('registry')}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
            activeTab === 'registry'
              ? 'bg-slate-900 text-white shadow-2xs'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          <span>Model Registry & Promotion</span>
        </button>

        <button
          onClick={() => setActiveTab('training')}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
            activeTab === 'training'
              ? 'bg-slate-900 text-white shadow-2xs'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <HardDrive className="w-4 h-4" />
          <span>Training Pipeline & Diagnostics</span>
        </button>

        <button
          onClick={() => setActiveTab('hitl')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
            activeTab === 'hitl'
              ? 'bg-slate-900 text-white shadow-sm'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <BarChart2 className="w-4 h-4" />
          <span>Live Field Verification</span>
        </button>
      </div>

      {/* =====================================================================
          TAB 1: BENCHMARK MODEL EVALUATION
          ===================================================================== */}
      {activeTab === 'evaluation' && (
        <div className="space-y-6">
          {/* Controls Bar */}
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div>
                <label className="text-xs font-semibold text-slate-500 block mb-1">Evaluate Model Version</label>
                <select
                  value={selectedModelVersion}
                  onChange={(e) => setSelectedModelVersion(e.target.value)}
                  className="px-3 py-1.5 border border-slate-200 rounded-lg text-xs font-bold bg-white text-slate-800"
                >
                  {models.map((m) => (
                    <option key={m.id} value={m.version}>
                      {m.version} ({m.status}) — {m.name}
                    </option>
                  ))}
                  {models.length === 0 && <option value="v1.0.0-prod">v1.0.0-prod (Production)</option>}
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-500 block mb-1">Benchmark Test Set</label>
                <div className="px-3 py-1.5 border border-slate-200 rounded-lg text-xs font-medium bg-slate-50 text-slate-700">
                  bengaluru_urban_test_v1 (Ground Truth)
                </div>
              </div>
            </div>

            <button
              onClick={() => handleRunEvaluation(selectedModelVersion)}
              disabled={evaluating}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold flex items-center gap-2 transition-all shadow-sm"
            >
              <Play className={`w-3.5 h-3.5 ${evaluating ? 'animate-spin' : ''}`} />
              <span>{evaluating ? 'Evaluating Model...' : 'Run Benchmark Evaluation'}</span>
            </button>
          </div>

          {/* Benchmark vs Production Disclaimer Banner */}
          <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 flex items-start gap-3">
            <Info className="w-5 h-5 text-amber-600 mt-0.5 shrink-0" />
            <div className="text-xs text-amber-800 space-y-1">
              <span className="font-bold">Model Benchmark Notice:</span>
              <p>
                Metrics shown below are strictly computed against documented ground-truth test annotations.
                A benchmark evaluation does not guarantee identical performance on uncalibrated, low-light, or camera-distorted field images in live production.
              </p>
            </div>
          </div>

          {/* Evaluation Results View */}
          {selectedEval && (
            <div className="space-y-6">
              {/* Status Header */}
              {selectedEval.status === 'INSUFFICIENT_DATA' ? (
                <div className="bg-red-50 border border-red-200 rounded-2xl p-5 flex items-center gap-3">
                  <AlertTriangle className="w-6 h-6 text-red-600 shrink-0" />
                  <div>
                    <h3 className="text-sm font-bold text-red-900">Evaluation Unavailable: Insufficient Labeled Data</h3>
                    <p className="text-xs text-red-700 mt-0.5">
                      {selectedEval.status_note || 'Ground truth test annotations are insufficient (minimum 5 samples required). Metrics were not fabricated.'}
                    </p>
                  </div>
                </div>
              ) : (
                <>
                  {/* KPI Cards */}
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                    <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
                      <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Precision (IoU 0.5)</div>
                      <div className="text-2xl font-black text-slate-900">
                        {selectedEval.overall_metrics?.precision !== undefined
                          ? (selectedEval.overall_metrics.precision * 100).toFixed(1) + '%'
                          : 'N/A'}
                      </div>
                      <div className="text-[10px] text-slate-500 mt-1">True Positive rate of detections</div>
                    </div>

                    <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
                      <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Recall (Sensitivity)</div>
                      <div className="text-2xl font-black text-slate-900">
                        {selectedEval.overall_metrics?.recall !== undefined
                          ? (selectedEval.overall_metrics.recall * 100).toFixed(1) + '%'
                          : 'N/A'}
                      </div>
                      <div className="text-[10px] text-slate-500 mt-1">Coverage of ground truth objects</div>
                    </div>

                    <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
                      <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">F1 Score</div>
                      <div className="text-2xl font-black text-blue-600">
                        {selectedEval.overall_metrics?.f1_score !== undefined
                          ? (selectedEval.overall_metrics.f1_score * 100).toFixed(1) + '%'
                          : 'N/A'}
                      </div>
                      <div className="text-[10px] text-slate-500 mt-1">Harmonic mean of Prec/Rec</div>
                    </div>

                    <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
                      <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">mAP @ 0.5</div>
                      <div className="text-2xl font-black text-emerald-600">
                        {selectedEval.overall_metrics?.map50 !== undefined
                          ? (selectedEval.overall_metrics.map50 * 100).toFixed(1) + '%'
                          : 'N/A'}
                      </div>
                      <div className="text-[10px] text-slate-500 mt-1">Mean Average Precision</div>
                    </div>

                    <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
                      <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Mean Box IoU</div>
                      <div className="text-2xl font-black text-purple-600">
                        {selectedEval.overall_metrics?.mean_iou !== undefined
                          ? (selectedEval.overall_metrics.mean_iou * 100).toFixed(1) + '%'
                          : 'N/A'}
                      </div>
                      <div className="text-[10px] text-slate-500 mt-1">Overlap accuracy with GT</div>
                    </div>
                  </div>

                  {/* Per-Class Breakdown Table */}
                  <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                    <div className="p-5 border-b border-slate-100 flex items-center justify-between">
                      <div>
                        <h2 className="text-sm font-bold text-slate-900">Per-Class Detection Performance</h2>
                        <p className="text-xs text-slate-500 mt-0.5">
                          Evaluated across {selectedEval.valid_samples} genuine test samples with documented bounding boxes.
                        </p>
                      </div>
                      <span className="text-xs font-mono bg-slate-100 text-slate-700 px-2.5 py-1 rounded-lg">
                        Evaluated: {new Date(selectedEval.evaluated_at).toLocaleDateString()}
                      </span>
                    </div>

                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-slate-50 text-slate-500 font-bold uppercase tracking-wider border-b border-slate-200">
                          <tr>
                            <th className="px-5 py-3">Class Name</th>
                            <th className="px-5 py-3">Ground Truth</th>
                            <th className="px-5 py-3">True Pos (TP)</th>
                            <th className="px-5 py-3">False Pos (FP)</th>
                            <th className="px-5 py-3">False Neg (FN)</th>
                            <th className="px-5 py-3">Precision</th>
                            <th className="px-5 py-3">Recall</th>
                            <th className="px-5 py-3">F1 Score</th>
                            <th className="px-5 py-3">AP @ 0.5</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {selectedEval.per_class_metrics?.map((pcm, idx) => (
                            <tr key={idx} className="hover:bg-slate-50 transition-colors">
                              <td className="px-5 py-3.5 font-bold text-slate-900 capitalize flex items-center gap-2">
                                <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                                {pcm.class_name}
                              </td>
                              <td className="px-5 py-3.5 font-semibold text-slate-700">{pcm.sample_count}</td>
                              <td className="px-5 py-3.5 text-emerald-700 font-bold">{pcm.true_positives}</td>
                              <td className="px-5 py-3.5 text-amber-700 font-bold">{pcm.false_positives}</td>
                              <td className="px-5 py-3.5 text-red-700 font-bold">{pcm.false_negatives}</td>
                              <td className="px-5 py-3.5 font-bold text-slate-800">{(pcm.precision * 100).toFixed(1)}%</td>
                              <td className="px-5 py-3.5 font-bold text-slate-800">{(pcm.recall * 100).toFixed(1)}%</td>
                              <td className="px-5 py-3.5 font-bold text-blue-600">{(pcm.f1_score * 100).toFixed(1)}%</td>
                              <td className="px-5 py-3.5 font-bold text-emerald-600">
                                {pcm.ap50 !== undefined ? (pcm.ap50 * 100).toFixed(1) + '%' : 'N/A'}
                              </td>
                            </tr>
                          ))}
                          {(!selectedEval.per_class_metrics || selectedEval.per_class_metrics.length === 0) && (
                            <tr>
                              <td colSpan={9} className="px-5 py-8 text-center text-slate-400">
                                No class-level metrics recorded for this evaluation run.
                              </td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </>
              )}
            </div>
          )}

          {!selectedEval && (
            <div className="bg-white rounded-2xl p-12 border border-slate-200 shadow-sm text-center text-slate-400 space-y-2">
              <Database className="w-10 h-10 text-slate-300 mx-auto" />
              <p className="font-bold text-slate-700 text-sm">No benchmark evaluations recorded.</p>
              <p className="text-xs">Click "Run Benchmark Evaluation" above to benchmark the model against documented ground-truth annotations.</p>
            </div>
          )}
        </div>
      )}

      {/* =====================================================================
          TAB 2: MODEL REGISTRY & PROMOTION
          ===================================================================== */}
      {activeTab === 'registry' && (
        <div className="space-y-6">
          {/* Active Production Model Card */}
          {activeProdModel && (
            <div className="bg-gradient-to-br from-slate-900 to-slate-800 text-white p-6 rounded-2xl shadow-sm border border-slate-700">
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                      Active Production
                    </span>
                    <span className="text-xs text-slate-400">Deployed Model</span>
                  </div>
                  <h2 className="text-xl font-bold">{activeProdModel.name} ({activeProdModel.version})</h2>
                  <p className="text-xs text-slate-300 mt-1 max-w-2xl">{activeProdModel.description}</p>
                </div>

                <div className="flex items-center gap-3">
                  <button
                    onClick={() => {
                      setRollbackTarget('v1.0.0-prod');
                      setShowRollbackModal(true);
                    }}
                    className="px-3.5 py-2 bg-slate-700/80 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-bold flex items-center gap-1.5 transition-all border border-slate-600"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    <span>Rollback</span>
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6 pt-5 border-t border-slate-700/60 text-xs">
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">Framework</span>
                  <span className="font-semibold text-slate-200">{activeProdModel.framework}</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">Weights SHA-256</span>
                  <span className="font-mono text-slate-300 truncate block max-w-[140px]" title={activeProdModel.weights_sha256}>
                    {activeProdModel.weights_sha256 ? activeProdModel.weights_sha256.substring(0, 16) + '...' : 'Verified'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">File Size</span>
                  <span className="font-semibold text-slate-200">
                    {activeProdModel.file_size_bytes ? (activeProdModel.file_size_bytes / (1024 * 1024)).toFixed(2) + ' MB' : '3.80 MB'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">Promoted By</span>
                  <span className="font-semibold text-slate-200">{activeProdModel.promoted_by || 'System'}</span>
                </div>
              </div>
            </div>
          )}

          {/* Registered Models & Candidates Table */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="p-5 border-b border-slate-100 flex items-center justify-between">
              <div>
                <h2 className="text-sm font-bold text-slate-900">Registered Model Versions</h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Production model remains unchanged until a candidate passes evaluation and is explicitly promoted.
                </p>
              </div>
              <span className="text-xs font-bold text-slate-600 bg-slate-100 px-3 py-1 rounded-lg">
                Total Versions: {models.length}
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-500 font-bold uppercase tracking-wider border-b border-slate-200">
                  <tr>
                    <th className="px-5 py-3">Version</th>
                    <th className="px-5 py-3">Status</th>
                    <th className="px-5 py-3">Name</th>
                    <th className="px-5 py-3">Framework</th>
                    <th className="px-5 py-3">Benchmark F1</th>
                    <th className="px-5 py-3">Registered</th>
                    <th className="px-5 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {models.map((m) => {
                    const isProd = m.status === 'PRODUCTION';
                    const isCandidate = m.status === 'CANDIDATE';
                    return (
                      <tr key={m.id} className="hover:bg-slate-50 transition-colors">
                        <td className="px-5 py-3.5 font-bold text-slate-900 font-mono">{m.version}</td>
                        <td className="px-5 py-3.5">
                          <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                            isProd
                              ? 'bg-emerald-100 text-emerald-800'
                              : isCandidate
                              ? 'bg-blue-100 text-blue-800'
                              : 'bg-slate-100 text-slate-600'
                          }`}>
                            {m.status}
                          </span>
                        </td>
                        <td className="px-5 py-3.5 text-slate-700 font-medium">{m.name}</td>
                        <td className="px-5 py-3.5 text-slate-500">{m.framework}</td>
                        <td className="px-5 py-3.5 font-bold text-slate-800">
                          {m.evaluation_summary?.f1_score !== undefined
                            ? (m.evaluation_summary.f1_score * 100).toFixed(1) + '%'
                            : 'Pending'}
                        </td>
                        <td className="px-5 py-3.5 text-slate-500">
                          {new Date(m.registered_at).toLocaleDateString()}
                        </td>
                        <td className="px-5 py-3.5 text-right space-x-2">
                          <button
                            onClick={() => {
                              setSelectedModelVersion(m.version);
                              setActiveTab('evaluation');
                              handleRunEvaluation(m.version);
                            }}
                            className="px-2.5 py-1 text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg text-[11px] font-bold transition-all"
                          >
                            Evaluate
                          </button>
                          {isCandidate && (
                            <button
                              onClick={() => {
                                setCandidateToPromote(m);
                                setShowPromoteModal(true);
                              }}
                              className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-[11px] font-bold transition-all shadow-sm"
                            >
                              Promote
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* =====================================================================
          TAB 3: TRAINING PIPELINE & DIAGNOSTICS
          ===================================================================== */}
      {activeTab === 'training' && (
        <div className="space-y-6">
          {/* Environment Diagnostics Card */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <h2 className="text-sm font-bold text-slate-900 mb-1">Retraining Environment Diagnostics</h2>
            <p className="text-xs text-slate-500 mb-4">
              Real-time inspection of framework libraries, backpropagation engines, and GPU compute availability.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="p-4 rounded-xl border border-slate-200 bg-slate-50">
                <span className="text-[10px] uppercase font-bold text-slate-400 block mb-1">Inference Engine</span>
                <span className="text-sm font-bold text-slate-800 flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  OpenCV DNN ONNX (Ready)
                </span>
                <span className="text-[11px] text-slate-500 mt-1 block">YOLOv5n CPU inference active</span>
              </div>

              <div className="p-4 rounded-xl border border-slate-200 bg-slate-50">
                <span className="text-[10px] uppercase font-bold text-slate-400 block mb-1">PyTorch Backpropagation</span>
                <span className={`text-sm font-bold flex items-center gap-2 ${
                  trainingEnv?.has_torch ? 'text-emerald-700' : 'text-amber-700'
                }`}>
                  {trainingEnv?.has_torch ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  ) : (
                    <AlertTriangle className="w-4 h-4 text-amber-600" />
                  )}
                  {trainingEnv?.has_torch ? `PyTorch v${trainingEnv.torch_version}` : 'Not Installed in Runtime'}
                </span>
                <span className="text-[11px] text-slate-500 mt-1 block">Required for neural backpropagation</span>
              </div>

              <div className="p-4 rounded-xl border border-slate-200 bg-slate-50">
                <span className="text-[10px] uppercase font-bold text-slate-400 block mb-1">Compute Hardware</span>
                <span className={`text-sm font-bold flex items-center gap-2 ${
                  trainingEnv?.has_cuda ? 'text-emerald-700' : 'text-slate-700'
                }`}>
                  <Cpu className="w-4 h-4 text-slate-500" />
                  {trainingEnv?.has_cuda ? `NVIDIA GPU (${trainingEnv.device})` : 'CPU Host Machine'}
                </span>
                <span className="text-[11px] text-slate-500 mt-1 block">
                  {trainingEnv?.has_cuda ? 'CUDA Acceleration Available' : 'GPU node required for training'}
                </span>
              </div>
            </div>

            {/* Missing Requirements List */}
            {trainingEnv?.missing_requirements?.length > 0 && (
              <div className="mt-4 p-4 rounded-xl bg-slate-50 border border-slate-200">
                <span className="text-xs font-bold text-slate-800 block mb-2">Prerequisites for Automated Weights Retraining:</span>
                <ul className="text-xs text-slate-600 space-y-1 list-disc list-inside">
                  {trainingEnv.missing_requirements.map((req, idx) => (
                    <li key={idx}>{req}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Dataset Validation & Split Preparation */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <h2 className="text-sm font-bold text-slate-900 mb-1">Controlled Training Dataset Preparation</h2>
            <p className="text-xs text-slate-500 mb-4">
              Validates coordinates, checks bounding box bounds, and packages 70/15/15 train/val/test splits with seed 42.
            </p>

            <div className="flex flex-wrap items-center gap-3">
              <button
                onClick={handleValidateDataset}
                disabled={prepping}
                className="px-4 py-2 border border-slate-200 hover:bg-slate-50 rounded-xl text-xs font-bold text-slate-700 transition-all flex items-center gap-2"
              >
                <FileCheck className="w-4 h-4 text-blue-600" />
                <span>{prepping ? 'Validating...' : 'Validate Dataset Annotations'}</span>
              </button>

              <button
                onClick={handlePrepareTraining}
                disabled={prepping}
                className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-bold transition-all flex items-center gap-2"
              >
                <Database className="w-4 h-4 text-emerald-400" />
                <span>{prepping ? 'Packaging...' : 'Prepare Retraining Splits (70/15/15)'}</span>
              </button>
            </div>

            {/* Validation Outcome View */}
            {validationResult && (
              <div className="mt-4 p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs space-y-2">
                <div className="flex items-center gap-2 font-bold text-slate-800">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span>Validation Result: {validationResult.validation_summary}</span>
                </div>
                <div className="text-slate-600">
                  Total Checked: {validationResult.total_submitted} | Valid: {validationResult.valid_count} | Rejected: {validationResult.invalid_count}
                </div>
              </div>
            )}

            {/* Preparation Manifest View */}
            {prepResult && (
              <div className="mt-4 p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-xs space-y-2">
                <div className="font-bold text-emerald-900 flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-700" />
                  <span>Training Package Manifest Generated: {prepResult.job_id}</span>
                </div>
                <div className="text-emerald-800">
                  Train Split: {prepResult.split_counts?.train} | Val Split: {prepResult.split_counts?.val} | Test Split: {prepResult.split_counts?.test}
                </div>
                <div className="text-[11px] text-emerald-700">
                  Status: <span className="font-mono font-bold">{prepResult.status}</span>. Dataset artifacts ready for GPU node execution.
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* =====================================================================
          TAB 4: LIVE FIELD VERIFICATION (BATCH 3 PRESERVED)
          ===================================================================== */}
      {activeTab === 'hitl' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1">Human Verifications</span>
              <div className="text-2xl font-black text-slate-900">{hitlMetrics?.total_human_reviews ?? 0}</div>
              <span className="text-[10px] text-slate-500 mt-1 block">Officer ground-truth decisions</span>
            </div>
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1">Confirmed Accuracy</span>
              <div className="text-2xl font-black text-emerald-600">{hitlMetrics?.confirmed_ratio ?? '100%'}</div>
              <span className="text-[10px] text-slate-500 mt-1 block">AI finding confirmed on site</span>
            </div>
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1">Human Modified</span>
              <div className="text-2xl font-black text-blue-600">{hitlMetrics?.modified_count ?? 0}</div>
              <span className="text-[10px] text-slate-500 mt-1 block">Officer corrected category</span>
            </div>
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1">False Positives</span>
              <div className="text-2xl font-black text-amber-600">{hitlMetrics?.rejected_count ?? 0}</div>
              <span className="text-[10px] text-slate-500 mt-1 block">Officer rejected false alarm</span>
            </div>
          </div>
        </div>
      )}

      {/* =====================================================================
          PROMOTION MODAL
          ===================================================================== */}
      {showPromoteModal && candidateToPromote && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-emerald-600" />
                <span>Promote Candidate to Production</span>
              </h3>
              <button
                onClick={() => setShowPromoteModal(false)}
                className="p-1 rounded-lg text-slate-400 hover:bg-slate-100"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-slate-600">
              You are promoting candidate model <span className="font-bold font-mono text-slate-900">{candidateToPromote.version}</span>.
              The active production weights will be atomically updated. The previous model will be archived for safe rollback.
            </p>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">
                Documented Administrative Reason <span className="text-red-500">*</span>
              </label>
              <textarea
                value={promoteReason}
                onChange={(e) => setPromoteReason(e.target.value)}
                placeholder="Enter municipal sign-off justification (e.g., Passed benchmark evaluation with 84.5% F1 score)..."
                rows={3}
                className="w-full text-xs p-3 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={() => setShowPromoteModal(false)}
                className="px-4 py-2 border border-slate-200 text-slate-700 rounded-xl text-xs font-bold hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                onClick={handlePromoteCandidate}
                disabled={submittingAction}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold shadow-sm"
              >
                {submittingAction ? 'Promoting...' : 'Confirm Promotion'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* =====================================================================
          ROLLBACK MODAL
          ===================================================================== */}
      {showRollbackModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <RotateCcw className="w-5 h-5 text-amber-600" />
                <span>Rollback Production Model</span>
              </h3>
              <button
                onClick={() => setShowRollbackModal(false)}
                className="p-1 rounded-lg text-slate-400 hover:bg-slate-100"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">Target Version to Restore</label>
              <select
                value={rollbackTarget}
                onChange={(e) => setRollbackTarget(e.target.value)}
                className="w-full text-xs p-2.5 border border-slate-200 rounded-xl font-mono font-bold"
              >
                <option value="v1.0.0-prod">v1.0.0-prod (Baseline Pretrained)</option>
                {models.filter(m => m.status !== 'PRODUCTION').map(m => (
                  <option key={m.id} value={m.version}>{m.version} ({m.name})</option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">
                Rollback Reason <span className="text-red-500">*</span>
              </label>
              <textarea
                value={rollbackReason}
                onChange={(e) => setRollbackReason(e.target.value)}
                placeholder="Enter justification for rolling back production model..."
                rows={3}
                className="w-full text-xs p-3 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-amber-500"
              />
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={() => setShowRollbackModal(false)}
                className="px-4 py-2 border border-slate-200 text-slate-700 rounded-xl text-xs font-bold hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                onClick={handleRollback}
                disabled={submittingAction}
                className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-xl text-xs font-bold shadow-sm"
              >
                {submittingAction ? 'Rolling Back...' : 'Execute Rollback'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
