import React, { useState, useEffect } from 'react';
import {
  Smartphone,
  ScanEye,
  ShieldCheck,
  CheckCircle2,
  MapPin,
  ArrowRight,
  Clock,
  Layers,
  Compass,
  FileText,
  Activity,
  AlertTriangle,
  HelpCircle,
  ExternalLink,
  ChevronRight,
  Cpu,
  Shield,
  Mail,
  Phone,
  Building2
} from 'lucide-react';
import EncroWatchLogo from '../components/EncroWatchLogo';
import { publicAPI } from '../services/api';

export default function LandingPage({ onEnterApp }) {
  const [stats, setStats] = useState(null);
  const [loadingStats, setLoadingStats] = useState(true);

  useEffect(() => {
    const fetchPublicStats = async () => {
      try {
        const res = await publicAPI.getStatistics(30);
        setStats(res.data);
      } catch (e) {
        console.warn('Could not load public statistics on landing page:', e);
      } finally {
        setLoadingStats(false);
      }
    };
    fetchPublicStats();
  }, []);

  const workflowSteps = [
    {
      number: '01',
      title: 'Report Obstruction',
      desc: 'Citizens and field surveyors capture sidewalk encroachments with geotagged mobile evidence.',
      icon: Smartphone,
    },
    {
      number: '02',
      title: 'AI Analysis & Triage',
      desc: 'Computer vision identifies obstruction boundaries, classifies encroachment types, and calculates corridor walkability index.',
      icon: ScanEye,
    },
    {
      number: '03',
      title: 'Officer Field Verification',
      desc: 'Assigned municipal ward officers conduct on-site inspections, verify spatial evidence, and initiate clearance.',
      icon: ShieldCheck,
    },
    {
      number: '04',
      title: 'Verified Resolution',
      desc: 'Dual photographic proof confirms clear pedestrian access before case closure with tamper-evident audit logging.',
      icon: CheckCircle2,
    },
  ];

  const reportableCategories = [
    {
      title: 'Street Vendor Encroachment',
      desc: 'Unauthorized commercial kiosks, fruit carts, or temporary stalls obstructing designated footpaths.',
      guidance: 'Capture stall width in relation to remaining usable walkway.',
      icon: Layers,
    },
    {
      title: 'Vehicular Footpath Parking',
      desc: 'Two-wheelers and passenger vehicles parked on raised sidewalks or pedestrian ramps.',
      guidance: 'Photograph vehicle position and unobstructed pedestrian clearance width.',
      icon: AlertTriangle,
    },
    {
      title: 'Construction Material & Debris',
      desc: 'Sand, bricks, scaffolding, or demolition waste blocking public rights-of-way.',
      guidance: 'Highlight hazard distance from the primary road boundary.',
      icon: Activity,
    },
    {
      title: 'Commercial Extensions',
      desc: 'Permanent awnings, display boards, or stairs extending beyond legal property lines.',
      guidance: 'Provide clear view of the curb and pedestrian flow bottleneck.',
      icon: Compass,
    },
  ];

  return (
    <div className="min-h-screen bg-[#F5F7FA] text-[#172033] flex flex-col font-sans selection:bg-emerald-500 selection:text-white">
      {/* 1. Header (Compact Single Bar: 68px) */}
      <header className="h-[68px] bg-white border-b border-slate-200 px-6 sm:px-10 flex items-center justify-between sticky top-0 z-40 shadow-xs">
        {/* Brand */}
        <EncroWatchLogo size="md" light={false} showSubtitle={true} />

        {/* Navigation Links */}
        <nav className="hidden md:flex items-center gap-6 text-xs font-semibold text-slate-600">
          <a href="#hero" className="text-slate-900 hover:text-emerald-700 transition-colors">
            Home
          </a>
          <a href="#features" className="hover:text-emerald-700 transition-colors">
            Features
          </a>
          <a href="#workflow" className="hover:text-emerald-700 transition-colors">
            How It Works
          </a>
          <button
            onClick={() => onEnterApp('public-transparency')}
            className="hover:text-emerald-700 transition-colors flex items-center gap-1 font-semibold"
          >
            Public Map
          </button>
          <a href="#about" className="hover:text-emerald-700 transition-colors">
            About
          </a>
          <a href="#contact" className="hover:text-emerald-700 transition-colors">
            Contact
          </a>
        </nav>

        {/* Authentication Controls */}
        <div className="flex items-center gap-2.5">
          <button
            onClick={() => onEnterApp('login')}
            className="px-3.5 py-1.5 text-xs font-semibold text-slate-700 hover:text-slate-900 rounded-lg hover:bg-slate-100 transition-colors"
          >
            Login
          </button>
          <button
            onClick={() => onEnterApp('register')}
            className="px-3.5 py-1.5 text-xs font-semibold text-slate-800 bg-slate-100 hover:bg-slate-200 border border-slate-200 rounded-lg transition-colors"
          >
            Sign Up
          </button>
          <button
            onClick={() => onEnterApp('citizen-report')}
            className="px-3.5 py-1.5 text-xs font-semibold text-white bg-[#059669] hover:bg-[#047857] rounded-lg shadow-2xs transition-colors flex items-center gap-1.5"
          >
            <span>Report Issue</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </header>

      {/* 2. Hero Section: Balanced Two-Column Layout */}
      <section id="hero" className="py-12 sm:py-16 px-6 sm:px-10 max-w-7xl mx-auto w-full">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
          {/* Left Column: Narrative & Primary CTAs */}
          <div className="lg:col-span-6 space-y-6">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md text-[11px] font-bold tracking-wider uppercase bg-slate-100 text-slate-700 border border-slate-200">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-600" />
              Urban Accessibility Intelligence
            </div>

            <h1 className="text-3xl sm:text-4xl lg:text-[42px] font-extrabold text-[#172033] tracking-tight leading-[1.2]">
              AI-Powered Urban Accessibility Monitoring
            </h1>

            <p className="text-sm sm:text-base text-slate-600 leading-relaxed font-normal max-w-xl">
              An enterprise municipal intelligence platform that identifies footpath obstructions, evaluates pedestrian walkability bottlenecks in accordance with urban mobility standards, and orchestrates field clearance verification for safer, barrier-free public rights-of-way.
            </p>

            {/* Action Buttons */}
            <div className="flex flex-wrap items-center gap-3 pt-2">
              <button
                onClick={() => onEnterApp('citizen-report')}
                className="px-6 py-3 rounded-lg bg-[#059669] hover:bg-[#047857] text-white text-xs font-bold shadow-xs flex items-center gap-2 transition-colors"
              >
                <Smartphone className="w-4 h-4" />
                <span>Report an Issue</span>
              </button>

              <button
                onClick={() => onEnterApp('public-transparency')}
                className="px-6 py-3 rounded-lg bg-white hover:bg-slate-50 text-slate-800 text-xs font-bold border border-slate-300 shadow-xs flex items-center gap-2 transition-colors"
              >
                <Compass className="w-4 h-4 text-blue-600" />
                <span>Explore Public Map</span>
              </button>
            </div>

            {/* Credibility Checklist */}
            <div className="pt-3 border-t border-slate-200/80 flex flex-wrap items-center gap-6 text-xs text-slate-500 font-medium">
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                IRC:SP:102 Accessibility Metrics
              </span>
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                Tamper-Evident SHA-256 Audit Trail
              </span>
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                Verified Municipal Closure
              </span>
            </div>
          </div>

          {/* Right Column: High-Credibility Urban Accessibility Visualization */}
          <div className="lg:col-span-6">
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
              {/* GIS Card Header */}
              <div className="bg-slate-900 text-white px-4 py-3 flex items-center justify-between text-xs border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-400" />
                  <span className="font-semibold text-slate-200 font-mono text-[11px]">
                    GIS CORRIDOR ASSESSMENT • WARD 142
                  </span>
                </div>
                <span className="text-[11px] text-slate-400 font-mono">IRC:SP:102 Standards</span>
              </div>

              {/* Corridor Visualization */}
              <div className="relative h-64 sm:h-72 bg-slate-100 overflow-hidden">
                <img
                  src="/uploads/original/vendor_mg_road.jpg"
                  alt="Urban Sidewalk Inspection Corridor"
                  onError={(e) => {
                    e.currentTarget.onerror = null;
                    e.currentTarget.src = '/uploads/original/clear_street.jpg';
                  }}
                  className="w-full h-full object-cover"
                />

                {/* Pedestrian Corridor Zone Overlay */}
                <div className="absolute inset-y-0 left-0 w-2/5 bg-emerald-600/20 border-r-2 border-dashed border-emerald-400 pointer-events-none flex flex-col justify-between p-3">
                  <span className="px-2 py-0.5 rounded bg-slate-900/80 text-emerald-300 font-mono text-[10px] font-bold w-fit">
                    Pedestrian Walking Path
                  </span>
                  <span className="px-2 py-0.5 rounded bg-slate-900/80 text-white font-mono text-[10px] w-fit">
                    Min Required: 1.8m
                  </span>
                </div>

                {/* Obstructed Footpath Indicator */}
                <div className="absolute top-1/4 left-1/4 p-2 bg-slate-900/85 backdrop-blur-xs text-white rounded-lg border border-red-500/80 text-[11px] space-y-0.5 shadow-md max-w-[210px]">
                  <div className="flex items-center gap-1.5 text-red-400 font-bold">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    <span>Sidewalk Obstruction</span>
                  </div>
                  <div className="text-[10px] text-slate-300">
                    Remaining Width: <strong className="text-white">0.65m</strong> (&lt; 1.8m minimum)
                  </div>
                  <div className="text-[10px] text-amber-300 font-medium">
                    Accessibility Bottleneck Detected
                  </div>
                </div>
              </div>

              {/* Real-time Assessment Telemetry Bar */}
              <div className="p-4 bg-white grid grid-cols-3 divide-x divide-slate-100 text-center text-xs">
                <div>
                  <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                    Path Walkability
                  </div>
                  <div className="text-base font-bold text-emerald-700 mt-0.5">82.4%</div>
                  <div className="text-[10px] text-slate-500">Benchmark Index</div>
                </div>
                <div>
                  <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                    Corridor Width
                  </div>
                  <div className="text-base font-bold text-slate-800 mt-0.5">2.4 m</div>
                  <div className="text-[10px] text-slate-500">Design Standard</div>
                </div>
                <div>
                  <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                    Enforcement Status
                  </div>
                  <div className="text-base font-bold text-blue-600 mt-0.5">Active Queue</div>
                  <div className="text-[10px] text-slate-500">Field Dispatch</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 3. Core Architectural Features */}
      <section id="features" className="py-12 px-6 sm:px-10 bg-slate-50 border-t border-slate-200">
        <div className="max-w-7xl mx-auto space-y-8">
          <div className="text-center max-w-2xl mx-auto">
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
              Platform Architecture
            </span>
            <h2 className="text-2xl font-bold text-slate-900 mt-1">
              Integrated Smart-City Accessibility Intelligence
            </h2>
            <p className="text-xs text-slate-500 mt-1.5 leading-relaxed">
              Engineered to replace manual, fragmented sidewalk complaint workflows with verifiable computer vision and cryptographically auditable municipal enforcement.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
            <div className="p-5 rounded-xl border border-slate-200 bg-white space-y-3 shadow-2xs">
              <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center border border-emerald-100">
                <ScanEye className="w-5 h-5" />
              </div>
              <h3 className="text-sm font-bold text-slate-900">AI-Assisted Detection</h3>
              <p className="text-xs text-slate-600 leading-relaxed font-normal">
                Dual OpenCV vision pipeline and YOLOv5 object segmentation assessing spatial corridor obstruction, residual pedestrian clearance width, and wheelchair accessibility bottlenecks.
              </p>
            </div>

            <div className="p-5 rounded-xl border border-slate-200 bg-white space-y-3 shadow-2xs">
              <div className="w-10 h-10 rounded-lg bg-blue-50 text-blue-700 flex items-center justify-center border border-blue-100">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <h3 className="text-sm font-bold text-slate-900">Municipal Verification</h3>
              <p className="text-xs text-slate-600 leading-relaxed font-normal">
                Field officer dispatch with photographic before/after clearance submissions and independent administrative review to eliminate false positives and unverified closures.
              </p>
            </div>

            <div className="p-5 rounded-xl border border-slate-200 bg-white space-y-3 shadow-2xs">
              <div className="w-10 h-10 rounded-lg bg-amber-50 text-amber-700 flex items-center justify-center border border-amber-100">
                <Clock className="w-5 h-5" />
              </div>
              <h3 className="text-sm font-bold text-slate-900">Incident Resolution</h3>
              <p className="text-xs text-slate-600 leading-relaxed font-normal">
                Strict SLA deadline tracking mapped by severity and obstruction category, triggering automated supervisory escalation when critical rights-of-way remain blocked.
              </p>
            </div>

            <div className="p-5 rounded-xl border border-slate-200 bg-white space-y-3 shadow-2xs">
              <div className="w-10 h-10 rounded-lg bg-purple-50 text-purple-700 flex items-center justify-center border border-purple-100">
                <Compass className="w-5 h-5" />
              </div>
              <h3 className="text-sm font-bold text-slate-900">Public Transparency</h3>
              <p className="text-xs text-slate-600 leading-relaxed font-normal">
                Open citizen portal publishing verified municipal resolution records with privacy blur on facial/vehicle details and coarse 1.1km grid spatial coordinates.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 4. Platform Workflow (4 Steps with Line Icons) */}
      <section id="workflow" className="py-12 px-6 sm:px-10 bg-white border-y border-slate-200">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-xl mx-auto mb-10">
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
              System Lifecycle
            </span>
            <h2 className="text-2xl font-bold text-slate-900 mt-1">
              End-to-End Municipal Resolution Workflow
            </h2>
            <p className="text-xs text-slate-500 mt-1.5">
              Structured accountability from citizen complaint to verified physical clearance.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {workflowSteps.map((step) => {
              const Icon = step.icon;
              return (
                <div
                  key={step.number}
                  className="p-5 rounded-xl border border-slate-200 bg-[#F5F7FA] space-y-3 relative flex flex-col justify-between"
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="w-10 h-10 rounded-lg bg-white border border-slate-200 text-slate-800 flex items-center justify-center shadow-2xs">
                        <Icon className="w-5 h-5 text-slate-700" />
                      </div>
                      <span className="text-xs font-mono font-bold text-slate-400">{step.number}</span>
                    </div>

                    <h3 className="text-sm font-bold text-slate-900">{step.title}</h3>
                    <p className="text-xs text-slate-600 leading-relaxed font-normal">{step.desc}</p>
                  </div>

                  <div className="pt-2 border-t border-slate-200/60 text-[10px] text-slate-400 font-medium">
                    Municipal Phase {step.number}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* 4. Verified Municipal Performance Stats (From Backend) */}
      <section className="py-12 px-6 sm:px-10 max-w-7xl mx-auto w-full">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-8">
          <div>
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
              Transparency Data
            </span>
            <h2 className="text-2xl font-bold text-slate-900 mt-1">
              Live Public Operations Telemetry
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Aggregated from genuine municipal incidents recorded across urban corridors.
            </p>
          </div>

          <button
            onClick={() => onEnterApp('public-transparency')}
            className="text-xs font-bold text-blue-600 hover:text-blue-700 flex items-center gap-1.5 self-start md:self-auto"
          >
            <span>Open Transparency Dashboard</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
            <div className="text-xs font-semibold text-slate-500">Total Cases Logged</div>
            <div className="text-2xl font-extrabold text-slate-900 mt-1.5">
              {loadingStats ? '—' : stats?.total_reports_received ?? stats?.total_reported ?? 0}
            </div>
            <div className="text-[11px] text-slate-400 mt-0.5">30-day municipal window</div>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
            <div className="text-xs font-semibold text-slate-500">Verified Clearances</div>
            <div className="text-2xl font-extrabold text-[#059669] mt-1.5">
              {loadingStats ? '—' : stats?.verified_resolutions ?? stats?.verified_resolved ?? 0}
            </div>
            <div className="text-[11px] text-emerald-700 font-medium mt-0.5">
              Confirmed obstruction removals
            </div>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
            <div className="text-xs font-semibold text-slate-500">Verified Resolution Rate</div>
            <div className="text-2xl font-extrabold text-slate-900 mt-1.5">
              {loadingStats
                ? '—'
                : `${stats?.resolution_rate_pct ?? stats?.verified_clearance_rate_pct ?? 0}%`}
            </div>
            <div className="text-[11px] text-slate-400 mt-0.5">Verified / total reports</div>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
            <div className="text-xs font-semibold text-slate-500">Avg. Resolution Duration</div>
            <div className="text-2xl font-extrabold text-slate-900 mt-1.5">
              {loadingStats
                ? '—'
                : `${stats?.average_resolution_days ?? stats?.avg_resolution_days ?? 0} days`}
            </div>
            <div className="text-[11px] text-slate-400 mt-0.5">Inspection to verification</div>
          </div>
        </div>
      </section>

      {/* 5. Reportable Encroachment Types & Citizen Guidelines */}
      <section id="categories" className="py-12 px-6 sm:px-10 bg-white border-t border-slate-200">
        <div className="max-w-7xl mx-auto space-y-8">
          <div>
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
              Citizen Reporting Guide
            </span>
            <h2 className="text-2xl font-bold text-slate-900 mt-1">
              Reportable Obstruction Categories
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              Guidelines for documenting physical barriers affecting pedestrian safety and wheelchair accessibility.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {reportableCategories.map((cat, i) => {
              const Icon = cat.icon;
              return (
                <div key={i} className="p-5 rounded-xl border border-slate-200 bg-[#F5F7FA] space-y-2.5">
                  <div className="w-9 h-9 rounded-lg bg-white border border-slate-200 text-slate-800 flex items-center justify-center">
                    <Icon className="w-4 h-4 text-slate-700" />
                  </div>
                  <h3 className="text-sm font-bold text-slate-900">{cat.title}</h3>
                  <p className="text-xs text-slate-600 leading-relaxed font-normal">{cat.desc}</p>
                  <div className="pt-2 border-t border-slate-200/60 text-[11px] text-slate-500">
                    <strong className="text-slate-700">Photo Tip:</strong> {cat.guidance}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* 6. Municipal Governance & Footer */}
      <footer id="about" className="mt-auto bg-[#111827] text-slate-400 py-12 px-6 sm:px-10 border-t border-slate-800">
        <div className="max-w-7xl mx-auto space-y-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-xs">
            {/* About Column */}
            <div className="space-y-3">
              <EncroWatchLogo size="md" light={true} showSubtitle={true} />
              <p className="text-slate-400 text-xs leading-relaxed">
                EncroWatch AI is an urban accessibility monitoring and municipal incident management platform designed for smart city transit authorities and urban local bodies.
              </p>
              <div className="text-[11px] text-slate-500">
                Adhering to Indian Road Congress IRC:SP:102 Pedestrian Accessibility Guidelines.
              </div>
            </div>

            {/* Platform Quick Links */}
            <div className="space-y-2.5">
              <div className="text-white font-semibold text-xs uppercase tracking-wider">Operational Portals</div>
              <ul className="space-y-1.5 text-slate-400">
                <li><button onClick={() => onEnterApp('citizen-report')} className="hover:text-emerald-400 transition-colors">Citizen Incident Reporting</button></li>
                <li><button onClick={() => onEnterApp('public-transparency')} className="hover:text-emerald-400 transition-colors">Public Transparency &amp; Open Data</button></li>
                <li><button onClick={() => onEnterApp('login')} className="hover:text-emerald-400 transition-colors">Municipal Officer Field Login</button></li>
                <li><button onClick={() => onEnterApp('login')} className="hover:text-emerald-400 transition-colors">Administrative Control Center</button></li>
                <li><button onClick={() => onEnterApp('register')} className="hover:text-emerald-400 transition-colors">Officer Account Registration</button></li>
              </ul>
            </div>

            {/* Contact Column */}
            <div id="contact" className="space-y-2.5">
              <div className="text-white font-semibold text-xs uppercase tracking-wider">Municipal Operations Contact</div>
              <div className="space-y-2 text-slate-400 text-xs">
                <div className="flex items-center gap-2">
                  <Building2 className="w-4 h-4 text-slate-500 shrink-0" />
                  <span>Encroachment Removal &amp; Urban Mobility Squad</span>
                </div>
                <div className="flex items-center gap-2">
                  <MapPin className="w-4 h-4 text-slate-500 shrink-0" />
                  <span>Central Municipal Corporation Headquarters, Bengaluru</span>
                </div>
                <div className="flex items-center gap-2">
                  <Mail className="w-4 h-4 text-slate-500 shrink-0" />
                  <span>control.room@encrowatch.ai</span>
                </div>
                <div className="flex items-center gap-2">
                  <Phone className="w-4 h-4 text-slate-500 shrink-0" />
                  <span>1800-425-WALK (Toll-Free Helpline)</span>
                </div>
              </div>
            </div>
          </div>

          <div className="pt-6 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-3 text-[11px] text-slate-500">
            <div>&copy; 2026 EncroWatch AI. All municipal records protected. Final-Year MCA Demonstration Initiative.</div>
            <div className="flex items-center gap-4">
              <span>SHA-256 Audit Trail</span>
              <span>&bull;</span>
              <span>RBAC Enforced</span>
              <span>&bull;</span>
              <span>PII Anonymized</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
