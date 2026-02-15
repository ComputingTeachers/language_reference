#!/usr/bin/env -S uv run --script
# /// script
# requires-python = "~=3.14"
# dependencies = [
#   "falcon",
# ]
# ///

import logging
from pathlib import Path
from typing import Iterable

import falcon

import _falcon_helpers

from make_ver.make_ver import LANGUAGES
from make_ver.language_versions import LanguageVersions
from make_ver.project_versions import ProjectVersions

log = logging.getLogger(__name__)


LANGUAGE_EXTENSIONS = frozenset((*LANGUAGES.keys(), *('ver.json',)))

class FileCollection():
    @staticmethod
    def walk_language_files(path: Path):  #  -> Generator[Path]
        def _exclude_dir(dir: str):
            return any((
                dir.startswith('_'),
                dir.startswith('cgi'),
                dir.startswith('.'),
                dir in ('bin', 'obj'),
            ))
        for root, dirs, files in path.walk():
            dirs = filter(_exclude_dir, dirs)
            for file in map(root.joinpath, files):
                if ''.join(file.suffixes).strip('.') in LANGUAGE_EXTENSIONS:
                    yield file

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.files = tuple(self.walk_language_files(self.path))

# Request Handler --------------------------------------------------------------

class IndexResource():
    def on_get(self, request, response):
        raise falcon.HTTPFound('/static/index.html')

class LanguageReferenceResource():
    def __init__(self, path: str | Path):
        self.lv = LanguageVersions(FileCollection(path).files)
    def on_get(self, request, response):
        response.media = {
            'versions': self.lv.all_versions,
            'languages': self.lv.languages,
        }
        response.status = falcon.HTTP_200

class ProjectListResource():
    def __init__(self, path: str | Path):
        self.project_names = tuple(
            str(f.relative_to(path)).replace('.ver.json','')
            for f in FileCollection(path).files
            if ''.join(f.suffixes) in {'.ver.json',}
        )
    def on_get(self, request, response):
        response.media = {'projects': self.project_names}
        response.status = falcon.HTTP_200

class ProjectResource():
    def __init__(self, path: str | Path):
        self.file_collection = FileCollection(path)
    #def on_index(self, request, response):
    #    response.media = {'projects': self.files.projects}
    #    response.status = falcon.HTTP_200
    def on_get(self, request, response, project_name: str):
        pv = ProjectVersions(self.project_files(project_name))
        response.media = {
            'versions': {
                'paths': pv.versions.paths,
                'parents': pv.versions.parents,
                'titles_to_language_ext': pv.titles_to_language_mapping,
            },
            'full_per_version': pv.full_per_version,
            'diffs_per_version': pv.diff_per_version,
        }
        response.status = falcon.HTTP_200
    def project_files(self, project_name: str) -> Iterable[Path]:
        def _filter_file(f):
            relative_path = f.relative_to(self.file_collection.path)
            return str(relative_path.parent.joinpath(relative_path.name.removesuffix(''.join(f.suffixes)))).startswith(project_name)
        return tuple(filter(_filter_file, self.file_collection.files))


# Setup App -------------------------------------------------------------------

def create_wsgi_app(path_project: Path|None, path_language: Path|None, path_static: Path|None, **kwargs):
    app = falcon.App()
    _falcon_helpers.update_json_handlers(app)
    app.add_route(r'/', IndexResource())
    if path_static:
        app.add_static_route(r'/static', str(path_static.resolve()))
    if path_language:
        app.add_route(r'/api/v1/language_reference.json', LanguageReferenceResource(path_language))
    if path_project:
        app.add_route(r'/api/v1/projects.json', ProjectListResource(path_project))
        _falcon_helpers.add_sink(app, r'/api/v1/projects/', ProjectResource(path_project), func_path_normalizer=_falcon_helpers.func_path_normalizer_no_extension)
    # TODO: Currently unable to drop into debugger on error - investigate?
    # https://falcon.readthedocs.io/en/stable/api/app.html#falcon.App.add_error_handler
    # add_error_handler(exception, handler=None)
    return app

# Export ----------------------------------------------------------------------

def export(path_export: Path, path_language: Path, path_project: Path, **kwargs) -> None:
    from falcon import testing as falcon_testing
    test_client = falcon_testing.TestClient(app)

    def write_url_to_file(url):
        log.info(url)
        file_path = path_export.joinpath(url.strip('/'))
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open('wt', encoding="utf-8") as filehandle:
            data = test_client.simulate_get(url)
            filehandle.write(data.text)
            return data.json

    if path_language:
        write_url_to_file('/api/v1/language_reference.json')
    if path_project:
        projects = write_url_to_file('/api/v1/projects.json')['projects']
        for project in projects:
            write_url_to_file(f'/api/v1/projects/{project}.json')


# Commandlin Args -------------------------------------------------------------

def get_args():
    import argparse

    parser = argparse.ArgumentParser(
        prog=__name__,
        description='''
            Provide a URL endpoint to return metadata of media
        ''',
    )

    parser.add_argument('--path_project', action='store', help='', type=Path)
    parser.add_argument('--path_language', action='store', help='', type=Path)
    parser.add_argument('--path_static', action='store', help='', type=Path)

    parser.add_argument('--host', action='store', default='0.0.0.0', help='')
    parser.add_argument('--port', action='store', default=8000, type=int, help='')

    parser.add_argument('--path_export', action='store', default=None, type=Path)

    parser.add_argument('--log_level', action='store', type=int, help='loglevel of output to stdout', default=logging.INFO)

    kwargs = vars(parser.parse_args())
    return kwargs

# Main ------------------------------------------------------------------------

if __name__ == '__main__':
    kwargs = get_args()

    logging.basicConfig(level=kwargs['log_level'])

    from wsgiref import simple_server
    app = create_wsgi_app(**kwargs)

    if kwargs['path_export']:
        export(**kwargs)
        exit()

    try:
        log.info(f'start {kwargs}')
        httpd = simple_server.make_server(kwargs['host'], kwargs['port'], app)
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass