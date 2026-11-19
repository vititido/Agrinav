from glob import glob

from setuptools import find_packages, setup

package_name = "agrinav_bringup"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (f"share/{package_name}/launch", glob("launch/*.launch.py")),
        (f"share/{package_name}/config", glob("config/*.yaml")),
        (f"share/{package_name}/rviz", glob("rviz/*.rviz")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Victor",
    maintainer_email="jamelsatel@gmail.com",
    description="Launch files and parameters that bring up the agrinav simulation and stack.",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": ["teleop = agrinav_bringup.teleop:main"],
    },
)
