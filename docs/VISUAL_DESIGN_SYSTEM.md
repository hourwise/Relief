# Relief — Visual Design System

**Identity: "Calm Clarity & Soft Organic Guidance"**

This is the single source of truth for how Relief looks, so the app and the
website cannot drift apart again. Where the two disagree, this document wins.

> **Priority order when they conflict**
> 1. **The working app** is authoritative for *behaviour*, navigation, which
>    filters exist, and what the data can answer.
> 2. **This document and the brand artwork** are authoritative for *visual
>    language* — palette, atmosphere, identity.
> 3. **Old Figma mockups are reference only.** Never restore removed
>    functionality just because a mockup shows it.

---

## 1. Palette

| Role | Hex | Token | Use |
|------|-----|-------|-----|
| Deep Forest Teal | `#1A6B5C` | `colors.primary` | Primary actions, pins, active states, headings on light |
| Soft Sage | `#6CA08E` | `colors.sage` | Secondary accents, inactive controls |
| Teal Light | `#2D8A77` | `colors.primaryLight` | Switch tracks, glow rings |
| Warm Amber | `#F4C453` | `colors.amber` | **Selected/recommended only.** Ratings, route dashes |
| Urgent Coral | `#E75F51` | `colors.urgent` | Need One Now, the urgent destination pin |
| Charcoal | `#212C28` | `colors.textPrimary` | Body text |
| Muted Grey-Green | `#63736C` | `colors.textSecondary` | Supporting text |
| Mint Surface | `#F3F8F5` | `colors.mintSurface` | App background |
| Secondary Surface | `#EBF3EF` | `colors.secondarySurface` | Inset panels |
| Warm translucent white | `rgba(255,255,255,0.94)` | `colors.glassBackground` | Floating cards |

**Amber is a signal, not a decoration.** If everything is amber, nothing is
selected. Reserve it for the one thing the user should look at.

**Coral is reserved for urgency** — Need One Now and its destination. Never use
it for ordinary errors; error states use the amber problem surface.

---

## 2. Typography

Plus Jakarta Sans for headings and buttons, Inter for body. Both already loaded
via `useAppFonts`; do not add a third family.

Hierarchy lives in `src/theme/typography.ts` — use the tokens, never ad-hoc
sizes. Body text must not go below 13px, and supporting text keeps
`lineHeight` ≥ 1.4× for readability under stress.

---

## 3. Radii, spacing, depth

- **Radii:** floating cards 22–24px (`borderRadius.xl`), chips/pills full,
  controls 14–18px. Nothing sharp; nothing fully circular except pins and
  avatars.
- **Spacing:** from `src/theme/spacing.ts`. Generous is correct — this app is
  used one-handed and in a hurry.
- **Depth:** soft and wide, never hard. Prefer a large blur at low opacity
  (`shadows.md`) over a tight dark drop shadow. Elevation should read as the
  surface floating on mist, not as a cut-out.
- **Touch targets:** 44×44 minimum, always. No exceptions.

---

## 4. Map styling

`src/theme/mapStyle.ts` (`RELIEF_MAP_STYLE`) is applied via `customMapStyle`,
with `userInterfaceStyle="light"` pinned — without it the map follows the device
theme and rendered dark navy against the light mint chrome.

Principles, in priority order:

1. **Legibility first.** Used in urgency, one-handed, sometimes by someone who
   is not calm. Roads, the user dot and our pins stay unambiguous.
2. **Recede, don't disappear.** Land and minor roads are quietened so the teal
   pins and the amber selection are the brightest things on screen.
3. **No decoration that costs information.** Labels are muted, never removed.
   POI *icons* are off; POI *labels* stay, because "next to the museum" is how
   people actually navigate. Medical, attraction and transit labels are
   explicitly kept — they are often where a facility is.

Land `#F4F9F6` · water `#CFE6E0` · parks `#DCEBE0` · primary roads white with a
`#D6E5DE` edge · labels `#4A5B54` with a white halo.

> **Do not** replace the interactive map with a static watercolour image. The
> watercolour belongs in the handoff, About and empty states — never over live
> street detail.

---

## 5. Marker states

| State | Treatment |
|-------|-----------|
| Normal | Teal circle, white ring, `MapPin` glyph, soft glow. Static. |
| Cluster | Teal circle, white count, soft mint halo. Static. |
| Selected | Amber pin, amber halo, **two concentric ripples** expanding outward, gentle breathing scale. |
| Urgent (Need One Now) | Same ripple treatment in coral. |

**Only the selected and urgent markers animate.** Animating every pin turns a
calm map into a fairground and costs frames on a dense viewport.

All motion is gated on `AccessibilityInfo.isReduceMotionEnabled()`. Under
reduce-motion the ripples render statically at rest — the marker still reads as
"this is the one" without any movement.

---

## 6. Route line

Relief draws a **direct line**, not a route: an 8px teal underlay with a 4px
amber dashed overlay, `geodesic`, from the user to the active destination.

It is dashed **deliberately** so it is never mistaken for turn-by-turn
guidance, consistent with the app's existing honesty that walking times are
straight-line estimates. Turn-by-turn remains a hand-off to Google Maps.

Drawing a true routed polyline would require the **Google Directions API**
(a separate, billed API). Until that is enabled, do not present the line as a
route in copy.

---

## 7. Motion

- Camera moves: 500ms, via the single `cameraTarget` pathway.
- Handoff fade: 420ms ease-out.
- Ripples: 2000ms ease-out, second ring offset 1000ms.
- Breathing: 900ms each way, ease-in-out.

**Never animate to fill time.** The handoff shows only while something is
genuinely resolving and dismisses the instant it is ready, with a 6s ceiling so
a hung request cannot strand the user behind a splash.

---

## 8. Artwork and logo usage

In `assets/branding/`:

| File | Ratio | Use |
|------|-------|-----|
| `relief-logo-horizontal.jpg` | 3:1 | **Primary lock-up.** About header, branded handoff |
| `relief-splash-mark.png/svg` | 1:1 | Native splash, compact contexts |
| `relief-watercolor-backdrop.jpg` | 1.83:1 | Handoff background, wide empty states |
| `relief-brand-poster.jpg` | 0.56:1 (**portrait**) | Supporting artwork **only inside a height-capped frame** |
| `relief-community-illustration.jpg` | 1:1 | Onboarding, About, empty states |
| `relief-street-illustration.jpg` | 0.56:1 | Permission explanation, empty states |

> **The About overflow bug, so it is not repeated.** `relief-brand-poster.jpg`
> is 941×1672 — a tall portrait poster. At `width: '100%'` with its correct
> aspect ratio it rendered ~640dp tall, swamping the screen. The ratio was never
> wrong; using a portrait poster at full bleed was. **Portrait artwork must be
> capped by height** (`Dimensions.get('window').height * 0.34`, max 320) inside
> a rounded frame with `resizeMode="contain"`.

The lock-up and backdrop are JPEGs with no alpha, on a warm-white ground. Place
them on a matching light surface or give them a rounded container — never float
them on a dark or saturated background.

**Use illustration sparingly.** Onboarding, About, empty states, permission
explanations and account surfaces. **Never over the urgent map.**

---

## 9. Accessibility constraints

These are not negotiable and outrank any visual preference:

- Text on a coloured fill must invert to white. A selected control with dark
  text on a dark fill is a defect — it shipped once already at roughly 1.5:1.
- Amenity booleans are tri-state. Unknown renders as "unavailable", **never**
  as "no".
- All motion respects reduce-motion.
- Every control carries a role, a label and — where it has one — a selected or
  busy state.
- Touch targets 44×44 minimum.
- Never rely on colour alone: pair it with a label, an icon or a shape.

---

## 10. What must not come back

Removed during stabilisation for reasons recorded in `CURRENT_STATE.md`:

- The four persistent quick-filter chips (duplicated the Filters button, two
  sources of truth).
- Filters for unpopulated columns, and the community-rating selector.
- Four-tab navigation — it is Find / Favourites / Profile.
- Unfinished Community / AI / route-planning / offline surfaces.
- Google sign-in while the provider is disabled in Supabase.

A mockup showing any of these is out of date, not a specification.
