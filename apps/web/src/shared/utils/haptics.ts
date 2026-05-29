/**
 * VirtualHaptic Utility
 * Mimics macOS trackpad haptics using subtle audio and visual cues.
 */

class VirtualHaptic {
  private audioCtx: AudioContext | null = null;

  private init() {
    if (!this.audioCtx) {
      const AudioCtxClass = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      this.audioCtx = new AudioCtxClass();
    }
  }

  /**
   * Plays a subtle "tick" sound that mimics a physical haptic bump.
   */
  public tick() {
    try {
      this.init();
      if (!this.audioCtx) return;

      const osc = this.audioCtx.createOscillator();
      const gain = this.audioCtx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(150, this.audioCtx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(0.01, this.audioCtx.currentTime + 0.1);

      gain.gain.setValueAtTime(0.1, this.audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, this.audioCtx.currentTime + 0.1);

      osc.connect(gain);
      gain.connect(this.audioCtx.destination);

      osc.start();
      osc.stop(this.audioCtx.currentTime + 0.1);
    } catch {
      // Ignore if audio is blocked or fails
    }
  }

  /**
   * Plays a slightly firmer "snap" sound for drops.
   */
  public snap() {
    try {
      this.init();
      if (!this.audioCtx) return;

      const osc = this.audioCtx.createOscillator();
      const gain = this.audioCtx.createGain();

      osc.type = 'triangle';
      osc.frequency.setValueAtTime(100, this.audioCtx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(0.01, this.audioCtx.currentTime + 0.15);

      gain.gain.setValueAtTime(0.15, this.audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, this.audioCtx.currentTime + 0.15);

      osc.connect(gain);
      gain.connect(this.audioCtx.destination);

      osc.start();
      osc.stop(this.audioCtx.currentTime + 0.15);
    } catch {
      // Ignore
    }
  }
}

export const haptics = new VirtualHaptic();
