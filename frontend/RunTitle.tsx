import React from "react";

export function RunTitle({ name, favorite, busy, toggle }: {
  name: string; favorite: boolean; busy: boolean; toggle: () => void;
}) {
  const label = favorite ? "Unfavorite run" : "Favorite run";
  return <div className="run-title-row">
    <h1>{name}</h1>
    <button type="button" className="icon-button run-favorite"
      aria-label={label} title={label} aria-pressed={favorite}
      disabled={busy} onClick={toggle}>
      <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true"
        fill={favorite ? "currentColor" : "none"} stroke="currentColor"
        strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
        <path d="m12 3 2.78 5.63L21 9.54l-4.5 4.39 1.06 6.2L12 17.2l-5.56 2.93 1.06-6.2L3 9.54l6.22-.91Z" />
      </svg>
    </button>
  </div>;
}
