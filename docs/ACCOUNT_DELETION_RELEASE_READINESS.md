# Relief account-deletion release readiness

**Status:** `SOURCE / RELEASE-READINESS AUDIT`
**Audit date:** 2026-08-14

This is the bounded release-readiness record for the deployed account-deletion
backend. It does not change Supabase, Auth, Storage, subscriptions, or store
console settings.

## Current user path

An authenticated user can open:

`Profile -> Delete account`

The action is in the normal Profile tab, not behind Feature Lab or a developer
route. The screen requires the exact phrase `DELETE MY ACCOUNT`, then shows a
destructive confirmation step.

## Behaviour exposed by the app

The production path now communicates that:

- recent authentication is required;
- the server checks subscription history before cleanup;
- success is shown only after the backend confirms Storage cleanup, governed
  user-linked data cleanup, and Auth deletion;
- canonical facility and provenance records may remain;
- retryable Storage, data-cleanup, Auth-deletion, and service failures do not
  become false success;
- accounts with subscription or payment history are blocked while retention
  and anonymisation handling remains unresolved.

The subscription-history error has a dedicated user-facing message and offers
the in-app data-request information screen. That screen truthfully reports that
no approved support contact or public data-rights URL is configured in this
build. It does not invent a contact, retention period, or deletion outcome.

After successful server confirmation, the client clears its local session and
the user returns to the signed-out application state.

## Public and support surfaces

No public website source, privacy-policy page, support page, or account-deletion
URL exists in this repository. The in-app Legal and support screen is a
truthful placeholder, not a published legal document. A real public URL and a
privacy/data-rights contact must be established before store submission.

The deployed backend therefore does not by itself make Relief release-ready.
The unresolved public/legal surface is a release blocker, while the backend
deployment remains accepted and closed.

## Platform requirements

Apple requires an in-app account-deletion initiation path for apps that support
account creation, and says the option should be easy to find, typically in
account settings. Apple also requires a privacy-policy link in App Store
Connect and an accessible privacy-policy link in the app:

- <https://developer.apple.com/support/offering-account-deletion-in-your-app/>
- <https://developer.apple.com/app-store/review/guidelines/>
- <https://developer.apple.com/help/app-store-connect/manage-app-information/manage-app-privacy/>

Google Play requires an in-app account-deletion path and a web resource where
users can request account and associated-data deletion. Google also requires a
public privacy policy, an in-app privacy-policy link, accurate retention and
deletion disclosures, and completed Data safety declarations:

- <https://support.google.com/googleplay/android-developer/answer/13327111>
- <https://support.google.com/googleplay/android-developer/answer/17190352>
- <https://support.google.com/googleplay/android-developer/answer/10787469>

## Requirement classification

### Satisfied in source or backend

- Normal in-app deletion path from Profile.
- Exact confirmation phrase and destructive reconfirmation.
- Recent-authentication gate.
- Server-confirmed success boundary.
- Fail-closed subscription-history handling.
- No client-supplied target account ID.
- Deployed Edge Function and governed database cleanup contract.

### Requires repository/public-material work

- Approved privacy policy accessible inside the app.
- Public privacy-policy URL.
- Public account/data-deletion request URL.
- Operational support or privacy/data-rights contact.
- Final wording for subscription/payment-history retention and anonymisation.
- Final wording for future photo/Storage deletion once photo uploads become
  public.

### Manual store-console or release tasks

- Add the privacy-policy URL in App Store Connect and Play Console.
- Complete Apple App Privacy answers and Google Play Data safety answers from
  the final production data inventory.
- Complete Google Play's account/data-deletion questions and provide the public
  deletion URL.
- Ensure the store listing, privacy policy, in-app copy, and deletion URL use
  the same approved retention/deletion wording.
- Perform the separate Android Studio physical-device and cloud EAS checks.

## Legal/business review required

Legal or accountable product review is still required for subscription and
payment-history retention, anonymisation, support handling, and any records
that must remain for legal, accounting, canonical, or provenance reasons. No
retention period or guaranteed manual-deletion outcome is stated here.

## Known verification limits

- Production currently has no Storage buckets or objects, so real object
  deletion remains unverified.
- Stale-auth live reproduction remains unverified.
- Reviewer/reporter reference cleanup is source-covered but was not exercised
  against existing production users.
