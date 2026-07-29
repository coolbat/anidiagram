"""Build AniDiagram with its runtime contracts and visual resources."""

from pathlib import Path
from shutil import copytree

from setuptools import setup
from setuptools.command.build_py import build_py as _build_py


RESOURCE_DIRECTORIES = ("assets", "runtime", "schemas", "styles")


class build_py(_build_py):
    """Copy repository-owned resources into the installed Python package."""

    def run(self) -> None:
        super().run()
        root = Path(__file__).resolve().parent
        destination = Path(self.build_lib) / "anidiagram" / "_resources"
        for name in RESOURCE_DIRECTORIES:
            copytree(root / name, destination / name, dirs_exist_ok=True)


setup(cmdclass={"build_py": build_py})
