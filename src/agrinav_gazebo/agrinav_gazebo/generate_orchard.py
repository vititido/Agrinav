"""Generate an orchard world (.sdf) and its ground truth from config/worlds.yaml.

ros2 run agrinav_gazebo generate_orchard orchard_small --sdf out.sdf
ros2 run agrinav_gazebo generate_orchard orchard_small --ground-truth gt.yaml
"""

import argparse
from pathlib import Path

import yaml

from agrinav_gazebo.orchard import OrchardParams, generate, to_ground_truth, to_sdf


def load_params(config: Path, world: str) -> OrchardParams:
    worlds = yaml.safe_load(config.read_text())["worlds"]
    if world not in worlds:
        raise SystemExit(f"unknown world '{world}', expected one of {sorted(worlds)}")
    return OrchardParams.from_dict(world, worlds[world])


def dump_ground_truth(data: dict) -> str:
    return yaml.safe_dump(data, sort_keys=False, default_flow_style=None, width=99)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("world", help="world name in the config file")
    parser.add_argument("--config", type=Path, required=True, help="path to worlds.yaml")
    parser.add_argument("--sdf", type=Path, help="write the SDF world here")
    parser.add_argument("--ground-truth", type=Path, help="write ground_truth.yaml here")
    args = parser.parse_args(argv)

    orchard = generate(load_params(args.config, args.world))
    for path, text in (
        (args.sdf, to_sdf(orchard) if args.sdf else None),
        (args.ground_truth, dump_ground_truth(to_ground_truth(orchard))),
    ):
        if path is None:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)


if __name__ == "__main__":
    main()
