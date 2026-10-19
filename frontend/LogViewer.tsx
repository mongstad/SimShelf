import React, { useEffect, useLayoutEffect, useRef, useState } from "react";
import { api } from "./api";
import {
  followLog,
  readLogPreference,
  saveLogPreference,
  type LogPreference,
} from "./logPresentation";

export function LogViewer({
  runId,
  stream,
}: {
  runId: string;
  stream: string;
}) {
  const [preference, setPreference] = useState(readLogPreference);
  const [log, setLog] = useState({ text: "", truncated: false });
  const [error, setError] = useState("");
  const panel = useRef<HTMLPreElement>(null);
  const follow = useRef<ReturnType<typeof followLog> | null>(null);
  function change(key: keyof LogPreference, value: boolean) {
    setPreference((previous) => {
      const next = { ...previous, [key]: value };
      saveLogPreference(next);
      return next;
    });
  }
  useLayoutEffect(() => {
    const controller = followLog(panel.current!, () =>
      change("autoScroll", false),
    );
    follow.current = controller;
    return () => {
      controller.dispose();
      follow.current = null;
    };
  }, []);
  useLayoutEffect(() => {
    follow.current?.setFollowing(preference.autoScroll);
  }, [preference.autoScroll, preference.wordWrap, log.text]);
  useEffect(() => {
    let live = true;
    let timer: ReturnType<typeof setTimeout>;
    async function load() {
      try {
        const result = await api<{ text: string; truncated: boolean }>(
          `/runs/${runId}/logs?stream=${stream}`,
        );
        if (live) {
          setLog(result);
          setError("");
        }
      } catch (e) {
        if (live) setError((e as Error).message);
      } finally {
        // Serialize requests so a slow older poll cannot replace newer output.
        if (live) timer = setTimeout(load, 3000);
      }
    }
    load();
    return () => {
      live = false;
      clearTimeout(timer);
    };
  }, [runId, stream]);
  return (
    <>
      {error && <p role="alert">{error}</p>}
      {log.truncated && (
        <p className="muted small">Showing the most recent 200 KB.</p>
      )}
      <pre
        ref={panel}
        className={`log-block live-log${preference.wordWrap ? " wrap" : ""}`}
        tabIndex={0}
        aria-label={
          stream === "stderr" ? "Standard error log" : "Standard output log"
        }
      >
        {log.text || "No output was recorded for this stream."}
      </pre>
      <div className="log-controls">
        <label>
          Word wrap
          <input
            type="checkbox"
            checked={preference.wordWrap}
            onChange={(e) => change("wordWrap", e.target.checked)}
          />
        </label>
        <label>
          Auto-scroll
          <input
            type="checkbox"
            checked={preference.autoScroll}
            onChange={(e) => change("autoScroll", e.target.checked)}
          />
        </label>
      </div>
    </>
  );
}
