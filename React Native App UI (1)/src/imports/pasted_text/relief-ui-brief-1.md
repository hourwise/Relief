Here is a detailed UI Design Brief for **Relief**, crafted specifically to merge high accessibility standards with a serene, organic aesthetic.

---

## 🎨 Visual Style Overview

* **Aesthetic Direction:** **"Calm Clarity & Soft Organic Guidance."** The design balances modern iOS/Android UI patterns (frosted glass, generous white space, soft drop shadows) with warm, organic textures (gentle watercolor misty washes and glowing elements).
* **Atmosphere:** Empathetic, clean, reassuring, and non-clinical. The interface avoids cold, utility-style map layouts in favor of an inviting, human-centric design.
* **Background Texture:** A subtle, low-contrast watercolor/misty gradient wash (`#F3F8F5` blending to `#EBF3EF`) applied subtly behind floating white cards, modal sheets, and the top navigation layer.

---

## 🎨 Colour Palette

To maintain WCAG AAA/AA compliance for readability while staying visually soft:

* **Primary / Brand Teal:** `#1A6B5C` *(Deep Forest Teal – 7.2:1 contrast ratio against white for buttons, active states, and text)*
* **Secondary / Sage Green:** `#6CA08E` *(Soft Sage – ideal for active toggles, subtle badges, and secondary highlights)*
* **Accent / Golden Glow:** `#F4C453` *(Warm Amber/Gold – used for glowing map pin halos, stars, and verified badges)*
* **Urgent Action / Coral Red:** `#E75F51` *(Soft Coral – retained for the high-priority "Need One Now" emergency action)*
* **Neutral Dark / Charcoal Text:** `#212C28` *(Deep Off-Black – high readability for primary text without high-contrast harshness)*
* **Neutral Muted:** `#63736C` *(Medium Gray-Green – perfect for secondary labels, distances, and subtext)*
* **Card & Sheet Surface:** `#FFFFFF` *(Pure White with 85% opacity + Blur for overlay cards)*

---

## 🔤 Typography Direction

* **Font Family:** **Plus Jakarta Sans** or **Outfit** *(Clean, highly accessible geometric sans-serifs with generous aperture and rounded friendly terminals)*.
* **Hierarchy:**
* **Brand Title / Headlines:** Bold / Semi-bold (e.g., `24px` / `28px` line-height).
* **Card Headers / Section Titles:** Semi-bold `18px`.
* **Body Text:** Medium `15px` with generous line-height (`22px`).
* **Captions & Badge Labels:** Semi-bold `12px` (All-caps with modest tracking for quick scanning).



---

## 🧩 Component Style Guide

* **Buttons:**
* *Primary:* Soft pill-shaped floating buttons (`28px` corner radius) with full color fill and smooth `0px 8px 20px rgba(26,107,92,0.15)` drop shadow.
* *Emergency ("Need One Now"):* Coral Red pill button with an animating warm radial outer glow pulse.


* **Cards & Floating Sheets:** Rounded bottom sheets and floating cards (`24px` border radius) using light borders (`1px solid rgba(255,255,255,0.8)`) on top of soft blur overlays (`backdrop-filter: blur(12px)`).
* **Filter Chips:** Pill shapes (`16px` height padding). Inactive chips feature light mint border and muted text; active chips feature full deep teal fill with high-contrast white text/icons.
* **Toggles:** Soft rounded switches. Inactive = pale gray-teal background (`#E2ECE8`); Active = Deep Teal thumb with Sage green fill.
* **Search Bar:** Floating rounded search container (`56px` height) with embedded location/filter icons, floating gracefully over the top layer of the map.

---

## 📍 Map & Cluster Markers

* **Map Marker Style:**
* Custom tear-drop map pin featuring the **Relief logo** (person inside location pin with leaf shape).
* **Glow Effect:** A soft, circular golden/mint halo layer beneath the pin (`filter: drop-shadow(0px 0px 8px rgba(244, 196, 83, 0.6))`) giving pins a "guiding light" aesthetic.
* **Category Badges:** Small mini-icons appended to pin heads (e.g., Wheelchair icon for RADAR/Changing Places, Baby icon for family rooms).


* **Cluster Marker Style:**
* Soft circular badges in Deep Teal with radial light mint rings surrounding them.
* Displays simple bold numbers in white, expanding smoothly on tap or zoom.



---

## 🎬 Motion & Animation

* **Pin Glow Pulse:** Subtle breathing glow animation (opacity scaling from `0.4` to `0.8` over 3 seconds) on active or recommended pins.
* **Sheet Transition:** Smooth spring-based bottom-sheet slide-up when selecting a facility or applying filters (`damping: 25, stiffness: 300`).
* **Emergency Pulse:** Gentle ripple animation behind the "Need One Now" button to signal immediate assistance without creating panic.

---

## 📐 Recommended Screen Hierarchy & Flow

```
[ Splash Screen ] 
       │
       ▼
[ Smooth Onboarding / Context Sheet ] ──► (Permission Request: Location)
       │
       ▼
[ Main Map / Home Experience ] 
       │
       ├─► Bottom Floating Card: "Need One Now" (Instant Nearest Route)
       ├─► Top Search & Quick Category Chips (Accessible, RADAR, Baby, Gender-Neutral)
       ├─► Filter Modal (Slide-up Sheet)
       └─► Facility Detail (Expanded Sheet / Full View)

```

---

## 📱 Screen-by-Screen Content & Layout

### 1. Splash Screen

* **Background:** Rich watercolor misty green wash with glowing ambient map nodes in the background.
* **Center Content:** Prominent **Relief logo** (white pin with teal leaf emblem) with elegant serif/sans tagline: *"Find Comfort, Feel Relief."*
* **Transition:** Fades smoothly into the location permission onboarding modal rather than abruptly dropping users into a blank map.

### 2. Onboarding / Home Intro (Polished Login Replacement)

* **Layout:** Non-intrusive floating modal sheet over a pre-blurred live map background.
* **Content:**
* Headline: *"Welcome to Relief"*
* Body: *"Find accessible, safe, and comfortable facilities nearby without friction."*
* Quick-select personal preferences (e.g., *"Show RADAR key facilities first"*, *"Need baby changing"*).
* CTA Button: *"Explore Nearby"* (No mandatory login required to view map; optional quick-login for community reviews).



### 3. Main Map Screen

* **Top Area:** Floating search pill with placeholder *"Search town, postcode, or venue..."* and an integrated Filter Icon button. Below it, a horizontal scrolling row of Quick Filters (*"Accessible"*, *"RADAR Key"*, *"Baby Changing"*, *"Free"*).
* **Map Center:** Custom soft pastel vector map layout (muted roads and landmasses to let pins pop). Interactive glowing pins for facilities.
* **Bottom Bar:**
* Prominent floating pill button: **"Need One Now"** (Coral Red, triggers instant route to the closest open, verified facility).
* Subtle bottom navigation bar (Icons: *Map/Explore*, *Saved*, *Community/Contribute*, *Profile*).



### 4. Filters Screen (Advanced Filters)

* **Layout:** Full bottom sheet with a sticky *"Apply Filters"* bottom bar.
* **Background:** Soft watercolor header banner fading into light clean list items.
* **Categories & Toggles:**
* **Accessibility & Key Access:** RADAR Key required, Changing Places, Step-Free / Ramp Access, Grab Rails.
* **Privacy & Environment:** Single Cubicle, Floor-to-Ceiling Doors, Quiet Space, Gender-Neutral.
* **Family & Baby:** Changing Inside Room, Pram Accessible, Family Toilet.
* **Safety & Hygiene:** Free Period Products, Sanitary Bins, Staff Nearby, Well Lit / CCTV.



### 5. Facility Detail Screen

* **Layout:** Expanding sheet with drag handle.
* **Header:** Venue Name (e.g., *"Ty Pawb"*), Walking/Driving distance (`3 mins walk`), Open/Closed status, and Community Rating (e.g., `4.8 ★`).
* **Highlight Badges:** Soft pastel chips for top features (*"RADAR Key Required"*, *"Step-Free"*, *"Very Clean"*).
* **Community Rating Breakdown:** Visual breakdown scales for Cleanliness, Privacy, Accessibility, and Safety.
* **Access Notes Section:** Clear, human-written instructions (e.g., *"Located on the left past reception. Ask staff if locked."*).
* **Primary Actions:** Large *"Get Directions"* button + Community buttons (*"Report Issue"*, *"Update Details"*).

---

## 🤖 Master Prompt for UI Generation (OpenDesign / Google Stitch)

> **Prompt:**
> "Design a modern, accessible, community-driven mobile app UI for 'Relief', a UK toilet finder app. Visual style: soft, calm, reassuring, clean organic aesthetic inspired by studio ghibli watercolor textures and modern iOS design. Primary color palette: Deep Teal (#1A6B5C), Soft Sage (#6CA08E), Warm Golden Amber (#F4C453), Coral Red (#E75F51), on crisp white blurred floating cards (#FFFFFF, 90% opacity). High accessibility contrast (WCAG AAA compliant), typography using Plus Jakarta Sans.
> Include 3 screens side-by-side:
> 1. **Main Map Screen:** Custom soft map background with glowing teal and amber teardrop map pins containing a leaf icon emblem. Top floating rounded search bar with horizontal quick-filter chips (Accessible, RADAR Key, Baby Changing). Bottom floating prominent Coral Red pill button reading 'Need One Now'.
> 2. **Advanced Filters Sheet:** Clean slide-up modal with soft watercolor header. Toggles and chips for Accessibility (RADAR key, Changing Places), Privacy (Single room, quiet space), and Safety.
> 3. **Facility Detail View:** Floating card showing venue name, distance, open/closed badge, accessibility star breakdown, human access instructions, and a large 'Get Directions' CTA button. Aesthetic should be inviting, clean, high-contrast, non-cluttered, and reassuring."
> 
>