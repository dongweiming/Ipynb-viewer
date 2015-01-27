# coding=utf-8
import os
import argparse

import markdown
from concurrent.futures import ThreadPoolExecutor
import tornado.autoreload
from tornado import web, httpserver, ioloop, log
from jinja2 import Environment, FileSystemLoader
from IPython.config import Config
from IPython.nbconvert.exporters import HTMLExporter
from IPython.html.services.notebooks.filenbmanager import FileNotebookManager

from handlers import handlers

here = os.path.dirname(__file__)
pjoin = os.path.join
app_log = log.app_log
log.enable_pretty_logging()

threads = 10
current_path = os.getcwd()
default_template = 'full'


def parse_arg():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--template', default=default_template)
    parser.add_argument('-p', '--port', type=int, default=8000)
    return parser.parse_args()


def main():
    args = parse_arg()

    config = Config()
    if args.template != default_template:
        app_log.info("Using custom template: %s", args.template)
    config.HTMLExporter.template_file = args.template
    config.NbconvertApp.fileext = 'html'
    # config.CSSHTMLHeaderTransformer.enabled = False

    template_path = pjoin(here, 'templates')
    static_path = pjoin(here, 'static')
    document_path = current_path

    exporter = HTMLExporter(config=config, log=app_log)
    env = Environment(loader=FileSystemLoader(template_path))
    env.filters['markdown'] = markdown.markdown

    # notebook
    notebook_manager = FileNotebookManager(
        notebook_dir=current_path,
        log=app_log
    )

    settings = dict(
        jinja2_env=env,
        static_path=static_path,
        exporter=exporter,
        config=config,
        pool=ThreadPoolExecutor(threads),
        gzip=True,
        log=app_log,
        render_timeout=20,
        document_path=document_path,
        notebook_manager=notebook_manager,
    )

    app = web.Application(handlers, debug=True, **settings)
    http_server = httpserver.HTTPServer(app, xheaders=True)
    app_log.info("Listening on port %i", args.port)
    http_server.listen(args.port)
    instance = ioloop.IOLoop.instance()
    tornado.autoreload.start(instance)
    instance.start()

if __name__ == '__main__':
    main()
