"""Seeded orchard layout, rendered to an SDF world and a ground-truth file.

Pure Python (numpy only) so it can be tested without ROS or Gazebo.

World layout: tree rows run along +x. Row ``i`` sits at ``y = i * row_spacing``
and tree ``j`` of a row at ``x = j * tree_spacing``, both plus a uniform jitter.
Objects go either in an aisle, in a band next to a tree line so the aisle center
stays drivable, or in the outer band of the two headlands beyond the row ends.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any

import numpy as np

LABELS = ("tree", "crate", "barrel", "person")
OBJECT_LABELS = ("crate", "barrel", "person")


@dataclass(frozen=True)
class ModelSpec:
    """Gazebo model used for a label and the axis-aligned box that encloses it.

    ``size`` is (x, y, z) in meters in the model frame; the model origin is on
    the ground at the center of the footprint. ``radius`` is the footprint
    radius used for clearance checks.
    """

    uri: str
    size: tuple[float, float, float]
    radius: float


@dataclass(frozen=True)
class OrchardParams:
    """Parameters of one generated world. Distances in meters, angles in radians."""

    name: str
    seed: int
    rows: int
    trees_per_row: int
    row_spacing: float
    tree_spacing: float
    jitter: float
    counts: dict[str, int]
    spawn: tuple[float, float, float]
    headland: float
    min_object_distance: float
    min_spawn_distance: float
    trunk_clearance: float
    aisle_band: float
    models: dict[str, ModelSpec]
    max_attempts: int = 10_000

    @classmethod
    def from_dict(cls, name: str, data: dict[str, Any]) -> OrchardParams:
        models = {
            label: ModelSpec(uri=m["uri"], size=tuple(m["size"]), radius=float(m["radius"]))
            for label, m in data["models"].items()
        }
        spawn = data["spawn"]
        return cls(
            name=name,
            seed=int(data["seed"]),
            rows=int(data["rows"]),
            trees_per_row=int(data["trees_per_row"]),
            row_spacing=float(data["row_spacing"]),
            tree_spacing=float(data["tree_spacing"]),
            jitter=float(data["jitter"]),
            counts={label: int(data["counts"][label]) for label in OBJECT_LABELS},
            spawn=(float(spawn["x"]), float(spawn["y"]), float(spawn["yaw"])),
            headland=float(data["headland"]),
            min_object_distance=float(data["min_object_distance"]),
            min_spawn_distance=float(data["min_spawn_distance"]),
            trunk_clearance=float(data["trunk_clearance"]),
            aisle_band=float(data["aisle_band"]),
            models=models,
        )


@dataclass(frozen=True)
class PlacedObject:
    id: str
    label: str
    x: float
    y: float
    yaw: float


@dataclass
class Orchard:
    params: OrchardParams
    objects: list[PlacedObject] = field(default_factory=list)

    @property
    def trees(self) -> list[PlacedObject]:
        return [o for o in self.objects if o.label == "tree"]


def generate(params: OrchardParams) -> Orchard:
    """Place trees and objects. Same params, same orchard."""
    rng = np.random.default_rng(params.seed)
    orchard = Orchard(params)

    for i in range(params.rows):
        for j in range(params.trees_per_row):
            dx, dy = rng.uniform(-params.jitter, params.jitter, size=2)
            orchard.objects.append(
                PlacedObject(
                    id=f"tree_{len(orchard.objects) + 1}",
                    label="tree",
                    x=round(float(j * params.tree_spacing + dx), 3),
                    y=round(float(i * params.row_spacing + dy), 3),
                    yaw=round(float(rng.uniform(-math.pi, math.pi)), 3),
                )
            )

    for label in OBJECT_LABELS:
        for n in range(1, params.counts[label] + 1):
            x, y = _sample_free_point(params, orchard, label, rng)
            orchard.objects.append(
                PlacedObject(
                    id=f"{label}_{n}",
                    label=label,
                    x=round(float(x), 3),
                    y=round(float(y), 3),
                    yaw=round(float(rng.uniform(-math.pi, math.pi)), 3),
                )
            )
    return orchard


def _candidate(params: OrchardParams, rng: np.random.Generator) -> tuple[float, float]:
    """Draw a point in an aisle band or in a headland band, with equal odds per band."""
    x_end = (params.trees_per_row - 1) * params.tree_spacing
    y_end = (params.rows - 1) * params.row_spacing
    n_aisles = params.rows - 1
    # Two bands per aisle (one along each tree line) plus one per headland.
    band = int(rng.integers(0, 2 * n_aisles + 2))
    if band < 2 * n_aisles:
        aisle, side = divmod(band, 2)
        offset = rng.uniform(params.trunk_clearance, params.aisle_band)
        y_line = (aisle + side) * params.row_spacing
        y = y_line + offset if side == 0 else y_line - offset
        x = rng.uniform(0.0, x_end)
        return x, y
    outer = rng.uniform(params.headland - params.aisle_band, params.headland - 0.5)
    x = -outer if band == 2 * n_aisles else x_end + outer
    y = rng.uniform(0.0, y_end)
    return x, y


def _is_free(params: OrchardParams, orchard: Orchard, label: str, x: float, y: float) -> bool:
    radius = params.models[label].radius
    sx, sy, _ = params.spawn
    if math.hypot(x - sx, y - sy) < params.min_spawn_distance:
        return False
    tree_r = params.models["tree"].radius
    for obj in orchard.objects:
        d = math.hypot(x - obj.x, y - obj.y)
        if obj.label == "tree":
            if d < tree_r + params.trunk_clearance + radius:
                return False
        elif d < params.min_object_distance:
            return False
    return True


def _sample_free_point(
    params: OrchardParams, orchard: Orchard, label: str, rng: np.random.Generator
) -> tuple[float, float]:
    for _ in range(params.max_attempts):
        x, y = _candidate(params, rng)
        if _is_free(params, orchard, label, x, y):
            return x, y
    raise ValueError(
        f"{params.name}: no free spot for a {label} after {params.max_attempts} attempts; "
        "reduce the object counts or the clearances"
    )


def to_ground_truth(orchard: Orchard) -> dict[str, Any]:
    """Ground truth in the world frame: one entry per object with its bounding box."""
    p = orchard.params
    sx, sy, syaw = p.spawn
    objects = []
    for obj in orchard.objects:
        size = p.models[obj.label].size
        objects.append(
            {
                "id": obj.id,
                "label": obj.label,
                "x": obj.x,
                "y": obj.y,
                "z": round(size[2] / 2.0, 3),
                "yaw": obj.yaw,
                "size": [float(s) for s in size],
            }
        )
    return {
        "world": p.name,
        "seed": p.seed,
        "frame": "world",
        "spawn": {"x": sx, "y": sy, "yaw": syaw},
        "objects": objects,
    }


def to_sdf(orchard: Orchard) -> str:
    """Render the orchard as an SDF 1.9 world."""
    p = orchard.params
    includes = "\n".join(
        f"""    <include>
      <uri>{p.models[o.label].uri}</uri>
      <name>{o.id}</name>
      <pose>{o.x} {o.y} 0 0 0 {o.yaw}</pose>
    </include>"""
        for o in orchard.objects
    )
    return f"""<?xml version="1.0"?>
<!-- Generated by agrinav_gazebo/generate_orchard (world {p.name}, seed {p.seed}).
     Do not edit: regenerate instead. -->
<sdf version="1.9">
  <world name="{p.name}">
    <physics name="1ms" type="ignored">
      <max_step_size>0.001</max_step_size>
      <real_time_factor>1.0</real_time_factor>
    </physics>
    <plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics"/>
    <plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands"/>
    <plugin filename="gz-sim-scene-broadcaster-system"
            name="gz::sim::systems::SceneBroadcaster"/>
    <plugin filename="gz-sim-sensors-system" name="gz::sim::systems::Sensors">
      <render_engine>ogre2</render_engine>
    </plugin>
    <plugin filename="gz-sim-imu-system" name="gz::sim::systems::Imu"/>
    <plugin filename="gz-sim-contact-system" name="gz::sim::systems::Contact"/>

    <!-- No shadows: the sensors render on the CPU when there is no GPU (CI,
         plain containers) and shadow maps add cost without helping perception. -->
    <scene>
      <ambient>0.6 0.6 0.6 1</ambient>
      <background>0.62 0.77 0.92 1</background>
      <shadows>false</shadows>
    </scene>

    <light type="directional" name="sun">
      <cast_shadows>false</cast_shadows>
      <pose>0 0 30 0 0 0</pose>
      <diffuse>0.9 0.9 0.85 1</diffuse>
      <specular>0.2 0.2 0.2 1</specular>
      <direction>-0.4 0.3 -0.85</direction>
    </light>

    <include>
      <uri>model://orchard_ground</uri>
      <name>ground</name>
    </include>

{includes}
  </world>
</sdf>
"""
