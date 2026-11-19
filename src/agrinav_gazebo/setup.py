from pathlib import Path

from setuptools import find_packages, setup

package_name = "agrinav_gazebo"


def tree(directory: str) -> list[tuple[str, list[str]]]:
    """Map every file under `directory` to share/<package>/<same relative dir>."""
    entries: dict[str, list[str]] = {}
    for path in sorted(Path(directory).rglob("*")):
        if path.is_file():
            dest = str(Path("share") / package_name / path.parent)
            entries.setdefault(dest, []).append(str(path))
    return list(entries.items())


setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        *tree("config"),
        *tree("models"),
        *tree("worlds"),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Victor",
    maintainer_email="jamelsatel@gmail.com",
    description="Seeded orchard world generator, Gazebo models and ground truth for agrinav.",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "generate_orchard = agrinav_gazebo.generate_orchard:main",
        ],
    },
)
