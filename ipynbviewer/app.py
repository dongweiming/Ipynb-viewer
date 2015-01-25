# coding=utf-8
import os
import sys

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
default_port = 8000
default_template_file = 'full'
current_path = os.getcwd()


def main():
    l = len(sys.argv)
    if l == 3:
        port = int(sys.argv[1])
        template = sys.argv[2]
    elif l == 2:
        port = int(sys.argv[1])
        template = default_template_file
    else:
        port = default_port
        template = default_template_file

    config = Config()
    config.HTMLExporter.template_file = template
    config.NbconvertApp.fileext = 'html'
    config.CSSHTMLHeaderTransformer.enabled = False

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
    app_log.info("Listening on port %i", port)
    http_server.listen(port)
    instance = ioloop.IOLoop.instance()
    tornado.autoreload.start(instance)
    instance.start()

if __name__ == '__main__':
    main()
