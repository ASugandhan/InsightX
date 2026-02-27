# NEXUS Frontend — Redesign & Animation Changes

## Overview

This document describes all required frontend changes to the NEXUS Payments Intelligence chat UI. Changes span: global theme/color, intro animation sequence, text animations, UX improvements (stop button), and font/hover gradient consistency.

---

## 1. Global Theme — Background & Gradient

### Background
- **Current:** Very dark, near-black background (`#050a1a` range).
- **Required:** Brighten the background. Use a deep navy/dark-blue that is noticeably lighter — something in the range of `#0a1628` to `#0d1f3c`. The background should feel "space-blue" rather than pure black.
- Apply this as a CSS gradient across the full page:
```css
background: linear-gradient(135deg, #0a1628 0%, #0d1a3a 40%, #091530 100%);
```

### Text Gradient
- **Required:** ALL prominent/display text (headings, brand name, section labels) should use a gradient that **matches the background gradient palette** — blues and teals:
```css
background: linear-gradient(135deg, #3B82F6, #1DD1EE, #63DEF9);
-webkit-background-clip: text;
-webkit-text-fill-color: transparent;
background-clip: text;
```
- Apply this gradient text style to: "Hi, I'm NEXUS.", section card labels (REVENUE, RISK, OPS, GROWTH), and any other accent text currently in teal/cyan.

### Font & Hover Animations — Unified Gradient Theme
- **ALL hover states** on interactive elements (cards, buttons, links, nav items) should animate to/from the same blue-teal gradient palette.
- Hover glow/border effects should use: `rgba(59,130,246,0.5)` to `rgba(29,209,238,0.5)`.
- Example for card hover:
```css
.card:hover {
  border-color: rgba(59,130,246,0.6);
  box-shadow: 0 0 24px rgba(29,209,238,0.15);
}
```
- Button hover states should shift background to a gradient: `linear-gradient(135deg, #1D4ED8, #0ea5e9)`.

---

## 2. Logo Replacement

Replace the existing NEXUS logo with the new animated logo component below. This logo is used in **two places**:
1. The top-left sidebar header.
2. The **intro loading/splash screen** (centered, larger version).

### New Logo Component

Create a file `NexusLogo.tsx` (or `.jsx`) and paste the following code **exactly**:

```tsx
import React from "react";

const nexusStyles = `
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&display=swap');

.nexus-card {
  position: relative;
  background: linear-gradient(135deg, #050a1a 0%, #080d2e 50%, #050c1f 100%);
  border: 1px solid rgba(59,130,246,0.28);
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 0 0 1px rgba(59,130,246,0.08), 0 20px 60px rgba(0,0,0,0.65), 0 0 80px rgba(29,78,216,0.07) inset;
  animation: cardReveal 0.6s cubic-bezier(0.16,1,0.3,1) both;
}
@keyframes cardReveal {
  from { opacity: 0; transform: scale(0.9) translateY(16px); }
  to   { opacity: 1; transform: scale(1) translateY(0); }
}
.nexus-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 220px 160px at 18% 50%, rgba(29,78,216,0.15) 0%, transparent 70%),
    radial-gradient(ellipse 180px 140px at 88% 50%, rgba(59,130,246,0.10) 0%, transparent 70%);
  animation: meshMove 8s ease-in-out infinite alternate;
  pointer-events: none;
  z-index: 0;
}
@keyframes meshMove {
  from { opacity: 0.7; transform: scale(1); }
  to   { opacity: 1; transform: scale(1.06) translateX(8px); }
}
.nexus-card::after {
  content: '';
  position: absolute;
  inset: 0;
  background-image: radial-gradient(circle, rgba(59,130,246,0.16) 1px, transparent 1px);
  background-size: 22px 22px;
  pointer-events: none;
  border-radius: 20px;
  z-index: 0;
}
.nexus-accent-bar {
  position: absolute;
  bottom: 0; left: 12%; right: 12%;
  height: 2px;
  background: linear-gradient(90deg, transparent, #1D4ED8, #3B82F6, transparent);
  border-radius: 2px;
  animation: barGlow 3s ease-in-out infinite 3s;
  z-index: 2;
}
@keyframes barGlow {
  0%,100% { opacity: 0.35; filter: blur(0px); }
  50%      { opacity: 1;    filter: blur(1px); }
}
.nexus-ar { fill: none; stroke: rgba(59,130,246,0.18); stroke-width: 0.7; animation: arPulse 3.2s ease-in-out infinite; transform-origin: 90px 90px; }
.nexus-ar:nth-child(2) { animation-delay: 1.1s; }
.nexus-ar:nth-child(3) { animation-delay: 2.2s; }
@keyframes arPulse {
  0%,100% { transform: scale(1);    opacity: 0.7; }
  50%      { transform: scale(1.14); opacity: 0;   }
}
.nexus-hb { animation: hFloat 5.5s ease-in-out infinite, hReveal 0.9s 0.9s cubic-bezier(0.34,1.56,0.64,1) both; transform-origin: 90px 90px; }
@keyframes hFloat {
  0%,100% { transform: translateY(0) scale(1);     }
  50%      { transform: translateY(-3px) scale(1.014); }
}
@keyframes hReveal {
  from { transform: scale(0) rotate(-30deg); opacity: 0; }
  to   { transform: scale(1) rotate(0deg);   opacity: 1; }
}
.nexus-hsh { animation: hSpin 9s linear infinite; transform-origin: 90px 90px; }
@keyframes hSpin {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}
.nexus-cl { stroke-dasharray: 60; stroke-dashoffset: 60; animation: drawL 0.45s ease-out forwards; }
.nexus-cl:nth-child(1) { animation-delay: 0.15s; }
.nexus-cl:nth-child(2) { animation-delay: 0.28s; }
.nexus-cl:nth-child(3) { animation-delay: 0.41s; }
.nexus-cl:nth-child(4) { animation-delay: 0.54s; }
.nexus-cl:nth-child(5) { animation-delay: 0.67s; }
.nexus-cl:nth-child(6) { animation-delay: 0.80s; }
@keyframes drawL { to { stroke-dashoffset: 0; } }
.nexus-no { animation: nReveal 0.48s cubic-bezier(0.34,1.56,0.64,1) both, nPulse 3s ease-in-out infinite; }
.nexus-no:nth-child(1) { animation-delay: 0.05s, 2.0s; transform-origin: 90px  32px; }
.nexus-no:nth-child(2) { animation-delay: 0.15s, 2.2s; transform-origin: 140px 61px; }
.nexus-no:nth-child(3) { animation-delay: 0.25s, 2.4s; transform-origin: 140px 119px; }
.nexus-no:nth-child(4) { animation-delay: 0.35s, 2.6s; transform-origin: 90px  148px; }
.nexus-no:nth-child(5) { animation-delay: 0.45s, 2.8s; transform-origin: 40px  119px; }
.nexus-no:nth-child(6) { animation-delay: 0.55s, 3.0s; transform-origin: 40px  61px;  }
@keyframes nReveal {
  from { transform: scale(0); opacity: 0; }
  to   { transform: scale(1); opacity: 1; }
}
@keyframes nPulse {
  0%,100% { transform: scale(1);   filter: drop-shadow(0 0 5px  rgba(29,209,238,0.85)); }
  50%      { transform: scale(1.3); filter: drop-shadow(0 0 12px rgba(99,222,249,1));    }
}
.nexus-nr { fill: none; stroke: #63DEF9; stroke-width: 0.8; opacity: 0; animation: nRipple 3s ease-out infinite; }
.nexus-nr:nth-child(1) { animation-delay: 2.0s; }
.nexus-nr:nth-child(2) { animation-delay: 2.2s; }
.nexus-nr:nth-child(3) { animation-delay: 2.4s; }
.nexus-nr:nth-child(4) { animation-delay: 2.6s; }
.nexus-nr:nth-child(5) { animation-delay: 2.8s; }
.nexus-nr:nth-child(6) { animation-delay: 3.0s; }
@keyframes nRipple {
  0%   { r: 8;  opacity: 0.9; }
  100% { r: 22; opacity: 0;   }
}
.nexus-cd { animation: cdPulse 2.2s ease-in-out infinite 1.8s; transform-origin: 90px 90px; }
@keyframes cdPulse {
  0%,100% { transform: scale(1);    opacity: 0.9; }
  50%      { transform: scale(1.65); opacity: 0.3; }
}
.nexus-fd { r: 2.2; fill: #63DEF9; filter: drop-shadow(0 0 3px #1DD1EE); opacity: 0.95; }
`;

const NexusLogo: React.FC<{ size?: number }> = ({ size = 180 }) => {
  return (
    <>
      <style>{nexusStyles}</style>
      <div className="nexus-card" style={{ width: size, height: size, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <svg width={size * 0.8} height={size * 0.8} viewBox="0 0 180 180" fill="none" xmlns="http://www.w3.org/2000/svg">
          {/* Ambient rings */}
          <circle className="nexus-ar" cx="90" cy="90" r="72" />
          <circle className="nexus-ar" cx="90" cy="90" r="58" />
          <circle className="nexus-ar" cx="90" cy="90" r="44" />

          {/* Node ripple rings */}
          <circle className="nexus-nr" cx="90"  cy="32"  r="8" />
          <circle className="nexus-nr" cx="140" cy="61"  r="8" />
          <circle className="nexus-nr" cx="140" cy="119" r="8" />
          <circle className="nexus-nr" cx="90"  cy="148" r="8" />
          <circle className="nexus-nr" cx="40"  cy="119" r="8" />
          <circle className="nexus-nr" cx="40"  cy="61"  r="8" />

          {/* Connection lines */}
          <g stroke="#3B82F6" strokeWidth="0.9" opacity="0.35">
            <line className="nexus-cl" x1="90"  y1="32"  x2="140" y2="61"  />
            <line className="nexus-cl" x1="140" y1="61"  x2="140" y2="119" />
            <line className="nexus-cl" x1="140" y1="119" x2="90"  y2="148" />
            <line className="nexus-cl" x1="90"  y1="148" x2="40"  y2="119" />
            <line className="nexus-cl" x1="40"  y1="119" x2="40"  y2="61"  />
            <line className="nexus-cl" x1="40"  y1="61"  x2="90"  y2="32"  />
          </g>

          {/* Hex glow blob */}
          <ellipse className="nexus-cd" cx="90" cy="90" rx="22" ry="22" fill="rgba(29,209,238,0.08)" />

          {/* Hex body */}
          <g className="nexus-hb">
            <polygon className="nexus-hsh"
              points="90,68 108,79 108,101 90,112 72,101 72,79"
              fill="none" stroke="rgba(59,130,246,0.22)" strokeWidth="0.8"
            />
            <polygon
              points="90,72 105,81 105,99 90,108 75,99 75,81"
              fill="rgba(29,78,216,0.18)"
              stroke="rgba(99,222,249,0.55)" strokeWidth="1.1"
            />
            {/* Gloss */}
            <ellipse cx="86" cy="82" rx="7" ry="4"
              fill="rgba(255,255,255,0.06)" transform="rotate(-20,86,82)"
            />
            {/* Shimmer */}
            <line x1="78" y1="84" x2="102" y2="84"
              stroke="rgba(99,222,249,0.10)" strokeWidth="0.5"
            />
            {/* Border */}
            <polygon
              points="90,70 107,80 107,100 90,110 73,100 73,80"
              fill="none" stroke="rgba(59,130,246,0.18)" strokeWidth="0.5"
            />
            {/* Inner ring */}
            <circle cx="90" cy="90" r="8"
              fill="none" stroke="rgba(99,222,249,0.3)" strokeWidth="0.7"
            />
            {/* Center dot */}
            <circle cx="90" cy="90" r="2.8"
              fill="#63DEF9"
              filter="url(#fdGlow)"
            />
          </g>

          {/* Nodes */}
          <circle className="nexus-no" cx="90"  cy="32"  r="4.5" fill="#1D4ED8" stroke="#63DEF9" strokeWidth="1.2" />
          <circle className="nexus-no" cx="140" cy="61"  r="4.5" fill="#1D4ED8" stroke="#63DEF9" strokeWidth="1.2" />
          <circle className="nexus-no" cx="140" cy="119" r="4.5" fill="#1D4ED8" stroke="#63DEF9" strokeWidth="1.2" />
          <circle className="nexus-no" cx="90"  cy="148" r="4.5" fill="#1D4ED8" stroke="#63DEF9" strokeWidth="1.2" />
          <circle className="nexus-no" cx="40"  cy="119" r="4.5" fill="#1D4ED8" stroke="#63DEF9" strokeWidth="1.2" />
          <circle className="nexus-no" cx="40"  cy="61"  r="4.5" fill="#1D4ED8" stroke="#63DEF9" strokeWidth="1.2" />

          {/* Flow dots */}
          <circle className="nexus-fd" cx="115" cy="69" />
          <circle className="nexus-fd" cx="65"  cy="111" style={{ animationDelay: '1.1s' }} />

          <defs>
            <filter id="fdGlow" x="-100%" y="-100%" width="300%" height="300%">
              <feGaussianBlur stdDeviation="2" result="blur" />
              <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
            </filter>
          </defs>
        </svg>
        <div className="nexus-accent-bar" />
      </div>
    </>
  );
};

export default NexusLogo;
```

**Usage:**
- In the sidebar: `<NexusLogo size={48} />` (small, no card wrapper needed — strip the card div for sidebar use, just use the SVG portion).
- In the splash screen: `<NexusLogo size={220} />` (large, centered).

---

## 3. Intro Animation Sequence

Implement a full-screen intro/splash that plays **once on first load** then transitions to the main app. The sequence must be:

### Phase 1 — Logo Splash (0s → ~2.5s)
- Full-screen dark overlay (same background gradient as global theme).
- Centered `<NexusLogo size={220} />` with its built-in `cardReveal` animation.
- Below the logo, show a subtle pulsing loading indicator (3 dots or a thin progress bar in the blue-teal gradient).

### Phase 2 — Fade Out Logo, Fade In Chat UI (~2.5s → ~3.5s)
- Logo and overlay fade out (`opacity: 0`, `transition: opacity 0.8s ease`).
- Simultaneously, the **sidebar + chatbox** fade in from `opacity: 0` to `opacity: 1` with `translateY(20px)` → `translateY(0)` (`transition: all 0.8s ease`).

### Phase 3 — Typing Animation in Chatbox Placeholder (~3.5s → ~5s)
- Once the chatbox is visible, the input placeholder should cycle through the example prompts using a **typewriter/cursor animation** (from [React Bits](https://reactbits.dev)).
- The prompts to cycle through:
  1. `"Why did failure rates spike on Tuesday between 2–4 PM IST?"`
  2. `"Which merchants are at highest fraud risk this week?"`
  3. `"Break down today's GMV by UPI, cards, wallets and BNPL"`
  4. `"Show top 10 merchants by GMV growth quarter-over-quarter"`
- Use the **Typewriter** or **RotatingText** component from React Bits. The text should type out, pause 2s, then delete and type the next one — looping indefinitely.
- Style the placeholder/cycling text in the same blue-teal gradient as the theme.

### Phase 4 — Intro Text Block (~3.5s → ~7s, then fade out)
- After the chat UI fades in, display a centered text block **over** the main content area (above the prompt cards):
```
Hi, I'm NEXUS.
Your AI chatbot for payment analytics and transaction intelligence.
Real-time insights, Clear explanations, Instant answers.
```
- Use the **SplitText** animation from [React Bits](https://reactbits.dev) — each word or character animates in one-by-one.
- "Hi, I'm NEXUS." should render in the blue-teal gradient text style.
- After the full text has appeared and held for ~2s, it should **fade out smoothly** (`opacity: 0`, `transition: opacity 0.7s ease`).

### Phase 5 — Final State (after ~7s)
- Show only the elements visible in **Image 3** (the final UI state):
  - The alert banner: "⚠ Failure rate spiked +31% since yesterday — ~₹2.1M revenue at risk. NEXUS has identified the root cause. **Ask why →**"
  - The 4 prompt cards: Revenue by channel, Fraud hotspots, Failure root cause, Top merchant performance.
  - The chatbox at the bottom.
  - The sidebar with history.
- These elements should already be rendered in the DOM but hidden (`opacity: 0`) during the intro phases, then revealed as the intro text fades out.

---

## 4. Stop Button (Cancel Generation)

When the AI is generating a response:
- **Replace** the send/submit button (↑ arrow) with a **Stop button**.
- The Stop button should be a square with rounded corners, showing a filled square "■" icon (standard stop icon).
- It should be styled with the same gradient border/glow as other interactive elements.
- Clicking it cancels the in-progress stream/generation and restores the send button.
- Implementation: toggle button state based on `isGenerating` boolean. Example:

```tsx
{isGenerating ? (
  <button
    onClick={handleStop}
    className="stop-btn"
    aria-label="Stop generation"
  >
    <svg width="16" height="16" viewBox="0 0 16 16">
      <rect x="3" y="3" width="10" height="10" rx="1.5" fill="currentColor" />
    </svg>
  </button>
) : (
  <button
    onClick={handleSend}
    className="send-btn"
    aria-label="Send message"
  >
    <svg .../>  {/* existing send arrow */}
  </button>
)}
```

- Style the stop button consistently:
```css
.stop-btn {
  background: linear-gradient(135deg, #1D4ED8, #0ea5e9);
  border: 1px solid rgba(99,222,249,0.4);
  border-radius: 8px;
  color: white;
  width: 36px; height: 36px;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer;
  transition: box-shadow 0.2s;
}
.stop-btn:hover {
  box-shadow: 0 0 12px rgba(29,209,238,0.4);
}
```

---

## 5. Summary Checklist

| # | Change | Status |
|---|--------|--------|
| 1 | Brighter background (deep navy, not pure black) | ☐ |
| 2 | All display/accent text uses blue-teal gradient | ☐ |
| 3 | Hover effects use unified blue-teal gradient theme | ☐ |
| 4 | Replace logo with new `NexusLogo` component | ☐ |
| 5 | Intro Phase 1: Logo splash with loading | ☐ |
| 6 | Intro Phase 2: Fade out logo, fade in sidebar + chatbox | ☐ |
| 7 | Intro Phase 3: Typewriter animation in chatbox placeholder (React Bits) | ☐ |
| 8 | Intro Phase 4: SplitText animation for "Hi, I'm NEXUS." block, then fade out | ☐ |
| 9 | Intro Phase 5: Final state shows alert banner + 4 prompt cards | ☐ |
| 10 | Stop button replaces send button during generation | ☐ |

---

## 6. References

- **React Bits Typewriter / RotatingText**: https://reactbits.dev — use for cycling placeholder prompts.
- **React Bits SplitText**: https://reactbits.dev — use for the "Hi, I'm NEXUS." intro text animation.
- **Logo code**: See Section 2 above (`NexusLogo.tsx`) — paste exactly as provided.
- **Color palette**:
  - Primary blue: `#1D4ED8`
  - Mid blue: `#3B82F6`
  - Teal accent: `#1DD1EE`
  - Light teal: `#63DEF9`
  - Background: `linear-gradient(135deg, #0a1628, #0d1a3a, #091530)`
