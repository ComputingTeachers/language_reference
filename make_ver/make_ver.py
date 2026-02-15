import inspect
import io
import json
import operator
import re
from collections.abc import Iterable, Set
from contextlib import contextmanager
from functools import cached_property, lru_cache, partial
from pathlib import Path
from textwrap import dedent
from types import MappingProxyType
from typing import NamedTuple, TypedDict


def _json_dumps(obj):
    if isinstance(obj, (dict, MappingProxyType)):
        return dict(obj)
    if isinstance(obj, (set,frozenset)):
        return tuple(obj)
    return obj


@contextmanager
def _testfiles():
    import tempfile
    td = tempfile.TemporaryDirectory()
    files: Set[Path] = set()
    def write_file(filename, data):
        path = Path(td.name).joinpath(filename)
        with path.open('wt', encoding='utf8') as filehandle:
           _ = filehandle.write(data)
        files.add(path)
    write_file('test.py', dedent('''
        print('Hello Test')
        print('Hello World')  # VER: hello_world
    '''))
    write_file('test.js', dedent('''
        console.log("Hello World")    // VER: hello_world
        //console.log("Hello Test")    // VER: test4
    '''))
    write_file('Test.java', dedent('''
        public class Test {                          // VER: test1
            public Test() {                          // VER: test2
                System.out.println("Hello World");   // VER: hello_world
            }                                        // VER: test2
            public static void main(String[] args) {new Test();}  // VER: test2
        }  // VER: test1
    '''))
    write_file('test.ver.json', dedent('''
        {"versions": {
            "": {"parents": []},
            "test1": {"parents": [""]},
            "test2": {"parents": ["test1"]},
            "hello_world": {"parents": ["test2"]},
            "test4": {"parents": []}
        }}
    '''))
    #write_file('test.ver', dedent('''
    #    VERNAME: base           base
    #'''))
    yield files
    td.cleanup()



class Version(str):
    # TODO: this may need to support multiple sets
    # AND OR EXCLUDE HIDE
    pass
type VersionPath = frozenset[Version]


class VersionDescription(TypedDict):
    name: Version
    parent: Version
    mutations: None | Iterable[re.Pattern]  # TODO: Incomplete (previously replacements)
class _Versions(TypedDict):
    versions: MappingProxyType[Version, VersionDescription]

class Versions():
    """
    >>> data = {"versions": {
    ...     "": {"parents": []},
    ...     "background": {"parents": [""]},
    ...     "copter": {"parents": ["background"]},
    ...     "collision_single": {"parents": ["copter"]},
    ...     "collision_multi": {"parents": ["collision_single"]},
    ...     "level": {"parents": ["collision_single"]},
    ...     "physics": {"parents": ["collision_single"]},
    ...     "parallax": {"parents": ["level"]},
    ...     "full": {"parents": ["parallax", "physics", "collision_multi"]},
    ...     "fish": {
    ...         "parents": ["fish_background", "collision_single"],
    ...         "mutations": [
    ...             {"type": "replace", "match":"CopterLevel", "replacement":"FishLevel"},
    ...             {"type": "replace", "match":"ship.gif", "replacement":"fish.gif"}
    ...         ]
    ...     }
    ... }}
    >>> versions = Versions(data)
    >>> sorted(versions.resolve_versions(Version('full')))
    ['', 'background', 'collision_multi', 'collision_single', 'copter', 'full', 'level', 'parallax', 'physics']
    >>> sorted(versions.resolve_versions(Version('collision_single')))
    ['', 'background', 'collision_single', 'copter']

    >>> sorted(versions.paths['copter'])
    ['', 'background', 'copter']

    >>> versions.parents
    mappingproxy({'': None, 'background': '', 'copter': 'background', 'collision_single': 'copter', 'collision_multi': 'collision_single', 'level': 'collision_single', 'physics': 'collision_single', 'parallax': 'level', 'full': None, 'fish': None})

    >>> json_data = json.dumps(versions.paths, default=_json_dumps)
    """
    def __init__(self, versions: _Versions):
        self.versions = versions['versions']

    def resolve_versions(self, *versions: Iterable[Version]) -> VersionPath:
        versions_to_resolve = set(versions)
        versions_resolved = set()
        while versions_to_resolve and ((version := versions_to_resolve.pop()) is not None):
            target_version_description = self.versions.get(version)
            versions_resolved.add(version)
            if target_version_description:
                versions_to_resolve |= set(target_version_description['parents'])
                versions_to_resolve -= versions_resolved
        return frozenset(versions_resolved)

    @cached_property
    def paths(self) -> MappingProxyType[Version, VersionPath]:
        return MappingProxyType({
            version: self.resolve_versions(version)
            for version in self.versions.keys()
        })

    @cached_property
    def parents(self) -> MappingProxyType[Version, Version]:
        return MappingProxyType({
            version: version_data['parents'][0] if len(version_data.get('parents', tuple())) == 1 else None
            for version, version_data in self.versions.items()
        })

class LanguageFileExtension(str):
    pass

class Comment(NamedTuple):
    start: str
    end: str = ''

COMMENTS_STYLE_C = (Comment(r'/*',r'*/'), Comment(r'//'))
COMMENTS_STYLE_PYTHON = (Comment(r'#'),)

class Language(NamedTuple):
    name: str
    ext: Iterable[LanguageFileExtension]
    comments: Iterable[Comment]
LANGUAGES: MappingProxyType[LanguageFileExtension, Language] = MappingProxyType({
    language_ext: language
    for language in map(lambda l: Language(*l), (
        ('python',('py',),COMMENTS_STYLE_PYTHON),
        ('javascript',('js',),COMMENTS_STYLE_C),
        ('html5/javascript',('html',),(Comment(r'<!--',r'-->'),)+COMMENTS_STYLE_C),
        ('java',('java',),COMMENTS_STYLE_C),
        ('visual basic',('vb',),(Comment(r"'"),)),
        ('php',('php',),COMMENTS_STYLE_PYTHON),
        ('c',('c',),COMMENTS_STYLE_C),
        ('c++',('cpp',),COMMENTS_STYLE_C),
        ('ruby',('rb',),COMMENTS_STYLE_PYTHON),
        ('csharp',('cs',),COMMENTS_STYLE_C),
        ('lua',('lua',),(Comment(r'--'),)),
        ('golang',('go',),COMMENTS_STYLE_C),
        ('rust',('rs',),COMMENTS_STYLE_C),
        # txt  =   '#',
    ))
    for language_ext in language.ext
})


class VersionEvaluator():
    """
    TODO: HIDE (replace with '???') NOT?

    >>> VersionEvaluator('collision_single')(frozenset(('base','collision_single','parallax')))
    True
    >>> VersionEvaluator('collision_single parallax NOT_ AND_')(frozenset(('base','collision_single')))
    True
    >>> VersionEvaluator('collision_single parallax NOT_ AND_')(frozenset(('base','collision_single','parallax')))
    False

    >>> VersionEvaluator('block_move mines OR_')(frozenset(('base',)))
    False
    >>> VersionEvaluator('block_move mines OR_')(frozenset(('base','block_move')))
    True
    >>> VersionEvaluator('block_move mines OR_')(frozenset(('base','mines')))
    True
    """
    def __init__(self, version_str: str = ''):
        version_str = version_str.replace(',',' ')
        self.tokens = tuple(filter(None, map(lambda v: v.strip(), version_str.split(' ')))) or ('',)
        # !!! WIP TEMP HACKs: to allow migration from old `make_ver` !!! REMOVE THIS SHIT!
        self.tokens = tuple(t for t in self.tokens if t.lower()!='hide')
        if len(self.tokens) == 3 and self.tokens[1].lower() == 'not':
            self.tokens = (self.tokens[0], self.tokens[2], 'NOT_', 'AND_')
        if len(self.tokens) == 4 and self.tokens[1].lower() == 'not':
            self.tokens = (self.tokens[0], self.tokens[2], 'NOT_', self.tokens[3], 'NOT_', 'OR_', 'AND_')  # probably a ballzup
        if len(self.tokens) == 2 and 'list_comprehension' not in self.tokens and 'AND_' not in self.tokens and 'NOT_' not in self.tokens and 'OR_' not in self.tokens:
                self.tokens = self.tokens + ('AND_',)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.tokens=})"

    def __call__(self, version_path: VersionPath) -> bool:
        if not version_path:
            return False
        stack = []
        for token in self.tokens:
            if _operator := getattr(operator, token.lower(), None):
                param_count = len(inspect.signature(_operator).parameters)
                try:
                    result = _operator(*(stack.pop() for i in range(param_count)))
                except IndexError:
                    raise Exception(f'{self.__class__.__name__} Out of tokens {self.tokens=} {version_path=}')
                stack.append(result)
            else:
                stack.append(token in version_path)
        assert len(stack) == 1, f"After evaluation of version_path, we should have a single value {self.tokens=} {version_path=}"
        return stack.pop()

    @cached_property
    def versions(self) -> VersionPath:
        return frozenset(token for token in self.tokens if not hasattr(operator, token))

class VersionModel():

    class Line(NamedTuple):
        line: str
        line_without_ver: str
        version_evaluator: VersionEvaluator

    @staticmethod
    @lru_cache
    def regex_ver(comment: Comment) -> re.Pattern:
        """
        >>> regex_ver = VersionModel.regex_ver

        >>> c = Comment(r'#')
        >>> test_py1 = '''print('helloworld') # VER: 1|2|3 # More comments'''
        >>> test_py2 = '''print('helloworld') # VER: 1|2|3#More comments'''
        >>> test_py3 = '''print('helloworld') #VER:1|2|3'''
        >>> regex_ver(c).search(test_py1)['ver']
        '1|2|3'
        >>> regex_ver(c).search(test_py2)['ver']
        '1|2|3'
        >>> regex_ver(c).search(test_py3)['ver']
        '1|2|3'

        >>> c = Comment(r'//')
        >>> test_js1 = '''console.log('helloworld') // VER: 1|2|3 // More comments'''
        >>> test_js2 = '''console.log('helloworld') // VER: 1|2|3//More comments'''
        >>> test_js3 = '''console.log('helloworld') //VER:1|2|3'''
        >>> regex_ver(c).search(test_js1)['ver']
        '1|2|3'
        >>> regex_ver(c).search(test_js2)['ver']
        '1|2|3'
        >>> regex_ver(c).search(test_js3)['ver']
        '1|2|3'

        >>> c = Comment(r'<!--',r'-->')
        >>> test_html1 = '''<a href=""> <!-- VER: 1|2|3 --><!-- more comments -->'''
        >>> test_html2 = '''<a href=""><!-- VER: 1|2|3--><!--more comments-->'''
        >>> test_html3 = '''<a href=""><!--VER:1|2|3-->'''
        >>> regex_ver(c).search(test_html1)['ver']
        '1|2|3'
        >>> regex_ver(c).search(test_html2)['ver']
        '1|2|3'
        >>> regex_ver(c).search(test_html3)['ver']
        '1|2|3'

        >>> c = Comment(r'/*','*/')
        >>> test_css1 = '''   border-radius: 4px; /* VER:1|2|3 */  '''
        >>> regex_ver(c).search(test_css1)['ver']
        '1|2|3'
        """
        return re.compile(
            r'''(?P<ver_remove>{comment_start}\s*VER:\s*(?P<ver>.+?)\s*)($|{comment_end})'''.format(
                comment_start=re.escape(comment.start),
                comment_end=re.escape(comment.end or comment.start)
            ), flags=re.IGNORECASE)

    @staticmethod
    @lru_cache
    def _regex_first_line_comment(comment) -> re.Pattern:
        """
        """
        return re.compile(
            r'''^(\s*){comment_start}\s*(.*)'''.format(
                comment_start=re.escape(comment.start)
            ), flags=re.IGNORECASE)
    @classmethod
    def _remove_first_line_comment(cls, line, comment):
        """
        >>> VersionModel._remove_first_line_comment('    #  x=x+1', Comment('#'))
        '    x=x+1'
        >>> VersionModel._remove_first_line_comment('    ## Real comment # Again', Comment('#'))
        '    # Real comment # Again'
        """
        return cls._regex_first_line_comment(comment).sub(r'\1\2', line, count=1)

    @staticmethod
    def remove_new_lines(line):
        return re.sub('[\n\r]', '', line)

    @classmethod
    def _parse_line(cls, language: Language, line: str) -> Line:
        r"""
        >>> VersionModel._parse_line(LANGUAGES['py'], "    print('Hello World')  #  VER:  test1 test2 AND_\n\r")
        Line(line="    print('Hello World')  #  VER:  test1 test2 AND_", line_without_ver="    print('Hello World')", version_evaluator=VersionEvaluator(self.tokens=('test1', 'test2', 'AND_')))
        """
        #print(f'_parse_line {language.name} {line[:10]}')
        line = cls.remove_new_lines(line)
        for comment in language.comments:
            if match := cls.regex_ver(comment).search(line):
                line_without_ver = line.replace(match['ver_remove'], '').rstrip()
                line_without_ver = cls._remove_first_line_comment(line_without_ver, comment)
                return cls.Line(
                    line=line,
                    line_without_ver=line_without_ver,
                    version_evaluator=VersionEvaluator(match['ver'])
                )
        return cls.Line(
            line=line,
            line_without_ver=line,
            version_evaluator=VersionEvaluator()
        )

    def __init__(self, source: io.IOBase, language: Language):
        self.lines = tuple(map(partial(self._parse_line, language), source))
