# Accessibility & Simplicity Addendum

## Core Principle

The app must be usable by an elderly person, a disabled user, or someone in distress within 10 seconds of opening it.

Design for:
- Low confidence with technology
- Poor eyesight
- Shaky hands
- Cognitive overload
- Anxiety/urgency
- Screen readers
- One-handed use

## Navigation Rules

- No more than 3 main tabs:
  - Find
  - Saved
  - Profile
- Home screen must have one obvious primary action:
  - “Need One Now”
- Avoid hidden menus where possible.
- Avoid gesture-only controls.
- Every icon must have a text label.
- Every important action must be reachable by tapping, not swiping.

## Button Rules

- Minimum tap target: 48x48 px.
- Primary buttons should be large and full-width where possible.
- Use plain words:
  - “Find nearby”
  - “Directions”
  - “Save”
  - “Report closed”
- Avoid vague labels:
  - “Submit”
  - “Proceed”
  - “Manage”

## Text Rules

- Use large default text.
- Support device font scaling.
- Avoid tiny grey text.
- Minimum body text: 16px.
- Important labels: 18–22px.
- Use short sentences.
- Avoid jargon.

## Visual Rules

- High contrast mode required.
- Do not rely on colour alone.
- Icons must be paired with text.
- Use calm teal theme, but ensure accessibility contrast.
- Keep cards simple:
  - Name
  - Distance
  - Open/Closed
  - Accessibility
  - Directions button

## Emergency Flow

The “Need One Now” flow should require no searching.

When tapped:
1. Ask for location permission if needed.
2. Show nearest suitable open facility.
3. Show distance and walking time.
4. Show one large “Directions” button.
5. Show backup options underneath.

No account should be required for this flow.

## Elder Mode

Add an optional simplified mode.

Features:
- Larger text
- Larger buttons
- Reduced filters
- Simplified home screen
- Voice guidance
- “Call family/contact” optional shortcut
- Fewer animations
- Stronger contrast

## Accessibility Mode

Include filters for:
- Wheelchair access
- Disabled toilet
- RADAR key
- Changing Places
- Step-free route
- Lift available
- Grab rails
- Emergency cord
- Wide doorway

## Cognitive Accessibility

- Avoid clutter.
- Use progressive disclosure.
- Show only essential information first.
- Put advanced filters behind “More filters”.
- Use reassuring confirmation messages:
  - “Route opened”
  - “Saved”
  - “Thanks, report received”

## Offline/Low Signal Behaviour

If signal is poor:
- Show last known nearby facilities.
- Show saved favourites.
- Allow directions to open in external maps.
- Clearly say when data may be outdated.

## Testing Requirement

Test with:
- Elderly users
- Disabled users
- IBS/Crohn’s users
- Parents with children
- Neurodivergent users
- Users with poor eyesight

Each test should answer:
- Can they find a nearby facility in under 10 seconds?
- Can they understand whether it is open?
- Can they start directions without help?
- Can they apply key filters without confusion?

## React Native / Expo Implementation Notes

Use:
- `AccessibilityInfo`
- `accessibilityLabel`
- `accessibilityHint`
- `accessibilityRole`
- `allowFontScaling`
- `Pressable` with large hitSlop
- reduced motion support
- haptic feedback for key actions
- screen reader testing on iOS and Android

Avoid:
- unlabeled icons
- tiny map pins without list alternatives
- drag-only map interactions
- complex onboarding
- mandatory account creation before use