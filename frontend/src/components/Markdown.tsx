import { Fragment, ReactNode } from "react";

function escapeHtml(text: string): string {
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function renderInline(text: string): ReactNode[] {
  const parts: ReactNode[] = [];
  const re = /(`[^`]+`)|(\*\*[^*]+\*\*)|(\*[^*]+\*)|(\[([^\]]+)\]\(([^)]+)\))/g;
  let last = 0;
  let idx = 0;

  let m: RegExpExecArray | null;
  while ((m = re.exec(text)) !== null) {
    const offset = m.index;
    if (offset > last) {
      parts.push(<Fragment key={idx++}>{escapeHtml(text.slice(last, offset))}</Fragment>);
    }
    const code = m[1];
    const bold = m[2];
    const italic = m[3];
    const linkText = m[5];
    const linkUrl = m[6];
    if (code) {
      parts.push(<code key={idx++} className="bg-gray-200 rounded px-1 text-sm font-mono">{escapeHtml(code.slice(1, -1))}</code>);
    } else if (bold) {
      parts.push(<strong key={idx++}>{escapeHtml(bold.slice(2, -2))}</strong>);
    } else if (italic) {
      parts.push(<em key={idx++}>{escapeHtml(italic.slice(1, -1))}</em>);
    } else if (linkText && linkUrl) {
      parts.push(<a key={idx++} href={linkUrl} target="_blank" rel="noopener noreferrer" className="text-blue-600 underline">{escapeHtml(linkText)}</a>);
    }
    last = offset + m[0].length;
  }

  if (last < text.length) {
    parts.push(<Fragment key={idx++}>{escapeHtml(text.slice(last))}</Fragment>);
  }
  return parts;
}

function renderCodeBlock(lang: string | undefined, code: string): ReactNode {
  return (
    <pre className="bg-gray-900 text-gray-100 rounded-lg p-4 my-2 overflow-x-auto text-sm">
      {lang && <div className="text-gray-500 text-xs mb-2 font-mono">{lang}</div>}
      <code className="font-mono">{escapeHtml(code)}</code>
    </pre>
  );
}

export default function Markdown({ content }: { content: string }) {
  const lines = content.split("\n");
  const blocks: ReactNode[] = [];
  let i = 0;
  let key = 0;

  while (i < lines.length) {
    const line = lines[i] as string;

    const fenceMatch = line.match(/^```(\w*)/);
    if (fenceMatch) {
      const lang = fenceMatch[1];
      const codeLines: string[] = [];
      i++;
      while (i < lines.length) {
        const cl = lines[i] as string;
        if (cl.startsWith("```")) break;
        codeLines.push(cl);
        i++;
      }
      i++;
      blocks.push(<div key={key++} className="animate-slide-up">{renderCodeBlock(lang, codeLines.join("\n"))}</div>);
      continue;
    }

    if (line.trim() === "") {
      blocks.push(<div key={key++} className="h-2" />);
      i++;
      continue;
    }

    const listMatch = line.match(/^(\s*)[-*]\s+(.*)/);
    if (listMatch) {
      const items: ReactNode[] = [];
      const indent = listMatch[1] as string;
      items.push(<li key={0} className="ml-4 list-disc">{renderInline(listMatch[2] as string)}</li>);
      i++;
      while (i < lines.length) {
        const nl = lines[i] as string;
        const next = nl.match(new RegExp(`^ {${indent.length}}[-*]\\s+(.*)`));
        if (!next) break;
        items.push(<li key={items.length} className="ml-4 list-disc">{renderInline(next[1] as string)}</li>);
        i++;
      }
      blocks.push(<ul key={key++} className="my-1 space-y-0.5">{items}</ul>);
      continue;
    }

    const orderedMatch = line.match(/^(\s*)(\d+)\.\s+(.*)/);
    if (orderedMatch) {
      const items: ReactNode[] = [];
      const indent = orderedMatch[1] as string;
      items.push(<li key={0} className="ml-4 list-decimal">{renderInline(orderedMatch[3] as string)}</li>);
      i++;
      while (i < lines.length) {
        const nl = lines[i] as string;
        const next = nl.match(new RegExp(`^ {${indent.length}}\\d+\\.\\s+(.*)`));
        if (!next) break;
        items.push(<li key={items.length} className="ml-4 list-decimal">{renderInline(next[1] as string)}</li>);
        i++;
      }
      blocks.push(<ol key={key++} className="my-1 space-y-0.5">{items}</ol>);
      continue;
    }

    blocks.push(<p key={key++} className="my-1">{renderInline(line)}</p>);
    i++;
  }

  return <div className="leading-relaxed">{blocks}</div>;
}
