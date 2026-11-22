import React, { useState, useEffect } from 'react';
import {
  Clock,
  AlertTriangle,
  CheckCircle2,
  ShieldAlert,
  Play,
  Save,
  RotateCcw,
  BarChart3,
  Layers,
  Settings,
  Star,
  Users,
  Info
} from 'lucide-react';
import { slaAPI, serviceFeedbackAPI, incidentsAPI } from '../../services/api';
import { StatusBadge, SeverityBadge } from '../../components/StatusBadge';
import { useLanguage } from '../../context/LanguageContext';

export default function SLAManagementPage() {
  const { t } = useLanguage();
  const [rules, setRules] = useState([]);
  const [loadingRules, setLoadingRules] = useState(true);
  const [savingRules, setSavingRules] = useState(false);
  const [evaluating, setEvaluating] = useState(false);
  const [evalResult, setEvalResult] = useState(null);

  // Active Incidents SLA tracking
  const [incidents, setIncidents] = useState([]);
  const [loadingIncidents, setLoadingIncidents] = useState(true);

  // Service Quality Summary
  const [qualitySummary, setQualitySummary] = useState(null);
  const [loadingQuality, setLoadingQuality] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoadingRules(true);
      setLoadingIncidents(true);
      setLoadingQuality(true);

      const [rulesRes, incRes, qualityRes] = await Promise.all([
        slaAPI.getRules(),
        incidentsAPI.list({ limit: 30 }),
        serviceFeedbackAPI.getSummary(),
      ]);

      setRules(rulesRes.data?.rules || []);
      setIncidents(incRes.data || []);
      setQualitySummary(qualityRes.data);
    } catch (err) {
      console.error('Failed to load SLA management data:', err);
    } finally {
      setLoadingRules(false);
      setLoadingIncidents(false);
      setLoadingQuality(false);
    }
  };

  const handleRuleChange = (idx, field, value) => {
    const updated = [...rules];
    updated[idx] = { ...updated[idx], [field]: Number(value) };
    setRules(updated);
  };

  const handleSaveRules = async () => {
    try {
      setSavingRules(true);
      const res = await slaAPI.updateRules({ rules });
      setRules(res.data?.rules || []);
      alert('SLA rules updated successfully.');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to update SLA rules.');
    } finally {
      setSavingRules(false);
    }
  };

  const handleRunEvaluation = async () => {
    try {
      setEvaluating(true);
      const res = await slaAPI.evaluate();
      setEvalResult(res.data);
      // Reload incidents to reflect newly evaluated milestones and escalations
      const incRes = await incidentsAPI.list({ limit: 30 });
      setIncidents(incRes.data || []);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to run SLA evaluation.');
    } finally {
      setEvaluating(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6 pb-20">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200/80 pb-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1 rounded-md bg-slate-100 text-slate-700 border border-slate-200">
              <Clock className="w-4 h-4" />
            </span>
            <h1 className="text-base font-bold text-slate-900 tracking-tight">
              {t('slaManagement') || 'Municipal SLA & Escalation Engine'}
            </h1>
          </div>
          <p className="text-xs text-slate-500 font-normal mt-0.5">
            Configure target response and resolution milestones, monitor automated supervisor escalations, and review citizen satisfaction benchmarks
          </p>
        </div>

        <button
          onClick={handleRunEvaluation}
          disabled={evaluating}
          className="px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold transition-all shadow-2xs flex items-center justify-center gap-1.5 disabled:opacity-50 self-start sm:self-auto"
        >
          <Play className="w-3.5 h-3.5 fill-white" />
          <span>{evaluating ? 'Evaluating Incidents...' : t('evaluateSLANow') || 'Run SLA Evaluation Sweep'}</span>
        </button>
      </div>

      {/* Evaluation Sweep Results Banner */}
      {evalResult && (
        <div className="bg-indigo-50 border border-indigo-200 rounded-2xl p-4 text-xs text-indigo-950 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 animate-scale-in">
          <div className="space-y-1">
            <div className="font-bold flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-indigo-600" />
              SLA Sweep Completed Successfully
            </div>
            <p className="text-indigo-800">
              Evaluated <strong>{evalResult.incidents_evaluated}</strong> active incidents &bull; Detected{' '}
              <strong className="text-amber-700">{evalResult.approaching_deadlines_detected}</strong> approaching deadlines &bull;{' '}
              <strong className="text-red-700">{evalResult.breaches_detected}</strong> SLA breaches &bull; Triggered{' '}
              <strong className="text-purple-700">{evalResult.escalations_triggered}</strong> supervisor escalations.
            </p>
          </div>
          <button
            onClick={() => setEvalResult(null)}
            className="text-indigo-600 hover:text-indigo-800 font-bold px-3 py-1 bg-white rounded-lg border border-indigo-200"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Top Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-500">
            <span>Citizen Satisfaction</span>
            <Star className="w-4 h-4 text-amber-500 fill-amber-500" />
          </div>
          <div className="text-2xl font-black text-slate-900 mt-2">
            {loadingQuality ? '...' : `${qualitySummary?.average_satisfaction ?? 'N/A'}/5`}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">
            From {qualitySummary?.total_feedbacks ?? 0} citizen reviews
          </div>
        </div>

        <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-500">
            <span>Timeliness Rating</span>
            <Clock className="w-4 h-4 text-blue-500" />
          </div>
          <div className="text-2xl font-black text-blue-600 mt-2">
            {loadingQuality ? '...' : `${qualitySummary?.average_timeliness ?? 'N/A'}/5`}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Resolution speed feedback</div>
        </div>

        <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-500">
            <span>Active Escalations</span>
            <ShieldAlert className="w-4 h-4 text-red-500" />
          </div>
          <div className="text-2xl font-black text-red-600 mt-2">
            {incidents.filter((i) => i.is_escalated).length}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Supervisory intervention active</div>
        </div>

        <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-500">
            <span>Active SLA Rules</span>
            <Settings className="w-4 h-4 text-indigo-500" />
          </div>
          <div className="text-2xl font-black text-indigo-600 mt-2">
            {rules.length}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Target policies configured</div>
        </div>
      </div>

      {/* SLA Rules Configuration Table */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
          <div>
            <h2 className="text-base font-bold text-slate-900">Municipal SLA Target Rules</h2>
            <p className="text-xs text-slate-500">
              Configurable operational milestone targets for field response and final clearance by category and severity.
            </p>
          </div>
          <button
            onClick={handleSaveRules}
            disabled={savingRules}
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold transition-colors flex items-center gap-1.5 shadow-xs disabled:opacity-50"
          >
            <Save className="w-3.5 h-3.5" />
            <span>{savingRules ? 'Saving...' : 'Save Rule Changes'}</span>
          </button>
        </div>

        {loadingRules ? (
          <div className="py-8 text-center text-slate-400 text-xs animate-pulse">Loading SLA rules...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 font-bold border-b border-slate-200">
                <tr>
                  <th className="p-3">Category</th>
                  <th className="p-3">Severity</th>
                  <th className="p-3">Response Target (Hours)</th>
                  <th className="p-3">Resolution Target (Hours)</th>
                  <th className="p-3">Escalation Threshold (%)</th>
                  <th className="p-3">Supervisor Role</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {rules.map((rule, idx) => (
                  <tr key={`${rule.category}-${rule.severity}`} className="hover:bg-slate-50/50">
                    <td className="p-3 font-semibold text-slate-900">{rule.category}</td>
                    <td className="p-3">
                      <SeverityBadge severity={rule.severity} />
                    </td>
                    <td className="p-3">
                      <input
                        type="number"
                        min={1}
                        max={168}
                        value={rule.response_target_hours}
                        onChange={(e) => handleRuleChange(idx, 'response_target_hours', e.target.value)}
                        className="w-20 px-2 py-1 bg-slate-50 border border-slate-200 rounded-lg text-xs font-mono font-bold"
                      />
                      <span className="ml-1 text-[11px] text-slate-400">hrs</span>
                    </td>
                    <td className="p-3">
                      <input
                        type="number"
                        min={1}
                        max={720}
                        value={rule.resolution_target_hours}
                        onChange={(e) => handleRuleChange(idx, 'resolution_target_hours', e.target.value)}
                        className="w-20 px-2 py-1 bg-slate-50 border border-slate-200 rounded-lg text-xs font-mono font-bold"
                      />
                      <span className="ml-1 text-[11px] text-slate-400">hrs</span>
                    </td>
                    <td className="p-3">
                      <input
                        type="number"
                        min={50}
                        max={95}
                        value={rule.escalation_threshold_pct}
                        onChange={(e) => handleRuleChange(idx, 'escalation_threshold_pct', e.target.value)}
                        className="w-16 px-2 py-1 bg-slate-50 border border-slate-200 rounded-lg text-xs font-mono font-bold"
                      />
                      <span className="ml-1 text-[11px] text-slate-400">%</span>
                    </td>
                    <td className="p-3 font-mono text-[11px] text-slate-600">
                      {rule.escalation_supervisor_role}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Incident SLA Status & Escalation Monitor */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-xs space-y-4">
        <h2 className="text-base font-bold text-slate-900">Live Incident Milestone & Escalation Monitor</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 font-bold border-b border-slate-200">
              <tr>
                <th className="p-3">Incident #</th>
                <th className="p-3">Type & Ward</th>
                <th className="p-3">Status</th>
                <th className="p-3">Severity</th>
                <th className="p-3">Response SLA</th>
                <th className="p-3">Resolution SLA</th>
                <th className="p-3">Escalation State</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {incidents.length > 0 ? (
                incidents.slice(0, 15).map((inc) => {
                  const sla = inc.sla_status;
                  const isEscalated = inc.is_escalated;

                  return (
                    <tr key={inc.id} className="hover:bg-slate-50/50">
                    <td className="p-3 font-mono font-bold text-blue-600">{inc.incident_number}</td>
                    <td className="p-3">
                      <div className="font-semibold text-slate-900">{inc.primary_encroachment_type}</div>
                      <div className="text-[11px] text-slate-400">{inc.location_name}</div>
                    </td>
                    <td className="p-3">
                      <StatusBadge status={inc.status} />
                    </td>
                    <td className="p-3">
                      <SeverityBadge severity={inc.severity} />
                    </td>
                    <td className="p-3">
                      {sla?.response_milestone ? (
                        <div className="space-y-0.5">
                          <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            sla.response_milestone.status === 'COMPLETED'
                              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                              : sla.response_milestone.status === 'OVERDUE'
                              ? 'bg-red-50 text-red-700 border border-red-200'
                              : 'bg-blue-50 text-blue-700 border border-blue-200'
                          }`}>
                            {sla.response_milestone.status}
                          </span>
                          <div className="text-[10px] text-slate-400">
                            {sla.response_milestone.time_remaining_minutes !== null
                              ? `${Math.round(sla.response_milestone.time_remaining_minutes / 60)}h remaining`
                              : ''}
                          </div>
                        </div>
                      ) : (
                        <span className="text-slate-400">On Track</span>
                      )}
                    </td>
                    <td className="p-3">
                      {sla?.resolution_milestone ? (
                        <div className="space-y-0.5">
                          <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            sla.resolution_milestone.status === 'COMPLETED'
                              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                              : sla.resolution_milestone.status === 'OVERDUE'
                              ? 'bg-red-50 text-red-700 border border-red-200'
                              : 'bg-indigo-50 text-indigo-700 border border-indigo-200'
                          }`}>
                            {sla.resolution_milestone.status}
                          </span>
                          <div className="text-[10px] text-slate-400">
                            {sla.resolution_milestone.time_remaining_minutes !== null
                              ? `${Math.round(sla.resolution_milestone.time_remaining_minutes / 60)}h remaining`
                              : ''}
                          </div>
                        </div>
                      ) : (
                        <span className="text-slate-400">In Progress</span>
                      )}
                    </td>
                    <td className="p-3">
                      {isEscalated ? (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300 flex items-center gap-1 w-fit">
                          <AlertTriangle className="w-3 h-3 text-amber-700" />
                          Escalated (L{inc.escalation_level})
                        </span>
                      ) : (
                        <span className="text-[11px] text-slate-400">Normal</span>
                      )}
                    </td>
                  </tr>
                );
              })
            ) : (
              <tr>
                <td colSpan={7} className="p-8 text-center text-slate-400">
                  No active incidents under SLA tracking.
                </td>
              </tr>
            )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
