import React from "react";

export function RunHistoryTitle({ name, favorite }: { name: string; favorite: boolean }) {
  return <span className="run-history-title">
    <span>{name}</span>
    {favorite && <span className="favorite-star">★</span>}
  </span>;
}
