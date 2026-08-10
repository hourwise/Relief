// ============================================================
// Project "Relief" — Branded handoff coordination
// ============================================================
// The handoff lives ABOVE the navigator so it can cover both
// cold start and sign-in transitions.
//
// Readiness is reported by the root entry screen. Find may also
// report its own first-load completion, but it is a lazy tab and
// must never be required before Home can be shown.
// ============================================================

import React, { createContext, useCallback, useContext, useMemo, useRef, useState } from 'react';

/** Why the handoff is showing. Drives the status line, and nothing else. */
export type HandoffReason = 'startup' | 'sign-in';

interface HandoffContextValue {
  reason: HandoffReason | null;
  /** Set by the root app once its startup decision and entry screen are ready. */
  reportAppReady: () => void;
  /** Kept for Find's own loading lifecycle; it also satisfies the handoff. */
  reportFindReady: () => void;
  /** Raised by the navigator when a sign-in completes. */
  beginSignInHandoff: () => void;
  /** True while the overlay should be on screen. */
  isActive: boolean;
  dismissed: boolean;
  markDismissed: () => void;
}

const HandoffContext = createContext<HandoffContextValue>({
  reason: null,
  reportAppReady: () => {},
  reportFindReady: () => {},
  beginSignInHandoff: () => {},
  isActive: false,
  dismissed: true,
  markDismissed: () => {},
});

export const useHandoff = () => useContext(HandoffContext);

export const HandoffProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [reason, setReason] = useState<HandoffReason | null>('startup');
  const [appReady, setAppReady] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  // Guards against a late readiness report from the previous session ending a
  // freshly started sign-in handoff.
  const generation = useRef(0);

  const reportAppReady = useCallback(() => setAppReady(true), []);
  const reportFindReady = useCallback(() => setAppReady(true), []);

  const beginSignInHandoff = useCallback(() => {
    generation.current += 1;
    setAppReady(false);
    setDismissed(false);
    setReason('sign-in');
  }, []);

  const markDismissed = useCallback(() => {
    setDismissed(true);
    setReason(null);
  }, []);

  const value = useMemo<HandoffContextValue>(
    () => ({
      reason,
      reportAppReady,
      reportFindReady,
      beginSignInHandoff,
      // Active while a reason is set and the root app has not reported ready.
      isActive: reason !== null && !appReady,
      dismissed,
      markDismissed,
    }),
    [
      reason,
      appReady,
      dismissed,
      reportAppReady,
      reportFindReady,
      beginSignInHandoff,
      markDismissed,
    ],
  );

  return <HandoffContext.Provider value={value}>{children}</HandoffContext.Provider>;
};
