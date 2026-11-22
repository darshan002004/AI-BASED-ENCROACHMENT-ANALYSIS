import React from 'react';
import { AlertOctagon, RotateCcw } from 'lucide-react';

export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught an unhandled rendering error:', error, errorInfo);
    this.setState({ errorInfo });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      const errorMsg =
        typeof this.state.error === 'string'
          ? this.state.error
          : this.state.error?.message || 'An unexpected rendering error occurred';

      return (
        <div className="min-h-screen bg-slate-900 flex flex-col items-center justify-center p-6 text-white text-center">
          <div className="max-w-md w-full bg-slate-800 rounded-3xl p-8 border border-slate-700 shadow-2xl space-y-5">
            <div className="w-14 h-14 bg-red-500/10 text-red-400 rounded-2xl mx-auto flex items-center justify-center border border-red-500/20">
              <AlertOctagon className="w-8 h-8" />
            </div>

            <div className="space-y-1">
              <h2 className="text-xl font-bold text-white">Application Encountered an Error</h2>
              <p className="text-xs text-slate-400">
                The user interface encountered an unexpected condition and prevented a crash.
              </p>
            </div>

            <div className="p-3.5 bg-slate-900/80 rounded-xl text-left border border-slate-800 overflow-x-auto text-xs text-red-300 font-mono">
              {errorMsg}
            </div>

            <button
              onClick={this.handleReset}
              className="w-full inline-flex items-center justify-center gap-2 px-5 py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl text-xs transition-colors shadow-lg shadow-blue-600/30"
            >
              <RotateCcw className="w-4 h-4" />
              Reload Application
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
