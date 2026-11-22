import React from 'react';

export default function EncroWatchLogo({ size = 'md', light = false, showSubtitle = false }) {
  const isSm = size === 'sm';
  const isLg = size === 'lg';

  const iconBox = isSm ? 'w-7 h-7 rounded-lg' : isLg ? 'w-10 h-10 rounded-xl' : 'w-8 h-8 rounded-lg';
  const textSize = isSm ? 'text-sm' : isLg ? 'text-xl' : 'text-base';

  return (
    <div className="flex items-center gap-2.5 select-none">
      {/* Modern crisp emblem: road and green pedestrian corridor */}
      <div className={`${iconBox} bg-[#0F172A] border border-slate-700 p-1 flex items-center justify-center shrink-0`}>
        <svg viewBox="0 0 32 32" className="w-full h-full fill-none" aria-hidden="true">
          {/* Road surface */}
          <path d="M12 28L15 4H17L20 28H12Z" fill="#334155" />
          {/* Dashed center line */}
          <line x1="16" y1="7" x2="16" y2="11" stroke="#F8FAFC" strokeWidth="1.5" strokeLinecap="round" />
          <line x1="16" y1="15" x2="16" y2="19" stroke="#F8FAFC" strokeWidth="1.5" strokeLinecap="round" />
          <line x1="16" y1="23" x2="16" y2="27" stroke="#F8FAFC" strokeWidth="1.5" strokeLinecap="round" />
          {/* Protected Pedestrian Green Pathway */}
          <path d="M4 28L10 4H12L6 28H4Z" fill="#059669" />
          {/* Accessibility Indicator Node */}
          <circle cx="8" cy="8" r="2" fill="#34D399" />
          {/* Right Road Shoulder */}
          <path d="M20 28L26 4H28L22 28H20Z" fill="#2563EB" opacity="0.6" />
        </svg>
      </div>

      <div className="leading-tight">
        <div className={`font-bold ${textSize} tracking-tight ${light ? 'text-white' : 'text-slate-900'}`}>
          <span>EncroWatch</span> <span className="text-emerald-500 font-extrabold">AI</span>
        </div>
        {showSubtitle && (
          <p className={`text-[10px] font-medium tracking-normal ${light ? 'text-slate-400' : 'text-slate-500'}`}>
            Urban Accessibility Intelligence
          </p>
        )}
      </div>
    </div>
  );
}
