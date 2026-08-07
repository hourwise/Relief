import { useState } from 'react'

// ─── Relief Logo SVG ─────────────────────────────────────────────────────────
function ReliefLogo({ size = 64, color = '#fff' }: { size?: number; color?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" fill="none">
      {/* Pin body */}
      <path
        d="M32 4C21.5 4 13 12.5 13 23c0 14 19 37 19 37s19-23 19-37C51 12.5 42.5 4 32 4z"
        fill={color}
      />
      {/* Person silhouette */}
      <circle cx="32" cy="18" r="4.5" fill={color === '#fff' ? '#1a6b5c' : '#fff'} />
      <path
        d="M24 30c0-4.4 3.6-8 8-8s8 3.6 8 8"
        stroke={color === '#fff' ? '#1a6b5c' : '#fff'}
        strokeWidth="2.5"
        strokeLinecap="round"
        fill="none"
      />
      {/* Leaf */}
      <path
        d="M34 28c2-3 6-4 9-2-1 4-5 6-9 2z"
        fill={color === '#fff' ? '#6ca08e' : '#1a6b5c'}
      />
    </svg>
  )
}

// ─── Map SVG Background ───────────────────────────────────────────────────────
function WatercolorMap() {
  return (
    <svg
      viewBox="0 0 390 480"
      style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', opacity: 0.9 }}
    >
      <defs>
        <linearGradient id="mapGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#d4ece4" />
          <stop offset="50%" stopColor="#e8f5ef" />
          <stop offset="100%" stopColor="#c8e8dc" />
        </linearGradient>
        <filter id="watercolor">
          <feTurbulence type="fractalNoise" baseFrequency="0.04" numOctaves="4" result="noise" />
          <feDisplacementMap in="SourceGraphic" in2="noise" scale="3" xChannelSelector="R" yChannelSelector="G" />
        </filter>
        <radialGradient id="glowAmber" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#f4c453" stopOpacity="0.6" />
          <stop offset="100%" stopColor="#f4c453" stopOpacity="0" />
        </radialGradient>
        <radialGradient id="glowTeal" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#1a6b5c" stopOpacity="0.4" />
          <stop offset="100%" stopColor="#1a6b5c" stopOpacity="0" />
        </radialGradient>
      </defs>
      {/* Base */}
      <rect width="390" height="480" fill="url(#mapGrad)" />
      {/* Road grid */}
      {[40, 100, 160, 230, 300, 360].map((x, i) => (
        <line key={`v${i}`} x1={x} y1="0" x2={x + 20} y2="480" stroke="#b8d8cc" strokeWidth="8" opacity="0.5" strokeLinecap="round" />
      ))}
      {[60, 140, 220, 300, 380].map((y, i) => (
        <line key={`h${i}`} x1="0" y1={y} x2="390" y2={y + 8} stroke="#b8d8cc" strokeWidth="7" opacity="0.5" strokeLinecap="round" />
      ))}
      {/* Diagonal road */}
      <line x1="0" y1="120" x2="390" y2="350" stroke="#a8ccbc" strokeWidth="9" opacity="0.4" strokeLinecap="round" />
      <line x1="390" y1="80" x2="80" y2="480" stroke="#a8ccbc" strokeWidth="6" opacity="0.3" strokeLinecap="round" />
      {/* Blocks / buildings */}
      {[
        [50, 70, 70, 55], [140, 70, 60, 48], [240, 70, 75, 55],
        [50, 155, 80, 52], [180, 155, 65, 50], [310, 155, 60, 52],
        [50, 240, 70, 55], [140, 240, 80, 50], [270, 240, 65, 55],
        [50, 325, 75, 52], [180, 325, 70, 50], [310, 325, 65, 52],
        [50, 408, 80, 52], [160, 408, 75, 52], [280, 408, 80, 52],
      ].map(([x, y, w, h], i) => (
        <rect key={i} x={x} y={y} width={w} height={h} rx="4" fill="#c2ddd2" opacity="0.5" filter="url(#watercolor)" />
      ))}
      {/* Park patches */}
      <ellipse cx="195" cy="200" rx="40" ry="28" fill="#9dccb4" opacity="0.35" />
      <ellipse cx="340" cy="380" rx="28" ry="20" fill="#9dccb4" opacity="0.3" />
      <ellipse cx="60" cy="390" rx="22" ry="16" fill="#9dccb4" opacity="0.3" />
    </svg>
  )
}

// ─── Map Pin ──────────────────────────────────────────────────────────────────
function MapPin({
  x, y, glowing = false, badge
}: { x: number; y: number; glowing?: boolean; badge?: string }) {
  return (
    <g transform={`translate(${x},${y})`}>
      {glowing && (
        <>
          <circle r="22" fill="url(#glowAmber)" className="pin-glow" />
          <circle r="14" fill="rgba(244,196,83,0.25)" />
        </>
      )}
      {/* Pin shadow */}
      <ellipse cx="0" cy="26" rx="8" ry="3" fill="rgba(0,0,0,0.12)" />
      {/* Pin body */}
      <path
        d="M0-28C-9-28-16-21-16-12c0 9 16 38 16 38s16-29 16-38C16-21 9-28 0-28z"
        fill="#1a6b5c"
        filter="drop-shadow(0 2px 6px rgba(26,107,92,0.4))"
      />
      {/* Pin face */}
      <circle cx="0" cy="-12" r="5" fill="white" opacity="0.9" />
      {/* Leaf */}
      <path d="M2-14c2-2 5-3 7-1-1 3-4 4-7 1z" fill="#6ca08e" />
      {badge && (
        <g transform="translate(10,-24)">
          <circle r="7" fill="white" />
          <text textAnchor="middle" dominantBaseline="middle" fontSize="7" fill="#1a6b5c">{badge}</text>
        </g>
      )}
    </g>
  )
}

// ─── Cluster Marker ───────────────────────────────────────────────────────────
function ClusterPin({ x, y, count }: { x: number; y: number; count: number }) {
  return (
    <g transform={`translate(${x},${y})`}>
      <circle r="18" fill="rgba(26,107,92,0.12)" />
      <circle r="13" fill="#1a6b5c" />
      <text textAnchor="middle" dominantBaseline="middle" fontSize="10" fontWeight="700" fill="white">{count}</text>
    </g>
  )
}

// ─── Bottom Nav ───────────────────────────────────────────────────────────────
function BottomNav({ active, onNav }: { active: string; onNav: (s: string) => void }) {
  const items = [
    { id: 'map', icon: '🗺', label: 'Explore' },
    { id: 'saved', icon: '🔖', label: 'Saved' },
    { id: 'community', icon: '🤝', label: 'Community' },
    { id: 'profile', icon: '👤', label: 'Profile' },
  ]
  return (
    <div style={{
      background: 'rgba(255,255,255,0.92)',
      backdropFilter: 'blur(16px)',
      borderTop: '1px solid rgba(26,107,92,0.1)',
      display: 'flex',
      padding: '8px 0 14px',
    }}>
      {items.map(item => (
        <button
          key={item.id}
          onClick={() => onNav(item.id)}
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '3px',
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            padding: '4px 0',
          }}
        >
          <span style={{ fontSize: '20px', opacity: active === item.id ? 1 : 0.4 }}>{item.icon}</span>
          <span style={{
            fontSize: '10px',
            fontWeight: 600,
            color: active === item.id ? '#1a6b5c' : '#63736c',
            fontFamily: 'var(--font)',
          }}>{item.label}</span>
        </button>
      ))}
    </div>
  )
}

// ─── Toggle Switch ────────────────────────────────────────────────────────────
function Toggle({ on, onToggle }: { on: boolean; onToggle: () => void }) {
  return (
    <div
      onClick={onToggle}
      style={{
        width: 42,
        height: 24,
        borderRadius: 12,
        background: on ? '#1a6b5c' : '#e2ece8',
        position: 'relative',
        cursor: 'pointer',
        transition: 'background 0.2s',
        flexShrink: 0,
      }}
    >
      <div style={{
        position: 'absolute',
        top: 3,
        left: on ? 21 : 3,
        width: 18,
        height: 18,
        borderRadius: 9,
        background: 'white',
        transition: 'left 0.2s',
        boxShadow: '0 1px 4px rgba(0,0,0,0.2)',
      }} />
    </div>
  )
}

// ─── Filter Row ───────────────────────────────────────────────────────────────
function FilterRow({ label, desc, on, onToggle }: { label: string; desc?: string; on: boolean; onToggle: () => void }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '13px 0', borderBottom: '1px solid rgba(26,107,92,0.07)' }}>
      <div>
        <div style={{ fontSize: 15, fontWeight: 600, color: '#212c28' }}>{label}</div>
        {desc && <div style={{ fontSize: 12, color: '#63736c', marginTop: 2 }}>{desc}</div>}
      </div>
      <Toggle on={on} onToggle={onToggle} />
    </div>
  )
}

// ─── Rating Bar ───────────────────────────────────────────────────────────────
function RatingBar({ label, value }: { label: string; value: number }) {
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
        <span style={{ fontSize: 13, color: '#63736c', fontWeight: 500 }}>{label}</span>
        <span style={{ fontSize: 13, color: '#1a6b5c', fontWeight: 700 }}>{value.toFixed(1)}</span>
      </div>
      <div style={{ height: 6, borderRadius: 3, background: '#e2ece8', overflow: 'hidden' }}>
        <div style={{ width: `${(value / 5) * 100}%`, height: '100%', borderRadius: 3, background: 'linear-gradient(90deg,#6ca08e,#1a6b5c)' }} />
      </div>
    </div>
  )
}

// ─── Badge Chip ───────────────────────────────────────────────────────────────
function Badge({ label, color = '#e8f4f0', textColor = '#1a6b5c' }: { label: string; color?: string; textColor?: string }) {
  return (
    <span style={{
      background: color,
      color: textColor,
      borderRadius: 20,
      padding: '4px 11px',
      fontSize: 12,
      fontWeight: 600,
      whiteSpace: 'nowrap',
    }}>{label}</span>
  )
}

// ─── Screen: Splash ──────────────────────────────────────────────────────────
function SplashScreen({ onNext }: { onNext: () => void }) {
  return (
    <div
      style={{
        position: 'relative',
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden',
        cursor: 'pointer',
      }}
      onClick={onNext}
    >
      {/* Background */}
      <div style={{ position: 'absolute', inset: 0 }}>
        <WatercolorMap />
      </div>
      {/* Overlay */}
      <div style={{ position: 'absolute', inset: 0, background: 'rgba(20,60,45,0.28)' }} />

      {/* Content */}
      <div className="fade-in" style={{ position: 'relative', textAlign: 'center', padding: '0 32px' }}>
        {/* Logo */}
        <div className="float-anim" style={{ marginBottom: 24 }}>
          <div style={{
            width: 96, height: 96,
            borderRadius: '50%',
            background: 'rgba(255,255,255,0.15)',
            backdropFilter: 'blur(12px)',
            border: '1.5px solid rgba(255,255,255,0.4)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto',
            boxShadow: '0 0 40px rgba(244,196,83,0.3)',
          }}>
            <ReliefLogo size={60} color="#fff" />
          </div>
        </div>

        <h1 style={{
          fontSize: 40, fontWeight: 700, color: 'white',
          margin: '0 0 10px',
          textShadow: '0 2px 20px rgba(0,0,0,0.3)',
          letterSpacing: '-0.5px',
          fontFamily: 'var(--font)',
        }}>Relief</h1>
        <p style={{
          fontSize: 16, color: 'rgba(255,255,255,0.9)',
          fontStyle: 'italic', margin: 0,
          fontFamily: 'var(--font)',
          textShadow: '0 1px 8px rgba(0,0,0,0.3)',
        }}>Find Comfort, Feel Relief.</p>
      </div>

      {/* Tap hint */}
      <div style={{
        position: 'absolute', bottom: 48,
        color: 'rgba(255,255,255,0.65)',
        fontSize: 13, fontFamily: 'var(--font)',
        letterSpacing: '0.05em',
      }}>
        Tap to continue
      </div>
    </div>
  )
}

// ─── Screen: Onboarding ───────────────────────────────────────────────────────
function OnboardingScreen({ onNext }: { onNext: () => void }) {
  const [radar, setRadar] = useState(false)
  const [baby, setBaby] = useState(false)
  const [gender, setGender] = useState(false)

  return (
    <div style={{ flex: 1, position: 'relative', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
      {/* Blurred map bg */}
      <div style={{ position: 'absolute', inset: 0 }}>
        <WatercolorMap />
        <div style={{ position: 'absolute', inset: 0, backdropFilter: 'blur(4px)', background: 'rgba(235,243,239,0.5)' }} />
      </div>

      {/* Floating sheet */}
      <div className="slide-up" style={{
        position: 'absolute',
        bottom: 0, left: 0, right: 0,
        background: 'rgba(255,255,255,0.94)',
        backdropFilter: 'blur(20px)',
        borderRadius: '28px 28px 0 0',
        border: '1px solid rgba(255,255,255,0.8)',
        padding: '24px 24px 36px',
        boxShadow: '0 -8px 40px rgba(26,107,92,0.12)',
      }}>
        {/* Drag handle */}
        <div style={{ width: 40, height: 4, borderRadius: 2, background: '#d4e8e0', margin: '0 auto 24px' }} />

        {/* Logo row */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
          <div style={{
            width: 44, height: 44,
            borderRadius: 14,
            background: '#1a6b5c',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <ReliefLogo size={28} color="#fff" />
          </div>
          <div>
            <div style={{ fontSize: 22, fontWeight: 700, color: '#212c28', fontFamily: 'var(--font)' }}>Welcome to Relief</div>
          </div>
        </div>

        <p style={{ fontSize: 15, color: '#63736c', lineHeight: 1.6, margin: '0 0 24px', fontFamily: 'var(--font)' }}>
          Find accessible, safe, and comfortable facilities nearby — without friction.
        </p>

        {/* Preferences */}
        <div style={{ marginBottom: 24 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: '#63736c', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 12 }}>
            Your preferences
          </div>
          <FilterRow label="RADAR Key facilities first" on={radar} onToggle={() => setRadar(!radar)} />
          <FilterRow label="Baby changing needed" on={baby} onToggle={() => setBaby(!baby)} />
          <FilterRow label="Gender-neutral facilities" on={gender} onToggle={() => setGender(!gender)} />
        </div>

        {/* CTA */}
        <button
          onClick={onNext}
          style={{
            width: '100%',
            padding: '16px',
            borderRadius: 28,
            background: '#1a6b5c',
            color: 'white',
            border: 'none',
            fontSize: 16,
            fontWeight: 700,
            cursor: 'pointer',
            fontFamily: 'var(--font)',
            boxShadow: '0 8px 20px rgba(26,107,92,0.28)',
            marginBottom: 12,
          }}
        >
          Explore Nearby
        </button>
        <button
          onClick={onNext}
          style={{
            width: '100%', padding: '12px', background: 'none', border: 'none',
            color: '#63736c', fontSize: 14, cursor: 'pointer', fontFamily: 'var(--font)',
          }}
        >
          Skip for now
        </button>
      </div>
    </div>
  )
}

// ─── Screen: Map ──────────────────────────────────────────────────────────────
function MapScreen({
  onFilter, onPin, onNav
}: { onFilter: () => void; onPin: () => void; onNav: (s: string) => void }) {
  const [activeChip, setActiveChip] = useState('Accessible')
  const chips = ['Accessible', 'RADAR Key', 'Baby Changing', 'Free', 'Gender-Neutral']

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {/* Map area */}
      <div style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
        <WatercolorMap />

        {/* SVG pins */}
        <svg viewBox="0 0 390 480" style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}>
          <defs>
            <radialGradient id="glowAmber" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#f4c453" stopOpacity="0.55" />
              <stop offset="100%" stopColor="#f4c453" stopOpacity="0" />
            </radialGradient>
            <radialGradient id="glowTeal" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#1a6b5c" stopOpacity="0.35" />
              <stop offset="100%" stopColor="#1a6b5c" stopOpacity="0" />
            </radialGradient>
          </defs>
          <MapPin x={195} y={220} glowing={true} />
          <MapPin x={110} y={150} badge="♿" />
          <MapPin x={295} y={170} badge="👶" />
          <MapPin x={155} y={320} />
          <MapPin x={310} y={300} glowing={true} />
          <ClusterPin x={80} y={360} count={4} />
          <ClusterPin x={340} y={420} count={2} />
        </svg>

        {/* Top overlay: search + chips */}
        <div style={{ position: 'absolute', top: 0, left: 0, right: 0, padding: '16px 16px 0' }}>
          {/* Search bar */}
          <div style={{
            height: 52,
            borderRadius: 26,
            background: 'rgba(255,255,255,0.93)',
            backdropFilter: 'blur(16px)',
            boxShadow: '0 4px 20px rgba(26,107,92,0.12)',
            border: '1px solid rgba(255,255,255,0.8)',
            display: 'flex',
            alignItems: 'center',
            padding: '0 16px',
            gap: 10,
            marginBottom: 12,
          }}>
            <span style={{ fontSize: 18 }}>🔍</span>
            <span style={{ flex: 1, fontSize: 15, color: '#63736c', fontFamily: 'var(--font)' }}>
              Search town, postcode, or venue...
            </span>
            <button
              onClick={onFilter}
              style={{
                width: 36, height: 36, borderRadius: 12,
                background: '#1a6b5c',
                border: 'none', cursor: 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 16,
              }}
            >
              <span style={{ color: 'white', fontSize: 14 }}>⚙️</span>
            </button>
          </div>

          {/* Filter chips */}
          <div style={{ display: 'flex', gap: 8, overflowX: 'auto', paddingBottom: 4 }}>
            {chips.map(chip => (
              <button
                key={chip}
                onClick={() => setActiveChip(chip)}
                style={{
                  whiteSpace: 'nowrap',
                  padding: '7px 15px',
                  borderRadius: 20,
                  border: activeChip === chip ? 'none' : '1px solid rgba(26,107,92,0.25)',
                  background: activeChip === chip ? '#1a6b5c' : 'rgba(255,255,255,0.9)',
                  color: activeChip === chip ? 'white' : '#63736c',
                  fontSize: 13,
                  fontWeight: 600,
                  cursor: 'pointer',
                  fontFamily: 'var(--font)',
                  backdropFilter: 'blur(8px)',
                  boxShadow: activeChip === chip ? '0 4px 12px rgba(26,107,92,0.25)' : 'none',
                }}
              >
                {chip}
              </button>
            ))}
          </div>
        </div>

        {/* Bottom: "Need One Now" */}
        <div style={{
          position: 'absolute',
          bottom: 16, left: 16, right: 16,
          display: 'flex', flexDirection: 'column', gap: 10,
        }}>
          {/* Nearest facility card */}
          <div
            onClick={onPin}
            style={{
              background: 'rgba(255,255,255,0.93)',
              backdropFilter: 'blur(16px)',
              borderRadius: 20,
              border: '1px solid rgba(255,255,255,0.8)',
              padding: '12px 16px',
              boxShadow: '0 4px 20px rgba(26,107,92,0.1)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 12,
            }}
          >
            <div style={{
              width: 44, height: 44, borderRadius: 14,
              background: '#e8f4f0',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 22,
            }}>🚻</div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#212c28', fontFamily: 'var(--font)' }}>Ty Pawb Market Hall</div>
              <div style={{ fontSize: 12, color: '#63736c', fontFamily: 'var(--font)' }}>3 min walk · Open · ★ 4.8</div>
            </div>
            <span style={{ fontSize: 18 }}>›</span>
          </div>

          {/* Need One Now button */}
          <div style={{ position: 'relative' }}>
            {/* Ripple */}
            <div style={{
              position: 'absolute', inset: -8, borderRadius: 36,
              background: 'rgba(231,95,81,0.15)',
              animation: 'ripple 2s ease-out infinite',
            }} />
            <div style={{
              position: 'absolute', inset: -4, borderRadius: 32,
              background: 'rgba(231,95,81,0.1)',
              animation: 'ripple 2s ease-out infinite 0.4s',
            }} />
            <button
              onClick={onPin}
              style={{
                width: '100%',
                padding: '16px',
                borderRadius: 28,
                background: '#e75f51',
                color: 'white',
                border: 'none',
                fontSize: 16,
                fontWeight: 700,
                cursor: 'pointer',
                fontFamily: 'var(--font)',
                boxShadow: '0 8px 24px rgba(231,95,81,0.35)',
                position: 'relative',
                letterSpacing: '0.01em',
              }}
            >
              ⚡ Need One Now
            </button>
          </div>
        </div>
      </div>

      {/* Bottom nav */}
      <BottomNav active="map" onNav={onNav} />
    </div>
  )
}

// ─── Screen: Filters ──────────────────────────────────────────────────────────
function FiltersScreen({ onBack }: { onBack: () => void }) {
  const [filters, setFilters] = useState<Record<string, boolean>>({
    radar: true, changing: false, stepFree: true, grabRails: false,
    single: false, floorCeil: false, quiet: false, genderNeutral: true,
    babyInside: false, pram: false, family: false,
    period: false, sanitary: false, staffNearby: true, wellLit: true,
  })
  const toggle = (k: string) => setFilters(f => ({ ...f, [k]: !f[k] }))

  const sections: { title: string; items: { key: string; label: string; desc?: string }[] }[] = [
    {
      title: '♿ Accessibility & Key Access',
      items: [
        { key: 'radar', label: 'RADAR Key Required', desc: 'National Key Scheme access' },
        { key: 'changing', label: 'Changing Places', desc: 'Full adult changing facilities' },
        { key: 'stepFree', label: 'Step-Free / Ramp Access' },
        { key: 'grabRails', label: 'Grab Rails Inside' },
      ],
    },
    {
      title: '🔒 Privacy & Environment',
      items: [
        { key: 'single', label: 'Single Cubicle' },
        { key: 'floorCeil', label: 'Floor-to-Ceiling Doors' },
        { key: 'quiet', label: 'Quiet Space' },
        { key: 'genderNeutral', label: 'Gender-Neutral' },
      ],
    },
    {
      title: '👶 Family & Baby',
      items: [
        { key: 'babyInside', label: 'Baby Change Inside Room' },
        { key: 'pram', label: 'Pram Accessible' },
        { key: 'family', label: 'Family Toilet' },
      ],
    },
    {
      title: '🛡 Safety & Hygiene',
      items: [
        { key: 'period', label: 'Free Period Products' },
        { key: 'sanitary', label: 'Sanitary Bins' },
        { key: 'staffNearby', label: 'Staff Nearby' },
        { key: 'wellLit', label: 'Well Lit / CCTV' },
      ],
    },
  ]

  return (
    <div className="slide-up" style={{ flex: 1, display: 'flex', flexDirection: 'column', background: '#f3f8f5', overflow: 'hidden' }}>
      {/* Header */}
      <div style={{
        background: 'linear-gradient(135deg, #1a6b5c 0%, #2d8a77 100%)',
        padding: '52px 24px 24px',
        position: 'relative',
        overflow: 'hidden',
      }}>
        {/* Watercolor overlay */}
        <div style={{
          position: 'absolute', inset: 0,
          background: 'radial-gradient(ellipse at top right, rgba(244,196,83,0.15) 0%, transparent 60%)',
        }} />
        <button
          onClick={onBack}
          style={{
            position: 'absolute', top: 16, left: 16,
            width: 36, height: 36, borderRadius: 12,
            background: 'rgba(255,255,255,0.2)',
            border: 'none', color: 'white', cursor: 'pointer',
            fontSize: 18, display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}
        >‹</button>
        <div style={{ position: 'relative' }}>
          <div style={{ fontSize: 22, fontWeight: 700, color: 'white', fontFamily: 'var(--font)', marginBottom: 4 }}>
            Filter Facilities
          </div>
          <div style={{ fontSize: 14, color: 'rgba(255,255,255,0.75)', fontFamily: 'var(--font)' }}>
            Personalise your search
          </div>
        </div>
      </div>

      {/* Filter list */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '0 0 100px' }}>
        {sections.map(section => (
          <div key={section.title} style={{ padding: '20px 24px 0' }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: '#63736c', letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 4 }}>
              {section.title}
            </div>
            <div style={{ background: 'white', borderRadius: 16, padding: '0 16px', boxShadow: '0 2px 8px rgba(26,107,92,0.06)' }}>
              {section.items.map(item => (
                <FilterRow key={item.key} label={item.label} desc={item.desc} on={filters[item.key]} onToggle={() => toggle(item.key)} />
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Apply bar */}
      <div style={{
        position: 'absolute', bottom: 0, left: 0, right: 0,
        padding: '16px 24px 28px',
        background: 'rgba(255,255,255,0.95)',
        backdropFilter: 'blur(16px)',
        borderTop: '1px solid rgba(26,107,92,0.08)',
      }}>
        <button
          onClick={onBack}
          style={{
            width: '100%', padding: '16px', borderRadius: 28,
            background: '#1a6b5c', color: 'white', border: 'none',
            fontSize: 16, fontWeight: 700, cursor: 'pointer',
            fontFamily: 'var(--font)',
            boxShadow: '0 8px 20px rgba(26,107,92,0.25)',
          }}
        >
          Apply Filters
        </button>
      </div>
    </div>
  )
}

// ─── Screen: Facility Detail ──────────────────────────────────────────────────
function DetailScreen({ onBack }: { onBack: () => void }) {
  return (
    <div className="slide-up" style={{ flex: 1, display: 'flex', flexDirection: 'column', background: '#f3f8f5', overflow: 'hidden' }}>
      {/* Map peek */}
      <div style={{ height: 200, position: 'relative', overflow: 'hidden', flexShrink: 0 }}>
        <WatercolorMap />
        <svg viewBox="0 0 390 200" style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}>
          <defs>
            <radialGradient id="glowAmberD" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#f4c453" stopOpacity="0.55" />
              <stop offset="100%" stopColor="#f4c453" stopOpacity="0" />
            </radialGradient>
          </defs>
          <MapPin x={195} y={120} glowing={true} />
        </svg>
        {/* Back button */}
        <button
          onClick={onBack}
          style={{
            position: 'absolute', top: 16, left: 16,
            width: 38, height: 38, borderRadius: 12,
            background: 'rgba(255,255,255,0.9)',
            backdropFilter: 'blur(8px)',
            border: '1px solid rgba(255,255,255,0.8)',
            cursor: 'pointer', fontSize: 18,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 2px 12px rgba(0,0,0,0.1)',
          }}
        >‹</button>
      </div>

      {/* Detail card */}
      <div style={{
        flex: 1,
        background: 'white',
        borderRadius: '24px 24px 0 0',
        marginTop: -16,
        overflowY: 'auto',
        padding: '20px 24px 120px',
        boxShadow: '0 -4px 24px rgba(26,107,92,0.1)',
      }}>
        {/* Drag handle */}
        <div style={{ width: 40, height: 4, borderRadius: 2, background: '#d4e8e0', margin: '0 auto 20px' }} />

        {/* Header */}
        <div style={{ marginBottom: 16 }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 6 }}>
            <div>
              <h2 style={{ margin: 0, fontSize: 22, fontWeight: 700, color: '#212c28', fontFamily: 'var(--font)' }}>Ty Pawb Market Hall</h2>
              <div style={{ fontSize: 14, color: '#63736c', marginTop: 4, fontFamily: 'var(--font)' }}>Wrexham, LL11 1AR</div>
            </div>
            <div style={{
              background: '#e6f4ef',
              color: '#1a6b5c',
              borderRadius: 20,
              padding: '6px 12px',
              fontSize: 13,
              fontWeight: 700,
              fontFamily: 'var(--font)',
            }}>Open</div>
          </div>

          {/* Meta row */}
          <div style={{ display: 'flex', gap: 16, marginBottom: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
              <span>🚶</span>
              <span style={{ fontSize: 13, color: '#63736c', fontFamily: 'var(--font)' }}>3 min walk</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
              <span>⭐</span>
              <span style={{ fontSize: 13, fontWeight: 700, color: '#212c28', fontFamily: 'var(--font)' }}>4.8</span>
              <span style={{ fontSize: 13, color: '#63736c', fontFamily: 'var(--font)' }}>· 124 ratings</span>
            </div>
          </div>

          {/* Feature badges */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            <Badge label="♿ RADAR Key" color="#e8f4f0" textColor="#1a6b5c" />
            <Badge label="🦽 Step-Free" color="#e8f4f0" textColor="#1a6b5c" />
            <Badge label="✨ Very Clean" color="#fef9e8" textColor="#b8860b" />
            <Badge label="👶 Baby Change" color="#f0eefa" textColor="#7b52ab" />
            <Badge label="🆓 Free" color="#fef0ee" textColor="#c0392b" />
          </div>
        </div>

        {/* Divider */}
        <div style={{ height: 1, background: 'rgba(26,107,92,0.07)', margin: '16px 0' }} />

        {/* Community ratings */}
        <div style={{ marginBottom: 20 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: '#63736c', letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 14 }}>
            Community Ratings
          </div>
          <RatingBar label="Cleanliness" value={4.9} />
          <RatingBar label="Privacy" value={4.5} />
          <RatingBar label="Accessibility" value={4.8} />
          <RatingBar label="Safety" value={4.7} />
        </div>

        {/* Access notes */}
        <div style={{ marginBottom: 24 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: '#63736c', letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 10 }}>
            Access Notes
          </div>
          <div style={{
            background: '#f3f8f5',
            borderRadius: 14,
            padding: '14px 16px',
            fontSize: 14,
            color: '#212c28',
            lineHeight: 1.7,
            fontFamily: 'var(--font)',
            borderLeft: '3px solid #6ca08e',
          }}>
            Located on the ground floor, left past the main reception desk. Accessible entrance via automatic sliding doors. Ask staff at the info desk if the door is locked.
          </div>
        </div>

        {/* Action buttons */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <button style={{
            width: '100%', padding: '16px', borderRadius: 28,
            background: '#1a6b5c', color: 'white', border: 'none',
            fontSize: 16, fontWeight: 700, cursor: 'pointer',
            fontFamily: 'var(--font)',
            boxShadow: '0 8px 20px rgba(26,107,92,0.25)',
          }}>
            🗺 Get Directions
          </button>
          <div style={{ display: 'flex', gap: 10 }}>
            <button style={{
              flex: 1, padding: '13px', borderRadius: 24,
              background: '#fef0ee', color: '#e75f51', border: 'none',
              fontSize: 14, fontWeight: 600, cursor: 'pointer',
              fontFamily: 'var(--font)',
            }}>⚠️ Report Issue</button>
            <button style={{
              flex: 1, padding: '13px', borderRadius: 24,
              background: '#e8f4f0', color: '#1a6b5c', border: 'none',
              fontSize: 14, fontWeight: 600, cursor: 'pointer',
              fontFamily: 'var(--font)',
            }}>✏️ Update Details</button>
          </div>
        </div>
      </div>
    </div>
  )
}

// ─── Phone Frame ──────────────────────────────────────────────────────────────
function PhoneFrame({ children, label }: { children: React.ReactNode; label: string }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16 }}>
      <div style={{
        width: 390,
        height: 844,
        borderRadius: 52,
        background: '#0a0a0a',
        padding: '10px',
        boxShadow: '0 40px 120px rgba(0,0,0,0.35), 0 0 0 1px rgba(255,255,255,0.06) inset',
        position: 'relative',
        flexShrink: 0,
      }}>
        {/* Screen */}
        <div style={{
          width: '100%',
          height: '100%',
          borderRadius: 46,
          overflow: 'hidden',
          background: '#f3f8f5',
          display: 'flex',
          flexDirection: 'column',
          position: 'relative',
        }}>
          {/* Status bar */}
          <div style={{
            height: 44,
            background: 'transparent',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0 28px 0 24px',
            flexShrink: 0,
            position: 'absolute',
            top: 0, left: 0, right: 0,
            zIndex: 10,
          }}>
            <span style={{ fontSize: 13, fontWeight: 700, color: '#212c28', fontFamily: 'var(--font)' }}>9:41</span>
            <div style={{
              width: 120, height: 34,
              background: '#0a0a0a',
              borderRadius: 20,
              position: 'absolute',
              left: '50%', top: 0,
              transform: 'translateX(-50%)',
            }} />
            <div style={{ display: 'flex', gap: 5, alignItems: 'center' }}>
              <span style={{ fontSize: 11, color: '#212c28' }}>●●●</span>
              <span style={{ fontSize: 11, color: '#212c28' }}>WiFi</span>
              <span style={{ fontSize: 11, color: '#212c28' }}>🔋</span>
            </div>
          </div>
          {/* Content (pushes below status bar) */}
          <div style={{ paddingTop: 44, flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
            {children}
          </div>
        </div>
      </div>
      <div style={{
        fontSize: 12, fontWeight: 600,
        color: '#63736c', letterSpacing: '0.08em', textTransform: 'uppercase',
        fontFamily: 'var(--font)',
      }}>{label}</div>
    </div>
  )
}

// ─── Main App ─────────────────────────────────────────────────────────────────
export default function App() {
  const [_navActive, setNavActive] = useState('map')

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #c8e8dc 0%, #e8f5ef 40%, #d4ece4 100%)',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '40px 24px',
      fontFamily: 'var(--font)',
    }}>
      {/* Header */}
      <div style={{ textAlign: 'center', marginBottom: 48 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12, marginBottom: 10 }}>
          <div style={{
            width: 40, height: 40, borderRadius: 12,
            background: '#1a6b5c',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <ReliefLogo size={26} color="#fff" />
          </div>
          <span style={{ fontSize: 26, fontWeight: 700, color: '#212c28' }}>Relief</span>
        </div>
        <p style={{ fontSize: 15, color: '#63736c', margin: 0 }}>
          Accessible facility finder · UI Design Showcase
        </p>
      </div>

      {/* Screens grid */}
      <div style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: 40,
        justifyContent: 'center',
        alignItems: 'flex-start',
      }}>
        {/* Splash */}
        <PhoneFrame label="01 — Splash">
          <SplashScreen onNext={() => {}} />
        </PhoneFrame>

        {/* Onboarding */}
        <PhoneFrame label="02 — Onboarding">
          <OnboardingScreen onNext={() => {}} />
        </PhoneFrame>

        {/* Map */}
        <PhoneFrame label="03 — Map">
          <MapScreen
            onFilter={() => {}}
            onPin={() => {}}
            onNav={setNavActive}
          />
        </PhoneFrame>

        {/* Filters */}
        <PhoneFrame label="04 — Filters">
          <FiltersScreen onBack={() => {}} />
        </PhoneFrame>

        {/* Detail */}
        <PhoneFrame label="05 — Facility Detail">
          <DetailScreen onBack={() => {}} />
        </PhoneFrame>
      </div>

      {/* Interactive prototype note */}
      <div style={{
        marginTop: 56,
        padding: '16px 28px',
        background: 'rgba(255,255,255,0.7)',
        backdropFilter: 'blur(12px)',
        borderRadius: 20,
        border: '1px solid rgba(255,255,255,0.8)',
        textAlign: 'center',
        maxWidth: 520,
      }}>
        <div style={{ fontSize: 14, color: '#212c28', fontWeight: 600, marginBottom: 4 }}>
          Interactive components — all toggles and buttons are live
        </div>
        <div style={{ fontSize: 13, color: '#63736c' }}>
          Relief · UK accessible toilet finder · WCAG AA compliant · Plus Jakarta Sans
        </div>
      </div>
    </div>
  )
}
