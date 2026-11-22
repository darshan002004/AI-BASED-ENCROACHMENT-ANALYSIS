import React, { useState } from 'react';
import { Copy, Check, Terminal, Code2 } from 'lucide-react';

function CodeBlock({ language, code }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy code:', err);
    }
  };

  return (
    <div className="my-3 rounded-xl overflow-hidden border border-slate-700/80 bg-[#0d1117] shadow-lg">
      <div className="flex items-center justify-between px-3.5 py-1.5 bg-[#161b22] border-b border-slate-700/60 text-xs">
        <div className="flex items-center gap-1.5 text-slate-300 font-mono text-[11px] font-semibold uppercase tracking-wider">
          <Terminal className="w-3.5 h-3.5 text-cyan-400" />
          <span>{language || 'code'}</span>
        </div>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium text-slate-300 hover:text-white bg-slate-800/80 hover:bg-slate-700 transition-colors border border-slate-600/50"
          title="Copy code to clipboard"
        >
          {copied ? (
            <>
              <Check className="w-3 h-3 text-emerald-400" />
              <span className="text-emerald-400">Copied!</span>
            </>
          ) : (
            <>
              <Copy className="w-3 h-3 text-slate-400" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>
      <div className="p-3.5 overflow-x-auto text-xs font-mono text-slate-100 leading-relaxed selection:bg-blue-600/40">
        <pre className="m-0 whitespace-pre">
          <code>{code}</code>
        </pre>
      </div>
    </div>
  );
}

export default function CodeMarkdownViewer({ content }) {
  if (!content) return null;

  // Split content into code blocks and normal markdown text
  const parts = [];
  const regex = /```([a-zA-Z0-9_-]*)\n([\s\S]*?)```/g;
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(content)) !== null) {
    if (match.index > lastIndex) {
      parts.push({
        type: 'text',
        value: content.slice(lastIndex, match.index),
      });
    }
    parts.push({
      type: 'code',
      language: match[1] || 'plaintext',
      value: match[2].trimEnd(),
    });
    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < content.length) {
    parts.push({
      type: 'text',
      value: content.slice(lastIndex),
    });
  }

  const renderInlineFormatted = (line, keyIdx) => {
    // Headers
    if (line.startsWith('### ')) {
      return (
        <h4 key={keyIdx} className="text-sm font-bold text-slate-900 mt-3 mb-1">
          {line.replace(/^###\s+/, '')}
        </h4>
      );
    }
    if (line.startsWith('## ')) {
      return (
        <h3 key={keyIdx} className="text-base font-bold text-slate-900 mt-4 mb-1.5 pb-1 border-b border-slate-100">
          {line.replace(/^##\s+/, '')}
        </h3>
      );
    }
    if (line.startsWith('# ')) {
      return (
        <h2 key={keyIdx} className="text-lg font-bold text-slate-900 mt-5 mb-2 pb-1 border-b border-slate-200">
          {line.replace(/^#\s+/, '')}
        </h2>
      );
    }

    // Bullet lists
    const isBullet = /^[-*]\s+/.test(line);
    const cleanLine = isBullet ? line.replace(/^[-*]\s+/, '') : line;

    // Parse inline code `code` and bold **text**
    const tokens = [];
    const inlineRegex = /(`[^`]+`|\*\*[^*]+\*\*)/g;
    let textIdx = 0;
    let inlineMatch;

    while ((inlineMatch = inlineRegex.exec(cleanLine)) !== null) {
      if (inlineMatch.index > textIdx) {
        tokens.push(cleanLine.slice(textIdx, inlineMatch.index));
      }
      const raw = inlineMatch[0];
      if (raw.startsWith('`') && raw.endsWith('`')) {
        tokens.push(
          <code key={`code-${inlineMatch.index}`} className="bg-slate-100 text-blue-700 px-1.5 py-0.5 rounded text-xs font-mono font-medium border border-slate-200/80">
            {raw.slice(1, -1)}
          </code>
        );
      } else if (raw.startsWith('**') && raw.endsWith('**')) {
        tokens.push(
          <strong key={`bold-${inlineMatch.index}`} className="font-semibold text-slate-900">
            {raw.slice(2, -2)}
          </strong>
        );
      }
      textIdx = inlineMatch.index + raw.length;
    }
    if (textIdx < cleanLine.length) {
      tokens.push(cleanLine.slice(textIdx));
    }

    if (isBullet) {
      return (
        <li key={keyIdx} className="ml-4 list-disc text-xs text-slate-700 leading-relaxed my-1">
          {tokens}
        </li>
      );
    }

    if (!line.trim()) {
      return <div key={keyIdx} className="h-2" />;
    }

    return (
      <p key={keyIdx} className="text-xs text-slate-700 leading-relaxed my-1.5">
        {tokens}
      </p>
    );
  };

  return (
    <div className="space-y-1">
      {parts.map((part, idx) => {
        if (part.type === 'code') {
          return <CodeBlock key={`block-${idx}`} language={part.language} code={part.value} />;
        }
        const lines = part.value.split('\n');
        return (
          <div key={`text-${idx}`}>
            {lines.map((line, lIdx) => renderInlineFormatted(line, `l-${idx}-${lIdx}`))}
          </div>
        );
      })}
    </div>
  );
}
