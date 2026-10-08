declare module 'claude-code' {
  interface PluginState {
    'handoff-mod': {
      /** Next percentage at which T1 asks; 0 means "use the configured threshold". */
      nextAt: number
      /** The threshold T1 last asked about; 0 means none. */
      askedAt: number
      /** "Do not ask again this session". */
      suppressed: boolean
      /** A $.ui.ask is open (T2). */
      askPending: boolean
      /** When the handoff turn started (ms), 0 when none; used to find the new file. */
      handoffStartedAt: number
      /** Turns completed since the handoff started; used to decide when to say that no file appeared. */
      handoffTurns: number
      /** The percentage the open T1 prompt reports; 0 while no prompt is open. */
      t1Percent: number
      /** The start-up list was skipped, resumed or dismissed in this session. */
      listDone: boolean
      /** The folded part of the start-up list was asked for (button or `/handoff-resume all`); D16. */
      expanded: boolean
    }
  }
}
