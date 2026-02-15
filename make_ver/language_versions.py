import io
from collections import defaultdict
from collections.abc import Iterable, Sequence
from functools import cached_property, reduce
from itertools import chain
from pathlib import Path
from types import MappingProxyType

from .make_ver import LANGUAGES, Language, Version, VersionModel


class LanguageVersions():
    r"""
    >>> from .make_ver import _testfiles
    >>> with _testfiles() as files:
    ...     l = LanguageVersions(files)

    `hello_world` is in the VERSION_ORDER and so will come first, then the rest are then ordered
    >>> l.all_versions
    ('hello_world', 'test1', 'test2', 'test4')
    >>> l.languages['js']['test4']
    'console.log("Hello Test")'
    """

    VERSION_ORDER = [  # TODO: these should be moved eventually
        'title',
        'download',
        'help',
        'run',
        'hello_world',
        'read_line_from_console',
        'comment',
        'define_variables',
        'define_constants',
        'arithmetic',
        'if_statement',
        'if_statement_more',
        'while_loop',
        'until_loop',
        'for_loop',
        'for_each_loop',
        'file_write',
        'file_read',
        'string_concatenation',
        'split_strings',
        'convert_string_to_integer_and_back',
        'convert_double_to_string_and_back',
        'function',
        'function_with_return_value',
        'function_with_params_by_reference',
        'function_with_params_by_value',
        'function_with_param_function',
        'define_fixed_array',
        'define_list',
        'define_2d_arrays_with_nested_arrays',
        'define_2d_arrays_with_1d_array_with_lookup_function',
        'define_2d_arrays_with_dictionary',
        'define_map',
        'define_set',
        'error_handling',
        'join_strings',
        'random_number',
        'class',
        'read_csv_into_array_of_classs',
        'sleep',
        'list_comprehension',
        'dict_comprehension',
    ]

    def __init__(self, files: Iterable[Path]):
        """
        Concept:
            `/java/main_stuff.java`
            `/java/graphics_stuff.java`
            `/java/network_stuff.java`
        are amalgamated/concatenated into `self.files['java']`
        This means that we can have
            `hello_world`
            `draw_sqaure`
            `get_http`
        defined in different files but still available as a version
        """
        def _amalgamate_files_with_same_extension(acc, path):
            acc[''.join(path.suffixes).strip('.')].append(path.read_text('utf-8'))
            return acc
        self.files = MappingProxyType({
            ext: "\n".join(file_content_list)
            for ext, file_content_list in reduce(
                _amalgamate_files_with_same_extension,
                files,
                defaultdict(list),
            ).items()
        })

    @property
    def all_versions(self) -> Sequence[Version]:
        versions = frozenset(chain.from_iterable(version_data.keys() for version_data in self.languages.values()))
        return tuple(v for v in self.VERSION_ORDER if v in versions) + tuple(sorted(v for v in versions if v not in self.VERSION_ORDER))

    @cached_property
    def languages(self) ->  MappingProxyType[str, MappingProxyType[Version, str]]:
        return MappingProxyType({
            language: self._build_versions(io.StringIO(self.files.get(language)), LANGUAGES[language])
            for language in LANGUAGES.keys()
        })

    @classmethod
    def _build_versions(cls, source: io.IOBase, language: Language) -> MappingProxyType[Version, str]:
        r"""
        >>> from textwrap import dedent
        >>> java = io.StringIO(dedent('''
        ...     import java.util.stream.Collectors;             // VER: list_comprehension,dict_comprehension
        ...     import static java.util.Map.entry;              // VER: dict_comprehension
        ...     public class Java {
        ...         public static void main(String[] args) {new Java();}
        ...         public Java() {
        ...             hello_world();
        ...             arithmetic();
        ...         }
        ...         void hello_world() {
        ...             // // Must be in file named `HelloWorld.java`                    // VER: hello_world
        ...             //public class HelloWorld {                                      // VER: hello_world
        ...                 //public static void main(String[] args) {new HelloWorld();} // VER: hello_world
        ...                 //public HelloWorld() {                                      // VER: hello_world
        ...                     System.out.println("Hello World");                       // VER: hello_world
        ...                 //}                                                          // VER: hello_world
        ...             //}                                                              // VER: hello_world
        ...         }
        ...         void list_comprehension() {
        ...             List<Integer> data1 = new ArrayList<>(Arrays.asList(new Integer[]{1,2,3,4,5,6})); // VER: list_comprehension
        ...         }
        ...         void dict_comprehension() {
        ...             Map<String,Integer> data3 = Map.ofEntries(  //  VER: dict_comprehension
        ...                 entry("a", 1),                          //  VER: dict_comprehension
        ...                 entry("b", 2)                           //  VER: dict_comprehension
        ...             );                                          //  VER: dict_comprehension
        ...         }
        ...     }
        ... '''))
        >>> versions = LanguageVersions._build_versions(java, LANGUAGES['java'])

        >>> sorted(versions.keys())
        ['dict_comprehension', 'hello_world', 'list_comprehension']

        >>> print(versions['hello_world'])
                // Must be in file named `HelloWorld.java`
                public class HelloWorld {
                    public static void main(String[] args) {new HelloWorld();}
                    public HelloWorld() {
                        System.out.println("Hello World");
                    }
                }

        >>> print(versions['list_comprehension'])
        import java.util.stream.Collectors;
                List<Integer> data1 = new ArrayList<>(Arrays.asList(new Integer[]{1,2,3,4,5,6}));

        >>> print(versions['dict_comprehension'])
        import java.util.stream.Collectors;
        import static java.util.Map.entry;
                Map<String,Integer> data3 = Map.ofEntries(
                    entry("a", 1),
                    entry("b", 2)
                );
        """
        lines = VersionModel(source, language).lines
        # We build a dict incrementally with the versions from each line.
        # This is not the way ProjectVersions works.
        # Perhaps we can get a list of all versions and then run the version evaluator for each line to include it?
        # The process below is definitely efficient to build, but I wonder if a single code path for versions would be neater and cleaner
        # For now LanguageVersions feels like it's own case, but it feels weird because `VER:` lines are used for different things in different ways
        def _reducer(acc: defaultdict[Version, list[str]], line: VersionModel.Line) -> defaultdict[Version, list[str]]:
            for version in line.version_evaluator.versions:
                if not version:  # Lines with not explicitly tagged with a version are not considered in LanguageVersions
                    continue
                acc[version].append(line.line_without_ver)
            return acc
        return MappingProxyType({
            version: "\n".join(lines)
            for version, lines in reduce(_reducer, lines, defaultdict(list[str])).items()
        })

    # @classmethod
    # def build_versions_from_path(cls: Self, path: str | Path) -> MappingProxyType[Version, str]:
    #     path = Path(path)
    #     language = LANGUAGES.get(path.suffix.strip('.'))
    #     assert language, f'Language unknown: {path.suffix}. Valid languages are {LANGUAGES.keys()}'
    #     with path.open() as source:
    #         return cls._build_versions(source, language)
