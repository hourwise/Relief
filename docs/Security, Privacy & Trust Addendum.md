# Security, Privacy & Trust Addendum

## Core Rule

Security and privacy must not be deferred. Every feature must be built with the assumption that users may be vulnerable, disabled, elderly, anxious, or sharing sensitive location-related needs.

## Authentication

- Do not require login for basic “Need One Now” search.
- Require login only for:
  - posting reviews
  - uploading photos
  - saving profile preferences
  - reporting repeated edits
  - premium entitlement sync
- Use Supabase Auth.
- Enable email verification.
- Never store passwords directly.
- Do not expose service role keys in the app or web frontend.

## Supabase Security

- Enable Row Level Security on every table.
- Default policy should be deny-all.
- Add explicit policies per action.
- Users may only edit their own profile, reviews, reports and saved places.
- Public facility data should be read-only from the client.
- Facility creation/editing should go into a moderation queue, not directly into live data.
- Admin actions must use server-side functions only.

## API Keys

- No secret keys in Expo public config.
- No Supabase service role key in mobile app.
- No map provider secret keys in client code.
- Use Vercel environment variables for server-only keys.
- Rotate keys if exposed.
- Use separate dev/staging/prod keys.

## Location Privacy

- Request location permission only when needed.
- Explain why location is needed in plain language.
- Do not continuously track users.
- Do not store precise user location history by default.
- Store only approximate analytics if needed.
- Allow manual postcode/town search for users who deny location.
- Clear location from memory when no longer needed.

## User Profiles

- Keep profiles minimal.
- Avoid asking for medical conditions directly.
- Use preference modes instead:
  - Accessibility mode
  - Family mode
  - IBS-friendly mode
  - Quiet mode
- Store preferences as optional filters, not health declarations.

## Reviews & Reports

- Prevent anonymous abuse:
  - rate limits
  - duplicate report checks
  - moderation queue for photos
  - admin review tools
- Do not allow users to post private personal details.
- Strip EXIF/location metadata from uploaded photos.
- Blur faces if possible before public display.
- Add “Report this photo/review” option.

## Contact Forms

- Use spam protection.
- Validate all inputs.
- Sanitize submitted text.
- Never trust client-side validation alone.
- Store form submissions server-side.
- Do not expose submitter email publicly.
- Add consent checkbox for contact.

## GDPR

- Publish Privacy Policy before beta.
- Publish Terms before payments.
- Provide:
  - account deletion
  - data export request
  - delete review/photo request
  - contact email for privacy requests
- Track consent for marketing emails separately.
- Do not add users to mailing lists from support forms unless they opt in.

## Payments

- Entitlements must be checked server-side or through RevenueCat.
- Do not unlock Plus features based only on local device state.
- Cache entitlement locally only for graceful offline use.
- Restore purchases must be available.
- Handle refunds, cancellations and expired subscriptions correctly.

## Web App / Vercel

- Use HTTPS only.
- Set secure headers.
- Use environment variables.
- Validate all API routes.
- Rate-limit forms.
- Log errors without logging sensitive personal data.
- Keep admin pages protected.

## Admin Panel

- Admin access must be role-based.
- Admin role must not be editable by the user.
- All admin actions should be logged.
- Moderation actions:
  - approve facility
  - reject facility
  - edit facility
  - remove photo
  - remove review
  - mark report resolved

## Testing

Before release, test:

- RLS policies
- unauthenticated access
- authenticated user access
- admin-only access
- payment unlock/restore/cancel flows
- form spam protection
- location denied flow
- account deletion
- photo metadata stripping

## Non-Negotiables

- No service role key in client.
- No live facility edits without moderation.
- No unnecessary location history.
- No medical-condition requirement.
- No payment unlocks based only on client state.