import React, { useState, useRef } from 'react';
import {
  Bug,
  Terminal,
  Sparkles,
  Send,
  Upload,
  FileCode,
  X,
  Copy,
  Check,
  RefreshCw,
  GitBranch,
  Mail,
  ShieldCheck,
  ExternalLink,
  Code2,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import CodeMarkdownViewer from '../../components/CodeMarkdownViewer';

const DEFAULT_BACKEND_URL = 'https://bugfix-backend-cl57.vercel.app';

const PRESET_TEMPLATES = [
  {
    title: 'YOLOv5 ONNX Inference',
    category: 'AI Pipeline',
    code: `import cv2
import numpy as np

def run_inference(onnx_path, image_path):
    net = cv2.dnn.readNetFromONNX(onnx_path)
    img = cv2.imread(image_path)
    # Bug: Blob shape and normalization mismatch for YOLOv5n 640x640
    blob = cv2.dnn.blobFromImage(img, 1.0, (640, 640), (0, 0, 0), swapRB=False, crop=False)
    net.setInput(blob)
    preds = net.forward()
    return preds
# Why are detection bounding boxes offset and confidence scores low?`
  },
  {
    title: 'MongoDB GeoSpatial Polygon',
    category: 'Database Query',
    code: `// Query to find incidents within a Municipal Ward boundary
db.incidents.find({
  location: {
    $geoWithin: {
      $geometry: {
        type: "Polygon",
        coordinates: [
          [ [77.5946, 12.9716], [77.5980, 12.9716], [77.5980, 12.9750], [77.5946, 12.9750] ]
        ]
      }
    }
  }
})
// Error: Loop is not closed in polygon geometry coordinates`
  },
  {
    title: 'FastAPI CORS & JWT Middleware',
    category: 'Backend Security',
    code: `@app.middleware("http")
async def verify_municipal_jwt(request: Request, call_next):
    # Bug: Pre-flight OPTIONS request blocked by JWT inspection before CORS headers are set
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    response = await call_next(request)
    return response`
  },
  {
    title: 'Haversine Distance Calculator',
    category: 'GIS Algorithm',
    code: `import math

def calculate_distance(lat1, lon1, lat2, lon2):
    # Need accurate distance in meters between field inspector and encroachment GPS pin
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return 6371 * c # Distance in KM
# Notice: lat1 and lat2 in math.cos() need math.radians() conversion!`
  }
];

export default function AIBugFixPage() {
  const [activeSubTab, setActiveSubTab] = useState('debugger'); // 'debugger' | 'cicd'
  const [codePrompt, setCodePrompt] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [copiedAll, setCopiedAll] = useState(false);

  // CI/CD Email state
  const [cicdEmail, setCicdEmail] = useState('');
  const [emailStatus, setEmailStatus] = useState(null);
  const [copiedYaml, setCopiedYaml] = useState(false);

  const fileInputRef = useRef(null);

  const readFileAsText = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target.result);
      reader.onerror = (e) => reject(e);
      reader.readAsText(file);
    });
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const removeFile = () => {
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleLoadTemplate = (template) => {
    setCodePrompt(template.code);
    setError(null);
  };

  const handleClear = () => {
    setCodePrompt('');
    setSelectedFile(null);
    setResult('');
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    if (!codePrompt.trim() && !selectedFile) return;

    setLoading(true);
    setResult('');
    setError(null);

    try {
      let fullCodePayload = codePrompt;
      if (selectedFile) {
        const fileContent = await readFileAsText(selectedFile);
        fullCodePayload = `// File: ${selectedFile.name}\n${fileContent}\n\n// Question / Issue:\n${codePrompt}`;
      }

      const response = await fetch(`${DEFAULT_BACKEND_URL}/api/bugfix`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code: fullCodePayload }),
      }).catch((err) => {
        throw new Error(`Connection to AI Engine failed: ${err.message}. Please verify internet access.`);
      });

      if (!response) return;

      if (!response.ok) {
        throw new Error(`AI Engine returned error code: HTTP ${response.status}`);
      }

      if (response.body) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let accumulated = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value, { stream: true });
          accumulated += chunk;
          setResult(accumulated);
        }
      } else {
        const text = await response.text();
        setResult(text || 'Analysis completed with no output.');
      }
    } catch (err) {
      console.error('BugFix analysis error:', err);
      setError(err.message || 'An unexpected error occurred while analyzing the code.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyAll = async () => {
    if (!result) return;
    try {
      await navigator.clipboard.writeText(result);
      setCopiedAll(true);
      setTimeout(() => setCopiedAll(false), 2000);
    } catch (e) {
      console.error('Failed to copy', e);
    }
  };

  const handleRegisterCicdEmail = async (e) => {
    e.preventDefault();
    if (!cicdEmail.trim()) return;

    try {
      const resp = await fetch(`${DEFAULT_BACKEND_URL}/api/email`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: cicdEmail.trim() }),
      });
      if (resp.ok) {
        setEmailStatus('success');
        setTimeout(() => setEmailStatus(null), 3000);
      } else {
        setEmailStatus('error');
      }
    } catch (err) {
      setEmailStatus('error');
    }
  };

  const safeYamlContent = `name: AI Code Review on Push

on:
  push:
    branches: [ main, develop ]

jobs:
  ai-review:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v3
        with:
          fetch-depth: 2

      - name: Identify Last Changed File
        id: detect_file
        run: |
          CHANGED_FILES=$(git diff --name-only \${{ github.event.before }} \${{ github.sha }})
          LAST_FILE=$(echo "$CHANGED_FILES" | tail -n 1)
          echo "last_file=$LAST_FILE" >> $GITHUB_OUTPUT

      - name: Read File Safely
        env:
          TARGET_FILE: \${{ steps.detect_file.outputs.last_file }}
        run: |
          cat "$TARGET_FILE" > filecontent.txt

      - name: Dispatch AI Code Review Payload
        env:
          USER_NAME: \${{ github.actor }}
          COMMIT_SHA: \${{ github.sha }}
          BACKEND_URL: ${DEFAULT_BACKEND_URL}
        run: |
          COMMIT_MSG=$(git log -1 --pretty=%B)
          COMMITTER_EMAIL=$(git log -1 --pretty=format:'%ae')
          CODE_CONTENT=$(cat filecontent.txt)

          JSON_PAYLOAD=$(jq -n \\
            --arg code "$CODE_CONTENT" \\
            --arg user "$USER_NAME" \\
            --arg commitId "$COMMIT_SHA" \\
            --arg commitMsg "$COMMIT_MSG" \\
            --arg email "$COMMITTER_EMAIL" \\
            '{code: $code, username: $user, commit_id: $commitId, commit_msg: $commitMsg, email: $email}')

          curl -X POST \\
            -H "Content-Type: application/json" \\
            -d "$JSON_PAYLOAD" \\
            "$BACKEND_URL/api/analyze"`;

  const handleCopyYaml = async () => {
    try {
      await navigator.clipboard.writeText(safeYamlContent);
      setCopiedYaml(true);
      setTimeout(() => setCopiedYaml(false), 2000);
    } catch (err) {
      console.error('Failed to copy YAML', err);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Studio Header */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/90 shadow-2xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-3.5">
            <div className="w-12 h-12 rounded-xl bg-blue-50 border border-blue-200/60 flex items-center justify-center shrink-0 text-blue-600 shadow-2xs">
              <Bug className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold text-slate-900 tracking-tight">
                  AI Script & BugFix Studio
                </h1>
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                  <Sparkles className="w-3 h-3 text-emerald-600" />
                  Live AI Engine
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-1 max-w-2xl leading-relaxed">
                Developer diagnostics and intelligent code correction for municipal engineers. Inspect, debug, and optimize Python ML pipelines, GIS queries, and backend scripts.
              </p>
            </div>
          </div>

          {/* Mode Switcher Tabs */}
          <div className="flex bg-slate-100 p-1 rounded-xl border border-slate-200 self-start md:self-auto">
            <button
              onClick={() => setActiveSubTab('debugger')}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeSubTab === 'debugger'
                  ? 'bg-white text-slate-900 shadow-2xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Terminal className="w-3.5 h-3.5 text-blue-600" />
              <span>Interactive Debugger</span>
            </button>
            <button
              onClick={() => setActiveSubTab('cicd')}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeSubTab === 'cicd'
                  ? 'bg-white text-slate-900 shadow-2xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <GitBranch className="w-3.5 h-3.5 text-purple-600" />
              <span>CI/CD Automation</span>
            </button>
          </div>
        </div>
      </div>

      {/* Mode 1: Interactive Debugger */}
      {activeSubTab === 'debugger' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Code Editor & Inputs (7 cols) */}
          <div className="lg:col-span-6 space-y-4">
            {/* Quick Municipal Code Presets */}
            <div className="bg-white rounded-2xl p-4 border border-slate-200/90 shadow-2xs space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                  <Code2 className="w-3.5 h-3.5 text-blue-600" />
                  Municipal Platform Presets
                </span>
                <span className="text-[10px] text-slate-400">Click to load into editor</span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                {PRESET_TEMPLATES.map((tmpl, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleLoadTemplate(tmpl)}
                    className="p-2.5 text-left rounded-xl bg-slate-50 hover:bg-blue-50/60 border border-slate-200/80 hover:border-blue-300 transition-all group"
                  >
                    <div className="text-[11px] font-bold text-slate-800 group-hover:text-blue-700 truncate">
                      {tmpl.title}
                    </div>
                    <div className="text-[9px] text-slate-400 mt-0.5 uppercase tracking-wide">
                      {tmpl.category}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Input Form */}
            <form onSubmit={handleSubmit} className="bg-white rounded-2xl p-5 border border-slate-200/90 shadow-2xs space-y-3.5">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                  <FileCode className="w-4 h-4 text-slate-500" />
                  Code Snippet or Bug Description
                </label>

                {/* Upload file badge */}
                <div className="flex items-center gap-2">
                  <input
                    ref={fileInputRef}
                    type="file"
                    onChange={handleFileChange}
                    className="hidden"
                    accept=".py,.js,.jsx,.ts,.tsx,.json,.sql,.sh,.yml,.yaml,.txt,.cpp,.java"
                  />
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold text-slate-600 bg-slate-100 hover:bg-slate-200 transition-colors border border-slate-200/80"
                  >
                    <Upload className="w-3 h-3 text-slate-500" />
                    <span>Upload File</span>
                  </button>
                  {codePrompt && (
                    <button
                      type="button"
                      onClick={handleClear}
                      className="text-xs text-slate-400 hover:text-rose-600 transition-colors"
                      title="Clear editor"
                    >
                      Clear
                    </button>
                  )}
                </div>
              </div>

              {/* Selected File Banner */}
              {selectedFile && (
                <div className="flex items-center justify-between px-3 py-2 bg-blue-50/80 border border-blue-200 rounded-xl text-xs text-blue-900">
                  <div className="flex items-center gap-2 truncate">
                    <FileCode className="w-4 h-4 text-blue-600 shrink-0" />
                    <span className="font-semibold truncate">{selectedFile.name}</span>
                    <span className="text-[10px] text-blue-500 font-mono">
                      ({(selectedFile.size / 1024).toFixed(1)} KB)
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={removeFile}
                    className="text-blue-400 hover:text-blue-700 p-0.5 rounded transition-colors"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              )}

              {/* Code Textarea */}
              <div className="relative">
                <textarea
                  rows={14}
                  value={codePrompt}
                  onChange={(e) => setCodePrompt(e.target.value)}
                  placeholder="Paste Python, GIS coordinates, SQL, or backend JavaScript code here to scan for bugs, syntax errors, and optimizations..."
                  className="w-full p-3.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-mono text-slate-900 placeholder:text-slate-400 focus:bg-white focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 resize-y leading-relaxed"
                />
              </div>

              {/* Submit Button */}
              <div className="flex items-center justify-between pt-1">
                <span className="text-[11px] text-slate-400 font-medium">
                  Supports streaming AI diagnosis
                </span>
                <button
                  type="submit"
                  disabled={loading || (!codePrompt.trim() && !selectedFile)}
                  className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold shadow-xs hover:shadow-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
                >
                  {loading ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      <span>Analyzing Code...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>Analyze & Fix Code</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>

          {/* Right Column: AI Diagnosis & Output (6 cols) */}
          <div className="lg:col-span-6 bg-white rounded-2xl border border-slate-200/90 shadow-2xs overflow-hidden flex flex-col min-h-[580px]">
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-3.5 border-b border-slate-100 bg-slate-50/70">
              <div className="flex items-center gap-2">
                <div className={`w-2.5 h-2.5 rounded-full ${loading ? 'bg-amber-400 animate-pulse' : (result ? 'bg-emerald-500' : 'bg-slate-300')}`} />
                <span className="text-xs font-bold text-slate-800">
                  {loading ? 'AI Engine Thinking...' : (result ? 'AI Analysis & Suggested Fix' : 'Output Console')}
                </span>
              </div>
              {result && (
                <button
                  onClick={handleCopyAll}
                  className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold text-slate-600 hover:text-slate-900 bg-white hover:bg-slate-100 border border-slate-200 transition-colors shadow-2xs"
                >
                  {copiedAll ? (
                    <>
                      <Check className="w-3 h-3 text-emerald-600" />
                      <span className="text-emerald-600">Copied</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3 h-3 text-slate-400" />
                      <span>Copy Full Output</span>
                    </>
                  )}
                </button>
              )}
            </div>

            {/* Content Body */}
            <div className="flex-1 p-5 overflow-y-auto max-h-[700px]">
              {error && (
                <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800 flex items-start gap-2.5">
                  <AlertCircle className="w-4 h-4 text-rose-600 mt-0.5 shrink-0" />
                  <div>
                    <div className="font-bold text-rose-900">Analysis Failed</div>
                    <p className="mt-0.5">{error}</p>
                  </div>
                </div>
              )}

              {loading && !result && (
                <div className="flex flex-col items-center justify-center h-80 text-center space-y-3">
                  <div className="w-10 h-10 rounded-full border-2 border-blue-600 border-t-transparent animate-spin" />
                  <div className="text-xs font-semibold text-slate-700">Connecting to BugFix AI Engine...</div>
                  <p className="text-[11px] text-slate-400 max-w-xs">
                    Scanning syntax trees, analyzing logical bottlenecks, and applying best practices.
                  </p>
                </div>
              )}

              {!loading && !result && !error && (
                <div className="flex flex-col items-center justify-center h-80 text-center space-y-3 text-slate-400">
                  <div className="w-12 h-12 rounded-2xl bg-slate-100 flex items-center justify-center text-slate-400">
                    <Terminal className="w-6 h-6" />
                  </div>
                  <div className="text-xs font-semibold text-slate-600">Ready to Analyze</div>
                  <p className="text-[11px] text-slate-400 max-w-sm">
                    Select a municipal template from the left or paste your Python/GIS script to generate explanations, bug fixes, and corrected code snippets.
                  </p>
                </div>
              )}

              {result && (
                <div className="prose prose-slate max-w-none">
                  <CodeMarkdownViewer content={result} />
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Mode 2: CI/CD Automation Tab */}
      {activeSubTab === 'cicd' && (
        <div className="bg-white rounded-2xl p-6 sm:p-8 border border-slate-200/90 shadow-2xs space-y-6">
          <div className="border-b border-slate-100 pb-4">
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <GitBranch className="w-5 h-5 text-purple-600" />
              Automated GitHub Actions Code Review Setup
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              Configure automatic AI bug scanning on every commit pushed to your municipal GitHub repository.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-1.5">
              <div className="text-xs font-bold text-slate-800">1. Create Workflow File</div>
              <p className="text-[11px] text-slate-500">
                In your repository, create <code className="bg-slate-200/70 text-slate-800 px-1 py-0.5 rounded text-[10px] font-mono">.github/workflows/ai-review.yml</code>
              </p>
            </div>
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-1.5">
              <div className="text-xs font-bold text-slate-800">2. Paste Safe YAML</div>
              <p className="text-[11px] text-slate-500">
                Copy the hardened workflow below, which runs on <code className="bg-slate-200/70 text-slate-800 px-1 py-0.5 rounded text-[10px] font-mono">ubuntu-latest</code>.
              </p>
            </div>
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-1.5">
              <div className="text-xs font-bold text-slate-800">3. Push & Get Reports</div>
              <p className="text-[11px] text-slate-500">
                Every push scans the last changed file and emails detailed diagnosis to your registered address.
              </p>
            </div>
          </div>

          {/* Workflow Code Container */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-700 font-mono">
                .github/workflows/ai-review.yml
              </span>
              <button
                onClick={handleCopyYaml}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-900 text-white hover:bg-slate-800 transition-colors shadow-2xs"
              >
                {copiedYaml ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" />
                    <span>Copy Workflow YAML</span>
                  </>
                )}
              </button>
            </div>
            <div className="bg-[#0f172a] rounded-xl p-4 overflow-x-auto text-xs font-mono text-cyan-300 leading-relaxed border border-slate-800">
              <pre className="m-0 whitespace-pre">
                <code>{safeYamlContent}</code>
              </pre>
            </div>
          </div>

          {/* Email Notification Subscription Card */}
          <div className="p-5 bg-gradient-to-r from-blue-50/50 to-indigo-50/50 rounded-xl border border-blue-200/80 space-y-3">
            <div className="flex items-center gap-2">
              <Mail className="w-4 h-4 text-blue-600" />
              <h3 className="text-xs font-bold text-slate-900">
                Register Notification Email for Automated Review Reports
              </h3>
            </div>
            <p className="text-[11px] text-slate-600">
              Enter your email to receive automatic diagnosis and code quality feedback when GitHub Actions triggers.
            </p>
            <form onSubmit={handleRegisterCicdEmail} className="flex flex-col sm:flex-row gap-2 max-w-lg">
              <input
                type="email"
                required
                value={cicdEmail}
                onChange={(e) => setCicdEmail(e.target.value)}
                placeholder="engineer@bbmp.gov.in or darshan002004@gmail.com"
                className="flex-1 px-3 py-2 bg-white border border-slate-300 rounded-lg text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              />
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg text-xs transition-colors shadow-2xs whitespace-nowrap"
              >
                Save Review Email
              </button>
            </form>
            {emailStatus === 'success' && (
              <div className="text-xs font-semibold text-emerald-600 flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Notification email successfully registered with AI Review engine!
              </div>
            )}
            {emailStatus === 'error' && (
              <div className="text-xs font-semibold text-rose-600 flex items-center gap-1.5">
                <AlertCircle className="w-3.5 h-3.5" />
                Could not connect to review server. Please check internet connectivity.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
