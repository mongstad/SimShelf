// Each keyed RunDetails instance owns one gate. Older reads cannot undo a save,
// and completion after navigation cannot update the next run or its notices.
export function runRequests() {
  let active = false, saving = false, revision = 0;
  return {
    activate() { active = true; ++revision; },
    dispose() { active = false; ++revision; },
    read() { return active && !saving ? ++revision : null; },
    save() {
      if (!active || saving) return null;
      saving = true;
      return ++revision;
    },
    current(ticket: number) { return active && ticket === revision; },
    finish() { saving = false; ++revision; },
  };
}
