export type LogPreference = { wordWrap: boolean; autoScroll: boolean };
const KEY = "simshelf-logs";
export function logPreference(raw: string | null): LogPreference {
  try {
    const value = JSON.parse(raw || "null");
    return {
      wordWrap: typeof value?.wordWrap === "boolean" ? value.wordWrap : true,
      autoScroll:
        typeof value?.autoScroll === "boolean" ? value.autoScroll : true,
    };
  } catch {
    return { wordWrap: true, autoScroll: true };
  }
}
// Also retain session preferences across unmounts when browser storage is unavailable.
let session = logPreference(null);
let initialized = false;
export function readLogPreference(): LogPreference {
  if (initialized) return session;
  initialized = true;
  try {
    session = logPreference(localStorage.getItem(KEY));
  } catch {
    /* session-only */
  }
  return session;
}
export function saveLogPreference(value: LogPreference) {
  session = value;
  try {
    localStorage.setItem(KEY, JSON.stringify(value));
  } catch {
    /* session-only */
  }
}

/** Only explicit upward input can disengage follow. Scroll/resize alone cannot. */
export function followLog(element: HTMLElement, paused: () => void) {
  let following = false;
  let scrollbar = false;
  let touchY: number | null = null;
  let top = element.scrollTop;
  const geometry = () =>
    [element.clientWidth, element.clientHeight, element.scrollHeight].join(":");
  let size = geometry();
  function pause() {
    if (following && element.scrollTop > 0) {
      following = false;
      paused();
    }
  }
  function layout() {
    if (following) element.scrollTop = element.scrollHeight;
    top = element.scrollTop;
    size = geometry();
  }
  const wheel = (event: WheelEvent) => {
    if (event.deltaY < 0 && !event.shiftKey && !event.ctrlKey) pause();
  };
  const key = (event: KeyboardEvent) => {
    if (
      ["ArrowUp", "PageUp", "Home"].includes(event.key) ||
      (event.key === " " && event.shiftKey)
    )
      pause();
  };
  const down = (event: PointerEvent) => {
    touchY = event.pointerType === "touch" ? event.clientY : null;
    const bounds = element.getBoundingClientRect();
    // Only the vertical scrollbar gutter; horizontal dragging must not pause follow.
    scrollbar =
      event.button === 0 &&
      event.clientX >= bounds.left + element.clientLeft + element.clientWidth;
    top = element.scrollTop;
    size = geometry();
  };
  const move = (event: PointerEvent) => {
    if (touchY !== null && event.pointerType === "touch") {
      if (event.clientY > touchY) pause();
      touchY = event.clientY;
    }
  };
  const up = () => {
    scrollbar = false;
    touchY = null;
  };
  const scroll = () => {
    if (scrollbar && geometry() === size && element.scrollTop < top) {
      // The thumb can reach zero in one event; test the previous position.
      if (following && top > 0) {
        following = false;
        paused();
      }
    }
    top = element.scrollTop;
    size = geometry();
  };
  element.addEventListener("wheel", wheel, { passive: true });
  element.addEventListener("keydown", key);
  element.addEventListener("pointerdown", down);
  element.addEventListener("pointermove", move);
  element.addEventListener("scroll", scroll);
  window.addEventListener("pointerup", up);
  window.addEventListener("pointercancel", up);
  window.addEventListener("blur", up);
  const observer = new ResizeObserver(layout);
  observer.observe(element);
  return {
    layout,
    setFollowing(value: boolean) {
      following = value;
      layout();
    },
    dispose() {
      observer.disconnect();
      element.removeEventListener("wheel", wheel);
      element.removeEventListener("keydown", key);
      element.removeEventListener("pointerdown", down);
      element.removeEventListener("pointermove", move);
      element.removeEventListener("scroll", scroll);
      window.removeEventListener("pointerup", up);
      window.removeEventListener("pointercancel", up);
      window.removeEventListener("blur", up);
    },
  };
}
