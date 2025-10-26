"use client";

import React from "react";

type Props = {
  data: unknown;
  maxHeight?: number | string;
};

export function JsonCodeBlock({ data, maxHeight = 360 }: Props) {
  const json = React.useMemo(() => {
    try {
      return JSON.stringify(data, null, 2);
    } catch {
      return String(data);
    }
  }, [data]);

  const [copied, setCopied] = React.useState(false);

  const tokens = React.useMemo(() => tokenize(json), [json]);
  const lines = React.useMemo(() => tokensToLines(tokens), [tokens]);

  async function copyToClipboard() {
    try {
      await navigator.clipboard.writeText(json);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      // Fallback for older browsers
      try {
        const ta = document.createElement('textarea');
        ta.value = json;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.focus();
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        setCopied(true);
        window.setTimeout(() => setCopied(false), 1500);
      } catch {
        // ignore
      }
    }
  }

  return (
    <div className="rounded-md border border-border bg-surface shadow-subtle overflow-hidden">
      <div className="flex items-center justify-end gap-2 border-b border-border/60 px-2 py-1.5">
        <button
          type="button"
          onClick={copyToClipboard}
          className="inline-flex items-center gap-2 rounded-md border border-border bg-surface px-2.5 py-1 text-xs font-medium text-text hover:-translate-y-px hover:shadow-subtle transition"
          aria-live="polite"
        >
          {copied ? 'Copied' : 'Copy JSON'}
        </button>
      </div>
      <div className="overflow-auto" style={{ maxHeight }}>
        <pre className="m-0 p-3 font-mono text-[12px] leading-5">
          {lines.map((segments, idx) => (
            <div key={idx} className="grid grid-cols-[3ch_1fr] gap-3 items-start">
              <span className="select-none text-text/50 text-right">{idx + 1}</span>
              <code className="whitespace-pre break-words text-text">
                {segments.length === 0 ? '\u00A0' : segments.map((seg, i) => (
                  <span key={i} className={seg.className} style={seg.style as React.CSSProperties}>
                    {seg.text}
                  </span>
                ))}
              </code>
            </div>
          ))}
        </pre>
      </div>
    </div>
  );
}

type Token = { text: string; type?: 'key' | 'string' | 'number' | 'boolean' | 'null' | 'punct' | 'space' };

function tokenize(input: string): Token[] {
  const tokens: Token[] = [];
  const len = input.length;
  let i = 0;
  function peekNonSpace(from: number) {
    let j = from;
    while (j < len) {
      const ch = input[j];
      if (ch === ' ' || ch === '\t' || ch === '\r' || ch === '\n') j++;
      else return input[j];
    }
    return '';
  }
  while (i < len) {
    const ch = input[i];
    // strings
    if (ch === '"') {
      const start = i;
      i++; // skip opening quote
      let escaped = false;
      while (i < len) {
        const c = input[i];
        if (escaped) {
          escaped = false;
        } else if (c === '\\') {
          escaped = true;
        } else if (c === '"') {
          i++; // include closing quote
          break;
        }
        i++;
      }
      const text = input.slice(start, i);
      // Determine if key by peeking ahead for ':'
      const next = peekNonSpace(i);
      tokens.push({ text, type: next === ':' ? 'key' : 'string' });
      continue;
    }
    // numbers
    if (ch === '-' || (ch >= '0' && ch <= '9')) {
      const start = i;
      i++;
      while (i < len && input[i] >= '0' && input[i] <= '9') i++;
      if (i < len && input[i] === '.') {
        i++;
        while (i < len && input[i] >= '0' && input[i] <= '9') i++;
      }
      if (i < len && (input[i] === 'e' || input[i] === 'E')) {
        i++;
        if (input[i] === '+' || input[i] === '-') i++;
        while (i < len && input[i] >= '0' && input[i] <= '9') i++;
      }
      tokens.push({ text: input.slice(start, i), type: 'number' });
      continue;
    }
    // booleans/null
    if (input.startsWith('true', i)) {
      tokens.push({ text: 'true', type: 'boolean' });
      i += 4;
      continue;
    }
    if (input.startsWith('false', i)) {
      tokens.push({ text: 'false', type: 'boolean' });
      i += 5;
      continue;
    }
    if (input.startsWith('null', i)) {
      tokens.push({ text: 'null', type: 'null' });
      i += 4;
      continue;
    }
    // whitespace
    if (ch === ' ' || ch === '\t' || ch === '\r' || ch === '\n') {
      const start = i;
      while (i < len && (input[i] === ' ' || input[i] === '\t' || input[i] === '\r' || input[i] === '\n')) i++;
      tokens.push({ text: input.slice(start, i), type: 'space' });
      continue;
    }
    // punctuation
    tokens.push({ text: ch, type: 'punct' });
    i++;
  }
  return tokens;
}

type LineSegment = { text: string; className?: string; style?: React.CSSProperties };

function tokensToLines(tokens: Token[]): LineSegment[][] {
  const lines: LineSegment[][] = [[]];
  const pushSegment = (seg: LineSegment) => {
    const parts = seg.text.split('\n');
    for (let p = 0; p < parts.length; p++) {
      if (p > 0) lines.push([]);
      if (parts[p].length) lines[lines.length - 1].push({ ...seg, text: parts[p] });
    }
    if (seg.text.endsWith('\n')) lines.push([]);
  };
  for (const t of tokens) {
    const style = styleFor(t.type);
    const className = classFor(t.type);
    pushSegment({ text: t.text, className, style });
  }
  return lines;
}

function classFor(type: Token['type']): string | undefined {
  switch (type) {
    case 'key':
      return 'text-primary';
    case 'string':
      return 'text-accent';
    case 'boolean':
      return 'text-text-muted italic';
    case 'null':
      return 'text-text-muted italic';
    default:
      return undefined;
  }
}

function styleFor(type: Token['type']): React.CSSProperties | undefined {
  switch (type) {
    case 'number':
      return { color: 'rgb(var(--color-primary-muted))' };
    default:
      return undefined;
  }
}

export default JsonCodeBlock;
