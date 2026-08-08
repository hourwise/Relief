// ============================================================
// Project "Relief" — Branded handoff coordination
// ============================================================
// The handoff has to live ABOVE the navigator, not inside
// FindScreen.
//
// Auth is a RootStack modal presented over Main, and Main stays
// mounted underneath it. A handoff owned by FindScreen therefore
// never replays when a guest signs in — FindScreen simply was
// never unmounted, so its "first run" state had already been
// consumed. Hoisting it here means one component can cover both
// cold start and sign-in, which also guarantees the user never
// sees two loading screens back to back.
// ============================================================

import React, { createContext, useCallback, useContext, useMemo, useRef, useState } from 'react';

/** Why the handoff is showing. Drives the status line, and nothing else. */
export type HandoffReason = 'startup' | 'sign-in';

interface HandoffContextValue {
  reason: HandoffReason | null;
  /** Set by Find when its first facility load has settled. */
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
  reportFindReady: () => {},
  beginSignInHandoff: () => {},
  isActive: false,
  dismissed: true,
  markDismissed: () => {},
});

export const useHandoff = () => useContext(HandoffContext);

export const HandoffProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [reason, setReason] = useState<HandoffReason | null>('startup');
  const [findReady, setFindReady] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  // Guards against a late readiness report from the previous session ending a
  // freshly started sign-in handoff.
  const generation = useRef(0);

  const reportFindReady = useCallback(() => setFindReady(true), []);

  const beginSignInHandoff = useCallback(() => {
    generation.current += 1;
    setFindReady(false);
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
      reportFindReady,
      beginSignInHandoff,
      // Active while a reason is set and Find has not yet reported ready.
      isActive: reason !== null && !findReady,
      dismissed,
      markDismissed,
    }),
    [reason, findReady, dismissed, reportFindReady, beginSignInHandoff, markDismissed],
  );

  return <HandoffContext.Provider value={value}>{children}</HandoffContext.Provider>;
};
