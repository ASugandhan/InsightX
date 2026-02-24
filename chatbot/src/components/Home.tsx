import { useState, useRef, useEffect, useCallback} from "react";
import type { FC, ChangeEvent, KeyboardEvent, DragEvent } from "react";
import { motion } from "framer-motion";
import Particles from "./Particles";

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
  confidence?: string;
  sampleSize?: number;
  execMs?: number;
  isError?: boolean;
}

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


const css = `
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Mono:ital,wght@0,400;0,500;1,400&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,400&display=swap');
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}

/* ── DARK THEME (default) ── */
:root {
  --bg-dark: linear-gradient(135deg, #060b14 0%, #0c1626 50%, #0a1120 100%);
  --bg-light: linear-gradient(135deg, #f6f9ff 0%, #eef3ff 100%);

  --glass-dark: rgba(255,255,255,0.06);
  --glass-light: rgba(255,255,255,0.65);

  --border-dark: rgba(255,255,255,0.08);
  --border-light: rgba(0,0,0,0.06);

  --text-dark: #f1f5ff;
  --text-light: #111827;

  --text-muted-dark: #94a3b8;
  --text-muted-light: #64748b;

  --accent: #6366f1;
  --accent-glow: 0 0 40px rgba(99,102,241,0.4);

  /* Legacy mappings to preserve other components */
  --accent2:#00b4ff;--amber:#f59e0b;--danger:#ff4d6a;--purple:#a78bfa;
  --bg:var(--bg-dark);--bg1:#0d1520;--bg2:#111c2e;--bg3:#162030;
  --text:var(--text-dark);--text2:var(--text-muted-dark);--text3:#505a6b;
  --border:var(--border-dark);--border2:rgba(255,255,255,0.06);
  --glow:var(--accent-glow);--shadow:rgba(0,0,0,0.4);
  --sidebar-w:260px;--topbar-h:56px;
  --ease-spring:cubic-bezier(.34,1.56,.64,1);--ease-out:cubic-bezier(.22,1,.36,1);
}

.light {
  --bg:var(--bg-light);--bg1:#ffffff;--bg2:#f8fafc;--bg3:#eef1f6;
  --text:var(--text-light);--text2:var(--text-muted-light);--text3:#8b95a3;
  --border:var(--border-light);--border2:rgba(15,25,35,0.14);
  --glow:0 0 40px rgba(99,102,241,0.2);--shadow:rgba(15,25,35,0.12);
}

html,body,#root{height:100%;width:100%;overflow:hidden;font-family:'DM Sans',sans-serif;-webkit-font-smoothing:antialiased;}
body{background:transparent;color:var(--text);margin:0;}
#root{display:flex;}
::-webkit-scrollbar{width:4px;}::-webkit-scrollbar-track{background:transparent;}::-webkit-scrollbar-thumb{background:var(--border2);border-radius:4px;}

.app-shell {
  min-height: 100vh;
  width: 100vw;
  display: flex;
  background: var(--bg-dark);
  color: var(--text-dark);
  transition: all 0.4s ease;
}

.light .app-shell {
  background: var(--bg-light);
  color: var(--text-light);
}

.panel {
  background: #0f172a; /* solid dark */
  border-radius: 18px;
  border: 1px solid rgba(255,255,255,0.06);
  transition: all 0.25s ease;
}

.light .panel {
  background: #ffffff;
  border: 1px solid rgba(0,0,0,0.06);
}

.panel:hover {
  background: rgba(255,255,255,0.06);
  backdrop-filter: blur(20px);
  transform: translateY(-4px);
  box-shadow: 0 10px 40px rgba(0,0,0,0.3);
}

.light .panel:hover {
  background: rgba(255,255,255,0.65);
}

.particles-bg{position:fixed!important;inset:0;z-index:0;pointer-events:none;}
.particles-bg canvas{display:block;width:100%!important;height:100%!important;}



/* radial glows */
.app::after{content:'';position:fixed;inset:0;pointer-events:none;z-index:0;
  background:radial-gradient(ellipse 600px 400px at 0% 0%,rgba(0,229,160,0.04) 0%,transparent 60%),
  radial-gradient(ellipse 500px 400px at 100% 100%,rgba(0,180,255,0.035) 0%,transparent 60%);
  transition:opacity .4s;}
[data-theme="light"] .app::after{
  background:radial-gradient(ellipse 600px 400px at 10% 0%,rgba(0,100,60,0.04) 0%,transparent 60%),
  radial-gradient(ellipse 500px 400px at 90% 100%,rgba(0,80,180,0.03) 0%,transparent 60%);}

/* ── SIDEBAR ── */
.sidebar {
  position:sticky;z-index:20;width:260px;min-width:260px;top:0;height:100vh;
  display:flex;flex-direction:column;
  transition:width .28s var(--ease-out),min-width .28s var(--ease-out);
  flex-shrink:0;overflow:hidden;
}
.sidebar.collapsed{width:56px;min-width:56px;}

/* ── SIDEBAR HEAD ── */
.sb-head{
  display:flex;align-items:center;gap:8px;
  padding:0 12px;height:var(--topbar-h);
  border-bottom:1px solid var(--border);
  flex-shrink:0;
}
.sidebar.collapsed .sb-head{
  flex-direction:column;justify-content:center;
  padding:10px 0;gap:6px;height:auto;min-height:var(--topbar-h);
}
.logo-mark{
  width:32px;height:32px;border-radius:8px;flex-shrink:0;
  background:linear-gradient(135deg,var(--accent),var(--accent2));
  display:flex;align-items:center;justify-content:center;
  font-family:'Syne',sans-serif;font-weight:800;font-size:12px;color:#000;
  box-shadow:0 0 18px var(--glow);
  transition:box-shadow .3s;
}
.logo-text{flex:1;min-width:0;overflow:hidden;transition:opacity .2s,max-width .28s;}
.logo-name{font-family:'Syne',sans-serif;font-size:14px;font-weight:800;letter-spacing:-.025em;white-space:nowrap;line-height:1.1;}
.logo-name em{color:var(--accent);font-style:normal;}
.logo-tagline{font-family:'DM Mono',monospace;font-size:9px;color:var(--text3);letter-spacing:.08em;text-transform:uppercase;white-space:nowrap;margin-top:2px;}
.sidebar.collapsed .logo-text{opacity:0;max-width:0;pointer-events:none;}

/* ── THEME TOGGLE — professional text button ── */
.theme-toggle-btn{
  flex-shrink:0;
  display:flex;align-items:center;gap:5px;
  padding:4px 8px;border-radius:6px;
  border:1px solid rgba(255,255,255,0.2);background:rgba(255,255,255,0.024);backdrop-filter:blur(16px);
  font-family:'DM Mono',monospace;font-size:10px;color:var(--text2);
  cursor:pointer;white-space:nowrap;
  transition:all .15s;letter-spacing:.04em;
}
.theme-toggle-btn:hover{border-color:var(--accent);color:var(--accent);background:rgba(0,229,160,0.15);}
.theme-toggle-btn svg{flex-shrink:0;}
.sidebar.collapsed .theme-toggle-btn{padding:4px;width:32px;justify-content:center;}
.sidebar.collapsed .theme-toggle-btn .ttb-label{display:none;}

/* ── MENU TOGGLE ── */
.menu-btn{
  width:28px;height:28px;border-radius:6px;flex-shrink:0;
  border:1px solid var(--border);background:#0f172a;cursor:pointer;
  display:flex;align-items:center;justify-content:center;
  transition:all .25s ease;
}
.light .menu-btn { background: #ffffff; border: 1px solid var(--border-light); }
.menu-btn:hover{border-color:var(--accent);background:rgba(255,255,255,0.06);backdrop-filter:blur(20px);transform:translateY(-2px);box-shadow:0 5px 20px rgba(0,0,0,0.3);}
.light .menu-btn:hover{background:rgba(255,255,255,0.65);}
.menu-btn svg{stroke:var(--text2);transition:stroke .15s;}.menu-btn:hover svg{stroke:var(--accent);}
.sidebar.collapsed .menu-btn{margin:0 auto;}

/* ── SIDEBAR BODY ── */
.sb-body{padding:10px 8px;display:flex;flex-direction:column;gap:8px;flex:1;overflow:hidden;}

.new-chat-btn{
  display:flex;align-items:center;justify-content:center;gap:6px;
  padding:9px 10px;border-radius:9px;flex-shrink:0;overflow:hidden;
  background:rgba(0,229,160,0.15);backdrop-filter:blur(24px);border:1px solid rgba(0,229,160,0.28);
  font-family:'Syne',sans-serif;font-size:11.5px;font-weight:600;color:var(--accent);
  cursor:pointer;white-space:nowrap;transition:all .2s;
}
[data-theme="light"] .new-chat-btn{background:rgba(0,122,82,0.12);border-color:rgba(0,122,82,0.28);}
.new-chat-btn:hover{background:rgba(0,229,160,0.25);border-color:var(--accent);box-shadow:0 0 18px var(--glow);transform:translateY(-1px);}
[data-theme="light"] .new-chat-btn:hover{background:linear-gradient(135deg,rgba(0,122,82,.15),rgba(0,102,187,.08));}
.sidebar.collapsed .new-chat-btn{padding:8px;}.sidebar.collapsed .nc-label{display:none;}

.hist-label{font-family:'DM Mono',monospace;font-size:9px;letter-spacing:.14em;text-transform:uppercase;color:var(--text3);padding:2px 4px;flex-shrink:0;}
.sidebar.collapsed .hist-label{display:none;}

.hist-list{flex:1;overflow-y:auto;display:flex;flex-direction:column;gap:2px;min-height:0;}
.hist-item{
  display:flex;align-items:center;gap:8px;padding:8px 9px;border-radius:7px;
  cursor:pointer;white-space:nowrap;overflow:hidden;transition:all .16s;
}
.hist-item:hover{background:rgba(255,255,255,0.08);transform:translateX(2px);}
[data-theme="light"] .hist-item:hover{background:rgba(0,0,0,0.04);}
.hist-item.active{background:rgba(0,229,160,0.15);backdrop-filter:blur(16px);}
[data-theme="light"] .hist-item.active{background:rgba(0,122,82,.08);}
.hist-dot{width:5px;height:5px;border-radius:50%;background:var(--text3);flex-shrink:0;transition:background .2s;}
.hist-item.active .hist-dot{background:var(--accent);box-shadow:0 0 6px rgba(0,229,160,.5);}
.hist-info{flex:1;min-width:0;overflow:hidden;}
.hist-title{font-size:11.5px;font-weight:500;color:var(--text2);overflow:hidden;text-overflow:ellipsis;transition:color .15s;}
.hist-item:hover .hist-title,.hist-item.active .hist-title{color:var(--text);}
.hist-time{font-family:'DM Mono',monospace;font-size:9px;color:var(--text3);}
.sidebar.collapsed .hist-info{display:none;}
.sidebar.collapsed .hist-dot{margin:0 auto;}

.sb-seed-label{font-family:'DM Mono',monospace;font-size:9px;letter-spacing:.12em;text-transform:uppercase;color:var(--text3);padding:6px 4px 3px;display:flex;align-items:center;gap:6px;}
.sb-seed-label::after{content:'';flex:1;height:1px;background:var(--border);}
.sidebar.collapsed .sb-seed-label{display:none;}
.hist-item.seeded .hist-dot{background:var(--accent2);opacity:.5;}
.hist-item.seeded{opacity:.65;}
.sidebar.collapsed .hist-item.seeded{display:none;}

/* ── MAIN CONTENT ── */
.content-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 0 140px;
  min-width: 0;
  z-index: 1;
  position: relative;
}

/* ── TOPBAR ── */
.topbar {
  width: 100%;
  max-width: 1100px;
  margin-bottom: 40px;
  padding: 16px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink:0;
  position:sticky;top:0;z-index:20;
}

.breadcrumb{font-family:'DM Mono',monospace;font-size:11px;color:var(--text3);display:flex;align-items:center;gap:5px;min-width:100px;}
.breadcrumb span{color:var(--accent);font-weight:500;}

.topbar-center{display:flex;align-items:center;gap:2px;}
.topbar-tab{
  padding:5px 11px;border-radius:6px;
  font-family:'DM Sans',sans-serif;font-size:12px;font-weight:500;color:var(--text2);
  cursor:pointer;border:none;background:transparent;transition:all .15s;
}
.topbar-tab:hover{color:var(--text);background:rgba(255,255,255,0.08);}
[data-theme="light"] .topbar-tab:hover{background:rgba(0,0,0,0.05);}
.topbar-tab.active{color:var(--accent);background:rgba(0,229,160,0.15);backdrop-filter:blur(16px);border:1px solid rgba(0,229,160,0.3);}
[data-theme="light"] .topbar-tab.active{background:rgba(0,122,82,.08);border-color:rgba(0,122,82,.25);}
.tab-badge{display:inline-flex;align-items:center;justify-content:center;background:var(--danger);color:#fff;font-family:'DM Mono',monospace;font-size:8px;font-weight:700;min-width:14px;height:14px;border-radius:7px;padding:0 3px;margin-left:4px;vertical-align:middle;}
.tab-badge.amber{background:var(--amber);}

.topbar-right{display:flex;align-items:center;gap:7px;}
.status-pill{display:flex;align-items:center;gap:5px;padding:4px 9px;border-radius:20px;border:1px solid rgba(255,255,255,0.2);background:rgba(255,255,255,0.024);backdrop-filter:blur(16px);font-family:'DM Mono',monospace;font-size:10px;color:var(--text2);}
.status-dot{width:5px;height:5px;border-radius:50%;animation:blink 2s infinite;}
.status-dot.demo{background:var(--amber);box-shadow:0 0 6px rgba(245,158,11,.5);}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}
.auth-btn{padding:5px 13px;border-radius:7px;font-family:'DM Sans',sans-serif;font-size:12px;font-weight:600;cursor:pointer;transition:all .18s;border:none;}
.login-btn{background:rgba(255,255,255,0.05);backdrop-filter:blur(16px);border:1px solid rgba(255,255,255,0.2);color:var(--text2);}
.login-btn:hover{border-color:var(--accent);color:var(--accent);background:rgba(0,229,160,0.1);}
.signup-btn{background:var(--accent);color:#000;font-weight:700;box-shadow:0 0 14px var(--glow);}
.signup-btn:hover{box-shadow:0 0 24px var(--glow);transform:translateY(-1px);}

/* ── TAB VIEW ── */
.tab-view{width:100%;flex:1;display:flex;flex-direction:column;}
.tab-page{flex:1;padding:24px 28px;display:flex;flex-direction:column;gap:18px;animation:tabIn .28s var(--ease-out) both;}
.tab-page>*{flex-shrink:0;}
@keyframes tabIn{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}

.page-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:2px;}
.page-title{font-family:'Syne',sans-serif;font-size:19px;font-weight:800;letter-spacing:-.03em;}
.page-subtitle{font-family:'DM Mono',monospace;font-size:10px;color:var(--text3);margin-top:3px;}
.page-actions{display:flex;gap:7px;}
.page-btn{padding:6px 13px;border-radius:7px;font-family:'DM Sans',sans-serif;font-size:12px;font-weight:600;cursor:pointer;border:1px solid rgba(255,255,255,0.2);background:rgba(255,255,255,0.024);backdrop-filter:blur(16px);color:var(--text2);transition:all .16s;}
.page-btn:hover{border-color:var(--accent);color:var(--accent);background:rgba(0,229,160,0.1);}
.page-btn.primary{background:var(--accent);backdrop-filter:none;border-color:var(--accent);color:#000;}
.page-btn.primary:hover{box-shadow:0 0 18px var(--glow);}

/* ── NARRATIVE BANNER ── */
.narrative-banner{
  position:relative;padding:13px 18px;
  background:rgba(255,77,106,0.1);backdrop-filter:blur(24px);border:1px solid rgba(255,77,106,0.28);border-radius:11px;
  display:flex;align-items:center;justify-content:space-between;gap:14px;
  cursor:pointer;transition:all .2s;overflow:hidden;
  animation:bannerIn .5s var(--ease-out) both;
}
[data-theme="light"] .narrative-banner{background:rgba(200,0,61,0.08);border-color:rgba(200,0,61,0.25);}
.narrative-banner:hover{border-color:rgba(255,77,106,0.5);transform:translateY(-1px);box-shadow:0 8px 28px rgba(255,77,106,0.12);}
@keyframes bannerIn{from{opacity:0;transform:translateY(-8px)}to{opacity:1;transform:translateY(0)}}
.nb-left{display:flex;align-items:center;gap:11px;}
.nb-pulse{width:9px;height:9px;border-radius:50%;background:var(--danger);flex-shrink:0;animation:nbPulse 1.5s infinite;}
@keyframes nbPulse{0%,100%{box-shadow:0 0 0 0 rgba(255,77,106,0.6)}50%{box-shadow:0 0 0 7px rgba(255,77,106,0)}}
.nb-text{font-size:12.5px;color:var(--text);}
.nb-text strong{color:var(--danger);font-weight:700;}
.nb-text em{font-style:normal;color:var(--amber);font-weight:600;}
.nb-cta{font-family:'DM Mono',monospace;font-size:10.5px;color:var(--danger);white-space:nowrap;display:flex;align-items:center;gap:4px;border:1px solid rgba(255,77,106,0.3);padding:5px 10px;border-radius:6px;transition:all .15s;flex-shrink:0;}
.nb-cta:hover{background:rgba(255,77,106,0.1);}

/* ── KPI CARDS ── */
.kpi-strip{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;width:100%;}
.kpi-card{
  background:rgba(255,255,255,0.04);backdrop-filter:blur(24px);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:14px 16px;
  text-align:left;position:relative;overflow:hidden;min-width:0;
  transition:border-color .2s,transform .18s,box-shadow .2s;cursor:default;
  box-shadow:inset 0 1px 0 rgba(255,255,255,0.2), 0 8px 32px rgba(0,0,0,0.4);
}
[data-theme="light"] .kpi-card{background:rgba(255,255,255,0.6);border-color:rgba(0,0,0,0.1);}
.kpi-card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,var(--accent),var(--accent2));transform:scaleX(0);transform-origin:left;transition:transform .28s var(--ease-out);}
.kpi-card.danger-card{border-color:rgba(255,77,106,0.28);animation:dangerPulse 3s infinite;}
@keyframes dangerPulse{0%,100%{box-shadow:0 0 0 0 rgba(255,77,106,0)}50%{box-shadow:0 0 0 4px rgba(255,77,106,0.07)}}
.kpi-card.danger-card::before{background:linear-gradient(90deg,var(--danger),#ff8a65);transform:scaleX(1);}
.kpi-card.amber-card::before{background:linear-gradient(90deg,var(--amber),#f97316);}
.kpi-card:hover{border-color:rgba(0,229,160,.3);transform:translateY(-2px);box-shadow:0 10px 28px var(--shadow);}
.kpi-card.danger-card:hover{border-color:rgba(255,77,106,0.55);}
.kpi-card:hover::before{transform:scaleX(1);}
.kpi-icon{font-size:15px;margin-bottom:8px;display:block;}
.kpi-label{font-family:'DM Mono',monospace;font-size:9px;color:var(--text3);text-transform:uppercase;letter-spacing:.13em;margin-bottom:4px;}
.kpi-value{font-family:'Syne',sans-serif;font-size:clamp(18px,2.2vw,24px);font-weight:700;color:var(--text);letter-spacing:-.02em;}
.kpi-card.danger-card .kpi-value{color:var(--danger);}
.kpi-delta{display:flex;align-items:center;gap:4px;font-family:'DM Mono',monospace;font-size:10px;margin-top:4px;}
.kpi-delta.up{color:var(--accent);}.kpi-delta.down{color:var(--danger);}.kpi-delta.neutral{color:var(--amber);}

/* ── SUGGESTIONS ── */
.suggestions{display:grid;grid-template-columns:1fr 1fr;gap:8px;width:100%;}
.sug-chip{
  background:rgba(255,255,255,0.04);backdrop-filter:blur(24px);border:1px solid rgba(255,255,255,0.08);border-radius:10px;
  padding:13px 15px;text-align:left;cursor:pointer;
  font-family:'DM Sans',sans-serif;font-size:12.5px;color:var(--text2);
  transition:all .18s;line-height:1.45;display:flex;flex-direction:column;gap:6px;
  box-shadow:inset 0 1px 0 rgba(255,255,255,0.08);
}
[data-theme="light"] .sug-chip{background:rgba(255,255,255,0.5);border-color:rgba(0,0,0,0.08);}
.sug-chip:hover{border-color:rgba(0,229,160,.35);color:var(--text);background:linear-gradient(135deg,rgba(0,229,160,.06),rgba(0,180,255,.03));transform:translateY(-2px);box-shadow:0 8px 22px var(--shadow);}
[data-theme="light"] .sug-chip:hover{background:linear-gradient(135deg,rgba(0,122,82,.05),rgba(0,102,187,.03));}
.sug-chip-header{display:flex;align-items:center;gap:8px;}
.sug-chip-icon{font-size:18px;line-height:1;}
.sug-chip strong{color:var(--text);font-size:12px;font-weight:700;font-family:'Syne',sans-serif;}
.sug-chip-tag{display:inline-block;font-family:'DM Mono',monospace;font-size:8.5px;padding:1px 6px;border-radius:3px;letter-spacing:.05em;}
.sug-chip-tag.revenue{background:rgba(0,229,160,.12);color:var(--accent);}
.sug-chip-tag.risk{background:rgba(255,77,106,.12);color:var(--danger);}
.sug-chip-tag.ops{background:rgba(0,180,255,.12);color:var(--accent2);}
.sug-chip-tag.growth{background:rgba(167,139,250,.12);color:var(--purple);}
[data-theme="light"] .sug-chip-tag.revenue{color:var(--accent);}
[data-theme="light"] .sug-chip-tag.risk{color:var(--danger);}
[data-theme="light"] .sug-chip-tag.ops{color:var(--accent2);}
[data-theme="light"] .sug-chip-tag.growth{color:var(--purple);}
.sug-chip-desc{font-size:11.5px;color:var(--text2);line-height:1.5;}

/* ── SAMPLE CONVO ── */
.sample-convo{width:100%;background:rgba(255,255,255,0.04);backdrop-filter:blur(24px);border:1px solid rgba(255,255,255,0.08);border-radius:12px;overflow:hidden;box-shadow:inset 0 1px 0 rgba(255,255,255,0.2), 0 8px 32px rgba(0,0,0,0.4);}
[data-theme="light"] .sample-convo{background:rgba(255,255,255,0.6);border-color:rgba(0,0,0,0.1);}
.sample-convo-head{padding:9px 14px;border-bottom:1px solid rgba(255,255,255,0.1);display:flex;align-items:center;gap:8px;background:rgba(0,229,160,0.08);}
[data-theme="light"] .sample-convo-head{background:rgba(0,122,82,0.06);border-bottom-color:rgba(0,0,0,0.06);}
.sample-convo-title{font-family:'DM Mono',monospace;font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--accent);}
.sample-convo-badge{font-family:'DM Mono',monospace;font-size:9px;padding:2px 7px;background:rgba(0,229,160,.1);color:var(--accent);border-radius:4px;margin-left:auto;}
[data-theme="light"] .sample-convo-badge{background:rgba(0,122,82,.1);}
.sample-q{display:flex;align-items:flex-start;gap:9px;padding:11px 14px;border-bottom:1px solid var(--border);}
.sample-q-avatar{width:24px;height:24px;border-radius:50%;background:rgba(255,255,255,0.032);backdrop-filter:blur(16px);border:1px solid rgba(255,255,255,0.08);display:flex;align-items:center;justify-content:center;font-family:'Syne',sans-serif;font-size:8.5px;font-weight:700;color:var(--text3);flex-shrink:0;}
[data-theme="light"] .sample-q-avatar{background:rgba(240,245,255,0.3);border-color:rgba(0,0,0,0.08);}
.sample-q-text{font-size:12.5px;color:var(--text2);line-height:1.55;padding-top:2px;}
.sample-a{display:flex;align-items:flex-start;gap:9px;padding:11px 14px;}
.sample-a-avatar{width:24px;height:24px;border-radius:50%;background:linear-gradient(135deg,var(--accent),var(--accent2));display:flex;align-items:center;justify-content:center;font-family:'Syne',sans-serif;font-size:8.5px;font-weight:700;color:#000;flex-shrink:0;}
.sample-a-text{font-size:12.5px;color:var(--text);line-height:1.6;}
.sample-a-text strong{color:var(--danger);}
.sample-a-chips{display:flex;gap:6px;margin-top:8px;flex-wrap:wrap;}
.sample-chip{font-family:'DM Mono',monospace;font-size:10px;padding:3px 8px;border-radius:5px;border:1px solid var(--border2);color:var(--text3);}
.sample-chip.danger{border-color:rgba(255,77,106,.3);color:var(--danger);background:rgba(255,77,106,.06);}
.sample-chip.ok{border-color:rgba(0,229,160,.3);color:var(--accent);background:rgba(0,229,160,.06);}
[data-theme="light"] .sample-chip.ok{color:var(--accent);border-color:rgba(0,122,82,.3);}
.sample-cta{padding:9px 14px;border-top:1px solid var(--border);text-align:center;font-family:'DM Mono',monospace;font-size:10.5px;color:var(--text3);}
.sample-cta span{color:var(--accent);cursor:pointer;}.sample-cta span:hover{text-decoration:underline;}

/* ── CHAT MESSAGES ── */
.chat-section {
  width: 100%;
  display: flex;
  justify-content: center;
  position: relative;
}
.chat-section::before {
  content: "";
  position: absolute;
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, rgba(99,102,241,0.25), transparent 70%);
  filter: blur(100px);
  z-index: -1;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  pointer-events: none;
}
.chat-area {
  width: 100%;
  max-width: 900px;
  display: flex;
  flex-direction: column;
  gap: 28px;
}
.welcome{margin:auto;display:flex;flex-direction:column;align-items:center;gap:20px;text-align:center;max-width:620px;width:100%;animation:welcomeIn .65s var(--ease-out) both;}
@keyframes welcomeIn{from{opacity:0;transform:translateY(24px) scale(.97)}to{opacity:1;transform:translateY(0) scale(1)}}
.welcome h1{font-family:'Syne',sans-serif;font-size:clamp(36px,6vw,64px);font-weight:800;line-height:1.05;letter-spacing:-.04em;}
.welcome h1 .hl{background:linear-gradient(90deg,var(--accent),var(--accent2));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}
.welcome-desc{font-size:16px;color:var(--text2);line-height:1.8;max-width:520px;}

.msg-row{display:flex;gap:11px;}
.msg-row.user{flex-direction:row-reverse;}
.avatar{width:32px;height:32px;border-radius:50%;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-family:'Syne',sans-serif;font-size:10px;font-weight:700;}
.avatar.ai{background:linear-gradient(135deg,var(--accent),var(--accent2));color:#000;box-shadow:0 0 12px var(--glow);}
.avatar.user{background:rgba(255,255,255,0.032);backdrop-filter:blur(16px);border:1px solid rgba(255,255,255,0.08);color:var(--text2);}
[data-theme="light"] .avatar.user{background:rgba(240,245,255,0.3);border-color:rgba(0,0,0,0.08);}
.bubble {
  max-width: 72%;
  padding: 18px 22px;
  font-size:13.5px;
  line-height:1.75;
  position:relative;
}

.bubble.user {
  align-self: flex-end;
  box-shadow: var(--accent-glow);
  background: var(--accent);
  color: #000;
  border:none;
}
.light .bubble.user {
  box-shadow: var(--accent-glow);
  background: var(--accent);
  color: #fff;
}

.bubble.ai {
  /* It inherits .panel because we will attach .panel to the message row bubbling or we can redefine here */
}

.bubble.error{border-color:rgba(255,77,106,.3);background:rgba(255,77,106,.05);}
.bubble-meta{display:flex;align-items:center;gap:7px;margin-bottom:5px;}
.bubble-time{font-family:'DM Mono',monospace;font-size:9.5px;color:var(--text3);}
.bubble-actions{display:flex;gap:4px;opacity:0;transition:opacity .2s;}
.msg-row:hover .bubble-actions{opacity:1;}
.bubble-action-btn{width:20px;height:20px;border-radius:5px;border:1px solid var(--border);background:rgba(255,255,255,0.03);backdrop-filter:blur(32px);cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:10px;color:var(--text3);transition:all .14s;}
.bubble-action-btn:hover{border-color:var(--accent);color:var(--accent);}

/* ── RESPONSE CHART ── */
.response-chart{margin-top:12px;background:rgba(255,255,255,0.04);backdrop-filter:blur(24px);border:1px solid rgba(255,255,255,0.12);border-radius:9px;padding:13px;box-shadow:inset 0 1px 0 rgba(255,255,255,0.08);}
[data-theme="light"] .response-chart{background:rgba(240,245,255,0.5);border-color:rgba(0,0,0,0.08);}
.chart-title{font-family:'DM Mono',monospace;font-size:9.5px;color:var(--accent);letter-spacing:.07em;text-transform:uppercase;margin-bottom:11px;}
.chart-bars{display:flex;flex-direction:column;gap:6px;}
.chart-row{display:flex;align-items:center;gap:9px;}
.chart-label{font-family:'DM Mono',monospace;font-size:10px;color:var(--text2);width:85px;flex-shrink:0;text-align:right;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.chart-track{flex:1;height:22px;background:rgba(255,255,255,0.05);border-radius:4px;overflow:hidden;position:relative;}
[data-theme="light"] .chart-track{background:rgba(0,0,0,0.05);}
.chart-fill{height:100%;border-radius:4px;background:linear-gradient(90deg,var(--accent),var(--accent2));width:0;transition:width 1s var(--ease-out);display:flex;align-items:center;justify-content:flex-end;min-width:2px;}
.chart-fill.amber{background:linear-gradient(90deg,var(--amber),#f97316);}.chart-fill.danger{background:linear-gradient(90deg,var(--danger),#ff8a65);}
.chart-val{font-family:'DM Mono',monospace;font-size:9px;color:rgba(0,0,0,.8);padding-right:6px;white-space:nowrap;}

/* ── DATA TABLE ── */
.data-card{margin-top:11px;background:rgba(255,255,255,0.04);backdrop-filter:blur(24px);border:1px solid rgba(255,255,255,0.12);border-radius:9px;overflow:hidden;box-shadow:inset 0 1px 0 rgba(255,255,255,0.08);}
[data-theme="light"] .data-card{background:rgba(240,245,255,0.5);border-color:rgba(0,0,0,0.08);}
.data-card-head{padding:7px 13px;border-bottom:1px solid rgba(255,255,255,0.1);font-family:'DM Mono',monospace;font-size:9.5px;color:var(--accent);letter-spacing:.07em;background:rgba(0,229,160,0.08);}
[data-theme="light"] .data-card-head{background:rgba(0,122,82,0.06);border-bottom-color:rgba(0,0,0,0.06);}
.data-table-wrap{overflow-x:auto;}
.data-table{width:100%;border-collapse:collapse;font-family:'DM Mono',monospace;font-size:11.5px;}
.data-table th{padding:7px 13px;text-align:left;color:var(--text3);font-weight:500;border-bottom:1px solid var(--border);white-space:nowrap;}
.data-table td{padding:6px 13px;color:var(--text);border-bottom:1px solid rgba(255,255,255,.03);}
[data-theme="light"] .data-table td{border-bottom-color:var(--border);}
.data-table tr:last-child td{border-bottom:none;}
.data-table .pos{color:var(--accent);}.data-table .neg{color:var(--danger);}
.data-table tbody tr{transition:background .12s;}.data-table tbody tr:hover{background:rgba(255,255,255,.025);}
[data-theme="light"] .data-table tbody tr:hover{background:rgba(0,0,0,.03);}

.msg-footer{display:flex;align-items:center;flex-wrap:wrap;gap:7px;margin-top:9px;padding-top:8px;border-top:1px solid var(--border);}
.msg-badge{font-family:'DM Mono',monospace;font-size:9px;padding:2px 7px;border-radius:4px;}
.msg-badge.conf{background:rgba(0,229,160,.1);color:var(--accent);}.msg-badge.samp{background:rgba(255,255,255,.05);color:var(--text3);}.msg-badge.exec{background:rgba(0,180,255,.08);color:var(--accent2);margin-left:auto;}
[data-theme="light"] .msg-badge.samp{background:rgba(0,0,0,.05);}

.typing{display:flex;gap:5px;align-items:center;padding:2px 0;}
.typing span{width:6px;height:6px;border-radius:50%;background:var(--accent);opacity:.35;animation:throb 1.1s infinite;}
.typing span:nth-child(2){animation-delay:.18s;}.typing span:nth-child(3){animation-delay:.36s;}
@keyframes throb{0%,60%,100%{transform:scale(1);opacity:.3}30%{transform:scale(1.4);opacity:1}}

/* ── INPUT ZONE ── */
.input-zone {
  position: fixed;
  bottom: 30px;
  transform: translateX(-50%);
  width: 100%;
  max-width: 900px;
  padding: 0 20px;
  z-index: 30;
  transition: left 0.28s cubic-bezier(.22,1,.36,1);
}
.input-label{font-family:'DM Mono',monospace;font-size:9.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--accent);margin-bottom:6px;display:flex;align-items:center;gap:6px;}
.input-label::before{content:'';display:inline-block;width:5px;height:5px;border-radius:50%;background:var(--accent);animation:blink 2s infinite;}
.input-shell {
  padding: 16px 18px;
  display:flex;flex-direction:column;
}
.input-shell:focus-within{border-color:var(--accent);box-shadow:0 0 0 3px rgba(99,102,241,.15),0 0 22px rgba(99,102,241,.1);}
.input-shell.drag-over{border-color:var(--accent);box-shadow:0 0 0 3px var(--glow);background:rgba(0,229,160,.04);}
.drag-hint{position:absolute;inset:0;border-radius:12px;display:flex;align-items:center;justify-content:center;font-family:'Syne',sans-serif;font-size:13px;font-weight:600;color:var(--accent);background:rgba(8,13,20,.88);backdrop-filter:blur(16px);pointer-events:none;opacity:0;transition:opacity .2s;z-index:10;}
.input-shell.drag-over .drag-hint{opacity:1;}
.input-shell-wrap{position:relative;}

.attach-preview-row{display:flex;flex-wrap:wrap;gap:6px;padding-bottom:9px;margin-bottom:4px;border-bottom:1px solid var(--border);}
.attach-thumb{position:relative;border-radius:7px;overflow:visible;display:flex;flex-direction:column;align-items:center;}
.attach-thumb img{width:58px;height:46px;object-fit:cover;border-radius:7px;border:1px solid var(--border2);display:block;}
.attach-thumb-file{width:58px;height:46px;border-radius:7px;background:rgba(255,255,255,0.03);backdrop-filter:blur(32px);border:1px solid var(--border2);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;}
.attach-thumb-file-icon{font-size:18px;line-height:1;}
.attach-thumb-file-ext{font-family:'DM Mono',monospace;font-size:7.5px;color:var(--accent);text-transform:uppercase;letter-spacing:.06em;background:rgba(0,229,160,.1);padding:1px 4px;border-radius:3px;}
.attach-thumb-name{font-family:'DM Mono',monospace;font-size:8px;color:var(--text3);max-width:58px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;text-align:center;margin-top:2px;}
.attach-remove-btn{position:absolute;top:-5px;right:-5px;width:16px;height:16px;border-radius:50%;background:var(--danger);border:2px solid var(--bg1);color:#fff;font-size:8px;font-weight:700;display:flex;align-items:center;justify-content:center;cursor:pointer;transition:transform .14s;z-index:5;}
.attach-remove-btn:hover{transform:scale(1.18);}

.attach-menu-wrap{position:relative;}
.attach-menu{position:absolute;bottom:calc(100% + 10px);right:0;background:rgba(255,255,255,0.056);backdrop-filter:blur(24px);border:1px solid rgba(255,255,255,0.08);border-radius:11px;padding:6px;min-width:195px;z-index:50;box-shadow:0 14px 44px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.1);animation:attachMenuIn .18s var(--ease-spring) both;}
@keyframes attachMenuIn{from{opacity:0;transform:translateY(6px) scale(.97)}to{opacity:1;transform:translateY(0) scale(1)}}
.attach-menu-item{display:flex;align-items:center;gap:9px;padding:8px 10px;border-radius:7px;cursor:pointer;transition:background .12s,color .12s;font-size:12.5px;color:var(--text2);}
.attach-menu-item:hover{background:rgba(0,229,160,.08);color:var(--text);}
[data-theme="light"] .attach-menu-item:hover{background:rgba(0,122,82,.07);}
.attach-menu-item:hover .ami-icon{color:var(--accent);}
.ami-icon{font-size:15px;width:20px;text-align:center;color:var(--text3);transition:color .12s;flex-shrink:0;}
.ami-label{flex:1;}.ami-sub{font-family:'DM Mono',monospace;font-size:9px;color:var(--text3);}
.attach-menu-divider{height:1px;background:var(--border);margin:3px 6px;}

.input-row{display:flex;align-items:center;gap:7px;}
.chat-input{flex:1;border:none;background:transparent;font-family:'DM Sans',sans-serif;font-size:13.5px;color:var(--text);resize:none;outline:none;min-height:22px;max-height:120px;line-height:1.55;display:block;vertical-align:middle;padding:0;}
.chat-input::placeholder{color:var(--text3);}
.input-actions{display:flex;align-items:center;gap:5px;flex-shrink:0;margin-bottom:1px;}
.attach-btn{width:32px;height:32px;border-radius:7px;background:rgba(255,255,255,0.05);backdrop-filter:blur(16px);border:1px solid rgba(255,255,255,0.08);cursor:pointer;display:flex;align-items:center;justify-content:center;color:var(--text3);transition:all .16s;position:relative;flex-shrink:0;}
.attach-btn:hover{border-color:var(--accent);color:var(--accent);background:rgba(0,229,160,0.1);}
.attach-btn.has-files{border-color:rgba(0,229,160,.45);color:var(--accent);background:rgba(0,229,160,.07);}
.attach-badge{position:absolute;top:-5px;right:-5px;background:var(--accent);color:#000;font-family:'DM Mono',monospace;font-size:8.5px;font-weight:700;width:14px;height:14px;border-radius:50%;display:flex;align-items:center;justify-content:center;border:2px solid var(--bg1);}
.send-btn{width:34px;height:34px;border-radius:8px;background:linear-gradient(135deg,var(--accent),var(--accent2));border:none;cursor:pointer;display:flex;align-items:center;justify-content:center;color:#000;transition:all .16s;box-shadow:0 0 14px var(--glow);flex-shrink:0;}
.send-btn:hover:not(:disabled){box-shadow:0 0 26px var(--glow);transform:scale(1.07);}
.send-btn:disabled{opacity:.3;cursor:not-allowed;}
.input-footer{display:flex;align-items:center;justify-content:space-between;margin-top:6px;font-family:'DM Mono',monospace;font-size:10px;color:var(--text3);padding:0 2px;}
.input-footer-right{display:flex;gap:10px;}
.input-footer kbd{padding:1px 5px;border:1px solid var(--border2);border-radius:4px;font-size:9px;font-family:'DM Mono',monospace;}

/* ── COPY TOAST ── */
.copy-toast{position:fixed;bottom:88px;left:50%;transform:translateX(-50%) translateY(10px);background:var(--accent);color:#000;font-family:'DM Mono',monospace;font-size:11px;font-weight:600;padding:5px 13px;border-radius:20px;box-shadow:0 4px 18px var(--glow);opacity:0;transition:all .22s var(--ease-spring);pointer-events:none;z-index:999;}
.copy-toast.show{opacity:1;transform:translateX(-50%) translateY(0);}

/* ── LIVE FEED PANEL (right-side overlay) ── */
.live-feed-panel{
  width:280px;min-width:280px;flex-shrink:0;
  background:rgba(255,255,255,0.048);backdrop-filter:blur(32px);border-left:1px solid rgba(255,255,255,0.08);
  display:flex;flex-direction:column;overflow:hidden;position:relative;z-index:10;
  animation:slideInRight .25s var(--ease-out) both;
  box-shadow:inset 1px 0 0 rgba(255,255,255,0.1), -2px 8px 32px rgba(0,0,0,0.2);
}
[data-theme="light"] .live-feed-panel{background:rgba(255,255,255,0.55);border-left-color:rgba(0,0,0,0.1);}
@keyframes slideInRight{from{opacity:0;transform:translateX(20px)}to{opacity:1;transform:translateX(0)}}
.rp-head{padding:0 14px;height:var(--topbar-h);flex-shrink:0;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;}
.rp-title{font-family:'Syne',sans-serif;font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--text2);}
.rp-live{display:flex;align-items:center;gap:4px;font-family:'DM Mono',monospace;font-size:9.5px;color:var(--danger);}
.rp-live-dot{width:5px;height:5px;border-radius:50%;background:var(--danger);animation:blink 1.2s infinite;}
.rp-body{flex:1;overflow-y:auto;padding:11px;display:flex;flex-direction:column;gap:8px;}
.rp-section-row{display:flex;align-items:center;justify-content:space-between;padding:2px 1px;margin-top:3px;}
.rp-section{font-family:'DM Mono',monospace;font-size:9px;letter-spacing:.12em;text-transform:uppercase;color:var(--text3);}

.mini-chart-card{background:rgba(255,255,255,0.032);backdrop-filter:blur(24px);border:1px solid rgba(255,255,255,0.1);border-radius:10px;padding:11px;}
[data-theme="light"] .mini-chart-card{background:rgba(240,245,255,0.4);border-color:rgba(0,0,0,0.06);}
.mini-chart-label{font-family:'DM Mono',monospace;font-size:9px;color:var(--text3);margin-bottom:9px;letter-spacing:.04em;}
.mini-chart{display:flex;align-items:flex-end;gap:3px;height:44px;}
.mini-bar{flex:1;border-radius:3px 3px 0 0;background:linear-gradient(180deg,rgba(0,229,160,.45),rgba(0,180,255,.18));transition:opacity .15s;cursor:pointer;}
[data-theme="light"] .mini-bar{background:linear-gradient(180deg,rgba(0,122,82,.5),rgba(0,102,187,.2));}
.mini-bar:hover{opacity:.7;}.mini-bar.hi{background:linear-gradient(180deg,var(--accent),var(--accent2));}
[data-theme="light"] .mini-bar.hi{background:linear-gradient(180deg,var(--accent),var(--accent2));}
.mini-chart-foot{display:flex;justify-content:space-between;margin-top:4px;font-family:'DM Mono',monospace;font-size:8.5px;color:var(--text3);}

.alert-summary-row{display:flex;gap:5px;margin-bottom:2px;}
.alert-summary-pill{flex:1;display:flex;flex-direction:column;align-items:center;padding:7px 5px;background:rgba(255,255,255,0.024);backdrop-filter:blur(16px);border-radius:8px;border:1px solid rgba(255,255,255,0.1);}
[data-theme="light"] .alert-summary-pill{background:rgba(240,245,255,0.3);border-color:rgba(0,0,0,0.05);}
.alert-summary-pill.danger{border-color:rgba(255,77,106,.2);background:rgba(255,77,106,.04);}
.alert-summary-pill.amber{border-color:rgba(245,158,11,.15);background:rgba(245,158,11,.03);}
.alert-summary-pill.ok{border-color:rgba(0,229,160,.15);background:rgba(0,229,160,.03);}
[data-theme="light"] .alert-summary-pill.ok{background:rgba(0,122,82,.04);}
.asp-count{font-family:'Syne',sans-serif;font-size:17px;font-weight:800;line-height:1;}
.asp-count.danger{color:var(--danger);}.asp-count.amber{color:var(--amber);}.asp-count.ok{color:var(--accent);}
.asp-label{font-family:'DM Mono',monospace;font-size:8px;color:var(--text3);margin-top:2px;text-align:center;letter-spacing:.04em;}

.alert-card{background:rgba(255,255,255,0.032);backdrop-filter:blur(24px);border-radius:9px;padding:10px 12px;display:flex;flex-direction:column;gap:5px;border:1px solid rgba(255,77,106,0.25);transition:border-color .14s,transform .14s;position:relative;overflow:hidden;}
[data-theme="light"] .alert-card{background:rgba(240,245,255,0.4);border-color:rgba(200,0,61,0.15);}
.alert-card::before{content:'';position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--danger);border-radius:3px 0 0 3px;}
.alert-card:hover{border-color:rgba(255,77,106,.4);transform:translateX(-2px);}
.alert-card.warn{border-color:rgba(245,158,11,.18);}.alert-card.warn::before{background:var(--amber);}
.alert-card.warn:hover{border-color:rgba(245,158,11,.4);}
.alert-head{display:flex;align-items:center;justify-content:space-between;gap:5px;}
.alert-head-left{display:flex;align-items:center;gap:5px;}
.alert-icon{font-size:11px;}
.alert-title{font-family:'Syne',sans-serif;font-size:11px;font-weight:600;color:var(--text);}
.alert-time{font-family:'DM Mono',monospace;font-size:8.5px;color:var(--text3);flex-shrink:0;}
.alert-body{font-size:11px;color:var(--text2);line-height:1.5;}
.alert-impact{font-family:'DM Mono',monospace;font-size:9.5px;color:var(--danger);font-weight:600;margin-top:1px;}
.alert-impact.warn{color:var(--amber);}
.alert-footer{display:flex;align-items:center;justify-content:space-between;}
.alert-tag{font-family:'DM Mono',monospace;font-size:8.5px;padding:2px 7px;border-radius:4px;font-weight:600;letter-spacing:.05em;}
.alert-tag.danger{background:rgba(255,77,106,.12);color:var(--danger);}
.alert-tag.warn{background:rgba(245,158,11,.12);color:var(--amber);}
.alert-action{font-family:'DM Mono',monospace;font-size:9px;color:var(--accent);cursor:pointer;text-decoration:underline;transition:opacity .14s;}
.alert-action:hover{opacity:.7;}

/* ── TABLE PAGES ── */
.full-table-wrap{background:rgba(255,255,255,0.04);backdrop-filter:blur(24px);border:1px solid rgba(255,255,255,0.08);border-radius:13px;overflow:hidden;box-shadow:inset 0 1px 0 rgba(255,255,255,0.2), 0 8px 32px rgba(0,0,0,0.4);}
[data-theme="light"] .full-table-wrap{background:rgba(255,255,255,0.6);border-color:rgba(0,0,0,0.1);}
.full-table-head{display:flex;align-items:center;justify-content:space-between;padding:13px 17px;border-bottom:1px solid rgba(255,255,255,0.1);}
.full-table-title{font-family:'Syne',sans-serif;font-size:13px;font-weight:700;}
.ft-search-input{padding:6px 10px;background:rgba(255,255,255,0.024);backdrop-filter:blur(16px);border:1px solid rgba(255,255,255,0.08);border-radius:7px;font-family:'DM Mono',monospace;font-size:11px;color:var(--text);outline:none;width:175px;transition:border-color .15s;}
.ft-search-input:focus{border-color:rgba(0,229,160,.4);box-shadow:0 0 0 2px rgba(0,229,160,0.15);}
[data-theme="light"] .ft-search-input:focus{border-color:rgba(0,122,82,.4);}
.ft-search-input::placeholder{color:var(--text3);}
.full-table{width:100%;border-collapse:collapse;font-size:12px;}
.full-table th{padding:9px 15px;text-align:left;font-family:'DM Mono',monospace;font-size:9.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--text3);border-bottom:1px solid var(--border);background:rgba(255,255,255,.015);white-space:nowrap;}
[data-theme="light"] .full-table th{background:rgba(0,0,0,.02);}
.full-table td{padding:9px 15px;border-bottom:1px solid rgba(255,255,255,.03);color:var(--text);vertical-align:middle;}
[data-theme="light"] .full-table td{border-bottom-color:var(--border);}
.full-table tbody tr{transition:background .11s;cursor:pointer;}
.full-table tbody tr:hover{background:rgba(255,255,255,.03);}
[data-theme="light"] .full-table tbody tr:hover{background:rgba(0,0,0,.025);}
.full-table tr:last-child td{border-bottom:none;}
.ft-badge{display:inline-block;font-family:'DM Mono',monospace;font-size:9px;padding:2px 7px;border-radius:4px;font-weight:600;}
.ft-badge.success{background:rgba(0,229,160,.12);color:var(--accent);}
.ft-badge.failed{background:rgba(255,77,106,.12);color:var(--danger);}
.ft-badge.pending{background:rgba(245,158,11,.12);color:var(--amber);}
.ft-badge.flagged{background:rgba(255,77,106,.18);color:var(--danger);}
.ft-badge.low{background:rgba(0,229,160,.12);color:var(--accent);}
.ft-badge.medium{background:rgba(245,158,11,.12);color:var(--amber);}
.ft-badge.high{background:rgba(255,77,106,.18);color:var(--danger);}
.ft-mono{font-family:'DM Mono',monospace;font-size:11px;}

.two-col-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;}
.three-col-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;}
.panel-card{background:rgba(255,255,255,0.04);backdrop-filter:blur(24px);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:17px 19px;box-shadow:inset 0 1px 0 rgba(255,255,255,0.2), 0 8px 32px rgba(0,0,0,0.4);}
[data-theme="light"] .panel-card{background:rgba(255,255,255,0.6);border-color:rgba(0,0,0,0.1);}
.panel-card-title{font-family:'Syne',sans-serif;font-size:13px;font-weight:700;margin-bottom:13px;display:flex;align-items:center;gap:7px;}
.metric-row{display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid var(--border);}
.metric-row:last-child{border-bottom:none;}
.metric-label{font-size:12px;color:var(--text2);}
.metric-val{font-family:'DM Mono',monospace;font-size:11.5px;font-weight:600;color:var(--text);}
.metric-val.green{color:var(--accent);}.metric-val.red{color:var(--danger);}.metric-val.amber{color:var(--amber);}

.gauge-wrap{text-align:center;padding:8px 0 12px;}
.gauge-score{font-family:'Syne',sans-serif;font-size:36px;font-weight:800;line-height:1;}
.gauge-label{font-family:'DM Mono',monospace;font-size:9.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--text3);margin-top:4px;}
.gauge-sub{font-size:11px;color:var(--text2);margin-top:5px;}

.report-card{background:rgba(255,255,255,0.04);backdrop-filter:blur(24px);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:15px 17px;display:flex;align-items:flex-start;gap:13px;cursor:pointer;transition:all .2s;box-shadow:inset 0 1px 0 rgba(255,255,255,0.2), 0 8px 32px rgba(0,0,0,0.4);}
[data-theme="light"] .report-card{background:rgba(255,255,255,0.6);border-color:rgba(0,0,0,0.1);}
.report-card:hover{border-color:rgba(0,229,160,.3);transform:translateY(-2px);box-shadow:0 8px 26px var(--shadow);}
.report-icon{font-size:24px;flex-shrink:0;margin-top:2px;}
.report-info{flex:1;min-width:0;}
.report-title{font-family:'Syne',sans-serif;font-size:13px;font-weight:700;margin-bottom:3px;}
.report-desc{font-size:11.5px;color:var(--text2);line-height:1.55;}
.report-meta{display:flex;align-items:center;gap:9px;margin-top:7px;}
.report-tag{font-family:'DM Mono',monospace;font-size:9px;padding:2px 7px;border-radius:4px;background:rgba(0,180,255,.1);color:var(--accent2);}
.report-date{font-family:'DM Mono',monospace;font-size:9px;color:var(--text3);}
.report-dl{font-family:'DM Mono',monospace;font-size:9.5px;color:var(--accent);flex-shrink:0;border:1px solid rgba(0,229,160,.25);padding:4px 9px;border-radius:6px;transition:all .14s;}
.report-dl:hover{background:var(--glow);}

/* ── AUTH MODAL ── */
.modal-overlay{position:fixed;inset:0;background:rgba(0,0,0,0.7);backdrop-filter:blur(24px);z-index:100;display:flex;align-items:center;justify-content:center;animation:fadeIn .2s ease;}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}
.modal{background:rgba(255,255,255,0.056);backdrop-filter:blur(32px);border:1px solid rgba(255,255,255,0.08);border-radius:16px;padding:32px 36px;width:min(360px,92vw);box-shadow:0 28px 72px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.12);position:relative;animation:scaleIn .22s var(--ease-spring) both;}
@keyframes scaleIn{from{opacity:0;transform:scale(.94)}to{opacity:1;transform:scale(1)}}
.modal-close{position:absolute;top:13px;right:13px;background:transparent;border:none;cursor:pointer;color:var(--text3);font-size:16px;width:28px;height:28px;display:flex;align-items:center;justify-content:center;border-radius:6px;transition:all .13s;}
.modal-close:hover{background:rgba(255,255,255,0.03);backdrop-filter:blur(32px);color:var(--text);}
.modal h2{font-family:'Syne',sans-serif;font-size:21px;font-weight:800;letter-spacing:-.03em;margin-bottom:5px;}
.modal p{font-size:12.5px;color:var(--text2);margin-bottom:20px;line-height:1.65;}
.field{margin-bottom:11px;}
.field label{display:block;font-family:'DM Mono',monospace;font-size:10px;color:var(--text3);margin-bottom:5px;letter-spacing:.05em;text-transform:uppercase;}
.field input{width:100%;padding:9px 12px;background:rgba(255,255,255,0.04);backdrop-filter:blur(24px);border:1px solid rgba(255,255,255,0.08);border-radius:8px;font-family:'DM Sans',sans-serif;font-size:13px;color:var(--text);outline:none;transition:border-color .15s,box-shadow .15s;box-shadow:inset 0 1px 0 rgba(255,255,255,0.08);}
.field input:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(0,229,160,0.15);}
.field input::placeholder{color:var(--text3);}
.modal-submit{width:100%;padding:11px;background:linear-gradient(135deg,var(--accent),var(--accent2));border:none;border-radius:9px;font-family:'Syne',sans-serif;font-size:14px;font-weight:700;color:#000;cursor:pointer;margin-top:4px;transition:all .17s;box-shadow:0 0 18px var(--glow);}
.modal-submit:hover{box-shadow:0 0 28px var(--glow);transform:translateY(-1px);}
.modal-toggle{text-align:center;margin-top:13px;font-size:12px;color:var(--text3);}
.modal-toggle button{background:none;border:none;cursor:pointer;color:var(--accent);font-family:'DM Sans',sans-serif;font-size:12px;font-weight:600;text-decoration:underline;}

/* ── LIGHTBOX ── */
.lightbox-overlay{position:fixed;inset:0;background:rgba(0,0,0,.92);backdrop-filter:blur(24px);z-index:200;display:flex;align-items:center;justify-content:center;animation:fadeIn .2s ease;cursor:zoom-out;}
.lightbox-img{max-width:90vw;max-height:88vh;border-radius:10px;box-shadow:0 24px 72px rgba(0,0,0,.7);}
.lightbox-close{position:fixed;top:15px;right:15px;background:rgba(255,255,255,.1);border:none;color:#fff;width:36px;height:36px;border-radius:50%;font-size:18px;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:background .14s;}
.lightbox-close:hover{background:rgba(255,255,255,.2);}

  .theme-btn {
    background: transparent;
    border: none;
    font-size: 18px;
    cursor: pointer;
    color: inherit;
    display:flex;
    align-items:center;
    justify-content:center;
  }
@media(max-width:960px){.two-col-grid{grid-template-columns:1fr;}.three-col-grid{grid-template-columns:1fr 1fr;}.live-feed-panel{display:none;}}
@media(max-width:720px){.kpi-strip{grid-template-columns:1fr 1fr;}.suggestions{grid-template-columns:1fr;}.chat-area{padding:40px 12px 120px; margin: 20px auto 120px;}.input-zone{padding:0 12px;bottom:16px;}.status-pill{display:none;}.bubble{max-width:88%;}.sidebar{margin:10px;}}
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
const SEEDED_HISTORY = [
  { id: "seed-1", title: "Why did UPI fail rate double on Tue?", time: "Yesterday" },
  { id: "seed-2", title: "Top merchants by QoQ GMV growth", time: "Feb 17" },
  { id: "seed-3", title: "Fraud cluster analysis — Week 6", time: "Feb 16" },
];

const DEMO_ANSWERS = [
  "Today's GMV breakdown: UPI leads at ₹2.31M (48%), Cards ₹1.54M (32%), Wallets ₹578K (12%), BNPL ₹386K (8%). UPI adoption grew 22% YoY — strong signal to prioritise UPI checkout optimisation.",
  "Highest fraud rates this week: Electronics (2.4%), International Fashion (1.8%), Luxury Goods (1.6%). Card-not-present transactions account for 78% of flagged cases. Recommend enabling 3DS2 for these categories immediately.",
  "Tuesday's failure spike (14.2% vs 4.1% baseline, 14:00–16:30 IST) traced to a payment gateway timeout on the HDFC corridor. 83% of failures were UPI. Estimated ₹2.1M revenue impact.",
  "Top 5 merchants by QoQ GMV growth: Meesho +67%, Nykaa +41%, Zepto +38%, Blinkit +35%, CRED +29%. Common thread: D2C and quick-commerce dominate.",
];
let demoIdx = 0;

const makeDemoChart = (text: string): ChartDataItem[] | undefined => {
  const t = text.toLowerCase();
  if (t.includes("merchant") || t.includes("growth")) return [{ label: "Meesho", value: 67 }, { label: "Nykaa", value: 41 }, { label: "Zepto", value: 38 }, { label: "Blinkit", value: 35 }, { label: "CRED", value: 29 }];
  if (t.includes("fail") || t.includes("success") || t.includes("rate")) return [{ label: "Success", value: 97.6 }, { label: "Failed", value: 2.4, color: "danger" }];
  if (t.includes("upi") || t.includes("channel") || t.includes("revenue")) return [{ label: "UPI", value: 48 }, { label: "Cards", value: 32 }, { label: "Wallet", value: 12, color: "amber" }, { label: "BNPL", value: 8 }];
  if (t.includes("fraud") || t.includes("risk") || t.includes("hotspot")) return [{ label: "Electronics", value: 2.4, color: "danger" }, { label: "Int'l Fashion", value: 1.8, color: "danger" }, { label: "Luxury", value: 1.6, color: "danger" }, { label: "Grocery", value: 0.3 }, { label: "Food", value: 0.2 }];
  return undefined;
};

const TXN_DATA = [
  { id: "TXN-8821", merchant: "Flipkart", amount: "₹12,840", method: "UPI", status: "success", time: "09:14 IST", risk: "low" },
  { id: "TXN-8820", merchant: "PhonePe", amount: "₹34,500", method: "NEFT", status: "flagged", time: "09:13 IST", risk: "high" },
  { id: "TXN-8819", merchant: "Myntra", amount: "₹1,899", method: "Wallet", status: "failed", time: "09:13 IST", risk: "medium" },
  { id: "TXN-8818", merchant: "Swiggy", amount: "₹349", method: "Card", status: "success", time: "09:12 IST", risk: "low" },
  { id: "TXN-8817", merchant: "Amazon IN", amount: "₹5,299", method: "UPI", status: "success", time: "09:11 IST", risk: "low" },
  { id: "TXN-8816", merchant: "BigBasket", amount: "₹2,310", method: "UPI", status: "failed", time: "09:11 IST", risk: "medium" },
  { id: "TXN-8815", merchant: "Nykaa", amount: "₹3,780", method: "Card", status: "success", time: "09:10 IST", risk: "low" },
  { id: "TXN-8814", merchant: "Zomato", amount: "₹218", method: "UPI", status: "success", time: "09:09 IST", risk: "low" },
];

const MERCHANT_DATA = [
  { name: "Flipkart", gmv: "₹8.42M", txns: "3,821", success: "98.2%", avg: "₹2,203", growth: "+14%", risk: "low" },
  { name: "Amazon IN", gmv: "₹6.91M", txns: "2,940", success: "99.1%", avg: "₹2,350", growth: "+8%", risk: "low" },
  { name: "Swiggy", gmv: "₹2.31M", txns: "9,102", success: "97.8%", avg: "₹254", growth: "+23%", risk: "low" },
  { name: "Meesho", gmv: "₹1.89M", txns: "4,210", success: "96.1%", avg: "₹449", growth: "+67%", risk: "medium" },
  { name: "Myntra", gmv: "₹1.74M", txns: "1,820", success: "93.4%", avg: "₹956", growth: "+11%", risk: "medium" },
  { name: "Nykaa", gmv: "₹1.42M", txns: "1,560", success: "97.9%", avg: "₹910", growth: "+41%", risk: "low" },
  { name: "Zomato", gmv: "₹890K", txns: "7,430", success: "98.6%", avg: "₹120", growth: "+19%", risk: "low" },
  { name: "JioMart", gmv: "₹640K", txns: "2,190", success: "91.8%", avg: "₹292", growth: "+9%", risk: "high" },
];

const RISK_ITEMS = [
  { id: "FG-291", type: "Fraud Cluster", severity: "critical", merchant: "PhonePe", amount: "₹34,500", detail: "Matches known fraud cluster — NEFT velocity attack pattern", time: "43s ago" },
  { id: "FG-290", type: "Card Decline", severity: "critical", merchant: "Myntra", amount: "₹1,899", detail: "Decline rate 6.2% — 3× baseline. Wallet fallback not triggering.", time: "7s ago" },
  { id: "FG-289", type: "UPI Latency", severity: "warning", merchant: "NPCI Corridor", amount: "—", detail: "P95 response 1.8s (+240ms). Monitoring — no SLA breach yet.", time: "2m ago" },
  { id: "FG-288", type: "Settlement Delay", severity: "warning", merchant: "BigBasket", amount: "₹6,841", detail: "3 transactions pending >2h. Auto-retry queued.", time: "4m ago" },
];

const REPORTS_DATA = [
  { icon: "📊", title: "Monthly Payment Performance", desc: "Full GMV, success rate, failure analysis and gateway comparison for February 2026.", tag: "MONTHLY", date: "Feb 18, 2026", size: "2.4 MB" },
  { icon: "🛡️", title: "Fraud & Risk Summary — Week 7", desc: "Weekly fraud cluster breakdown, flagged transaction inventory, and ML model accuracy metrics.", tag: "WEEKLY", date: "Feb 17, 2026", size: "890 KB" },
  { icon: "🏪", title: "Merchant Health Scorecard", desc: "Tier-1 and Tier-2 merchant performance ranking by GMV, success rate and chargeback ratio.", tag: "MONTHLY", date: "Feb 15, 2026", size: "1.1 MB" },
  { icon: "💳", title: "Payment Method Distribution", desc: "UPI vs Card vs Wallet vs BNPL share analysis with YoY trend and conversion funnel.", tag: "WEEKLY", date: "Feb 14, 2026", size: "740 KB" },
];

const fmtTime = (d: Date): string => d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

// ── Sub-components ──

const ResponseChart: FC<{ data: ChartDataItem[] }> = ({ data }) => {
  const [animated, setAnimated] = useState(false);
  const max = Math.max(...data.map((d: ChartDataItem) => d.value), 1);
  useEffect(() => { const t = setTimeout(() => setAnimated(true), 100); return () => clearTimeout(t); }, []);
  return (
    <div className="response-chart">
      <div className="chart-title">▸ DATA VISUALIZATION</div>
      <div className="chart-bars">
        {data.map((bar: ChartDataItem, i: number) => (
          <div className="chart-row" key={i}>
            <div className="chart-label" title={bar.label}>{bar.label}</div>
            <div className="chart-track">
              <div className={`chart-fill${bar.color ? " " + bar.color : ""}`} style={{ width: animated ? `${(bar.value / max) * 100}%` : "0%" }}>
                <span className="chart-val">{bar.value}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// The requested theme toggle logic provides a simpler button inside the topbar.
// We'll replace the existing generic theme button logic with the requested explicit one inside the topbar.

const NarrativeBanner: FC<{ onAsk: (text: string) => void }> = ({ onAsk }) => (
  <div className="narrative-banner" onClick={() => onAsk("Why did our failure rate spike 31% since yesterday? Show me the root cause.")}>
    <div className="nb-left">
      <div className="nb-pulse" />
      <div className="nb-text">
        <strong>⚠ Failure rate spiked +31%</strong> since yesterday — <em>~₹2.1M revenue at risk.</em> InsightX has identified the root cause.
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
      <div className="sample-a-avatar">IX</div>
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
      <div className="panel-card-title"><span>💡</span>Ask InsightX AI</div>
      <div className="suggestions">
        {SUGGESTIONS.map(s => (
          <button key={s.title} className="sug-chip" onClick={() => onSuggestion(s.desc)}>
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
  </div>
);

const TransactionsPage: FC = () => {
  const [search, setSearch] = useState<string>("");
  const [filter, setFilter] = useState<string>("all");
  const filtered = TXN_DATA.filter((t: any) => {
    const ms = t.id.toLowerCase().includes(search.toLowerCase()) || t.merchant.toLowerCase().includes(search.toLowerCase());
    const mf = filter === "all" || t.status === filter;
    return ms && mf;
  });
  return (
    <div className="tab-page">
      <div className="page-header">
        <div>
          <div className="page-title">Transaction Ledger</div>
          <div className="page-subtitle">48,291 transactions today · Real-time feed</div>
        </div>
        <div className="page-actions">
          {["all", "success", "failed", "flagged"].map(f => (
            <button key={f} className={`page-btn${filter === f ? " primary" : ""}`} onClick={() => setFilter(f)}>{f === "all" ? "All" : f.charAt(0).toUpperCase() + f.slice(1)}</button>
          ))}
        </div>
      </div>
      <div className="three-col-grid">
        <div className="kpi-card"><span className="kpi-icon">✅</span><div className="kpi-label">Success</div><div className="kpi-value">47,007</div><div className="kpi-delta up">▲ 97.6%</div></div>
        <div className="kpi-card danger-card"><span className="kpi-icon">❌</span><div className="kpi-label">Failed</div><div className="kpi-value">1,284</div><div className="kpi-delta down">▼ 2.4%</div></div>
        <div className="kpi-card amber-card"><span className="kpi-icon">🚩</span><div className="kpi-label">Flagged / Pending</div><div className="kpi-value">39 / 12</div><div className="kpi-delta neutral">◆ Under review</div></div>
      </div>
      <div className="full-table-wrap">
        <div className="full-table-head">
          <span className="full-table-title">Live Transactions</span>
          <input className="ft-search-input" placeholder="Search TXN ID or merchant…" value={search} onChange={e => setSearch(e.target.value)} />
        </div>
        <div className="data-table-wrap">
          <table className="full-table">
            <thead><tr><th>TXN ID</th><th>Merchant</th><th>Amount</th><th>Method</th><th>Status</th><th>Risk</th><th>Time</th></tr></thead>
            <tbody>
              {filtered.map(t => (
                <tr key={t.id}>
                  <td className="ft-mono">{t.id}</td><td>{t.merchant}</td><td className="ft-mono">{t.amount}</td>
                  <td><span className="ft-badge pending">{t.method}</span></td>
                  <td><span className={`ft-badge ${t.status}`}>{t.status}</span></td>
                  <td><span className={`ft-badge ${t.risk}`}>{t.risk}</span></td>
                  <td className="ft-mono" style={{ color: "var(--text3)" }}>{t.time}</td>
                </tr>
              ))}
              {filtered.length === 0 && <tr><td colSpan={7} style={{ textAlign: "center", color: "var(--text3)", padding: "28px", fontFamily: "'DM Mono',monospace", fontSize: "11px" }}>No transactions match your filter.</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

const MerchantsPage: FC = () => {
  const [search, setSearch] = useState<string>("");
  const filtered = MERCHANT_DATA.filter((m: any) => m.name.toLowerCase().includes(search.toLowerCase()));
  return (
    <div className="tab-page">
      <div className="page-header">
        <div><div className="page-title">Merchant Performance</div><div className="page-subtitle">Top merchants by GMV · Feb 18, 2026</div></div>
        <div className="page-actions"><button className="page-btn">Export CSV</button><button className="page-btn primary">Add Merchant</button></div>
      </div>
      <div className="kpi-strip">
        <div className="kpi-card"><span className="kpi-icon">🏪</span><div className="kpi-label">Active Merchants</div><div className="kpi-value">2,841</div><div className="kpi-delta up">▲ +14 this week</div></div>
        <div className="kpi-card"><span className="kpi-icon">🏆</span><div className="kpi-label">Top Merchant GMV</div><div className="kpi-value">₹8.42M</div><div className="kpi-delta up">▲ Flipkart</div></div>
        <div className="kpi-card amber-card"><span className="kpi-icon">⚠️</span><div className="kpi-label">At-Risk Merchants</div><div className="kpi-value">12</div><div className="kpi-delta neutral">◆ Needs review</div></div>
        <div className="kpi-card"><span className="kpi-icon">📈</span><div className="kpi-label">Fastest Growing</div><div className="kpi-value">Meesho</div><div className="kpi-delta up">▲ +67% QoQ</div></div>
      </div>
      <div className="full-table-wrap">
        <div className="full-table-head">
          <span className="full-table-title">Merchant Directory</span>
          <input className="ft-search-input" placeholder="Search merchants…" value={search} onChange={e => setSearch(e.target.value)} />
        </div>
        <div className="data-table-wrap">
          <table className="full-table">
            <thead><tr><th>Merchant</th><th>GMV Today</th><th>Transactions</th><th>Success Rate</th><th>Avg Ticket</th><th>QoQ Growth</th><th>Risk Level</th></tr></thead>
            <tbody>
              {filtered.map(m => (
                <tr key={m.name}>
                  <td style={{ fontFamily: "'Syne',sans-serif", fontWeight: 700 }}>{m.name}</td>
                  <td className="ft-mono">{m.gmv}</td><td className="ft-mono">{m.txns}</td>
                  <td><span className={`ft-badge ${parseFloat(m.success) >= 97 ? "success" : parseFloat(m.success) >= 93 ? "pending" : "failed"}`}>{m.success}</span></td>
                  <td className="ft-mono">{m.avg}</td>
                  <td style={{ color: m.growth.startsWith("+") ? "var(--accent)" : "var(--danger)", fontFamily: "'DM Mono',monospace", fontWeight: 700 }}>{m.growth}</td>
                  <td><span className={`ft-badge ${m.risk}`}>{m.risk}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

const RiskPage: FC = () => (
  <div className="tab-page">
    <div className="page-header">
      <div><div className="page-title">Risk & Fraud Intelligence</div><div className="page-subtitle">ML-powered · 39 active alerts · Updated 7s ago</div></div>
      <div className="page-actions"><button className="page-btn">Dismiss All</button><button className="page-btn primary">Block Merchant</button></div>
    </div>
    <div className="two-col-grid">
      <div className="panel-card">
        <div className="panel-card-title"><span>🛡️</span>Overall Risk Score</div>
        <div className="gauge-wrap">
          <div className="gauge-score" style={{ color: "var(--amber)" }}>38</div>
          <div className="gauge-label">Risk Index · out of 100</div>
          <div className="gauge-sub">Moderate risk environment. 2 critical alerts active.</div>
        </div>
        <div className="metric-row"><span className="metric-label">Fraud Rate</span><span className="metric-val green">0.08%</span></div>
        <div className="metric-row"><span className="metric-label">Chargeback Rate</span><span className="metric-val">0.32%</span></div>
        <div className="metric-row"><span className="metric-label">ML Model Accuracy</span><span className="metric-val green">97.4%</span></div>
        <div className="metric-row"><span className="metric-label">False Positive Rate</span><span className="metric-val amber">1.8%</span></div>
      </div>
      <div className="panel-card">
        <div className="panel-card-title"><span>📉</span>Fraud by Category</div>
        {[{ label: "Electronics", val: 2.4, color: "red" }, { label: "Int'l Fashion", val: 1.8, color: "red" }, { label: "Luxury Goods", val: 1.6, color: "red" }, { label: "Travel", val: 0.8, color: "amber" }, { label: "Grocery", val: 0.3, color: "" }, { label: "Food Delivery", val: 0.2, color: "" }].map(r => (
          <div className="metric-row" key={r.label}>
            <span className="metric-label">{r.label}</span>
            <span className={`metric-val ${r.color}`}>{r.val}%</span>
          </div>
        ))}
      </div>
    </div>
    <div className="full-table-wrap">
      <div className="full-table-head">
        <span className="full-table-title">Active Risk Alerts</span>
        <span style={{ fontFamily: "'DM Mono',monospace", fontSize: 11, color: "var(--danger)" }}>● LIVE</span>
      </div>
      <div className="data-table-wrap">
        <table className="full-table">
          <thead><tr><th>Alert ID</th><th>Type</th><th>Severity</th><th>Merchant</th><th>Amount</th><th>Detail</th><th>Time</th></tr></thead>
          <tbody>
            {RISK_ITEMS.map(r => (
              <tr key={r.id}>
                <td className="ft-mono">{r.id}</td><td>{r.type}</td>
                <td><span className={`ft-badge ${r.severity === "critical" ? "failed" : r.severity === "warning" ? "medium" : "low"}`}>{r.severity}</span></td>
                <td>{r.merchant}</td><td className="ft-mono">{r.amount}</td>
                <td style={{ maxWidth: 240, fontSize: 11, color: "var(--text2)" }}>{r.detail}</td>
                <td className="ft-mono" style={{ color: "var(--text3)" }}>{r.time}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  </div>
);

const ReportsPage: FC = () => (
  <div className="tab-page">
    <div className="page-header">
      <div><div className="page-title">Reports & Exports</div><div className="page-subtitle">Scheduled reports, on-demand exports, and audit trails</div></div>
      <div className="page-actions"><button className="page-btn">Schedule Report</button><button className="page-btn primary">Generate Custom</button></div>
    </div>
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {REPORTS_DATA.map(r => (
        <div key={r.title} className="report-card">
          <div className="report-icon">{r.icon}</div>
          <div className="report-info">
            <div className="report-title">{r.title}</div>
            <div className="report-desc">{r.desc}</div>
            <div className="report-meta">
              <span className="report-tag">{r.tag}</span>
              <span className="report-date">{r.date} · {r.size}</span>
            </div>
          </div>
          <div className="report-dl">⬇ Download</div>
        </div>
      ))}
    </div>
  </div>
);

// ── Live Feed Page (separate tab) ──
const LiveFeedPage: FC = () => (
  <div className="tab-page">
    <div className="page-header">
      <div>
        <div className="page-title">Live Feed</div>
        <div className="page-subtitle">Real-time transaction stream & active alerts · auto-refreshing</div>
      </div>
      <div className="page-actions">
        <button className="page-btn">Pause Feed</button>
        <button className="page-btn primary">Export Alerts</button>
      </div>
    </div>

    {/* Summary pills */}
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 10 }}>
      <div className="kpi-card danger-card"><span className="kpi-icon">🔴</span><div className="kpi-label">Critical Alerts</div><div className="kpi-value" style={{ fontSize: 24 }}>2</div><div className="kpi-delta down">▼ Immediate action</div></div>
      <div className="kpi-card amber-card"><span className="kpi-icon">🟡</span><div className="kpi-label">Warnings</div><div className="kpi-value" style={{ fontSize: 24 }}>5</div><div className="kpi-delta neutral">◆ Monitoring</div></div>
      <div className="kpi-card"><span className="kpi-icon">✅</span><div className="kpi-label">Success Rate (live)</div><div className="kpi-value">97.6%</div><div className="kpi-delta up">▲ Healthy</div></div>
      <div className="kpi-card"><span className="kpi-icon">⚡</span><div className="kpi-label">TXN Volume / min</div><div className="kpi-value">341</div><div className="kpi-delta up">▲ +8% vs avg</div></div>
    </div>

    {/* Mini volume chart */}
    <div className="panel-card">
      <div className="panel-card-title"><span>📊</span>Transaction Volume — Last 12 Hours</div>
      <div className="mini-chart" style={{ height: 80 }}>
        {CHART_BARS.map((h, i) => (
          <div key={i} className={`mini-bar${i === CHART_BARS.length - 1 ? " hi" : ""}`} style={{ height: `${h}%`, borderRadius: "4px 4px 0 0" }} />
        ))}
      </div>
      <div className="mini-chart-foot"><span>10:00</span><span>Now</span></div>
    </div>

    {/* Active alerts */}
    <div className="full-table-wrap">
      <div className="full-table-head">
        <span className="full-table-title">Active Alerts</span>
        <span style={{ fontFamily: "'DM Mono',monospace", fontSize: 11, color: "var(--danger)", display: "flex", alignItems: "center", gap: 5 }}>
          <span style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--danger)", display: "inline-block", animation: "blink 1.2s infinite" }} />
          LIVE
        </span>
      </div>
      <div style={{ padding: "12px", display: "flex", flexDirection: "column", gap: 8 }}>
        <div className="alert-card">
          <div className="alert-head"><div className="alert-head-left"><span className="alert-icon">🔴</span><span className="alert-title">Fraud Spike — PhonePe</span></div><span className="alert-time">43s ago</span></div>
          <div className="alert-body">₹34,500 NEFT flagged by ML model. Matches fraud cluster #FG-291.</div>
          <div className="alert-impact">⚠ ₹34,500 at risk · immediate action required</div>
          <div className="alert-footer"><span className="alert-tag danger">CRITICAL</span><span className="alert-action">Investigate →</span></div>
        </div>
        <div className="alert-card">
          <div className="alert-head"><div className="alert-head-left"><span className="alert-icon">🔴</span><span className="alert-title">Elevated Declines — Myntra</span></div><span className="alert-time">7s ago</span></div>
          <div className="alert-body">Card decline rate 6.2% — 3× above baseline. Wallet fallback not triggering.</div>
          <div className="alert-impact">⚠ ~₹280K/hr revenue bleed if unresolved</div>
          <div className="alert-footer"><span className="alert-tag danger">CRITICAL</span><span className="alert-action">View Details →</span></div>
        </div>
        <div className="alert-card warn">
          <div className="alert-head"><div className="alert-head-left"><span className="alert-icon">🟡</span><span className="alert-title">UPI Latency Spike</span></div><span className="alert-time">2m ago</span></div>
          <div className="alert-body">P95 response 1.8s (+240ms). Monitoring NPCI corridor — no SLA breach yet.</div>
          <div className="alert-impact warn">◆ Monitor · no revenue impact yet</div>
          <div className="alert-footer"><span className="alert-tag warn">WARNING</span><span className="alert-action">Monitor →</span></div>
        </div>
        <div className="alert-card warn">
          <div className="alert-head"><div className="alert-head-left"><span className="alert-icon">🟡</span><span className="alert-title">Settlement Delay — BigBasket</span></div><span className="alert-time">4m ago</span></div>
          <div className="alert-body">3 transactions pending &gt;2h. Affects ₹6,841. Auto-retry queued.</div>
          <div className="alert-impact warn">◆ ₹6,841 settlement delayed</div>
          <div className="alert-footer"><span className="alert-tag warn">WARNING</span><span className="alert-action">Retry Now →</span></div>
        </div>
      </div>
    </div>
  </div>
);

// ── Sidebar ──
const Sidebar: FC<{ collapsed: boolean; onToggle: () => void; activeHist: string | null; onHistClick: (id: string) => void; onNewChat: () => void; historyItems: HistoryItem[]; onSuggestion: (text: string) => void }> = ({ collapsed, onToggle, activeHist, onHistClick, onNewChat, historyItems, onSuggestion }) => (
  <aside className={`sidebar panel${collapsed ? " collapsed" : ""}`}>
    <div className="sb-head">
      <div className="logo-mark">IX</div>
      {!collapsed && (
        <div className="logo-text">
          <div className="logo-name">Insight<em>X</em></div>
          <div className="logo-tagline">Payments Intelligence</div>
        </div>
      )}
// theme toggle moved
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
      {historyItems.length > 0 && (
        <>
          <div className="hist-label">Recent</div>
          <div className="hist-list">
            {historyItems.map((h: HistoryItem) => (
              <div key={h.id} className={`hist-item${activeHist === h.id ? " active" : ""}`} onClick={() => onHistClick(h.id)} title={h.title}>
                <div className="hist-dot" />
                <div className="hist-info"><div className="hist-title">{h.title}</div><div className="hist-time">{h.time}</div></div>
              </div>
            ))}
          </div>
        </>
      )}
      <div className="sb-seed-label">Try these</div>
      <div className="hist-list">
        {SEEDED_HISTORY.map(h => (
          <div key={h.id} className="hist-item seeded" onClick={() => onSuggestion(h.title)} title={h.title}>
            <div className="hist-dot" />
            <div className="hist-info"><div className="hist-title">{h.title}</div><div className="hist-time">{h.time}</div></div>
          </div>
        ))}
      </div>
    </div>
  </aside>
);

// ── Topbar ──
const NAV_TABS = ["Overview", "Transactions", "Merchants", "Risk", "Reports", "Live Feed"];

const Topbar: FC<{ activeTab: string; onTabChange: (tab: string) => void; onLogin: () => void; onSignup: () => void; theme: string; onThemeToggle: () => void; }> = ({ activeTab, onTabChange, onLogin, onSignup, theme, onThemeToggle }) => (
  <header className="topbar panel">
    <div className="breadcrumb">insightx <span>/</span> <span>{activeTab.toLowerCase().replace(" ", "-")}</span></div>
    <div className="topbar-center">
      {NAV_TABS.map((t: string) => (
        <button key={t} className={`topbar-tab${activeTab === t ? " active" : ""}`} onClick={() => onTabChange(t)}>
          {t}
          {t === "Risk" && <span className="tab-badge">39</span>}
          {t === "Transactions" && <span className="tab-badge amber">12</span>}
          {t === "Live Feed" && <span className="tab-badge">7</span>}
        </button>
      ))}
    </div>
    <div className="topbar-right">
      <div className="status-pill"><div className="status-dot demo" /><span>DEMO</span></div>
      <button
        onClick={onThemeToggle}
        className="theme-btn"
      >
        {theme === 'dark' ? '☀️' : '🌙'}
      </button>
      <button className="auth-btn login-btn" onClick={onLogin}>Log in</button>
      <button className="auth-btn signup-btn" onClick={onSignup}>Sign up</button>
    </div>
  </header>
);

// ── Welcome Screen ──
const WelcomeScreen: FC<{ onSuggestion: (text: string) => void }> = ({ onSuggestion }) => (
  <div className="welcome">
    <h1>Your payments are <span className="hl">losing money</span> right now.</h1>
    <p className="welcome-desc">InsightX tells you exactly why — in plain English, before your analyst opens their laptop. No SQL. No dashboards. Just answers.</p>
    <NarrativeBanner onAsk={onSuggestion} />
    <SampleConvo onAsk={onSuggestion} />
    <div className="suggestions">
      {SUGGESTIONS.map(s => (
        <button key={s.title} className="sug-chip" onClick={() => onSuggestion(s.desc)}>
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
  <motion.div
    className={`msg-row ${message.role}`}
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.3 }}
  >
    <div className={`avatar ${message.role}`}>{message.role === "ai" ? "IX" : "U"}</div>
    <div className={`bubble panel ${message.role}${message.isError ? " error" : ""}`}>
      <div className="bubble-meta">
        <span className="bubble-time">{fmtTime(message.timestamp)}</span>
        <div className="bubble-actions">
          <button className="bubble-action-btn" title="Copy" onClick={() => onCopy(message.text)}>⎘</button>
        </div>
      </div>
      {message.attachments && message.attachments.length > 0 && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 10 }}>
          {message.attachments.map((att: any, i: number) =>
            att.preview
              ? <img key={i} src={att.preview} alt={att.name} style={{ width: 110, height: 75, borderRadius: 8, objectFit: "cover", border: "1px solid var(--border2)", cursor: "pointer" }} onClick={() => onImageClick(att.preview)} />
              : <div key={i} style={{ display: "flex", alignItems: "center", gap: 7, padding: "6px 10px", background: "var(--bg2)", border: "1px solid var(--border2)", borderRadius: 8, fontFamily: "'DM Mono',monospace", fontSize: 11, color: "var(--text2)" }}>
                <span style={{ fontSize: 16 }}>{FILE_ICONS[att.type as keyof typeof FILE_ICONS] || "📎"}</span>
                <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: 140 }}>{att.name}</span>
              </div>
          )}
        </div>
      )}
      {message.text}
      {message.chartData && message.chartData.length > 0 && <ResponseChart data={message.chartData} />}
      {message.role === "ai" && message.confidence && (
        <div className="msg-footer">
          <span className="msg-badge conf">Confidence: {message.confidence}</span>
          {message.sampleSize && <span className="msg-badge samp">{message.sampleSize.toLocaleString()} records</span>}
          {message.execMs && <span className="msg-badge exec">{message.execMs.toFixed(0)}ms</span>}
        </div>
      )}
    </div>
  </motion.div>
);

const TypingIndicator: FC = () => (
  <motion.div
    className="msg-row ai"
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.3 }}
  >
    <div className="avatar ai">IX</div><div className="bubble panel ai"><div className="typing"><span /><span /><span /></div></div>
  </motion.div>
);

// ── Input Bar ──
const ATTACH_MENU_ITEMS = [
  { icon: "🖼️", label: "Image", sub: "PNG, JPG, WEBP, GIF", accept: "image/*" },
  { icon: "📄", label: "PDF", sub: "Any PDF document", accept: "application/pdf" },
  { icon: "📊", label: "Spreadsheet", sub: "CSV, XLS, XLSX", accept: ".csv,.xls,.xlsx" },
  { icon: "📝", label: "Document", sub: "DOC, DOCX, TXT", accept: ".doc,.docx,.txt" },
  { icon: "📎", label: "Any File", sub: "All file types", accept: "*" },
];

const InputBar: FC<{ input: string; isTyping: boolean; attachedFiles: FileAttachment[]; onChange: (e: ChangeEvent<HTMLTextAreaElement>) => void; onKeyDown: (e: KeyboardEvent<HTMLTextAreaElement>) => void; onSend: () => void; onFilesAttach: (files: File[]) => void; onRemoveAttach: (id: string) => void; textareaRef: React.RefObject<HTMLTextAreaElement>; sidebarCollapsed: boolean }> = ({ input, isTyping, attachedFiles, onChange, onKeyDown, onSend, onFilesAttach, onRemoveAttach, textareaRef, sidebarCollapsed }) => {
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
    <div className="input-zone" style={{ left: `calc(50% + ${window.innerWidth > 720 ? (sidebarCollapsed ? 28 : 130) : 0}px)` }}>
      <div className="input-label">Ask InsightX AI anything about your payments</div>
      <div className="input-shell-wrap">
        <div
          className={`input-shell panel${dragOver ? " drag-over" : ""}`}
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
              placeholder={attachedFiles.length > 0 ? "Add context… (optional)" : "e.g. Why did failure rates spike on Tuesday? Which merchants are at risk?"}
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
                <button
                  className={`attach-btn${attachedFiles.length > 0 ? " has-files" : ""}${menuOpen ? " active" : ""}`}
                  onClick={() => setMenuOpen(o => !o)}
                  title="Attach files"
                >
                  {attachedFiles.length > 0 && <span className="attach-badge">{attachedFiles.length}</span>}
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
                  </svg>
                </button>
              </div>
              <button className="send-btn" onClick={onSend} disabled={!canSend}>
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="12" y1="19" x2="12" y2="5" /><polyline points="5 12 12 5 19 12" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
      <input ref={fileInputRef} type="file" multiple style={{ display: "none" }} onChange={handleFileChange} />
      <div className="input-footer">
        <span>Drag & drop files to attach</span>
        <div className="input-footer-right"><span><kbd>↵</kbd> Send</span><span><kbd>⇧↵</kbd> Newline</span></div>
      </div>
    </div>
  );
};

// ── Auth Modal ──
const AuthModal: FC<{ mode: string; onClose: () => void; onToggleMode: () => void }> = ({ mode, onClose, onToggleMode }) => (
  <div className="modal-overlay" onClick={onClose}>
    <div className="modal" onClick={e => e.stopPropagation()}>
      <button className="modal-close" onClick={onClose}>✕</button>
      <h2>{mode === "login" ? "Welcome back" : "Create account"}</h2>
      <p>{mode === "login" ? "Log in to your InsightX workspace." : "Start making smarter payment decisions."}</p>
      {mode === "signup" && <div className="field"><label>Full Name</label><input type="text" placeholder="Jane Doe" /></div>}
      <div className="field"><label>Work Email</label><input type="email" placeholder="jane@company.com" /></div>
      <div className="field"><label>Password</label><input type="password" placeholder="••••••••" /></div>
      <button className="modal-submit">{mode === "login" ? "Log in →" : "Create account →"}</button>
      <div className="modal-toggle">{mode === "login" ? "Don't have an account? " : "Already have an account? "}<button onClick={onToggleMode}>{mode === "login" ? "Sign up" : "Log in"}</button></div>
    </div>
  </div>
);

const CopyToast: FC<{ show: boolean }> = ({ show }) => <div className={`copy-toast${show ? " show" : ""}`}>✓ Copied to clipboard</div>;

// ── Root App ──
export default function InsightX() {
  const [collapsed, setCollapsed] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<string>("Overview");
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

  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const copyTimer = useRef<NodeJS.Timeout | undefined>(undefined);

  const [theme, setTheme] = useState<'dark' | 'light'>('dark');

  useEffect(() => {
    document.documentElement.classList.remove('dark', 'light');
    document.documentElement.classList.add(theme);
    localStorage.setItem("ix-theme", theme);
  }, [theme]);

  // Initial load
  useEffect(() => {
    const s = localStorage.getItem("ix-theme");
    if (s === "light" || s === "dark") setTheme(s);
  }, []);

  const toggleTheme = () => {
    setTheme(theme === "light" ? "dark" : "light");
  };

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, isTyping]);

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
    setActiveTab("Overview");
    sendMessage(text);
  };

  const sendMessage = async (text: string): Promise<void> => {
    const hasAtt = attachedFiles.length > 0;
    if ((!text.trim() && !hasAtt) || isTyping) return;
    const attachmentMeta = attachedFiles.map((af: FileAttachment) => ({ name: af.file.name, type: af.type, preview: af.preview }));
    const displayText = text.trim() || `[Attached ${attachedFiles.length} file${attachedFiles.length > 1 ? "s" : ""}]`;
    const userMsg: Message = { id: Date.now() + "u", role: "user", text: displayText, timestamp: new Date(), attachments: attachmentMeta.length > 0 ? attachmentMeta : undefined };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setAttachedFiles([]);
    if (textareaRef.current) textareaRef.current.style.height = "auto";
    setIsTyping(true);
    setActiveTab("Overview");
    try {
      await new Promise(r => setTimeout(r, 800 + Math.random() * 600));
      const prefix = hasAtt ? `Received ${attachedFiles.length} file(s). Demo: ` : "";
      const aiMsg: Message = { id: Date.now() + "a", role: "ai", text: prefix + DEMO_ANSWERS[demoIdx++ % DEMO_ANSWERS.length], timestamp: new Date(), confidence: "HIGH (0.91)", sampleSize: 248500, execMs: 42, chartData: makeDemoChart(text) };
      setMessages(prev => [...prev, aiMsg]);
      const entry: HistoryItem = { id: Date.now().toString(), title: (text.trim() || (attachmentMeta[0]?.name ?? "File")).slice(0, 38), time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) };
      setHistoryItems(prev => [entry, ...prev.slice(0, 14)]);
      setActiveHist(entry.id);
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : "Something went wrong.";
      setMessages(prev => [...prev, { id: Date.now() + "e", role: "ai", isError: true, timestamp: new Date(), text: `⚠ ${errorMsg}` }]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleNewChat = () => {
    setMessages([]); setActiveHist(null); setAttachedFiles([]); setActiveTab("Overview");
  };

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
      <div className="app-shell">
        <Particles
          particleCount={200}
          particleSpread={10}
          speed={0.1}
          particleColors={["#0011ff", "#09f505", "#FF0000"]}
          moveParticlesOnHover={false}
          particleHoverFactor={1}
          alphaParticles={false}
          particleBaseSize={100}
          sizeRandomness={1}
          cameraDistance={20}
          disableRotation={false}
          className="particles-bg"
        />
        <Sidebar
          collapsed={collapsed}
          onToggle={() => setCollapsed(c => !c)}
          activeHist={activeHist}
          onHistClick={(id: string) => setActiveHist(id)}
          onNewChat={handleNewChat}
          historyItems={historyItems}
          onSuggestion={handleSuggestion}
        />
        <div className="content-wrapper">
          <Topbar activeTab={activeTab} onTabChange={setActiveTab} onLogin={() => { setAuthMode("login"); setModal("auth"); }} onSignup={() => { setAuthMode("signup"); setModal("auth"); }} theme={theme} onThemeToggle={toggleTheme} />
          <div className="tab-view">
            {activeTab === "Overview" && (
              <>
                <div className="chat-section">
                  {messages.length === 0 && !isTyping ? (
                    <div className="chat-area">
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
                </div>
                <InputBar input={input} isTyping={isTyping} attachedFiles={attachedFiles} onChange={(e: ChangeEvent<HTMLTextAreaElement>) => { setInput(e.target.value); autoResize(); }} onKeyDown={(e: KeyboardEvent<HTMLTextAreaElement>) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(input); } }} onSend={() => sendMessage(input)} onFilesAttach={handleFilesAttach} onRemoveAttach={handleRemoveAttach} textareaRef={textareaRef as React.RefObject<HTMLTextAreaElement>} sidebarCollapsed={collapsed} />
              </>
            )}
            {activeTab === "Transactions" && <TransactionsPage />}
            {activeTab === "Merchants" && <MerchantsPage />}
            {activeTab === "Risk" && <RiskPage />}
            {activeTab === "Reports" && <ReportsPage />}
            {activeTab === "Live Feed" && <LiveFeedPage />}
          </div>
        </div>
        {modal === "auth" && <AuthModal mode={authMode} onClose={() => setModal(null)} onToggleMode={() => setAuthMode(m => m === "login" ? "signup" : "login")} />}
      </div>
    </>
  );
}