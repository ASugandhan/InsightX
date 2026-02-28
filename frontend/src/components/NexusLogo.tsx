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
  to   { opacity: 1; transform: scale(1.06); }
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
        <svg width={size} height={size} viewBox="0 0 180 180" fill="none" xmlns="http://www.w3.org/2000/svg">
          {/* Ambient rings */}
          <circle className="nexus-ar" cx="90" cy="90" r="72" />
          <circle className="nexus-ar" cx="90" cy="90" r="58" />
          <circle className="nexus-ar" cx="90" cy="90" r="44" />

          {/* Node ripple rings */}
          <circle className="nexus-nr" cx="90" cy="32" r="8" />
          <circle className="nexus-nr" cx="140" cy="61" r="8" />
          <circle className="nexus-nr" cx="140" cy="119" r="8" />
          <circle className="nexus-nr" cx="90" cy="148" r="8" />
          <circle className="nexus-nr" cx="40" cy="119" r="8" />
          <circle className="nexus-nr" cx="40" cy="61" r="8" />

          {/* Connection lines */}
          <g stroke="#3B82F6" strokeWidth="0.9" opacity="0.35">
            <line className="nexus-cl" x1="90" y1="32" x2="140" y2="61" />
            <line className="nexus-cl" x1="140" y1="61" x2="140" y2="119" />
            <line className="nexus-cl" x1="140" y1="119" x2="90" y2="148" />
            <line className="nexus-cl" x1="90" y1="148" x2="40" y2="119" />
            <line className="nexus-cl" x1="40" y1="119" x2="40" y2="61" />
            <line className="nexus-cl" x1="40" y1="61" x2="90" y2="32" />
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
          <circle className="nexus-no" cx="90" cy="32" r="4.5" fill="#1D4ED8" stroke="#63DEF9" strokeWidth="1.2" />
          <circle className="nexus-no" cx="140" cy="61" r="4.5" fill="#1D4ED8" stroke="#63DEF9" strokeWidth="1.2" />
          <circle className="nexus-no" cx="140" cy="119" r="4.5" fill="#1D4ED8" stroke="#63DEF9" strokeWidth="1.2" />
          <circle className="nexus-no" cx="90" cy="148" r="4.5" fill="#1D4ED8" stroke="#63DEF9" strokeWidth="1.2" />
          <circle className="nexus-no" cx="40" cy="119" r="4.5" fill="#1D4ED8" stroke="#63DEF9" strokeWidth="1.2" />
          <circle className="nexus-no" cx="40" cy="61" r="4.5" fill="#1D4ED8" stroke="#63DEF9" strokeWidth="1.2" />

          {/* Flow dots */}
          <circle className="nexus-fd" cx="115" cy="69" />
          <circle className="nexus-fd" cx="65" cy="111" style={{ animationDelay: '1.1s' }} />

          <defs>
            <filter id="fdGlow" x="-100%" y="-100%" width="300%" height="300%">
              <feGaussianBlur stdDeviation="2" result="blur" />
              <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
            </filter>
          </defs>
        </svg>
        <div className="nexus-accent-bar" />
      </div>
    </>
  );
};

export default NexusLogo;
