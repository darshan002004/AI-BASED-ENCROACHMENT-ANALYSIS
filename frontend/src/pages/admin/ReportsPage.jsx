import React, { useState, useEffect } from 'react';
import {
  FileText,
  Download,
  Calendar,
  Filter,
  CheckCircle2,
  AlertTriangle,
  MapPin,
  Clock,
  Printer
} from 'lucide-react';
import { reportsAPI, analyticsAPI, incidentsAPI } from '../../services/api';

export default function ReportsPage() {
  const [selectedReport, setSelectedReport] = useState('Incident Report');
  const [kpis, setKpis] = useState(null);
  const [firstIncidentId, setFirstIncidentId] = useState(null);

  useEffect(() => {
    analyticsAPI.getKPIs()
      .then((res) => setKpis(res.data))
      .catch(console.warn);

    (incidentsAPI.list || incidentsAPI.getAll)({ limit: 1 })
      .then((res) => {
        if (res.data && res.data.length > 0) {
          setFirstIncidentId(res.data[0].id || res.data[0]._id);
        }
      })
      .catch(console.warn);
  }, []);

  const reportCategories = [
    {
      id: 'Incident Report',
      title: 'Incident Report',
      description: 'Comprehensive dossier of cataloged road and footpath encroachments with geocodes and severity.',
      records: kpis ? `${kpis.total_incidents} Records` : 'Cataloged Incidents',
      icon: FileText,
      color: 'text-blue-600',
      bg: 'bg-blue-50'
    },
    {
      id: 'Monthly Report',
      title: 'Monthly Report',
      description: 'Longitudinal monthly trends, seasonal variations, and municipal clearance statistics.',
      records: 'Annual Aggregated Data',
      icon: Calendar,
      color: 'text-purple-600',
      bg: 'bg-purple-50'
    },
    {
      id: 'Area Report',
      title: 'Area Report',
      description: 'Ward-by-ward walkability index, hotspot density rankings, and top affected urban corridors.',
      records: kpis ? `${kpis.active_hotspots} Active Clusters` : 'Active Ward Hotspots',
      icon: MapPin,
      color: 'text-emerald-600',
      bg: 'bg-emerald-50'
    },
    {
      id: 'Severity Report',
      title: 'Severity Report',
      description: 'Focus on high-severity barriers violating IRC:SP:102-2014 and ADA accessibility thresholds.',
      records: kpis ? `${kpis.high_severity_count} High-Priority` : 'High-Priority Incidents',
      icon: AlertTriangle,
      color: 'text-red-600',
      bg: 'bg-red-50'
    },
    {
      id: 'Resolution Report',
      title: 'Resolution Report',
      description: 'Audit log of field officer site clearances verified by dual-inference AI Before/After analysis.',
      records: kpis ? `${kpis.verified_resolved_count} Verified Clearances` : 'Verified Field Clearances',
      icon: CheckCircle2,
      color: 'text-teal-600',
      bg: 'bg-teal-50'
    }
  ];

  const handleGeneratePDF = (reportName) => {
    if (firstIncidentId) {
      window.open(reportsAPI.getIncidentPDFUrl(firstIncidentId), '_blank');
    } else {
      alert('No incident records are available to generate a PDF dossier. Please report an incident first.');
    }
  };

  const handleExportCSV = (reportName) => {
    window.open(reportsAPI.getCSVUrl(), '_blank');
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200/80 pb-4">
        <div>
          <h1 className="text-base font-bold text-slate-900 tracking-tight">Report Generation &amp; Export</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Export official municipal compliance audits, walkability assessments, and spatial incident datasets
          </p>
        </div>

        {/* Global Quick Action Buttons */}
        <div className="flex items-center gap-2 self-start sm:self-auto">
          <button
            onClick={() => handleGeneratePDF(selectedReport)}
            className="px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold shadow-2xs flex items-center gap-1.5 transition-colors"
          >
            <Printer className="w-3.5 h-3.5" />
            <span>Generate PDF</span>
          </button>
          <button
            onClick={() => handleExportCSV(selectedReport)}
            className="px-3.5 py-1.5 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-lg text-xs font-semibold shadow-2xs flex items-center gap-1.5 transition-colors"
          >
            <Download className="w-3.5 h-3.5 text-slate-500" />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* 5 Report Categories */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {reportCategories.map((rep) => {
          const Icon = rep.icon;
          const isSelected = selectedReport === rep.id;

          return (
            <div
              key={rep.id}
              onClick={() => setSelectedReport(rep.id)}
              className={`bg-white rounded-xl p-5 border transition-all duration-150 shadow-2xs flex flex-col justify-between cursor-pointer ${
                isSelected
                  ? 'border-slate-800 ring-1 ring-slate-800'
                  : 'border-slate-200/90 hover:border-slate-300'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className={`w-9 h-9 rounded-lg ${rep.bg} flex items-center justify-center ${rep.color} border border-slate-100`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <span className="text-[11px] font-medium text-slate-500 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                    {rep.records}
                  </span>
                </div>

                <h3 className="text-sm font-bold text-slate-900 mb-1">{rep.title}</h3>
                <p className="text-xs text-slate-500 leading-relaxed font-normal">
                  {rep.description}
                </p>
              </div>

              {/* Action Buttons for this Report */}
              <div className="pt-4 mt-4 border-t border-slate-100 flex items-center gap-2">
                <button
                  onClick={(e) => { e.stopPropagation(); handleGeneratePDF(rep.id); }}
                  className="flex-1 py-1.5 px-3 text-xs font-semibold text-white bg-slate-900 hover:bg-slate-800 rounded-lg shadow-2xs flex items-center justify-center gap-1.5 transition-colors"
                >
                  <FileText className="w-3.5 h-3.5" />
                  <span>Generate PDF</span>
                </button>
                <button
                  onClick={(e) => { e.stopPropagation(); handleExportCSV(rep.id); }}
                  className="py-1.5 px-3 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg flex items-center justify-center gap-1.5 transition-colors border border-slate-200"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>CSV</span>
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
