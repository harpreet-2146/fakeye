import React from 'react';
import { useNavigate } from 'react-router-dom';
import Orb from '../components/Orb';

export default function Landing() {
  const navigate = useNavigate();

  return (
    <div className="relative w-full min-h-screen bg-black text-white overflow-hidden">
      
      {/* Orb Background */}
      <div className="absolute inset-0 z-0">
        <div style={{ width: '100%', height: '100%', position: 'relative' }}>
          <Orb
            hoverIntensity={0.5}
            rotateOnHover={true}
            hue={0}
            forceHoverState={false}
          />
        </div>
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-black/60 pointer-events-none" />
      </div>

      {/* Styles */}
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');

        .landing-title {
          font-family: 'Inter', sans-serif;
          font-weight: 900;
          letter-spacing: -0.03em;
          line-height: 0.95;
          font-size: clamp(52px, 8vw, 120px);
          background: linear-gradient(90deg, #FFFFFF, #C9D6FF 40%, #E2E2FF 70%);
          -webkit-background-clip: text;
          background-clip: text;
          color: transparent;
        }

        .cta-pill {
          background: linear-gradient(90deg, rgba(255,255,255,0.15), rgba(255,255,255,0.05));
          border: 1px solid rgba(255,255,255,0.15);
        }

        .cta-pill:hover {
          transform: translateY(-3px) scale(1.02);
        }

        .tag-pill {
          background: rgba(255,255,255,0.06);
          border: 1px solid rgba(255,255,255,0.1);
          padding: 6px 14px;
          border-radius: 999px;
          font-size: 12px;
          color: #E5E7EB;
        }
      `}</style>

      {/* Content */}
      <main className="relative z-10 flex items-center justify-center min-h-screen px-6">
        <div className="max-w-4xl text-center">

          <h1 className="landing-title">FAKEYE</h1>

          <p className="mt-6 text-lg md:text-xl text-gray-300 leading-relaxed max-w-2xl mx-auto">
            Detect fake content instantly.  
            A sharp eye for misinformation — powered by intelligence, built for clarity.
          </p>

          <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
            <button
              onClick={() => navigate('/get-started')}
              className="cta-pill inline-flex items-center gap-3 px-8 py-3 rounded-full text-base font-semibold shadow-lg transition-all duration-200 focus:outline-none"
            >
              <span>Get started</span>
              <svg
                className="w-4 h-4"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M5 12h14M13 5l7 7-7 7" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>

            <a
              href="#about"
              className="text-sm text-gray-400 hover:text-white transition underline-offset-4"
            >
              Learn more
            </a>
          </div>

          <div className="mt-6 flex items-center justify-center gap-3 flex-wrap">
            <div className="tag-pill">Fake News Detection</div>
            <div className="tag-pill">AI Analysis</div>
            <div className="tag-pill">Real-time Verdict</div>
          </div>

        </div>
      </main>
    </div>
  );
}
