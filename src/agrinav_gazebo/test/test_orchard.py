"""Generator properties: determinism, clearances and agreement with the versioned files."""

import math
from pathlib import Path

import pytest
import yaml

from agrinav_gazebo.generate_orchard import dump_ground_truth, load_params
from agrinav_gazebo.orchard import generate, to_ground_truth, to_sdf

PKG = Path(__file__).resolve().parents[1]
CONFIG = PKG / "config" / "worlds.yaml"
WORLDS = ["orchard_small", "orchard"]


@pytest.fixture(params=WORLDS)
def params(request):
    return load_params(CONFIG, request.param)


def test_same_seed_same_world(params) -> None:
    assert to_sdf(generate(params)) == to_sdf(generate(params))


def test_different_seed_different_world(params) -> None:
    other = type(params)(**{**params.__dict__, "seed": params.seed + 1})
    assert to_ground_truth(generate(params)) != to_ground_truth(generate(other))


def test_object_counts(params) -> None:
    orchard = generate(params)
    labels = [o.label for o in orchard.objects]
    assert labels.count("tree") == params.rows * params.trees_per_row
    for label, count in params.counts.items():
        assert labels.count(label) == count


def test_ids_are_unique_and_numbered(params) -> None:
    ids = [o.id for o in generate(params).objects]
    assert len(ids) == len(set(ids))
    assert "crate_1" in ids and "tree_1" in ids


def test_clearances(params) -> None:
    orchard = generate(params)
    objects = [o for o in orchard.objects if o.label != "tree"]
    sx, sy, _ = params.spawn
    tree_r = params.models["tree"].radius
    for obj in objects:
        r = params.models[obj.label].radius
        assert math.hypot(obj.x - sx, obj.y - sy) >= params.min_spawn_distance, obj.id
        for tree in orchard.trees:
            gap = math.hypot(obj.x - tree.x, obj.y - tree.y) - tree_r - r
            # Never inside or touching a trunk, and at least the configured clearance.
            assert gap >= params.trunk_clearance, (obj.id, tree.id)
        for other in objects:
            if other is not obj:
                d = math.hypot(obj.x - other.x, obj.y - other.y)
                assert d >= params.min_object_distance, (obj.id, other.id)


def test_aisle_center_stays_free(params) -> None:
    """Objects inside the orchard sit within aisle_band of a tree line."""
    orchard = generate(params)
    x_end = (params.trees_per_row - 1) * params.tree_spacing
    for obj in orchard.objects:
        if obj.label == "tree" or not 0.0 <= obj.x <= x_end:
            continue
        offset = obj.y % params.row_spacing
        to_line = min(offset, params.row_spacing - offset)
        assert to_line <= params.aisle_band + 1e-9, obj.id


def test_impossible_layout_raises(params) -> None:
    crowded = type(params)(
        **{**params.__dict__, "counts": {"crate": 500, "barrel": 0, "person": 0}}
    )
    with pytest.raises(ValueError, match="no free spot"):
        generate(crowded)


@pytest.mark.parametrize("world", WORLDS)
def test_versioned_ground_truth_is_current(world: str) -> None:
    expected = dump_ground_truth(to_ground_truth(generate(load_params(CONFIG, world))))
    versioned = (PKG / "worlds" / world / "ground_truth.yaml").read_text()
    assert versioned == expected, "regenerate with generate_orchard --ground-truth"
    assert yaml.safe_load(versioned)["spawn"] == {"x": -3.0, "y": 3.0, "yaw": 0.0}
