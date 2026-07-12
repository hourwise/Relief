# Relief Design System & Mobile Implementation Guide

This document defines the visual identity and design tokens for the Relief brand, intended to ensure consistency between the Web App and the React Native Mobile App.

## 1. Brand Essence
- **Tone**: Calm, Premium, Reassuring, Compassionate.
- **Inspiration**: Studio Ghibli warmth, watercolor textures, soft organic shapes.
- **Visual Hooks**: Glowing location pins, soft map lines, rounded corners.

## 2. Color Palette

```javascript
const colors = {
  primary: '#0F766E',      // Deep Teal (Buttons, Headers)
  primaryLight: '#14B8A6', // Secondary Teal (Accents, Glows)
  background: '#F8FAFC',   // Off-white/Slate-50 (Main background)
  white: '#FFFFFF',        // Card backgrounds
  text: '#0F172A',         // Slate-900 (Headings)
  textMuted: '#64748B',    // Slate-500 (Body text)
  success: '#10B981',      // Emerald (Open facilities)
  warning: '#F59E0B',      // Amber (Urgent/Closing soon)
  error: '#EF4444',        // Red (Closed/Broken)
  tealSoft: '#F0FDFA',     // Teal-50 (Icon backgrounds)
};
```

## 3. Typography
- **Primary Font**: `Inter` (Clean, highly readable).
- **Secondary/Heading Font**: `Plus Jakarta Sans` (Soft, modern).
- **Guidelines**: 
  - Use large, readable font sizes for accessibility.
  - High contrast ratio (Text #0F172A on Background #F8FAFC).

## 4. Visual Styles

### 🏮 Glowing Pins (Mobile Implementation)
For the mobile map, location pins should have a "glow" effect.
- **Shadow**: `shadowColor: '#14B8A6'`, `shadowOffset: { width: 0, height: 0 }`, `shadowOpacity: 0.6`, `shadowRadius: 10`.
- **Animation**: Subtle pulse (scale 1.0 to 1.1) every 2-3 seconds.

### 🎨 Watercolor Textures
- **Backgrounds**: Use a subtle grain or noise overlay (5% opacity) to avoid "flat" digital looks.
- **Gradients**: Use soft radial gradients (e.g., `primaryLight` at 10% opacity) in the corners of screens to add warmth.

### ⏹️ Containers & Cards
- **Border Radius**: `24px` (Very rounded for a friendly feel).
- **Shadows**: Very soft, subtle elevation. Avoid harsh black shadows.
- **Backdrop**: Use `BlurView` (React Native) or semi-transparent white backgrounds (`rgba(255, 255, 255, 0.8)`) for a "glassmorphism" feel.

## 5. Asset Usage
- **Logo**: Use `Logo2.jpeg` (circular crop preferred).
- **Illustrations**: Soft, Ghibli-inspired illustrations with thin lines and watercolor fills.
- **Icons**: Use `Lucide-React` (Web) / `Lucide-React-Native` (Mobile). Use the `secondary` (#14B8A6) color for active icons.

---

## 6. Mobile Component Mapping

| Web Component | Mobile Equivalent | Style Note |
| :--- | :--- | :--- |
| `btn-primary` | `TouchableOpacity` | Background: `#0F766E`, Radius: `12px` |
| `card` | `View` | Background: `#FFFFFF`, Radius: `24px`, Padding: `16px` |
| `watercolor-texture` | `ImageBackground` | Use a low-opacity watercolor pattern asset |
| `glow-pin` | `Animated.View` | Implement with `Shadow` and `Pulse` animation |

## 7. Strapline
> **"Find Comfort, Feel Relief"**
> Use this in onboarding screens and splash screens to reinforce the brand promise.
