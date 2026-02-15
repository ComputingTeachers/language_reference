import io
import json
from difflib import unified_diff
from functools import cached_property
from types import MappingProxyType
from typing import NamedTuple

from .make_ver import (
    LANGUAGES,
    LanguageFileExtension,
    Version,
    VersionModel,
    Versions,
    _Versions,
)


class ProjectVersions():
    r"""
    Read in a project and have all permutations of that project in an object

    >>> from .make_ver import _testfiles
    >>> with _testfiles() as files:
    ...     p = ProjectVersions(files)

    >>> sorted(p.versions.paths['hello_world'])
    ['', 'hello_world', 'test1', 'test2']

    >>> print(p.full_per_version['java: Test']['test2'])
    <BLANKLINE>
    public class Test {
        public Test() {
        }
        public static void main(String[] args) {new Test();}
    }

    >>> print(p.diff_per_version['java: Test']['test2'])
    --- test1
    +++ test2
    @@ -1,3 +1,6 @@
    <BLANKLINE>
     public class Test {
    +    public Test() {
    +    }
    +    public static void main(String[] args) {new Test();}
     }
    """
    class StemExt(NamedTuple):
        stem: str
        ext: LanguageFileExtension
        def __str__(self) -> str:
            return f'{self.ext}: {self.stem}'
    def __init__(self, files):
        self.files_by_stem_ext = MappingProxyType({
            self.StemExt(
                f.stem,
                LanguageFileExtension(''.join(f.suffixes).strip('.'))
            ): f.open(encoding='utf8').read()
            for f in files
        })

    @property
    def _titles(self) -> frozenset[StemExt]:
        EXCLUDE_EXTS = frozenset(('ver', 'json', 'yaml', 'yml', 'ver.json'))
        return frozenset(
            stem_ext
            for stem_ext in self.files_by_stem_ext.keys()
            if stem_ext.ext not in EXCLUDE_EXTS
        )

    @property
    def titles_to_language_mapping(self) -> dict[str, str]:
        return {str(s): s.ext for s in self._titles}

    @cached_property
    def versions(self) -> Versions:
        """
        Parse versions from .ver or .yaml file
        """
        file_exts = frozenset(s.ext for s in self.files_by_stem_ext.keys())
        if {'yaml', 'yml'} & file_exts:
            raise NotImplementedError('yaml version file format not implemented')
        if {'ver.json',} & file_exts:
            return Versions(_Versions(json.loads(next(iter(f for s, f in self.files_by_stem_ext.items() if s.ext == 'ver.json')))))
        raise Exception('no version information')

    def full(self, title: StemExt) -> MappingProxyType[Version, str]:
        lines = VersionModel(io.StringIO(self.files_by_stem_ext[title]), LANGUAGES[title.ext]).lines
        return MappingProxyType({
            version_name: '\n'.join(
                line.line_without_ver
                for line in lines
                if line.version_evaluator(version_path)
            )
            for version_name, version_path in self.versions.paths.items()
        })

    @cached_property
    def full_per_version(self) -> MappingProxyType[str, MappingProxyType[Version, str]]:
        return MappingProxyType({str(l): self.full(l) for l in self._titles})

    def diff(self, title: StemExt) -> MappingProxyType[Version, str]:
        return MappingProxyType({
            version: "\n".join(unified_diff(
                self.full(title)[parent].split("\n"),
                self.full(title)[version].split("\n"),
                fromfile=parent, tofile=version, n=2, lineterm=''))
            for version, parent in self.versions.parents.items()
            if parent is not None
        })

    @cached_property
    def diff_per_version(self) -> MappingProxyType[str, MappingProxyType[Version, str]]:
        return MappingProxyType({str(l): self.diff(l) for l in self._titles})
