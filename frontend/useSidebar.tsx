import React, { useEffect, useRef, useState } from "react";

const KEY = "simshelf-sidebar";
const MIN = 200;
const MAX = 480;
const DEFAULT = 228;
export function sidebarPreference(raw: string | null): {
  width: number;
  collapsed: boolean;
} {
  try {
    const value = JSON.parse(raw || "null");
    return {
      width:
        typeof value?.width === "number" && Number.isFinite(value.width)
          ? Math.round(Math.min(MAX, Math.max(MIN, value.width)))
          : DEFAULT,
      collapsed: value?.collapsed === true,
    };
  } catch {
    return { width: DEFAULT, collapsed: false };
  }
}
export function sidebarMaximum(viewport: number) {
  return Math.max(MIN, Math.min(MAX, viewport - 480));
}

export function useSidebar() {
  const [preference, setPreference] = useState(() => {
    try {
      return sidebarPreference(localStorage.getItem(KEY));
    } catch {
      return sidebarPreference(null);
    }
  });
  const [viewport, setViewport] = useState(window.innerWidth);
  const [dragging, setDragging] = useState(false);
  const drag = useRef<{
    id: number;
    x: number;
    width: number;
    target: HTMLElement;
  } | null>(null);
  const maximum = sidebarMaximum(viewport);
  const width = Math.min(preference.width, maximum);
  function stop() {
    const active = drag.current;
    drag.current = null;
    if (active?.target.hasPointerCapture(active.id))
      active.target.releasePointerCapture(active.id);
    setDragging(false);
  }
  useEffect(() => {
    // Browser-local presentation only. Unavailable/quota-limited storage must not block navigation.
    try {
      localStorage.setItem(KEY, JSON.stringify(preference));
    } catch {
      /* session-only */
    }
  }, [preference]);
  useEffect(() => {
    const resize = () => {
      stop();
      setViewport(window.innerWidth);
    };
    const leave = (event: PointerEvent) => {
      if (!event.relatedTarget) stop();
    };
    window.addEventListener("resize", resize);
    window.addEventListener("blur", stop);
    window.addEventListener("pointerout", leave);
    return () => {
      window.removeEventListener("resize", resize);
      window.removeEventListener("blur", stop);
      window.removeEventListener("pointerout", leave);
      const active = drag.current;
      if (active?.target.hasPointerCapture(active.id))
        active.target.releasePointerCapture(active.id);
    };
  }, []);
  const setWidth = (next: number) =>
    setPreference((p) => ({
      ...p,
      width: Math.round(Math.max(MIN, Math.min(maximum, next))),
    }));
  const separator =
    !preference.collapsed && viewport > 650 ? (
      <div
        className="sidebar-resizer"
        role="separator"
        tabIndex={0}
        aria-label="Resize sidebar"
        aria-orientation="vertical"
        aria-controls="sidebar-navigation"
        aria-valuemin={MIN}
        aria-valuemax={maximum}
        aria-valuenow={width}
        aria-valuetext={`${width} pixels`}
        title="Resize sidebar: drag, or use Left/Right arrows; Home/End for limits"
        onPointerDown={(event) => {
          if (event.button !== 0 || !event.isPrimary) return;
          event.preventDefault();
          event.currentTarget.focus();
          event.currentTarget.setPointerCapture(event.pointerId);
          drag.current = {
            id: event.pointerId,
            x: event.clientX,
            width,
            target: event.currentTarget,
          };
          setDragging(true);
        }}
        onPointerMove={(event) => {
          if (drag.current?.id === event.pointerId)
            setWidth(drag.current.width + event.clientX - drag.current.x);
        }}
        onPointerUp={stop}
        onPointerCancel={stop}
        onLostPointerCapture={stop}
        onClick={(event) => {
          event.preventDefault();
          event.stopPropagation();
        }}
        onKeyDown={(event) => {
          const next =
            event.key === "ArrowLeft"
              ? width - 10
              : event.key === "ArrowRight"
                ? width + 10
                : event.key === "Home"
                  ? MIN
                  : event.key === "End"
                    ? maximum
                    : null;
          if (next !== null) {
            event.preventDefault();
            setWidth(next);
          }
        }}
      />
    ) : null;
  const label = preference.collapsed ? "Expand sidebar" : "Collapse sidebar";
  const toggle = (
    <button
      className="icon-button sidebar-toggle"
      aria-label={label}
      title={label}
      aria-expanded={!preference.collapsed}
      aria-controls="sidebar-navigation"
      onClick={() => {
        stop();
        setPreference((p) => ({ ...p, collapsed: !p.collapsed }));
      }}
    >
      <svg
        width="18"
        height="18"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.6"
        aria-hidden="true"
      >
        <rect x="3" y="4" width="18" height="16" rx="2" />
        <path d="M9 4v16" />
        <path d={preference.collapsed ? "m13 9 3 3-3 3" : "m17 9-3 3 3 3"} />
      </svg>
    </button>
  );
  return {
    collapsed: preference.collapsed,
    dragging,
    separator,
    toggle,
    style: { "--sidebar-width": `${width}px` } as React.CSSProperties,
  };
}
