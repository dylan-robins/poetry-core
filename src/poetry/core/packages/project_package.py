from __future__ import annotations

import warnings

from typing import TYPE_CHECKING
from typing import Literal
from typing import Mapping
from typing import Sequence
from typing import TypedDict

from poetry.core.constraints.version import parse_constraint
from poetry.core.packages.package import Package
from poetry.core.packages.utils.utils import create_nested_marker
from poetry.core.version.markers import parse_marker


if TYPE_CHECKING:
    from typing_extensions import NotRequired

    from poetry.core.constraints.version import Version
    from poetry.core.packages.dependency import Dependency

    SupportedPackageFormats = Literal["sdist", "wheel"]

    BuildConfigSpec = TypedDict(
        "BuildConfigSpec",
        {"script": NotRequired[str], "generate-setup-file": NotRequired[bool]},
    )

    class PackageSpec(TypedDict):
        include: str
        to: str
        format: list[SupportedPackageFormats]

    class IncludeSpec(TypedDict):
        path: str
        format: list[SupportedPackageFormats]


class ProjectPackage(Package):
    def __init__(
        self,
        name: str,
        version: str | Version,
        pretty_version: str | None = None,
    ) -> None:
        if pretty_version is not None:
            warnings.warn(
                "The `pretty_version` parameter is deprecated and will be removed"
                " in a future release.",
                DeprecationWarning,
                stacklevel=2,
            )

        super().__init__(name, version)

        # Attributes must be immutable for clone() to be safe!
        # (For performance reasons, clone only creates a copy instead of a deep copy).

        self.build_config: BuildConfigSpec = {}
        self.packages: Sequence[PackageSpec] = []
        self.include: Sequence[IncludeSpec] = []
        self.exclude: Sequence[IncludeSpec] = []
        self.custom_urls: Mapping[str, str] = {}

        if self._python_versions == "*":
            self._python_constraint = parse_constraint("~2.7 || >=3.4")

    @property
    def build_script(self) -> str | None:
        return self.build_config.get("script")

    def is_root(self) -> bool:
        return True

    def to_dependency(self) -> Dependency:
        dependency = super().to_dependency()

        dependency.is_root = True

        return dependency

    @property
    def python_versions(self) -> str:
        return self._python_versions

    @python_versions.setter
    def python_versions(self, value: str) -> None:
        self._python_versions = value

        if value == "*":
            value = "~2.7 || >=3.4"

        self._python_constraint = parse_constraint(value)
        self._python_marker = parse_marker(
            create_nested_marker("python_version", self._python_constraint)
        )

    @property
    def version(self) -> Version:
        # override version to make it settable
        return super().version

    @version.setter
    def version(self, value: str | Version) -> None:
        self._set_version(value)

    @property
    def urls(self) -> dict[str, str]:
        urls = super().urls

        urls.update(self.custom_urls)

        return urls

    def __hash__(self) -> int:
        # The parent Package class's __hash__ incorporates the version because
        # a Package's version is immutable. But a ProjectPackage's version is
        # mutable. So call Package's parent hash function.
        return super(Package, self).__hash__()

    def build_should_generate_setup(self) -> bool:
        value: bool = self.build_config.get("generate-setup-file", False)
        return value
