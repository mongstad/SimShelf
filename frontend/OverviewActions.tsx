import React from "react";
import { Icon } from "./Icon";
import type { Simulation } from "./types";

export function OverviewActions({ simulation, hasSimulations, add, record, launch }: {
  simulation?: Pick<Simulation, "available">;
  hasSimulations: boolean;
  add: () => void;
  record: () => void;
  launch: () => void;
}) {
  return <div className="heading-actions">
    {!simulation && <button onClick={add}>
      <Icon name="plus" />
      Add simulation
    </button>}
    <button onClick={record} disabled={!hasSimulations}>
      <Icon name="terminal" />
      Terminal / editor
    </button>
    {simulation && <button className="primary" title="Configure and launch this simulation"
      disabled={!simulation.available} onClick={launch}>
      <Icon name="plus" />
      New run…
    </button>}
  </div>;
}
