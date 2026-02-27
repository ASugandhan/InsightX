import React, { useState, useEffect } from "react";
import NEXUS from "./components/Home";
import FloatingLines from "./components/FloatingLines";
import NexusLogo from "./components/NexusLogo";
import "./App.css";

const splashCSS = `
.splash-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0a1628 0%, #0d1a3a 40%, #091530 100%);
  transition: opacity 0.8s cubic-bezier(0.4, 0, 0.2, 1), transform 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}
.splash-overlay.fade-out {
  opacity: 0;
  transform: scale(1.05);
  pointer-events: none;
}

/* Loading dots */
.splash-dots {
  display: flex;
  gap: 8px;
  margin-top: 32px;
}
.splash-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: linear-gradient(135deg, #3B82F6, #1DD1EE);
  animation: splashDotPulse 1.4s ease-in-out infinite;
}
.splash-dot:nth-child(2) { animation-delay: 0.2s; }
.splash-dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes splashDotPulse {
  0%, 100% { transform: scale(0.6); opacity: 0.3; }
  50% { transform: scale(1.2); opacity: 1; }
}

/* Main content fade-in */
.app-shell.intro-hidden .main-area,
.app-shell.intro-hidden .background-layer {
  opacity: 0;
  transform: translateY(20px);
}
.app-shell.intro-visible .main-area,
.app-shell.intro-visible .background-layer {
  opacity: 1;
  transform: translateY(0);
  transition: opacity 0.8s ease, transform 0.8s ease;
}
`;

function SplashScreen({ onDone }: { onDone: () => void }) {
  const [fadeOut, setFadeOut] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setFadeOut(true), 2500);
    const removeTimer = setTimeout(() => onDone(), 3300);
    return () => { clearTimeout(timer); clearTimeout(removeTimer); };
  }, [onDone]);

  return (
    <div className={`splash-overlay${fadeOut ? " fade-out" : ""}`}>
      <style>{splashCSS}</style>
      <NexusLogo size={220} />
      <div className="splash-dots">
        <div className="splash-dot" />
        <div className="splash-dot" />
        <div className="splash-dot" />
      </div>
    </div>
  );
}

function App() {
  const [showSplash, setShowSplash] = useState(true);
  const [introPhase, setIntroPhase] = useState<"hidden" | "visible">("hidden");

  const handleSplashDone = () => {
    setShowSplash(false);
    setIntroPhase("visible");
  };

  return (
    <div className={`app-shell intro-${introPhase}`}>
      {showSplash && <SplashScreen onDone={handleSplashDone} />}
      <div className="background-layer">
        <FloatingLines
          enabledWaves={["top", "bottom"]}
          lineCount={5}
          lineDistance={5}
          bendRadius={5}
          bendStrength={-0.5}
          interactive={true}
          parallax={true}
        />
      </div>
      <div className="main-area">
        <NEXUS introReady={introPhase === "visible"} />
      </div>
    </div>
  );
}

export default App;
