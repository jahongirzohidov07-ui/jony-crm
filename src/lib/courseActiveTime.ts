/** Foreground, focused, recently engaged time; never a proficiency score. */
export class CourseActiveTime {
  private total = 0;
  private last: number | null = null;
  private touched: number | null = null;
  engage(now: number) { this.tick(now, true); this.touched = now; this.last = now; }
  tick(now: number, active: boolean) {
    if (this.last !== null && this.touched !== null && active) {
      this.total += Math.max(0, Math.min(now, this.touched + 60000) - this.last);
      this.total = Math.min(this.total, 600000);
    }
    this.last = active ? now : null;
  }
  seconds() { return Math.floor(this.total / 1000); }
  reset() { this.total = 0; this.last = null; this.touched = null; }
}
