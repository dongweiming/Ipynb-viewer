# coding=utf-8
import os
import logging

import markdown
from concurrent.futures import ThreadPoolExecutor
import tornado.autoreload
from tornado import web, httpserver, ioloop, log
from jinja2 import Environment, FileSystemLoader
from IPython.config import Config
from IPython.nbconvert.exporters import HTMLExporter

from handlers import handlers

here = os.path.dirname(__file__)
pjoin = os.path.join
app_log = log.app_log
log.enable_pretty_logging()

threads = 10
PORT = 54001


def main():
    config = Config()
    config.HTMLExporter.template_file = 'full'
    config.NbconvertApp.fileext = 'html'
    config.CSSHTMLHeaderTransformer.enabled = False

    template_path = pjoin(here, 'templates')
    static_path = pjoin(here, 'static')
    document_path = pjoin(here, 'documents')

    exporter = HTMLExporter(config=config, log=app_log)
    env = Environment(loader=FileSystemLoader(template_path))
    env.filters['markdown'] = markdown.markdown

    settings = dict(
        jinja2_env=env,
        static_path=static_path,
        exporter=exporter,
        config=config,
        pool=ThreadPoolExecutor(threads),
        gzip=True,
        render_timeout=20,
        document_path=document_path
    )

    app = web.Application(handlers, debug=True, **settings)
    http_server = httpserver.HTTPServer(app, xheaders=True)
    app_log.info("Listening on port %i", PORT)
    http_server.listen(PORT)
    instance = ioloop.IOLoop.instance()
    tornado.autoreload.start(instance)
    instance.start()

if __name__ == '__main__':
    main()
