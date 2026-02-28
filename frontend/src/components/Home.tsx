import { useState, useRef, useEffect, useCallback, FC, ChangeEvent, KeyboardEvent } from "react";
import NexusLogo from "./NexusLogo";
import { indexdbService } from "../services/indexdbService";

declare global {
  interface Window {
    SpeechRecognition?: any;
    webkitSpeechRecognition?: any;
  }
}

// ── Type Definitions ──
interface FileAttachment {
  id: string;
  file: File;
  type: string;
  preview?: string;
}

interface Message {
  id: string;
  role: "user" | "ai";
  text: string;
  timestamp: Date;
  attachments?: { name: string; type: string; preview?: string }[];
  chartData?: ChartDataItem[];
  chartType?: ChartType;
  confidence?: string;
  sampleSize?: number;
  execMs?: number;
  isError?: boolean;
}

type ChartType = "bar" | "line" | "pie";

interface ChartDataItem {
  label: string;
  value: number;
  color?: string;
}

interface HistoryItem {
  id: string;
  title: string;
  time: string;
}

// ── Session title helpers ──
const DEFAULT_SESSION_TITLE_PREFIX = "Chat - ";
const MAX_HISTORY_TITLE_LEN = 72;

const normalizeTitleText = (text: string): string => {
  return text
    .replace(/```[\s\S]*?```/g, " ")
    .replace(/`[^`]*`/g, " ")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/^#{1,6}\s+/gm, "")
    .replace(/^\s*[-*+]\s+/gm, "")
    .replace(/^\s*\d+\.\s+/gm, "")
    .replace(/\|/g, " ")
    .replace(/\s+/g, " ")
    .replace(/^[#>*`\-:\s]+/, "")
    .replace(/^(answer|summary|result|insight)\s*:\s*/i, "")
    .trim();
};

const summarizeTitle = (text: string): string => {
  const normalized = normalizeTitleText(text);
  if (!normalized) return "";
  const candidateLines = normalized
    .split(/\r?\n|[;|]/)
    .map((s) => s.trim())
    .filter((s) => s.split(/\s+/).length >= 4);
  const base = candidateLines[0] || normalized;
  const sentences = base
    .split(/(?<=[.!?])\s+/)
    .map((s) => s.trim())
    .filter(Boolean);
  const explanatory = sentences.find((s) => !s.endsWith("?")) || sentences[0] || base;
  const oneLine = explanatory.replace(/\n/g, " ").trim();
  return oneLine.length > MAX_HISTORY_TITLE_LEN
    ? `${oneLine.slice(0, MAX_HISTORY_TITLE_LEN - 1).trimEnd()}...`
    : oneLine;
};

const isFallbackTitle = (title?: string): boolean => {
  const value = (title || "").trim();
  return !value || value.startsWith(DEFAULT_SESSION_TITLE_PREFIX) || value.startsWith("Discussion:");
};

const deriveSessionHistoryTitle = (session: { title?: string; messages: Message[] }): string => {
  const persistedTitle = (session.title || "").trim();
  if (persistedTitle && !persistedTitle.startsWith(DEFAULT_SESSION_TITLE_PREFIX)) {
    return summarizeTitle(persistedTitle);
  }
  const firstAiMessage = session.messages.find((msg) => msg.role === "ai" && !msg.isError && msg.text.trim());
  if (firstAiMessage) {
    const aiSummary = summarizeTitle(firstAiMessage.text);
    if (aiSummary) return aiSummary;
  }
  const firstUserMessage = session.messages.find((msg) => msg.role === "user" && msg.text.trim());
  if (firstUserMessage) {
    const userSummary = summarizeTitle(firstUserMessage.text);
    if (userSummary) return `Discussion: ${userSummary}`.slice(0, MAX_HISTORY_TITLE_LEN);
  }
  return "New chat";
};

const css = `
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}

/* ── DARK THEME (default) ── */
:root{
  --accent:#3B82F6;--accent2:#1DD1EE;--amber:#f59e0b;--danger:#ff4d6a;--purple:#a78bfa;
  --bg:#0a1628;--bg1:#050a14;--bg2:#0a1628;--bg3:#10192d;
  --text:#ffffff;--text2:#e0e7ff;--text3:#a0aec0;
  --border:rgba(255,255,255,0.08);--border2:rgba(255,255,255,0.12);
  --glow:rgba(59,130,246,0.2);--shadow:rgba(0,0,0,0.5);
  --sidebar-w:240px;--topbar-h:56px;
  --ease-spring:cubic-bezier(.34,1.56,.64,1);--ease-out:cubic-bezier(.22,1,.36,1);
}

/* ── LIGHT THEME ── */
[data-theme="light"]{
  --accent:#1D4ED8;--accent2:#0ea5e9;--amber:#c07000;--danger:#c8003d;--purple:#6d48c7;
  --bg:#edf2f8;--bg1:#ffffff;--bg2:#f8fafd;--bg3:#e9eff7;
  --text:#101a27;--text2:#3c4b5f;--text3:#7b889c;
  --border:rgba(15,25,35,0.11);--border2:rgba(15,25,35,0.17);
  --glow:rgba(29,78,216,0.14);--shadow:rgba(15,25,35,0.14);
}

html,body,#root{height:100dvh;min-height:100dvh;width:100%;overflow:hidden;-webkit-font-smoothing:antialiased;}
body{background:var(--bg);color:var(--text);margin:0;}
#root{display:flex;}
::-webkit-scrollbar{width:4px;}::-webkit-scrollbar-track{background:transparent;}::-webkit-scrollbar-thumb{background:var(--border2);border-radius:4px;}

.app{display:flex;width:100%;height:100dvh;min-height:100dvh;position:relative;inset:0;overflow:hidden;padding:18px;gap:18px;}
.app::before{content:'';position:fixed;inset:0;z-index:0;pointer-events:none;background:radial-gradient(1200px 520px at 50% 42%, rgba(10,22,40,0.26) 0%, rgba(10,22,40,0.54) 72%, rgba(10,22,40,0.72) 100%),linear-gradient(180deg, rgba(10,22,40,0.36) 0%, rgba(10,22,40,0.5) 100%);}
.app::after{content:'';position:fixed;inset:0;pointer-events:none;z-index:0;
  background:radial-gradient(ellipse 600px 400px at 0% 0%,rgba(59,130,246,0.04) 0%,transparent 60%),
  radial-gradient(ellipse 500px 400px at 100% 100%,rgba(29,209,238,0.035) 0%,transparent 60%);
  transition:opacity .4s;}
[data-theme="light"] .app::after{
  background:radial-gradient(ellipse 600px 400px at 10% 0%,rgba(29,78,216,0.04) 0%,transparent 60%),
  radial-gradient(ellipse 500px 400px at 90% 100%,rgba(14,165,233,0.03) 0%,transparent 60%);}

/* ── SIDEBAR ── */
.sidebar{
  position:relative;z-index:20;width:var(--sidebar-w);min-width:var(--sidebar-w);height:100%;
  background:rgba(10,22,40,0.55);backdrop-filter:blur(22px);
  display:flex;flex-direction:column;
  transition:width .28s var(--ease-out),min-width .28s var(--ease-out);
  flex-shrink:0;overflow:hidden;border-radius:24px;border:1px solid rgba(59,130,246,0.18);
  box-shadow:0 10px 36px rgba(0,0,0,0.22), inset 0 1px 0 rgba(59,130,246,0.08);
}
.sidebar.collapsed{width:56px;min-width:56px;}

.sb-head{
  display:flex;align-items:center;gap:8px;
  padding:0 16px;height:var(--topbar-h);
  border-bottom:1px solid var(--border);flex-shrink:0;
}
.sidebar.collapsed .sb-head{flex-direction:column;justify-content:center;padding:10px 0;gap:6px;height:auto;min-height:var(--topbar-h);}
.logo-mark{width:40px;height:40px;flex-shrink:0;display:flex;align-items:center;justify-content:center;position:relative;}
.logo-mark .nexus-card{border-radius:10px;}
.sidebar.collapsed .logo-mark{margin-bottom:4px;}
.logo-text{flex:1;min-width:0;overflow:hidden;transition:opacity .2s,max-width .28s;}
.logo-name{font-size:14px;font-weight:800;letter-spacing:-.025em;white-space:nowrap;line-height:1.1;}
.logo-name em{color:var(--accent);font-style:normal;}
.logo-tagline{font-size:9px;color:var(--text3);letter-spacing:.08em;text-transform:uppercase;white-space:nowrap;margin-top:2px;}
.sidebar.collapsed .logo-text{opacity:0;max-width:0;pointer-events:none;}

.menu-btn{
  width:28px;height:28px;border-radius:6px;flex-shrink:0;
  border:1px solid rgba(255,255,255,0.2);background:rgba(255,255,255,0.05);backdrop-filter:blur(8px);cursor:pointer;
  display:flex;align-items:center;justify-content:center;transition:all .15s;
}
.menu-btn:hover{border-color:var(--accent);background:rgba(59,130,246,0.1);}
.menu-btn svg{stroke:var(--text2);transition:stroke .15s;}.menu-btn:hover svg{stroke:var(--accent);}
.sidebar.collapsed .menu-btn{margin:0 auto;}

.sb-body{padding:14px 12px;display:flex;flex-direction:column;gap:12px;flex:1;overflow:hidden;min-height:0;}
.sb-divider{height:1px;background:linear-gradient(90deg,transparent,rgba(255,255,255,.18),transparent);margin:6px 2px;}

.new-chat-btn{
  display:flex;align-items:center;justify-content:center;gap:6px;
  padding:11px 14px;border-radius:9px;flex-shrink:0;overflow:hidden;
  background:rgba(59,130,246,0.15);backdrop-filter:blur(12px);border:1px solid rgba(59,130,246,0.28);
  font-size:11.5px;font-weight:600;color:var(--accent);cursor:pointer;white-space:nowrap;transition:all .2s;
}
[data-theme="light"] .new-chat-btn{background:rgba(29,78,216,0.12);border-color:rgba(29,78,216,0.28);}
.new-chat-btn:hover{background:rgba(59,130,246,0.25);border-color:var(--accent);box-shadow:0 0 18px var(--glow);transform:translateY(-1px);}
.sidebar.collapsed .new-chat-btn{padding:8px;}.sidebar.collapsed .nc-label{display:none;}

.hist-label{font-size:9px;letter-spacing:.14em;text-transform:uppercase;color:var(--text3);padding:2px 4px;flex-shrink:0;}
.sidebar.collapsed .hist-label{display:none;}

.hist-list{flex:1;overflow-y:auto;display:flex;flex-direction:column;gap:6px;min-height:0;}
.hist-item{
  display:flex;align-items:center;gap:8px;padding:12px 14px;border-radius:12px;border:1px solid transparent;background:rgba(255,255,255,0.02);
  cursor:pointer;white-space:nowrap;overflow:hidden;transition:all .16s;
}
.hist-item:hover{background:rgba(255,255,255,0.1);border-color:rgba(255,255,255,0.18);transform:translateY(-1px);}
[data-theme="light"] .hist-item:hover{background:rgba(0,0,0,0.04);}
.hist-item.active{background:rgba(255,255,255,0.14);border-color:rgba(255,255,255,0.28);backdrop-filter:blur(10px);}
[data-theme="light"] .hist-item.active{background:rgba(0,122,82,.08);}
.hist-dot{width:5px;height:5px;border-radius:50%;background:var(--text3);flex-shrink:0;transition:background .2s;}
.hist-item.active .hist-dot{background:var(--accent);box-shadow:0 0 6px rgba(0,229,160,.5);}
.hist-info{flex:1;min-width:0;overflow:hidden;}
.hist-title{font-size:11.5px;font-weight:500;color:var(--text2);overflow:hidden;text-overflow:ellipsis;transition:color .15s;}
.hist-item:hover .hist-title,.hist-item.active .hist-title{color:var(--text);}
.hist-time{font-size:9px;color:var(--text3);}
/* ── DELETE BUTTON (from Doc 2) ── */
.hist-delete{width:20px;height:20px;display:flex;align-items:center;justify-content:center;border-radius:6px;border:1px solid transparent;background:transparent;color:var(--text3);cursor:pointer;opacity:0;transition:all .14s;flex-shrink:0;}
.hist-item:hover .hist-delete,.hist-item.active .hist-delete{opacity:1;}
.hist-delete:hover{border-color:rgba(255,77,106,0.35);background:rgba(255,77,106,0.10);color:#ff8aa0;}
.sidebar.collapsed .hist-info{display:none;}
.sidebar.collapsed .hist-delete{display:none;}
.sidebar.collapsed .hist-dot{margin:0 auto;}

/* ── MAIN CONTENT ── */
.main{flex:1;display:flex;flex-direction:column;overflow:hidden;position:relative;z-index:1;min-width:0;background:transparent;border:none;box-shadow:none;}
[data-theme="light"] .main{background:transparent;border:none;box-shadow:none;}

/* ── TAB VIEW ── */
.tab-view{width:min(1120px,calc(100% - 28px));margin:0 auto 18px;flex:1;min-height:0;overflow:hidden;display:flex;flex-direction:column;border-radius:0;border:none;background:transparent;backdrop-filter:none;}
[data-theme="light"] .tab-view{border:none;background:transparent;}
.tab-page{flex:1;min-height:0;overflow-y:auto;padding:32px 36px;display:flex;flex-direction:column;gap:26px;animation:tabIn .28s var(--ease-out) both;}
.tab-page>*{flex-shrink:0;}
@keyframes tabIn{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}

.page-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;}
.page-title{font-size:19px;font-weight:800;letter-spacing:-.03em;}
.page-subtitle{font-size:10px;color:var(--text3);margin-top:3px;}
.page-actions{display:flex;gap:7px;}
.page-btn{padding:8px 16px;border-radius:9px;font-size:13px;font-weight:600;cursor:pointer;border:1.5px solid rgba(255,255,255,0.2);background:rgba(13,21,32,0.3);backdrop-filter:blur(8px);color:var(--text2);transition:all .2s var(--ease-out);}
.page-btn:hover{border-color:var(--accent);color:var(--accent);background:rgba(0,229,160,0.08);}
.page-btn.primary{background:rgba(255,255,255,0.95);backdrop-filter:none;border-color:rgba(255,255,255,0.95);color:#0a0e27;font-weight:700;box-shadow:0 8px 24px rgba(0,229,160,0.2);}
.page-btn.primary:hover{background:#ffffff;transform:translateY(-2px);box-shadow:0 12px 32px rgba(0,229,160,0.25);}

/* ── NARRATIVE BANNER ── */
.narrative-banner{
  position:relative;padding:20px 24px;max-width:600px;
  background:rgba(255,77,106,0.08);backdrop-filter:blur(12px);border:1px solid rgba(255,77,106,0.28);
  border-radius:14px;display:flex;align-items:center;justify-content:space-between;gap:12px;
  cursor:pointer;transition:all .3s var(--ease-out);overflow:hidden;margin:0 auto;
  animation:bannerIn .6s var(--ease-out) both;
}
.narrative-banner:hover{border-color:rgba(255,77,106,0.5);transform:translateY(-4px);box-shadow:0 12px 40px rgba(255,77,106,0.15);}
@keyframes bannerIn{from{opacity:0;transform:translateY(-8px)}to{opacity:1;transform:translateY(0)}}
.nb-left{display:flex;align-items:center;gap:12px;}
.nb-pulse{width:10px;height:10px;border-radius:50%;background:var(--danger);flex-shrink:0;animation:nbPulse 2s infinite;}
@keyframes nbPulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.6;transform:scale(1.3)}}
.nb-text{font-size:14px;color:#ffffff;font-weight:500;}
.nb-text strong{color:var(--accent2);font-weight:700;}
.nb-cta{font-size:12px;color:var(--accent2);white-space:nowrap;font-weight:600;display:flex;align-items:center;gap:4px;border:none;padding:0;background:none;cursor:pointer;transition:all .2s;}
.nb-cta:hover{color:var(--accent);}

/* ── KPI CARDS ── */
.kpi-strip{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;width:100%;}
.kpi-card{background:rgba(255,255,255,0.06);backdrop-filter:blur(14px);border:1.5px solid rgba(255,255,255,0.12);border-radius:12px;padding:20px 22px;text-align:left;position:relative;overflow:hidden;min-width:0;transition:border-color .2s,transform .18s,box-shadow .2s;cursor:default;box-shadow:0 8px 24px rgba(0,0,0,0.15);}
[data-theme="light"] .kpi-card{background:rgba(255,255,255,0.5);border-color:rgba(0,0,0,0.08);}
.kpi-card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,var(--accent),var(--accent2));transform:scaleX(0);transform-origin:left;transition:transform .28s var(--ease-out);}
.kpi-card.danger-card{border-color:rgba(255,77,106,0.28);animation:dangerPulse 3s infinite;}
@keyframes dangerPulse{0%,100%{box-shadow:0 0 0 0 rgba(255,77,106,0)}50%{box-shadow:0 0 0 4px rgba(255,77,106,0.07)}}
.kpi-card.danger-card::before{background:linear-gradient(90deg,var(--danger),#ff8a65);transform:scaleX(1);}
.kpi-card.amber-card::before{background:linear-gradient(90deg,var(--amber),#f97316);}
.kpi-card:hover{border-color:rgba(59,130,246,.6);transform:translateY(-4px);box-shadow:0 0 24px rgba(29,209,238,0.15);}
.kpi-card.danger-card:hover{border-color:rgba(255,77,106,0.55);box-shadow:0 12px 32px rgba(255,77,106,0.12);}
.kpi-card:hover::before{transform:scaleX(1);}
.kpi-icon{font-size:15px;margin-bottom:8px;display:block;}
.kpi-label{font-size:10px;font-weight:700;color:var(--text3);text-transform:uppercase;letter-spacing:.13em;margin-bottom:4px;}
.kpi-value{font-size:clamp(22px,2.8vw,28px);font-weight:800;color:var(--text);letter-spacing:-0.03em;}
.kpi-card.danger-card .kpi-value{color:var(--danger);}
.kpi-delta{display:flex;align-items:center;gap:4px;font-size:10px;margin-top:4px;}
.kpi-delta.up{color:var(--accent);}.kpi-delta.down{color:var(--danger);}.kpi-delta.neutral{color:var(--amber);}

/* ── SUGGESTIONS ── */
.suggestions{display:grid;grid-template-columns:1fr 1fr;gap:12px;width:100%;}
.sug-chip{background:rgba(255,255,255,0.06);backdrop-filter:blur(16px);border:1.5px solid rgba(255,255,255,0.12);border-radius:14px;padding:18px 16px;text-align:left;cursor:pointer;font-size:12px;color:var(--text2);transition:all .25s var(--ease-out);line-height:1.4;display:flex;flex-direction:column;gap:10px;border-left:4px solid rgba(255,255,255,.18);}
.sug-chip:hover{transform:translateY(-6px);box-shadow:0 16px 40px rgba(0,0,0,0.3);}
.sug-chip-header{display:flex;align-items:center;gap:8px;}
.sug-chip-icon{font-size:18px;line-height:1;}
.sug-chip.revenue{border-left-color:#00e5a0;}.sug-chip.risk{border-left-color:#ff4d6a;}.sug-chip.ops{border-left-color:#00b4ff;}.sug-chip.growth{border-left-color:#a78bfa;}
.sug-chip.revenue .sug-chip-icon,.sug-chip.risk .sug-chip-icon,.sug-chip.ops .sug-chip-icon,.sug-chip.growth .sug-chip-icon{width:26px;height:26px;border-radius:7px;display:inline-flex;align-items:center;justify-content:center;background:rgba(255,255,255,.07);}
.sug-chip.revenue .sug-chip-icon{background:rgba(0,229,160,.16);}.sug-chip.risk .sug-chip-icon{background:rgba(255,77,106,.16);}.sug-chip.ops .sug-chip-icon{background:rgba(0,180,255,.16);}.sug-chip.growth .sug-chip-icon{background:rgba(167,139,250,.16);}
.sug-chip strong{color:var(--text);font-size:14px;font-weight:700;}
.sug-chip-tag{display:inline-block;font-size:8.5px;padding:1px 6px;border-radius:3px;letter-spacing:.05em;}
.sug-chip-tag.revenue{background:rgba(0,229,160,.12);color:var(--accent);}.sug-chip-tag.risk{background:rgba(255,77,106,.12);color:var(--danger);}.sug-chip-tag.ops{background:rgba(0,180,255,.12);color:var(--accent2);}.sug-chip-tag.growth{background:rgba(167,139,250,.12);color:var(--purple);}
[data-theme="light"] .sug-chip-tag.revenue{color:var(--accent);}[data-theme="light"] .sug-chip-tag.risk{color:var(--danger);}[data-theme="light"] .sug-chip-tag.ops{color:var(--accent2);}[data-theme="light"] .sug-chip-tag.growth{color:var(--purple);}
.sug-chip-desc{font-size:11.5px;color:var(--text2);line-height:1.5;}

/* ── SAMPLE CONVO ── */
.sample-convo{width:100%;background:rgba(13,21,32,0.45);backdrop-filter:blur(12px);border:1px solid rgba(255,255,255,0.12);border-radius:12px;overflow:hidden;position:relative;}
.sample-convo::before{content:'';position:absolute;inset:0;padding:1px;border-radius:12px;background:linear-gradient(135deg,rgba(0,229,160,.46),rgba(0,180,255,.18),rgba(167,139,250,.28));-webkit-mask:linear-gradient(#000 0 0) content-box,linear-gradient(#000 0 0);-webkit-mask-composite:xor;mask-composite:exclude;pointer-events:none;}
[data-theme="light"] .sample-convo{background:rgba(255,255,255,0.5);border-color:rgba(0,0,0,0.08);}
.sample-convo-head{padding:12px 18px;border-bottom:1px solid rgba(255,255,255,0.1);display:flex;align-items:center;gap:8px;background:rgba(0,229,160,0.08);}
.sample-convo-title{font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--accent);}
.sample-convo-badge{font-size:9px;padding:2px 7px;background:rgba(0,229,160,.1);color:var(--accent);border-radius:4px;margin-left:auto;}
.sample-q{display:flex;align-items:flex-start;gap:9px;padding:16px 18px;border-bottom:1px solid var(--border);}
.sample-q-avatar{width:24px;height:24px;border-radius:50%;background:rgba(17,28,46,0.4);backdrop-filter:blur(8px);border:1px solid rgba(255,255,255,0.15);display:flex;align-items:center;justify-content:center;font-size:8.5px;font-weight:700;color:var(--text3);flex-shrink:0;}
.sample-q-text{font-size:12.5px;color:var(--text2);line-height:1.55;padding-top:2px;}
.sample-a{display:flex;align-items:flex-start;gap:9px;padding:16px 18px;}
.sample-a-avatar{width:24px;height:24px;border-radius:50%;background:linear-gradient(135deg,var(--accent),var(--accent2));display:flex;align-items:center;justify-content:center;font-size:8.5px;font-weight:700;color:#000;flex-shrink:0;}
.sample-a-text{font-size:12.5px;color:var(--text);line-height:1.6;}
.sample-a-text strong{color:var(--danger);font-weight:600;background:rgba(255,77,106,.12);padding:1px 6px;border-radius:4px;}
.sample-a-chips{display:flex;gap:6px;margin-top:10px;flex-wrap:wrap;}
.sample-chip{font-size:10px;padding:3px 8px;border-radius:5px;border:1px solid var(--border2);color:var(--text3);}
.sample-chip.danger{border-color:rgba(255,77,106,.3);color:var(--danger);background:rgba(255,77,106,.06);}
.sample-chip.ok{border-color:rgba(0,229,160,.3);color:var(--accent);background:rgba(0,229,160,.06);}
.sample-cta{padding:12px 18px;border-top:1px solid var(--border);text-align:center;font-size:10.5px;color:var(--text3);}
.sample-cta span{color:var(--accent);cursor:pointer;}.sample-cta span:hover{text-decoration:underline;}

/* ── CHAT MESSAGES ── */
.chat-area{flex:1;overflow-y:auto;padding:28px 32px;display:flex;flex-direction:column;gap:24px;scroll-behavior:smooth;background:transparent;border-radius:22px;}
.welcome{margin:auto;display:flex;flex-direction:column;align-items:center;gap:32px;text-align:center;max-width:800px;width:100%;animation:welcomeIn .8s var(--ease-out) both;max-height:100%;justify-content:center;}
@keyframes welcomeIn{from{opacity:0;transform:translateY(32px)}to{opacity:1;transform:translateY(0)}}
.welcome h1{font-size:clamp(32px,5vw,48px);font-weight:900;line-height:1.1;letter-spacing:-.06em;margin:0;background:linear-gradient(135deg,#3B82F6,#1DD1EE,#63DEF9);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}
.welcome-desc{font-size:16px;color:#cbd5e1;line-height:1.6;max-width:600px;font-weight:400;margin:0;}

.msg-row{display:flex;gap:16px;animation:msgIn .3s var(--ease-out) both;}
@keyframes msgIn{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)}}
.msg-row.user{flex-direction:row-reverse;}
.avatar{width:32px;height:32px;border-radius:50%;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;}
.avatar.ai{background:transparent;box-shadow:none;}
.avatar.user{background:rgba(17,28,46,0.4);backdrop-filter:blur(8px);border:1px solid rgba(255,255,255,0.15);color:var(--text2);}
[data-theme="light"] .avatar.user{background:rgba(240,245,255,0.3);border-color:rgba(0,0,0,0.08);}
.bubble{max-width:72%;padding:18px 22px;border-radius:13px;font-size:15px;line-height:1.8;border:1px solid transparent;position:relative;}
.bubble.user{background:rgba(59,130,246,0.12);border-color:rgba(59,130,246,0.35);border-bottom-right-radius:4px;backdrop-filter:blur(12px);}
[data-theme="light"] .bubble.user{background:linear-gradient(135deg,rgba(29,78,216,.07),rgba(14,165,233,.04));border-color:rgba(29,78,216,.2);}
.bubble.ai{background:rgba(6,12,22,0.62);backdrop-filter:blur(14px);border-color:rgba(255,255,255,0.15);border-bottom-left-radius:4px;}
.bubble.ai::before{content:'';position:absolute;left:-1px;top:8px;bottom:8px;width:2px;border-radius:999px;background:linear-gradient(180deg,rgba(59,130,246,.9),rgba(29,209,238,.72));box-shadow:0 0 10px rgba(59,130,246,.45);animation:aiPulse 1.8s ease-in-out infinite;}
@keyframes aiPulse{0%,100%{opacity:.45}50%{opacity:1}}
[data-theme="light"] .bubble.ai{background:rgba(255,255,255,0.45);border-color:rgba(0,0,0,0.06);}
.bubble.error{border-color:rgba(255,77,106,.3);background:rgba(255,77,106,.05);}
.bubble-text{white-space:pre-wrap;word-break:break-word;line-height:1.75;}

.bubble-meta{display:flex;align-items:center;gap:7px;margin-top:14px;padding-top:12px;border-top:1px solid rgba(255,255,255,0.06);}
[data-theme="light"] .bubble-meta{border-top-color:rgba(0,0,0,0.06);}
.bubble-time{font-size:9.5px;color:var(--text3);}
.bubble-actions{display:flex;gap:4px;opacity:0;transition:opacity .2s;margin-left:auto;}
.msg-row:hover .bubble-actions{opacity:1;}
.bubble-action-btn{width:20px;height:20px;border-radius:5px;border:1px solid var(--border);background:var(--bg2);cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:10px;color:var(--text3);transition:all .14s;}
.bubble-action-btn:hover{border-color:var(--accent);color:var(--accent);}

/* ── RESPONSE CHART ── */
.response-chart{margin-top:22px;background:rgba(10,22,40,0.4);backdrop-filter:blur(16px);border:1px solid rgba(59,130,246,0.25);border-radius:12px;padding:20px;box-shadow:0 8px 32px rgba(0,0,0,0.3),inset 0 1px 0 rgba(255,255,255,0.05);transition:transform 0.2s,border-color 0.2s;}
.response-chart:hover{border-color:rgba(59,130,246,0.45);transform:translateY(-2px);}
[data-theme="light"] .response-chart{background:rgba(240,245,255,0.4);border-color:rgba(0,0,0,0.06);}
.chart-title{font-size:10px;font-weight:800;color:var(--accent2);letter-spacing:.12em;text-transform:uppercase;margin-bottom:18px;display:flex;align-items:center;gap:6px;}
.chart-title::before{content:'';width:4px;height:4px;background:var(--accent2);border-radius:50%;box-shadow:0 0 8px var(--accent2);}
.chart-bars{display:flex;flex-direction:column;gap:14px;}
.chart-row{display:flex;align-items:center;gap:12px;padding:4px;border-radius:6px;transition:background 0.2s;}
.chart-row:hover{background:rgba(255,255,255,0.04);}
.chart-label{font-size:11px;font-weight:500;color:var(--text2);width:90px;flex-shrink:0;text-align:right;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.chart-track{flex:1;height:24px;background:rgba(0,0,0,0.3);border-radius:6px;overflow:hidden;position:relative;border:1px solid rgba(255,255,255,0.05);}
[data-theme="light"] .chart-track{background:rgba(0,0,0,0.05);}
.chart-fill{height:100%;border-radius:4px;background:linear-gradient(90deg,#3B82F6 0%,#1DD1EE 100%);width:0;transition:width 1s cubic-bezier(0.34,1.56,0.64,1);display:flex;align-items:center;justify-content:flex-end;min-width:2px;position:relative;box-shadow:0 0 15px rgba(59,130,246,0.3);}
.chart-fill::after{content:'';position:absolute;top:0;left:0;right:0;bottom:0;background:linear-gradient(90deg,transparent,rgba(255,255,255,0.12),transparent);transform:translateX(-100%);animation:chartShimmer 3s infinite;}
@keyframes chartShimmer{100%{transform:translateX(100%);}}
.chart-fill.amber{background:linear-gradient(90deg,#f59e0b,#fbbf24);box-shadow:0 0 15px rgba(245,158,11,0.3);}
.chart-fill.danger{background:linear-gradient(90deg,#ff4d6a,#ff8a65);box-shadow:0 0 15px rgba(255,77,106,0.3);}
.chart-val{font-size:10px;font-weight:700;color:rgba(255,255,255,0.95);padding-right:8px;white-space:nowrap;text-shadow:0 1px 2px rgba(0,0,0,0.4);}
/* Pie / Line chart styles */
.chart-layout{display:grid;grid-template-columns:180px 1fr;gap:14px;align-items:center;}
.donut{width:160px;height:160px;border-radius:50%;border:1px solid rgba(255,255,255,0.1);box-shadow:inset 0 0 0 1px rgba(255,255,255,0.06);}
.pie-legend{display:flex;flex-direction:column;gap:8px;}
.legend-item{display:flex;align-items:center;gap:8px;font-size:11px;color:var(--text2);}
.legend-dot{width:10px;height:10px;border-radius:50%;flex-shrink:0;}
.line-wrap{height:190px;background:rgba(0,0,0,0.2);border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:8px;}
.line-svg{width:100%;height:100%;}
.line-axis{font-size:9px;fill:var(--text3);}
.line-stroke{fill:none;stroke:#3B82F6;stroke-width:2.4;stroke-linecap:round;stroke-linejoin:round;}
.line-fill{fill:rgba(59,130,246,0.12);}
.line-point{fill:#1DD1EE;stroke:#0a1628;stroke-width:1.2;}

/* ── DATA TABLE ── */
.data-card{margin-top:11px;background:rgba(255,255,255,0.05);backdrop-filter:blur(14px);border:1.5px solid rgba(255,255,255,0.1);border-radius:10px;overflow:hidden;}
[data-theme="light"] .data-card{background:rgba(240,245,255,0.4);border-color:rgba(0,0,0,0.06);}
.data-card-head{padding:7px 13px;border-bottom:1px solid rgba(255,255,255,0.1);font-size:9.5px;color:var(--accent);letter-spacing:.07em;background:rgba(0,229,160,0.08);}
.data-table-wrap{overflow-x:auto;}
.data-table{width:100%;border-collapse:collapse;font-size:11.5px;}
.data-table th{padding:7px 13px;text-align:left;color:var(--text3);font-weight:500;border-bottom:1px solid var(--border);white-space:nowrap;}
.data-table td{padding:6px 13px;color:var(--text);border-bottom:1px solid rgba(255,255,255,.03);}
.data-table tr:last-child td{border-bottom:none;}
.data-table .pos{color:var(--accent);}.data-table .neg{color:var(--danger);}
.data-table tbody tr{transition:background .12s;}.data-table tbody tr:hover{background:rgba(255,255,255,.025);}

.msg-footer{display:flex;align-items:center;flex-wrap:wrap;gap:10px;margin-top:12px;padding-top:10px;border-top:1px solid var(--border);}
.msg-badge{font-size:9px;padding:2px 7px;border-radius:4px;}
.msg-badge.conf{background:rgba(0,229,160,.1);color:var(--accent);}.msg-badge.samp{background:rgba(255,255,255,.05);color:var(--text3);}.msg-badge.exec{background:rgba(0,180,255,.08);color:var(--accent2);margin-left:auto;}

.typing{display:flex;gap:5px;align-items:center;padding:2px 0;}
.typing span{width:6px;height:6px;border-radius:50%;background:var(--accent);opacity:.35;animation:throb 1.1s infinite;}
.typing span:nth-child(2){animation-delay:.18s;}.typing span:nth-child(3){animation-delay:.36s;}
@keyframes throb{0%,60%,100%{transform:scale(1);opacity:.3}30%{transform:scale(1.4);opacity:1}}

/* ── INPUT ZONE ── */
.input-zone{width:min(1120px,calc(100% - 28px));margin:0 auto 10px;padding:12px 20px;border:1px solid rgba(255,255,255,0.18);border-radius:16px;background:rgba(8,12,30,0.5);backdrop-filter:blur(22px);flex-shrink:0;box-shadow:0 10px 34px rgba(0,0,0,0.2),inset 0 1px 0 rgba(255,255,255,0.06);display:flex;flex-direction:column;transition:all .25s var(--ease-out);position:relative;}
[data-theme="light"] .input-zone{background:rgba(255,255,255,0.5);border-color:rgba(0,0,0,0.08);}
.input-zone:focus-within{border-color:rgba(59,130,246,.4);box-shadow:0 0 0 4px rgba(59,130,246,.1),0 12px 40px rgba(59,130,246,.15);}
.input-zone.drag-over{border-color:var(--accent);box-shadow:0 0 0 3px var(--glow);background:rgba(0,229,160,.04);}
.drag-hint{position:absolute;inset:0;border-radius:16px;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:600;color:var(--accent);background:rgba(8,13,20,.88);backdrop-filter:blur(6px);pointer-events:none;opacity:0;transition:opacity .2s;z-index:10;}
.input-zone.drag-over .drag-hint{opacity:1;}

.attach-preview-row{display:flex;flex-wrap:wrap;gap:8px;padding-bottom:12px;margin-bottom:8px;border-bottom:1px solid var(--border);}
.attach-thumb{position:relative;border-radius:7px;overflow:visible;display:flex;flex-direction:column;align-items:center;}
.attach-thumb img{width:58px;height:46px;object-fit:cover;border-radius:7px;border:1px solid var(--border2);display:block;}
.attach-thumb-file{width:58px;height:46px;border-radius:7px;background:var(--bg2);border:1px solid var(--border2);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;}
.attach-thumb-file-icon{font-size:18px;line-height:1;}
.attach-thumb-file-ext{font-size:7.5px;color:var(--accent);text-transform:uppercase;letter-spacing:.06em;background:rgba(0,229,160,.1);padding:1px 4px;border-radius:3px;}
.attach-thumb-name{font-size:8px;color:var(--text3);max-width:58px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;text-align:center;margin-top:2px;}
.attach-remove-btn{position:absolute;top:-5px;right:-5px;width:16px;height:16px;border-radius:50%;background:var(--danger);border:2px solid var(--bg1);color:#fff;font-size:8px;font-weight:700;display:flex;align-items:center;justify-content:center;cursor:pointer;transition:transform .14s;z-index:5;}
.attach-remove-btn:hover{transform:scale(1.18);}

.attach-menu-wrap{position:relative;}
.attach-menu{position:absolute;bottom:calc(100% + 10px);right:0;background:rgba(3,5,9,0.72);backdrop-filter:blur(18px);border:1px solid rgba(255,255,255,0.17);border-radius:11px;padding:6px;min-width:195px;z-index:50;box-shadow:0 14px 44px rgba(0,0,0,0.38);animation:attachMenuIn .18s var(--ease-spring) both;}
@keyframes attachMenuIn{from{opacity:0;transform:translateY(6px) scale(.97)}to{opacity:1;transform:translateY(0) scale(1)}}
.attach-menu-item{display:flex;align-items:center;gap:9px;padding:10px 12px;border-radius:7px;cursor:pointer;transition:background .12s,color .12s;font-size:12.5px;color:var(--text2);}
.attach-menu-item:hover{background:rgba(0,229,160,.08);color:var(--text);}
[data-theme="light"] .attach-menu-item:hover{background:rgba(0,122,82,.07);}
.attach-menu-item:hover .ami-icon{color:var(--accent);}
.ami-icon{font-size:15px;width:20px;text-align:center;color:var(--text3);transition:color .12s;flex-shrink:0;}
.ami-label{flex:1;}.ami-sub{font-size:9px;color:var(--text3);}
.attach-menu-divider{height:1px;background:var(--border);margin:3px 6px;}

.input-row{display:flex;align-items:center;gap:7px;}
.chat-input{flex:1;border:none !important;background:transparent !important;font-size:13.5px;color:var(--text);resize:none;outline:none;min-height:22px;max-height:120px;line-height:1.55;display:block;vertical-align:middle;padding:0 !important;box-shadow:none !important;}
.chat-input::placeholder{color:#8ea3c2;font-style:italic;}
.input-actions{display:flex;align-items:center;gap:5px;flex-shrink:0;margin-bottom:1px;}
.attach-btn{width:32px;height:32px;border-radius:7px;background:rgba(255,255,255,0.05);backdrop-filter:blur(8px);border:1px solid rgba(255,255,255,0.15);cursor:pointer;display:flex;align-items:center;justify-content:center;color:var(--text3);transition:all .16s;position:relative;flex-shrink:0;}
.attach-btn:hover{border-color:var(--accent);color:var(--accent);background:rgba(59,130,246,0.1);}
.attach-btn.has-files{border-color:rgba(59,130,246,.45);color:var(--accent);background:rgba(59,130,246,.07);}
.attach-badge{position:absolute;top:-5px;right:-5px;background:var(--accent);color:#fff;font-size:8.5px;font-weight:700;width:14px;height:14px;border-radius:50%;display:flex;align-items:center;justify-content:center;border:2px solid var(--bg1);}
.mic-btn.listening{color:#ff6b6b;border-color:#ff6b6b;background:rgba(255,107,107,0.16);box-shadow:0 0 10px rgba(255,107,107,0.25);}
.send-btn{width:36px;height:36px;border-radius:10px;background:linear-gradient(135deg,#ffffff 0%,#f0f0f0 100%);border:none;cursor:pointer;display:flex;align-items:center;justify-content:center;color:#0a0e27;transition:all .2s var(--ease-out);box-shadow:0 4px 16px rgba(255,255,255,0.25);flex-shrink:0;font-weight:700;}
.send-btn:hover:not(:disabled){box-shadow:0 8px 28px rgba(255,255,255,0.3);transform:scale(1.08) translateY(-2px);}
.send-btn:disabled{opacity:.4;cursor:not-allowed;}
.stop-btn{width:36px;height:36px;border-radius:8px;background:linear-gradient(135deg,#1D4ED8,#0ea5e9);border:1px solid rgba(99,222,249,0.4);cursor:pointer;display:flex;align-items:center;justify-content:center;color:#fff;transition:box-shadow .2s;flex-shrink:0;}
.stop-btn:hover{box-shadow:0 0 12px rgba(29,209,238,0.4);}
.listening-indicator{margin-top:8px;display:flex;align-items:center;gap:6px;font-size:10px;color:#ff9ca8;}
.listening-dot{width:7px;height:7px;border-radius:50%;background:#ff6b6b;animation:listenPulse 1s ease-in-out infinite;}
@keyframes listenPulse{0%,100%{opacity:.45;transform:scale(1);}50%{opacity:1;transform:scale(1.2);}}

/* ── COPY TOAST ── */
.copy-toast{position:fixed;bottom:88px;left:50%;transform:translateX(-50%) translateY(10px);background:var(--accent);color:#000;font-size:11px;font-weight:600;padding:5px 13px;border-radius:20px;box-shadow:0 4px 18px var(--glow);opacity:0;transition:all .22s var(--ease-spring);pointer-events:none;z-index:999;}
.copy-toast.show{opacity:1;transform:translateX(-50%) translateY(0);}

/* ── LIVE FEED PANEL ── */
.live-feed-panel{width:280px;min-width:280px;flex-shrink:0;background:rgba(3,5,9,0.5);backdrop-filter:blur(22px);border-left:1px solid rgba(255,255,255,0.12);display:flex;flex-direction:column;overflow:hidden;position:relative;z-index:10;animation:slideInRight .25s var(--ease-out) both;}
[data-theme="light"] .live-feed-panel{background:rgba(255,255,255,0.45);border-left-color:rgba(0,0,0,0.08);}
@keyframes slideInRight{from{opacity:0;transform:translateX(20px)}to{opacity:1;transform:translateX(0)}}

.mini-chart{display:flex;align-items:flex-end;gap:3px;height:44px;}
.mini-bar{flex:1;border-radius:3px 3px 0 0;background:linear-gradient(180deg,rgba(0,229,160,.45),rgba(0,180,255,.18));transition:opacity .15s;cursor:pointer;}
[data-theme="light"] .mini-bar{background:linear-gradient(180deg,rgba(0,122,82,.5),rgba(0,102,187,.2));}
.mini-bar:hover{opacity:.7;}.mini-bar.hi{background:linear-gradient(180deg,var(--accent),var(--accent2));}
.mini-chart-foot{display:flex;justify-content:space-between;margin-top:4px;font-size:8.5px;color:var(--text3);}

/* ── ALERT CARDS ── */
.alert-card{background:rgba(17,28,46,0.4);backdrop-filter:blur(10px);border-radius:9px;padding:16px 18px;display:flex;flex-direction:column;gap:8px;border:1px solid rgba(255,77,106,0.25);transition:border-color .14s,transform .14s;position:relative;overflow:hidden;}
[data-theme="light"] .alert-card{background:rgba(240,245,255,0.4);border-color:rgba(200,0,61,0.15);}
.alert-card::before{content:'';position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--danger);border-radius:3px 0 0 3px;}
.alert-card:hover{border-color:rgba(255,77,106,.4);transform:translateX(-2px);}
.alert-card.warn{border-color:rgba(245,158,11,.18);}.alert-card.warn::before{background:var(--amber);}
.alert-card.warn:hover{border-color:rgba(245,158,11,.4);}
.alert-head{display:flex;align-items:center;justify-content:space-between;gap:5px;}
.alert-head-left{display:flex;align-items:center;gap:5px;}
.alert-icon{font-size:11px;}
.alert-title{font-size:11px;font-weight:600;color:var(--text);}
.alert-time{font-size:8.5px;color:var(--text3);flex-shrink:0;}
.alert-body{font-size:11px;color:var(--text2);line-height:1.5;}
.alert-impact{font-size:9.5px;color:var(--danger);font-weight:600;margin-top:1px;}
.alert-impact.warn{color:var(--amber);}
.alert-footer{display:flex;align-items:center;justify-content:space-between;}
.alert-tag{font-size:8.5px;padding:2px 7px;border-radius:4px;font-weight:600;letter-spacing:.05em;}
.alert-tag.danger{background:rgba(255,77,106,.12);color:var(--danger);}
.alert-tag.warn{background:rgba(245,158,11,.12);color:var(--amber);}
.alert-action{font-size:9px;color:var(--accent);cursor:pointer;text-decoration:underline;transition:opacity .14s;}
.alert-action:hover{opacity:.7;}

/* ── TABLE PAGES ── */
.full-table-wrap{background:rgba(255,255,255,0.05);backdrop-filter:blur(16px);border:1.5px solid rgba(255,255,255,0.12);border-radius:14px;overflow:hidden;box-shadow:0 8px 28px rgba(0,0,0,0.12);}
[data-theme="light"] .full-table-wrap{background:rgba(255,255,255,0.5);border-color:rgba(0,0,0,0.08);}
.full-table-head{display:flex;align-items:center;justify-content:space-between;padding:16px 20px;border-bottom:1px solid rgba(255,255,255,0.1);}
.full-table-title{font-size:13px;font-weight:700;}
.ft-search-input{padding:6px 10px;background:rgba(13,21,32,0.3);backdrop-filter:blur(8px);border:1px solid rgba(255,255,255,0.15);border-radius:7px;font-size:11px;color:var(--text);outline:none;width:175px;transition:border-color .15s;}
.ft-search-input:focus{border-color:rgba(0,229,160,.4);box-shadow:0 0 0 2px rgba(0,229,160,0.15);}
.ft-search-input::placeholder{color:var(--text3);}
.full-table{width:100%;border-collapse:collapse;font-size:12px;}
.full-table th{padding:13px 18px;text-align:left;font-size:9.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--text3);border-bottom:1px solid var(--border);background:rgba(255,255,255,.015);white-space:nowrap;}
[data-theme="light"] .full-table th{background:rgba(0,0,0,.02);}
.full-table td{padding:12px 18px;border-bottom:1px solid rgba(255,255,255,.03);color:var(--text);vertical-align:middle;}
[data-theme="light"] .full-table td{border-bottom-color:var(--border);}
.full-table tbody tr{transition:background .11s;cursor:pointer;}
.full-table tbody tr:hover{background:rgba(255,255,255,.03);}
[data-theme="light"] .full-table tbody tr:hover{background:rgba(0,0,0,.025);}
.full-table tr:last-child td{border-bottom:none;}
.ft-badge{display:inline-block;font-size:9px;padding:2px 7px;border-radius:4px;font-weight:600;}
.ft-badge.success{background:rgba(0,229,160,.12);color:var(--accent);}
.ft-badge.failed{background:rgba(255,77,106,.12);color:var(--danger);}
.ft-badge.pending{background:rgba(245,158,11,.12);color:var(--amber);}
.ft-badge.flagged{background:rgba(255,77,106,.18);color:var(--danger);}
.ft-badge.low{background:rgba(0,229,160,.12);color:var(--accent);}
.ft-badge.medium{background:rgba(245,158,11,.12);color:var(--amber);}
.ft-badge.high{background:rgba(255,77,106,.18);color:var(--danger);}
.ft-mono{font-size:11px;}

.two-col-grid{display:grid;grid-template-columns:1fr 1fr;gap:20px;}
.three-col-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;}
.panel-card{background:rgba(255,255,255,0.06);backdrop-filter:blur(16px);border:1.5px solid rgba(255,255,255,0.12);border-radius:14px;padding:26px 28px;box-shadow:0 8px 28px rgba(0,0,0,0.12);}
[data-theme="light"] .panel-card{background:rgba(255,255,255,0.5);border-color:rgba(0,0,0,0.08);}
.panel-card-title{font-size:13px;font-weight:700;margin-bottom:18px;display:flex;align-items:center;gap:7px;}
.metric-row{display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:1px solid var(--border);}
.metric-row:last-child{border-bottom:none;}
.metric-label{font-size:12px;color:var(--text2);}
.metric-val{font-size:11.5px;font-weight:600;color:var(--text);}
.metric-val.green{color:var(--accent);}.metric-val.red{color:var(--danger);}.metric-val.amber{color:var(--amber);}

.gauge-wrap{text-align:center;padding:10px 0 16px;}
.gauge-score{font-size:36px;font-weight:800;line-height:1;}
.gauge-label{font-size:9.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--text3);margin-top:4px;}
.gauge-sub{font-size:11px;color:var(--text2);margin-top:5px;}

.report-card{background:rgba(255,255,255,0.06);backdrop-filter:blur(16px);border:1.5px solid rgba(255,255,255,0.12);border-radius:13px;padding:22px 24px;display:flex;align-items:flex-start;gap:18px;cursor:pointer;transition:all .24s var(--ease-out);box-shadow:0 6px 20px rgba(0,0,0,0.1);}
[data-theme="light"] .report-card{background:rgba(255,255,255,0.5);border-color:rgba(0,0,0,0.08);}
.report-card:hover{transform:translateY(-6px);box-shadow:0 16px 40px rgba(0,0,0,0.3);}
.report-icon{font-size:24px;flex-shrink:0;margin-top:2px;}
.report-info{flex:1;min-width:0;}
.report-title{font-size:13px;font-weight:700;margin-bottom:3px;}
.report-desc{font-size:11.5px;color:var(--text2);line-height:1.55;}
.report-meta{display:flex;align-items:center;gap:9px;margin-top:10px;}
.report-tag{font-size:9px;padding:2px 7px;border-radius:4px;background:rgba(0,180,255,.1);color:var(--accent2);}
.report-date{font-size:9px;color:var(--text3);}
.report-dl{font-size:9.5px;color:var(--accent);flex-shrink:0;border:1px solid rgba(0,229,160,.25);padding:4px 9px;border-radius:6px;transition:all .14s;}
.report-dl:hover{background:var(--glow);}

/* ── AUTH MODAL ── */
.modal-overlay{position:fixed;inset:0;background:rgba(0,0,0,0.6);backdrop-filter:blur(10px);z-index:100;display:flex;align-items:center;justify-content:center;animation:fadeIn .2s ease;}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}
.modal{background:rgba(10,14,27,0.45);backdrop-filter:blur(24px);border:1.5px solid rgba(255,255,255,0.15);border-radius:18px;padding:32px 36px;width:min(360px,92vw);box-shadow:0 32px 88px rgba(0,0,0,0.3);position:relative;animation:scaleIn .22s var(--ease-spring) both;}
@keyframes scaleIn{from{opacity:0;transform:scale(.94)}to{opacity:1;transform:scale(1)}}
.modal-close{position:absolute;top:13px;right:13px;background:transparent;border:none;cursor:pointer;color:var(--text3);font-size:16px;width:28px;height:28px;display:flex;align-items:center;justify-content:center;border-radius:6px;transition:all .13s;}
.modal-close:hover{background:var(--bg2);color:var(--text);}
.modal h2{font-size:21px;font-weight:800;letter-spacing:-.03em;margin-bottom:5px;}
.modal p{font-size:12.5px;color:var(--text2);margin-bottom:20px;line-height:1.65;}
.field{margin-bottom:11px;}
.field label{display:block;font-size:10px;color:var(--text3);margin-bottom:5px;letter-spacing:.05em;text-transform:uppercase;}
.field input{width:100%;padding:9px 12px;background:rgba(13,21,32,0.4);backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,0.15);border-radius:8px;font-size:13px;color:var(--text);outline:none;transition:border-color .15s,box-shadow .15s;}
.field input:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(0,229,160,0.15);}
.field input::placeholder{color:var(--text3);}
.modal-submit{width:100%;padding:11px;background:linear-gradient(135deg,var(--accent),var(--accent2));border:none;border-radius:9px;font-size:14px;font-weight:700;color:#000;cursor:pointer;margin-top:4px;transition:all .17s;box-shadow:0 0 18px var(--glow);}
.modal-submit:hover{box-shadow:0 0 28px var(--glow);transform:translateY(-1px);}
.modal-toggle{text-align:center;margin-top:13px;font-size:12px;color:var(--text3);}
.modal-toggle button{background:none;border:none;cursor:pointer;color:var(--accent);font-size:12px;font-weight:600;text-decoration:underline;}

/* ── LIGHTBOX ── */
.lightbox-overlay{position:fixed;inset:0;background:rgba(0,0,0,.88);backdrop-filter:blur(12px);z-index:200;display:flex;align-items:center;justify-content:center;animation:fadeIn .2s ease;cursor:zoom-out;}
.lightbox-img{max-width:90vw;max-height:88vh;border-radius:10px;box-shadow:0 24px 72px rgba(0,0,0,.7);}
.lightbox-close{position:fixed;top:15px;right:15px;background:rgba(255,255,255,.1);border:none;color:#fff;width:36px;height:36px;border-radius:50%;font-size:18px;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:background .14s;}
.lightbox-close:hover{background:rgba(255,255,255,.2);}

/* ── INTRO / SPLIT-TEXT ANIMATION ── */
.intro-text-block{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center;max-width:600px;width:100%;z-index:30;pointer-events:none;display:flex;flex-direction:column;align-items:center;gap:12px;}
.intro-text-block.fade-out{opacity:0;transition:opacity 0.7s ease;}
.split-line{overflow:hidden;}
.split-word{display:inline-block;opacity:0;transform:translateY(20px);animation:splitWordIn 0.4s ease-out forwards;}
@keyframes splitWordIn{to{opacity:1;transform:translateY(0);}}
.intro-greeting{font-size:clamp(32px,5vw,48px);font-weight:900;background:linear-gradient(135deg,#3B82F6,#1DD1EE,#63DEF9);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;opacity:0;animation:greetingFloatIn 0.9s var(--ease-spring) forwards,greetingBob 3.5s ease-in-out infinite 0.9s;animation-delay:var(--greeting-delay,0s);margin-bottom:8px;}
@keyframes greetingFloatIn{0%{opacity:0;transform:translateY(40px) scale(0.85);}100%{opacity:1;transform:translateY(0) scale(1);}}
@keyframes greetingBob{0%,100%{transform:translateY(0);}50%{transform:translateY(-8px);}}
.intro-line-2,.intro-line-3{font-size:16px;color:#cbd5e1;line-height:1.6;max-width:500px;}
.welcome-hidden{opacity:0;pointer-events:none;}
.welcome-reveal{opacity:1;transition:opacity 0.8s ease;pointer-events:auto;}

@media(max-width:960px){.two-col-grid{grid-template-columns:1fr;}.three-col-grid{grid-template-columns:1fr 1fr;}.live-feed-panel{display:none;}}
@media(max-width:720px){.app{padding:0;gap:0;}.sidebar{border-radius:0;border-left:0;border-top:0;border-bottom:0;}.main{border-radius:0;border:0;}.topbar,.tab-view{width:100%;margin:0;border-radius:0;border-left:0;border-right:0;}.kpi-strip{grid-template-columns:1fr 1fr;}.suggestions{grid-template-columns:1fr;}.chat-area{padding:14px 12px;}.input-zone{padding:8px 12px 12px;}.status-pill{display:none;}.bubble{max-width:88%;}}
@media(max-width:480px){.kpi-strip{grid-template-columns:1fr 1fr;}.welcome h1{font-size:24px;}.topbar{padding:0 10px;}.topbar-center{display:none;}}
`;

// ── Data ──
const getFileType = (file: File): string => {
  const m = file.type;
  if (m.startsWith("image/")) return "image";
  if (m === "application/pdf") return "pdf";
  if (m === "text/csv" || file.name.endsWith(".csv")) return "csv";
  if (m.includes("excel") || m.includes("spreadsheet") || file.name.match(/\.xlsx?$/)) return "excel";
  if (m.includes("word") || file.name.match(/\.docx?$/)) return "doc";
  return "other";
};
const FILE_ICONS = { image: "🖼️", pdf: "📄", csv: "📊", excel: "📗", doc: "📝", other: "📎" };

const KPI_CARDS = [
  { icon: "💰", label: "Total GMV Today", value: "$4.82M", delta: "+12.4%", dir: "up", variant: "" },
  { icon: "✅", label: "Success Rate", value: "97.6%", delta: "+0.4pp", dir: "up", variant: "" },
  { icon: "❌", label: "Failed Txns Today", value: "1,284", delta: "+31%", dir: "down", variant: "danger-card" },
  { icon: "🚨", label: "Fraud Flagged", value: "0.08%", delta: "−0.02pp", dir: "up", variant: "" },
];

const SUGGESTIONS = [
  { tag: "revenue", tagLabel: "REVENUE", icon: "💰", title: "Revenue by channel", desc: "Break down today's GMV by UPI, cards, wallets and BNPL" },
  { tag: "risk", tagLabel: "RISK", icon: "🛡️", title: "Fraud hotspots", desc: "Which merchant categories have the highest fraud rate this week?" },
  { tag: "ops", tagLabel: "OPS", icon: "⚡", title: "Failure root cause", desc: "Why did failure rates spike on Tuesday between 2–4 PM IST?" },
  { tag: "growth", tagLabel: "GROWTH", icon: "📈", title: "Top merchant performance", desc: "Show top 10 merchants by GMV growth quarter-over-quarter" },
];

const CHART_BARS = [42, 58, 51, 67, 73, 55, 88, 64, 79, 91, 70, 85];

const makeDemoChart = (text: string): ChartDataItem[] | undefined => {
  const t = text.toLowerCase();
  if (t.includes("merchant") || t.includes("growth")) return [{ label: "Meesho", value: 67 }, { label: "Nykaa", value: 41 }, { label: "Zepto", value: 38 }, { label: "Blinkit", value: 35 }, { label: "CRED", value: 29 }];
  if (t.includes("fail") || t.includes("success") || t.includes("rate")) return [{ label: "Success", value: 97.6 }, { label: "Failed", value: 2.4, color: "danger" }];
  if (t.includes("upi") || t.includes("channel") || t.includes("revenue")) return [{ label: "UPI", value: 48 }, { label: "Cards", value: 32 }, { label: "Wallet", value: 12, color: "amber" }, { label: "BNPL", value: 8 }];
  if (t.includes("fraud") || t.includes("risk") || t.includes("hotspot")) return [{ label: "Electronics", value: 2.4, color: "danger" }, { label: "Int'l Fashion", value: 1.8, color: "danger" }, { label: "Luxury", value: 1.6, color: "danger" }, { label: "Grocery", value: 0.3 }, { label: "Food", value: 0.2 }];
  return undefined;
};

const fmtTime = (d: Date): string => d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

// ── Chart helpers ──
const inferChartType = (data: ChartDataItem[]): ChartType => {
  if (!data || data.length === 0) return "bar";
  const labels = data.map(d => d.label.toLowerCase());
  const isTime = labels.every(l => /^\d{1,2}$/.test(l) || l.includes("hour") || l.includes("day") || l.includes("month") || l.includes("week") || l.includes("date"));
  const total = data.reduce((s, d) => s + (Number.isFinite(d.value) ? d.value : 0), 0);
  const near100 = total > 95 && total < 105;
  if (isTime) return "line";
  if (data.length <= 8 && near100) return "pie";
  return "bar";
};

const fmtChartVal = (v: number): string => {
  if (Math.abs(v) >= 1000000) return `${(v / 1000000).toFixed(2)}M`;
  if (Math.abs(v) >= 1000) return `${(v / 1000).toFixed(1)}K`;
  return Number.isInteger(v) ? `${v}` : v.toFixed(2);
};

const resolveChartColor = (raw: string | undefined, i: number): string => {
  const palette = ["#3B82F6", "#1DD1EE", "#f59e0b", "#ff4d6a", "#10b981", "#8b5cf6"];
  if (!raw) return palette[i % palette.length];
  const v = raw.toLowerCase();
  if (v === "amber") return "#f59e0b";
  if (v === "danger") return "#ff4d6a";
  if (v === "ok") return "#10b981";
  if (v.startsWith("#") || v.startsWith("rgb") || v.startsWith("hsl")) return raw;
  return palette[i % palette.length];
};

const ResponseChart: FC<{ data: ChartDataItem[]; chartType?: ChartType }> = ({ data, chartType }) => {
  const [animated, setAnimated] = useState(false);
  useEffect(() => { const t = setTimeout(() => setAnimated(true), 120); return () => clearTimeout(t); }, []);

  const type = chartType || inferChartType(data);
  const positiveData = data.filter(d => Number.isFinite(d.value) && d.value > 0);
  const rawSum = positiveData.reduce((s, d) => s + d.value, 0) || 1;
  const significantPieData = positiveData.filter(d => (d.value / rawSum) >= 0.01); // >= 1%
  const topShare = significantPieData.length
    ? Math.max(...significantPieData.map(d => d.value)) / (significantPieData.reduce((s, d) => s + d.value, 0) || 1)
    : 0;
  const effectiveType = type === "pie" && (significantPieData.length <= 1 || topShare >= 0.98) ? "bar" : type;
  const max = Math.max(...data.map(d => Math.abs(d.value)), 1);

  if (effectiveType === "pie") {
    const pieData = significantPieData;
    const sum = pieData.reduce((s, d) => s + d.value, 0) || 1;
    let cursor = 0;
    const segments = pieData.map((d, i) => {
      const start = (cursor / sum) * 360;
      cursor += d.value;
      const end = (cursor / sum) * 360;
      return `${resolveChartColor(d.color, i)} ${start}deg ${end}deg`;
    });
    return (
      <div className="response-chart">
        <div className="chart-title">Visual breakdown</div>
        <div className="chart-layout">
          <div className="donut" style={{ background: `conic-gradient(${segments.join(",")})` }} />
          <div className="pie-legend">
            {pieData.map((d, i) => {
              const color = resolveChartColor(d.color, i);
              const pct = ((d.value / sum) * 100).toFixed(1);
              return (
                <div key={i} className="legend-item">
                  <span className="legend-dot" style={{ background: color }} />
                  <span>{d.label}: {fmtChartVal(d.value)} ({pct}%)</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  }

  if (effectiveType === "line") {
    const w = 560, h = 170, padX = 22, padY = 18;
    const stepX = data.length > 1 ? (w - padX * 2) / (data.length - 1) : 0;
    const points = data.map((d, i) => ({ x: padX + i * stepX, y: h - padY - ((d.value / max) * (h - padY * 2)), label: d.label, value: d.value }));
    const linePath = points.map((p, i) => `${i === 0 ? "M" : "L"}${p.x},${p.y}`).join(" ");
    const areaPath = `${linePath} L${padX + (data.length - 1) * stepX},${h - padY} L${padX},${h - padY} Z`;
    return (
      <div className="response-chart">
        <div className="chart-title">Trend line</div>
        <div className="line-wrap">
          <svg className="line-svg" viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none">
            <path className="line-fill" d={areaPath} style={{ opacity: animated ? 1 : 0 }} />
            <path className="line-stroke" d={linePath} style={{ opacity: animated ? 1 : 0 }} />
            {points.map((p, i) => <circle key={i} className="line-point" cx={p.x} cy={p.y} r="3.2" />)}
            {points.map((p, i) => <text key={`x-${i}`} className="line-axis" x={p.x} y={h - 3} textAnchor="middle">{p.label}</text>)}
          </svg>
        </div>
      </div>
    );
  }

  return (
    <div className="response-chart">
      <div className="chart-title">Visual breakdown</div>
      <div className="chart-bars">
        {data.map((bar, i) => (
          <div className="chart-row" key={i}>
            <div className="chart-label" title={bar.label}>{bar.label}</div>
            <div className="chart-track">
              <div
                className={`chart-fill${bar.color ? " " + bar.color : ""}`}
                style={{ width: animated ? `${Math.max(2, (Math.abs(bar.value) / max) * 100)}%` : "0%" }}
              >
                <span className="chart-val">{fmtChartVal(bar.value)}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};


const NarrativeBanner: FC<{ onAsk: (text: string) => void }> = ({ onAsk }) => (
  <div className="narrative-banner" onClick={() => onAsk("Why did our failure rate spike 31% since yesterday? Show me the root cause.")}>
    <div className="nb-left">
      <div className="nb-pulse" />
      <div className="nb-text">
        <strong>⚠ Failure rate spiked +31%</strong> since yesterday — <em>~₹2.1M revenue at risk.</em> NEXUS has identified the root cause.
      </div>
    </div>
    <div className="nb-cta">Ask why →</div>
  </div>
);

const SampleConvo: FC<{ onAsk: (text: string) => void }> = ({ onAsk }) => (
  <div className="sample-convo">
    <div className="sample-convo-head">
      <span className="sample-convo-title">▸ SEE HOW IT WORKS</span>
      <span className="sample-convo-badge">EXAMPLE</span>
    </div>
    <div className="sample-q">
      <div className="sample-q-avatar">U</div>
      <div className="sample-q-text">Why did failure rates spike on Tuesday between 2–4 PM IST?</div>
    </div>
    <div className="sample-a">
      <div className="sample-a-avatar">NX</div>
      <div style={{ flex: 1 }}>
        <div className="sample-a-text">
          Tuesday's failure spike (<strong>14.2% vs 4.1% baseline</strong>) traces to a payment gateway timeout on the HDFC corridor. 83% of failures were UPI. Estimated <strong>₹2.1M revenue impact</strong>. Gateway was restored at 16:28 IST.
        </div>
        <div className="sample-a-chips">
          <span className="sample-chip danger">↑ 14.2% failure rate</span>
          <span className="sample-chip danger">₹2.1M impacted</span>
          <span className="sample-chip ok">✓ Resolved 16:28 IST</span>
          <span className="sample-chip">Confidence: HIGH</span>
        </div>
      </div>
    </div>
    <div className="sample-cta">
      Ask a similar question — <span onClick={() => onAsk("Why did failure rates spike on Tuesday between 2–4 PM IST?")}>try this one →</span>
    </div>
  </div>
);

// ── Tab pages ──
const OverviewPage: FC<{ onSuggestion: (text: string) => void }> = ({ onSuggestion }) => (
  <div className="tab-page">
    <div className="page-header">
      <div>
        <div className="page-title">Payment Intelligence Overview</div>
        <div className="page-subtitle">Live data snapshot · Feb 18, 2026 · 09:14 IST</div>
      </div>
      <div className="page-actions">
        <button className="page-btn">Export</button>
        <button className="page-btn primary">Set Alert</button>
      </div>
    </div>
    <NarrativeBanner onAsk={onSuggestion} />
    <div className="kpi-strip">
      {KPI_CARDS.map(k => (
        <div key={k.label} className={`kpi-card ${k.variant}`}>
          <span className="kpi-icon">{k.icon}</span>
          <div className="kpi-label">{k.label}</div>
          <div className="kpi-value">{k.value}</div>
          <div className={`kpi-delta ${k.dir}`}>{k.dir === "up" ? "▲" : "▼"} {k.delta} vs yesterday</div>
        </div>
      ))}
    </div>
    <div className="panel-card">
      <div className="panel-card-title"><span>💡</span>Ask NEXUS AI</div>
      <div className="suggestions">
        {SUGGESTIONS.map(s => (
          <button key={s.title} className={`sug-chip ${s.tag}`} onClick={() => onSuggestion(s.desc)}>
            <div className="sug-chip-header">
              <span className="sug-chip-icon">{s.icon}</span>
              <div>
                <span className={`sug-chip-tag ${s.tag}`}>{s.tagLabel}</span>
                <strong style={{ display: "block", marginTop: 2 }}>{s.title}</strong>
              </div>
            </div>
            <div className="sug-chip-desc">{s.desc}</div>
          </button>
        ))}
      </div>
    </div>
    <SampleConvo onAsk={onSuggestion} />
  </div>
);

// ── Sidebar (Doc 3 base + Doc 2 delete button) ──
const Sidebar: FC<{
  collapsed: boolean;
  onToggle: () => void;
  activeHist: string | null;
  onHistClick: (id: string) => void;
  onDeleteHist: (id: string) => void;
  onNewChat: () => void;
  historyItems: HistoryItem[];
  onSuggestion: (text: string) => void;
  onLogin: () => void;
}> = ({ collapsed, onToggle, activeHist, onHistClick, onDeleteHist, onNewChat, historyItems, onLogin }) => (
  <aside className={`sidebar${collapsed ? " collapsed" : ""}`}>
    <div className="sb-head">
      <div className="logo-mark"><NexusLogo size={40} /></div>
      {!collapsed && (
        <div className="logo-text">
          <div className="logo-name"><em>NEXUS</em></div>
          <div className="logo-tagline">Payments Intelligence</div>
        </div>
      )}
      <button className="menu-btn" onClick={onToggle} title="Toggle sidebar">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" strokeWidth="2" strokeLinecap="round">
          <line x1="3" y1="6" x2="21" y2="6" /><line x1="3" y1="12" x2="21" y2="12" /><line x1="3" y1="18" x2="21" y2="18" />
        </svg>
      </button>
    </div>
    <div className="sb-body">
      <button className="new-chat-btn" onClick={onNewChat}>
        <span style={{ fontSize: 15, lineHeight: 1 }}>＋</span>
        <span className="nc-label">New Analysis</span>
      </button>
      <div className="sb-divider" />
      {historyItems.length > 0 && (
        <>
          <div className="hist-label">Recent</div>
          <div className="hist-list">
            {historyItems.map((h: HistoryItem) => (
              <div key={h.id} className={`hist-item${activeHist === h.id ? " active" : ""}`} onClick={() => onHistClick(h.id)} title={h.title}>
                <div className="hist-dot" />
                <div className="hist-info">
                  <div className="hist-title">{h.title}</div>
                  <div className="hist-time">{h.time}</div>
                </div>
                <button
                  className="hist-delete"
                  title="Delete chat permanently"
                  onClick={(e) => { e.stopPropagation(); onDeleteHist(h.id); }}
                >✕</button>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
    <div className="sb-foot" style={{ padding: "12px", borderTop: "1px solid var(--border)", flexShrink: 0 }}>
      <button
        className="auth-btn login-btn"
        style={{ width: "100%", padding: "8px", borderRadius: "8px", fontSize: 13 }}
        onClick={onLogin}
        title="Log in"
      >{collapsed ? "→" : "Log in"}</button>
    </div>
  </aside>
);

// ── Welcome Screen ──
const WelcomeScreen: FC<{ onSuggestion: (text: string) => void }> = ({ onSuggestion }) => (
  <div className="welcome">
    <h1>Hi, I'm NEXUS,</h1>
    <p className="welcome-desc">
      Your AI chatbot for payment analytics and transaction intelligence<br /><br />
      Real-time insights, Clear explanations, Instant answers
    </p>
    <div style={{ marginTop: 0, display: "flex", gap: 12 }}>
      <NarrativeBanner onAsk={onSuggestion} />
    </div>
    <div className="suggestions">
      {SUGGESTIONS.map(s => (
        <button key={s.title} className={`sug-chip ${s.tag}`} onClick={() => onSuggestion(s.desc)}>
          <div className="sug-chip-header">
            <span className="sug-chip-icon">{s.icon}</span>
            <div>
              <span className={`sug-chip-tag ${s.tag}`}>{s.tagLabel}</span>
              <strong style={{ display: "block", marginTop: 2 }}>{s.title}</strong>
            </div>
          </div>
          <div className="sug-chip-desc">{s.desc}</div>
        </button>
      ))}
    </div>
  </div>
);

// ── Chat Message ──
const ChatMessage: FC<{ message: Message; onCopy: (text: string) => void; onImageClick: (src: string) => void }> = ({ message, onCopy, onImageClick }) => (
  <div className={`msg-row ${message.role}`}>
    <div className={`avatar ${message.role}`}>
      {message.role === "ai" ? <NexusLogo size={32} /> : "U"}
    </div>
    <div className={`bubble ${message.role}${message.isError ? " error" : ""}`}>
      {message.attachments && message.attachments.length > 0 && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 10 }}>
          {message.attachments.map((att: any, i: number) =>
            att.preview
              ? <img key={i} src={att.preview} alt={att.name} style={{ width: 110, height: 75, borderRadius: 8, objectFit: "cover", border: "1px solid var(--border2)", cursor: "pointer" }} onClick={() => onImageClick(att.preview)} />
              : <div key={i} style={{ display: "flex", alignItems: "center", gap: 7, padding: "6px 10px", background: "var(--bg2)", border: "1px solid var(--border2)", borderRadius: 8, fontSize: 11, color: "var(--text2)" }}>
                <span style={{ fontSize: 16 }}>{FILE_ICONS[att.type as keyof typeof FILE_ICONS] || "📎"}</span>
                <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: 140 }}>{att.name}</span>
              </div>
          )}
        </div>
      )}
      <div className="bubble-text">{message.text}</div>
      {message.chartData && message.chartData.length > 0 && <ResponseChart data={message.chartData} chartType={message.chartType} />}
      <div className="bubble-meta">
        <span className="bubble-time">{fmtTime(message.timestamp)}</span>
        <div className="bubble-actions">
          <button className="bubble-action-btn" title="Copy" onClick={() => onCopy(message.text)}>⎘</button>
        </div>
      </div>
    </div>
  </div>
);

const TypingIndicator: FC = () => (
  <div className="msg-row ai">
    <div className="avatar ai"><NexusLogo size={32} /></div>
    <div className="bubble ai"><div className="typing"><span /><span /><span /></div></div>
  </div>
);

// ── Auth Modal ──
const AuthModal: FC<{ mode: string; onClose: () => void; onToggleMode: () => void }> = ({ mode, onClose, onToggleMode }) => (
  <div className="modal-overlay" onClick={onClose}>
    <div className="modal" onClick={e => e.stopPropagation()}>
      <button className="modal-close" onClick={onClose}>✕</button>
      <h2>{mode === "login" ? "Welcome back" : "Create account"}</h2>
      <p>{mode === "login" ? "Log in to your NEXUS workspace." : "Start making smarter payment decisions."}</p>
      {mode === "signup" && <div className="field"><label>Full Name</label><input type="text" placeholder="Jane Doe" /></div>}
      <div className="field"><label>Work Email</label><input type="email" placeholder="jane@company.com" /></div>
      <div className="field"><label>Password</label><input type="password" placeholder="••••••••" /></div>
      <button className="modal-submit">{mode === "login" ? "Log in →" : "Create account →"}</button>
      <div className="modal-toggle">{mode === "login" ? "Don't have an account? " : "Already have an account? "}<button onClick={onToggleMode}>{mode === "login" ? "Sign up" : "Log in"}</button></div>
    </div>
  </div>
);

// ── Input Bar ──
const ATTACH_MENU_ITEMS = [
  { icon: "🖼️", label: "Image", sub: "PNG, JPG, WEBP, GIF", accept: "image/*" },
  { icon: "📄", label: "PDF", sub: "Any PDF document", accept: "application/pdf" },
  { icon: "📊", label: "Spreadsheet", sub: "CSV, XLS, XLSX", accept: ".csv,.xls,.xlsx" },
  { icon: "📝", label: "Document", sub: "DOC, DOCX, TXT", accept: ".doc,.docx,.txt" },
  { icon: "📎", label: "Any File", sub: "All file types", accept: "*" },
];

const InputBar: FC<{
  input: string; isTyping: boolean; attachedFiles: FileAttachment[];
  onChange: (e: ChangeEvent<HTMLTextAreaElement>) => void;
  onKeyDown: (e: KeyboardEvent<HTMLTextAreaElement>) => void;
  onSend: () => void; onStop: () => void; onVoiceToggle: () => void;
  isListening: boolean; speechSupported: boolean;
  onFilesAttach: (files: File[]) => void; onRemoveAttach: (id: string) => void;
  textareaRef: React.RefObject<HTMLTextAreaElement>; typewriterText?: string;
}> = ({ input, isTyping, attachedFiles, onChange, onKeyDown, onSend, onStop, onVoiceToggle, isListening, speechSupported, onFilesAttach, onRemoveAttach, textareaRef, typewriterText }) => {
  const [menuOpen, setMenuOpen] = useState<boolean>(false);
  const [dragOver, setDragOver] = useState<boolean>(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!menuOpen) return;
    const h = (e: MouseEvent) => { if (menuRef.current && !menuRef.current.contains(e.target as Node)) setMenuOpen(false); };
    document.addEventListener("mousedown", h);
    return () => document.removeEventListener("mousedown", h);
  }, [menuOpen]);
  const openPicker = (accept: string) => { setMenuOpen(false); setTimeout(() => { if (fileInputRef.current) { fileInputRef.current.accept = accept; fileInputRef.current.click(); } }, 50); };
  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => { if (e.target.files) { onFilesAttach(Array.from(e.target.files)); e.target.value = ""; } };
  const canSend = (input.trim() || attachedFiles.length > 0) && !isTyping;
  return (
    <div
      className={`input-zone${dragOver ? " drag-over" : ""}`}
      onDragOver={e => { e.preventDefault(); setDragOver(true); }}
      onDragLeave={() => setDragOver(false)}
      onDrop={e => { e.preventDefault(); setDragOver(false); if (e.dataTransfer.files) onFilesAttach(Array.from(e.dataTransfer.files)); }}
    >
      <div className="drag-hint">⬇ Drop files here to attach</div>
      {attachedFiles.length > 0 && (
        <div className="attach-preview-row">
          {attachedFiles.map((af: FileAttachment) => (
            <div key={af.id} className="attach-thumb">
              {af.preview
                ? <img src={af.preview} alt={af.file.name} />
                : <div className="attach-thumb-file"><span className="attach-thumb-file-icon">{FILE_ICONS[af.type as keyof typeof FILE_ICONS]}</span><span className="attach-thumb-file-ext">{af.file.name.split(".").pop()?.slice(0, 5)}</span></div>}
              <div className="attach-thumb-name" title={af.file.name}>{af.file.name}</div>
              <button className="attach-remove-btn" onClick={() => onRemoveAttach(af.id)}>✕</button>
            </div>
          ))}
        </div>
      )}
      <div className="input-row">
        <textarea
          ref={textareaRef}
          className="chat-input"
          rows={1}
          placeholder={attachedFiles.length > 0 ? "Add context… (optional)" : (typewriterText || "Ask NEXUS anything about your payments...")}
          value={input}
          onChange={onChange}
          onKeyDown={onKeyDown}
        />
        <div className="input-actions">
          <div className="attach-menu-wrap" ref={menuRef}>
            {menuOpen && (
              <div className="attach-menu">
                {ATTACH_MENU_ITEMS.map((item, i) => (
                  <div key={i}>
                    {i === 4 && <div className="attach-menu-divider" />}
                    <div className="attach-menu-item" onClick={() => openPicker(item.accept)}>
                      <span className="ami-icon">{item.icon}</span>
                      <div className="ami-label"><div>{item.label}</div><div className="ami-sub">{item.sub}</div></div>
                    </div>
                  </div>
                ))}
              </div>
            )}
            <button className={`attach-btn${attachedFiles.length > 0 ? " has-files" : ""}${menuOpen ? " active" : ""}`} onClick={() => setMenuOpen(o => !o)} title="Attach files">
              {attachedFiles.length > 0 && <span className="attach-badge">{attachedFiles.length}</span>}
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
              </svg>
            </button>
          </div>
          {speechSupported && !isTyping && (
            <button className={`attach-btn mic-btn${isListening ? " listening active" : ""}`} onClick={onVoiceToggle} title={isListening ? "Stop voice input" : "Start voice input"} aria-label={isListening ? "Stop voice input" : "Start voice input"}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 14a3 3 0 0 0 3-3V7a3 3 0 0 0-6 0v4a3 3 0 0 0 3 3z" /><path d="M19 11a7 7 0 0 1-14 0" />
                <line x1="12" y1="18" x2="12" y2="22" /><line x1="8" y1="22" x2="16" y2="22" />
              </svg>
            </button>
          )}
          {isTyping ? (
            <button className="stop-btn" onClick={onStop} aria-label="Stop generation">
              <svg width="16" height="16" viewBox="0 0 16 16"><rect x="3" y="3" width="10" height="10" rx="1.5" fill="currentColor" /></svg>
            </button>
          ) : (
            <button className="send-btn" onClick={onSend} disabled={!canSend}>
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="12" y1="19" x2="12" y2="5" /><polyline points="5 12 12 5 19 12" />
              </svg>
            </button>
          )}
        </div>
      </div>
      {isListening && <div className="listening-indicator"><span className="listening-dot" /><span>Listening...</span></div>}
      <input ref={fileInputRef} type="file" multiple style={{ display: "none" }} onChange={handleFileChange} />
    </div>
  );
};

const CopyToast: FC<{ show: boolean }> = ({ show }) => <div className={`copy-toast${show ? " show" : ""}`}>✓ Copied to clipboard</div>;

// ── Typewriter prompts ──
const TYPEWRITER_PROMPTS = [
  "Why did failure rates spike on Tuesday between 2–4 PM IST?",
  "Which merchants are at highest fraud risk this week?",
  "Break down today's GMV by UPI, cards, wallets and BNPL",
  "Show top 10 merchants by GMV growth quarter-over-quarter",
];

// ── SplitText Intro ──
const INTRO_LINES = [
  { text: "Hi, I'm NEXUS.", className: "intro-greeting" },
  { text: "Your AI chatbot for payment analytics and transaction intelligence.", className: "intro-line-2" },
  { text: "Real-time insights, Clear explanations, Instant answers.", className: "intro-line-3" },
];

const SplitTextIntro: FC<{ onDone: () => void }> = ({ onDone }) => {
  const [fadeOut, setFadeOut] = useState(false);
  useEffect(() => {
    const holdTimer = setTimeout(() => setFadeOut(true), 6500);
    const doneTimer = setTimeout(() => onDone(), 7200);
    return () => { clearTimeout(holdTimer); clearTimeout(doneTimer); };
  }, [onDone]);
  const l2Words = INTRO_LINES[1].text.split(" ");
  return (
    <div className={`intro-text-block${fadeOut ? " fade-out" : ""}`}>
      <h1 className="intro-greeting" style={{ '--greeting-delay': '0s' } as any}>Hi, I'm NEXUS.</h1>
      {[INTRO_LINES[1], INTRO_LINES[2]].map((line, li) => {
        const words = line.text.split(" ");
        const wordOffset = li === 1 ? l2Words.length : 0;
        return (
          <div key={li} className={`split-line ${line.className}`}>
            {words.map((word, wi) => {
              const delay = (wordOffset + wi) * 0.08 + 1.0;
              return <span key={wi} className="split-word" style={{ animationDelay: `${delay}s` }}>{word}{wi < words.length - 1 ? "\u00A0" : ""}</span>;
            })}
          </div>
        );
      })}
    </div>
  );
};

// ── Root App ──
export default function NEXUS({ introReady }: { introReady?: boolean }) {
  const [collapsed, setCollapsed] = useState<boolean>(false);
  
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState<string>("");
  const [isTyping, setIsTyping] = useState<boolean>(false);
  const [activeHist, setActiveHist] = useState<string | null>(null);
  const [modal, setModal] = useState<string | null>(null);
  const [authMode, setAuthMode] = useState<string>("login");
  const [historyItems, setHistoryItems] = useState<HistoryItem[]>([]);
  const [copyShow, setCopyShow] = useState<boolean>(false);
  const [attachedFiles, setAttachedFiles] = useState<FileAttachment[]>([]);
  const [lightboxSrc, setLightboxSrc] = useState<string | null>(null);
  const [showIntroText, setShowIntroText] = useState<boolean>(true);
  const [welcomeRevealed, setWelcomeRevealed] = useState<boolean>(false);
  const [isListening, setIsListening] = useState<boolean>(false);
  const [speechSupported, setSpeechSupported] = useState<boolean>(false);
  const [typewriterText, setTypewriterText] = useState<string>("");

  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const copyTimer = useRef<NodeJS.Timeout | undefined>(undefined);
  const abortRef = useRef<NodeJS.Timeout | undefined>(undefined);
  const abortControllerRef = useRef<AbortController | null>(null);
  const recognitionRef = useRef<any>(null);
  const currentSessionIdRef = useRef<string | null>(null);

  // ── Helper: convert DB sessions → sidebar HistoryItems ──
  const toHistoryItems = useCallback(
    (sessions: Array<{ id: string; title: string; updatedAt: Date; messages: Message[] }>): HistoryItem[] => {
      return sessions
        .filter((s) => Array.isArray(s.messages) && s.messages.length > 0)
        .map((s) => {
          const firstUser = s.messages.find((m) => m.role === "user");
          const title = deriveSessionHistoryTitle(s);
          const baseTime = firstUser?.timestamp || s.updatedAt || new Date();
          return {
            id: s.id,
            title,
            time: new Date(baseTime).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          };
        })
        .slice(0, 15);
    },
    []
  );

  useEffect(() => { document.documentElement.setAttribute("data-theme", "dark"); }, []);
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, isTyping]);

  // ── Speech recognition ──
  useEffect(() => {
    const SpeechRecognitionCtor = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognitionCtor) return;
    setSpeechSupported(true);
    const recognition = new SpeechRecognitionCtor();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "en-US";
    recognition.onstart = () => setIsListening(true);
    recognition.onend = () => setIsListening(false);
    recognition.onerror = () => setIsListening(false);
    recognition.onresult = (event: any) => {
      const transcript = Array.from(event.results || []).map((r: any) => r[0]?.transcript || "").join(" ").trim();
      if (!transcript) return;
      setInput(prev => (prev ? `${prev} ${transcript}` : transcript));
      requestAnimationFrame(() => autoResize());
    };
    recognitionRef.current = recognition;
    return () => { try { recognition.stop(); } catch { } recognitionRef.current = null; };
  }, []);

  // ── Typewriter effect ──
  useEffect(() => {
    if (!introReady) return;
    let promptIdx = 0, charIdx = 0, isDeleting = false;
    let timeout: NodeJS.Timeout;
    const tick = () => {
      const currentPrompt = TYPEWRITER_PROMPTS[promptIdx % TYPEWRITER_PROMPTS.length];
      if (!isDeleting) {
        charIdx++;
        setTypewriterText(currentPrompt.slice(0, charIdx));
        if (charIdx >= currentPrompt.length) { timeout = setTimeout(() => { isDeleting = true; tick(); }, 2000); return; }
        timeout = setTimeout(tick, 40 + Math.random() * 30);
      } else {
        charIdx--;
        setTypewriterText(currentPrompt.slice(0, charIdx));
        if (charIdx <= 0) { isDeleting = false; promptIdx++; timeout = setTimeout(tick, 300); return; }
        timeout = setTimeout(tick, 20);
      }
    };
    const startDelay = setTimeout(tick, 1000);
    return () => { clearTimeout(startDelay); clearTimeout(timeout); };
  }, [introReady]);

  // ── Load persisted chat history from IndexDB on mount ──
  useEffect(() => {
    const loadChatHistory = async () => {
      try {
        const sessions = await indexdbService.loadSessions();
        const sessionId = await indexdbService.getCurrentSessionId();
        let resolvedSessionId = sessionId;
        let savedMessages = await indexdbService.loadMessagesBySessionId(sessionId);

        if (!savedMessages.length) {
          const latestWithMessages = sessions.find((s) => {
            const candidate = s as { messages?: unknown[] };
            return Array.isArray(candidate.messages) && candidate.messages.length > 0;
          });
          if (latestWithMessages) {
            resolvedSessionId = latestWithMessages.id;
            await indexdbService.switchSession(resolvedSessionId);
            savedMessages = await indexdbService.loadMessagesBySessionId(resolvedSessionId);
          }
        }

        currentSessionIdRef.current = resolvedSessionId;
        setActiveHist(resolvedSessionId);
        setHistoryItems(
          toHistoryItems(sessions as Array<{ id: string; title: string; updatedAt: Date; messages: Message[] }>)
        );
        if (savedMessages.length > 0) {
          setMessages(savedMessages);
        } else {
          setMessages([]);
        }
      } catch (error) {
        console.error("Failed to load chat history:", error);
      }
    };
    loadChatHistory();
  }, [toHistoryItems]);

  const autoResize = () => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = `${Math.min(ta.scrollHeight, 120)}px`;
  };

  const handleCopy = useCallback((text: string): void => {
    navigator.clipboard.writeText(text).catch(() => { });
    setCopyShow(true);
    clearTimeout(copyTimer.current);
    copyTimer.current = setTimeout(() => setCopyShow(false), 1800);
  }, []);

  const handleFilesAttach = useCallback((files: File[]): void => {
    const toAdd = files.slice(0, 10 - attachedFiles.length);
    toAdd.forEach(file => {
      const type = getFileType(file);
      const af = { id: Date.now() + Math.random() + "", file, type };
      if (type === "image") {
        const reader = new FileReader();
        reader.onload = (e: ProgressEvent<FileReader>) => { setAttachedFiles(prev => prev.map(x => x.id === af.id ? { ...x, preview: e.target?.result as string } : x)); };
        reader.readAsDataURL(file);
      }
      setAttachedFiles(prev => [...prev, af]);
    });
  }, [attachedFiles.length]);

  const handleRemoveAttach = useCallback((id: string): void => {
    setAttachedFiles(prev => prev.filter(f => f.id !== id));
  }, []);

  const handleSuggestion = (text: string): void => {
    
    sendMessage(text);
  };

  const handleVoiceToggle = useCallback((): void => {
    if (!recognitionRef.current) return;
    if (isListening) { recognitionRef.current.stop(); return; }
    try { recognitionRef.current.start(); } catch { setIsListening(false); }
  }, [isListening]);

  const handleStop = useCallback((): void => {
    if (abortControllerRef.current) { abortControllerRef.current.abort(); abortControllerRef.current = null; }
    if (abortRef.current) { clearTimeout(abortRef.current); abortRef.current = undefined; }
    setIsTyping(false);
  }, []);

  // ── Load a specific session by id ──
  const loadSessionById = async (sessionId: string) => {
    try {
      await indexdbService.switchSession(sessionId);
      currentSessionIdRef.current = sessionId;
      const session = await indexdbService.loadSession(sessionId);
      if (session && session.messages) {
        setMessages(session.messages);
        setActiveHist(sessionId);
        setAttachedFiles([]);
        
      }
    } catch (error) {
      console.error("Failed to load session:", error);
    }
  };

  // ── Delete a session by id ──
  const handleDeleteSession = async (sessionId: string) => {
    const ok = window.confirm("Delete this chat permanently? This cannot be undone.");
    if (!ok) return;
    try {
      await indexdbService.deleteSession(sessionId);
      const remaining = historyItems.filter((h) => h.id !== sessionId);
      setHistoryItems(remaining);
      if (currentSessionIdRef.current === sessionId) {
        const sessions = await indexdbService.loadSessions();
        const nextSession = sessions.find((s) => Array.isArray(s.messages) && s.messages.length > 0);
        if (nextSession) {
          await loadSessionById(nextSession.id);
        } else {
          const newSessionId = await indexdbService.createNewSession();
          currentSessionIdRef.current = newSessionId;
          setMessages([]);
          setActiveHist(null);
          setAttachedFiles([]);
          
        }
      }
    } catch (error) {
      console.error("Failed to delete session:", error);
    }
  };

  const sendMessage = async (text: string): Promise<void> => {
    const hasAtt = attachedFiles.length > 0;
    if ((!text.trim() && !hasAtt) || isTyping) return;
    const attachmentMeta = attachedFiles.map((af: FileAttachment) => ({ name: af.file.name, type: af.type, preview: af.preview }));
    const displayText = text.trim() || `[Attached ${attachedFiles.length} file${attachedFiles.length > 1 ? "s" : ""}]`;
    const userMsg: Message = { id: Date.now() + "u", role: "user", text: displayText, timestamp: new Date(), attachments: attachmentMeta.length > 0 ? attachmentMeta : undefined };
    setMessages(prev => [...prev, userMsg]);

    // Save user message to IndexDB
    await indexdbService.saveMessage(userMsg);

    setInput("");
    setAttachedFiles([]);
    if (textareaRef.current) textareaRef.current.style.height = "auto";
    setIsTyping(true);
    
    try {
      const abortController = new AbortController();
      abortControllerRef.current = abortController;
      const t = setTimeout(() => abortController.abort(), 180000);
      abortRef.current = t;
      const response = await fetch("http://localhost:8000/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: text, session_id: "nexus-web" }),
        signal: abortController.signal,
      });
      if (!response.ok) throw new Error(`API error: ${response.status}`);
      const data = await response.json();
      const aiMsg: Message = {
        id: data.id || Date.now() + "a",
        role: "ai",
        text: data.text,
        timestamp: new Date(data.timestamp || Date.now()),
        confidence: "HIGH",
        sampleSize: data.rowCount,
        execMs: data.executionMs,
        chartData: data.chartData || makeDemoChart(text),
        chartType: (data.chartType as ChartType | undefined),
      };
      setMessages(prev => [...prev, aiMsg]);

      // Save AI message to IndexDB
      await indexdbService.saveMessage(aiMsg);

      // Update sidebar with smart title from AI response
      const sessionId = currentSessionIdRef.current!;
      const aiTitle = summarizeTitle(aiMsg.text) || "Conversation summary";
      const entry: HistoryItem = {
        id: sessionId,
        title: aiTitle,
        time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setHistoryItems(prev => {
        const existingIndex = prev.findIndex(h => h.id === sessionId);
        if (existingIndex >= 0) {
          const updated = [...prev];
          const existing = updated[existingIndex];
          updated[existingIndex] = {
            ...entry,
            title: isFallbackTitle(existing.title) ? aiTitle : existing.title,
          };
          return [updated[existingIndex], ...updated.filter((_, i) => i !== existingIndex)];
        } else {
          return [entry, ...prev.slice(0, 14)];
        }
      });
      setActiveHist(sessionId);
    } catch (err: unknown) {
      if (err instanceof Error && err.name === "AbortError") { return; }
      const errorMsg = err instanceof Error ? err.message : "Something went wrong.";
      const errorMessage: Message = { id: Date.now() + "e", role: "ai", isError: true, timestamp: new Date(), text: `⚠ ${errorMsg}` };
      setMessages(prev => [...prev, errorMessage]);
      await indexdbService.saveMessage(errorMessage);
    } finally {
      if (abortRef.current) { clearTimeout(abortRef.current); abortRef.current = undefined; }
      setIsTyping(false);
      abortControllerRef.current = null;
    }
  };

  // ── New chat via IndexDB ──
  const handleNewChat = async () => {
    const newSessionId = await indexdbService.createNewSession();
    currentSessionIdRef.current = newSessionId;
    setMessages([]);
    setActiveHist(null);
    setAttachedFiles([]);
    
  };

  const handleIntroDone = useCallback(() => {
    setShowIntroText(false);
    setWelcomeRevealed(true);
  }, []);

  return (
    <>
      <style>{css}</style>
      <CopyToast show={copyShow} />
      {lightboxSrc && (
        <div className="lightbox-overlay" onClick={() => setLightboxSrc(null)}>
          <button className="lightbox-close">✕</button>
          <img className="lightbox-img" src={lightboxSrc} alt="Full size" onClick={e => e.stopPropagation()} />
        </div>
      )}
      <div className="app">
        <Sidebar
          collapsed={collapsed}
          onToggle={() => setCollapsed(c => !c)}
          activeHist={activeHist}
          onHistClick={(id: string) => loadSessionById(id)}
          onDeleteHist={(id: string) => handleDeleteSession(id)}
          onNewChat={handleNewChat}
          historyItems={historyItems}
          onSuggestion={handleSuggestion}
          onLogin={() => { setAuthMode("login"); setModal("auth"); }}
        />
        <div className="main">
          <div className="tab-view" style={{ position: "relative" }}>
            {introReady && showIntroText && messages.length === 0 && (
              <SplitTextIntro onDone={handleIntroDone} />
            )}
            {(
              <>
                {messages.length === 0 && !isTyping ? (
                  <div className={`chat-area ${!welcomeRevealed && introReady && showIntroText ? "welcome-hidden" : "welcome-reveal"}`}>
                    <WelcomeScreen onSuggestion={handleSuggestion} />
                    <div ref={bottomRef} />
                  </div>
                ) : (
                  <div className="chat-area">
                    {messages.map((m: Message) => <ChatMessage key={m.id} message={m} onCopy={handleCopy} onImageClick={(src: string) => setLightboxSrc(src)} />)}
                    {isTyping && <TypingIndicator />}
                    <div ref={bottomRef} />
                  </div>
                )}
                <InputBar
                  input={input} isTyping={isTyping} attachedFiles={attachedFiles}
                  onChange={(e: ChangeEvent<HTMLTextAreaElement>) => { setInput(e.target.value); autoResize(); }}
                  onKeyDown={(e: KeyboardEvent<HTMLTextAreaElement>) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(input); } }}
                  onSend={() => sendMessage(input)} onStop={handleStop}
                  onVoiceToggle={handleVoiceToggle} isListening={isListening} speechSupported={speechSupported}
                  onFilesAttach={handleFilesAttach} onRemoveAttach={handleRemoveAttach}
                  textareaRef={textareaRef as React.RefObject<HTMLTextAreaElement>}
                  typewriterText={typewriterText}
                />
              </>
            )}
          </div>
        </div>
        {modal === "auth" && <AuthModal mode={authMode} onClose={() => setModal(null)} onToggleMode={() => setAuthMode(m => m === "login" ? "signup" : "login")} />}
      </div>
    </>
  );
}
