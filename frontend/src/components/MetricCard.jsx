import React from 'react';

export default function MetricCard({ icon: Icon, value, label, iconBg, iconColor }) {
  return (
    <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm hover:shadow-md transition-shadow duration-200 flex items-center gap-4">
      <div className={`w-12 h-12 rounded-full ${iconBg} flex items-center justify-center shrink-0`}>
        <Icon className={`w-6 h-6 ${iconColor}`} />
      </div>
      <div>
        <div className="text-2xl font-bold text-slate-800 tracking-tight leading-tight">{value}</div>
        <div className="text-xs font-medium text-slate-400 mt-0.5">{label}</div>
      </div>
    </div>
  );
}
