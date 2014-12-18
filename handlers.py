# coding=utf-8
import io
import os
import time
from datetime import datetime
from contextlib import contextmanager

from tornado.log import app_log
from tornado import web, gen
from tornado.ioloop import IOLoop

from IPython.nbformat.current import reads_json
from IPython.nbconvert.exporters import Exporter
from IPython.html import DEFAULT_STATIC_FILES_PATH as ipython_static_path

component_path = os.path.join(ipython_static_path, 'components')
date_fmt = "%a, %d %b %Y %H:%M:%S UTC"


class NbFormatError(Exception):
    pass

exporters = {}


def render_notebook(exporter, nb, url=None, config=None):
    if not isinstance(exporter, Exporter):
        exporter_cls = exporter
        if exporter_cls not in exporters:
            app_log.info("instantiating %s" % exporter_cls.__name__)
            exporters[exporter_cls] = exporter_cls(config=config, log=app_log)
        exporter = exporters[exporter_cls]

    css_theme = nb.get('metadata', {}).get('_nbviewer', {}).get('css', None)

    if not css_theme or not css_theme.strip():
        # whitespace
        css_theme = None

    # get the notebook title, if any
    try:
        name = nb.metadata.name
    except AttributeError:
        name = ''

    if not name and url is not None:
        name = url.rsplit('/')[-1]

    if not name.endswith(".ipynb"):
        name = name + ".ipynb"

    html, resources = exporter.from_notebook_node(nb)

    config = {
        'download_name': name,
        'css_theme': css_theme,
    }
    return html, config


class LocalFileHandler(web.RequestHandler):

    """Renderer for /localfile
    Serving notebooks from the local filesystem
    """

    @property
    def pool(self):
        return self.settings['pool']

    @property
    def exporter(self):
        return self.settings['exporter']

    @property
    def config(self):
        return self.settings['config']

    def render_template(self, name, **ns):
        template = self.settings['jinja2_env'].get_template(name)
        return template.render(**ns)

    @contextmanager
    def time_block(self, message):
        """context manager for timing a block
        logs millisecond timings of the block
        """
        tic = time.time()
        yield
        dt = time.time() - tic
        log = app_log.info if dt > 1 else app_log.debug
        log("%s in %.2f ms", message, 1e3 * dt)

    @property
    def render_timeout(self):
        """0 render_timeout means never finish early"""
        return self.settings.setdefault('render_timeout', 0)

    @gen.coroutine
    def get(self, path):
        if not path:
            raise web.HTTPError(404)
        abspath = os.path.join(
            self.settings.get('document_path'),
            path,
        )
        app_log.info("looking for file: '%s'" % abspath)
        if not os.path.exists(abspath):
            raise web.HTTPError(404)
        with io.open(abspath, encoding='utf-8') as f:
            nbdata = f.read()
            yield self.finish_notebook(nbdata,
                                       url=path,
                                       msg="file from localfile: %s" % path,  # noqa
                                       )

    def initialize(self):
        loop = IOLoop.current()
        if self.render_timeout:
            self.slow_timeout = loop.add_timeout(
                loop.time() + self.render_timeout,
                self.finish_early
            )

    def finish_early(self):
        """When the render is slow, draw a 'waiting' page instead

        rely on the cache to deliver the page to a future request.
        """
        if self._finished:
            return
        app_log.info("finishing early %s", self.request.uri)
        html = self.render_template('slow_notebook.html')
        self.set_status(202)  # Accepted
        self.finish(html)

        # short circuit some methods because the rest of the rendering will
        # still happen
        self.write = self.finish = self.redirect = lambda chunk=None: None

    @gen.coroutine
    def finish_notebook(self, json_notebook, url, msg=None):
        """render a notebook from its JSON body.

        msg is extra information for the log message when rendering fails.
        """

        if msg is None:
            msg = url

        try:
            nb = reads_json(json_notebook)
        except ValueError:
            app_log.error("Failed to render %s", msg, exc_info=True)
            raise web.HTTPError(400, "Error reading JSON notebook")

        try:
            app_log.debug("Requesting render of %s", url)
            with self.time_block("Rendered %s" % url):
                app_log.info(
                    "rendering %d B notebook from %s",
                    len(json_notebook), url)
                nbhtml, config = yield self.pool.submit(
                    render_notebook, self.exporter, nb, url,
                    config=self.config,
                )
        except NbFormatError as e:
            app_log.error("Invalid notebook %s: %s", msg, e)
            raise web.HTTPError(400, str(e))
        except Exception as e:
            app_log.error("Failed to render %s", msg, exc_info=True)
            raise web.HTTPError(400, str(e))
        else:
            app_log.debug("Finished render of %s", url)

        html = self.render_template('notebook.html',
                                    body=nbhtml,
                                    url=url,
                                    date=datetime.utcnow().strftime(date_fmt),
                                    **config)
        yield self._finish(html)

    @gen.coroutine
    def _finish(self, content=''):
        "Has not yet cached"
        content = content.replace(
            'https://cdnjs.cloudflare.com/ajax/libs/require.js/2.1.10/require.min.js',  # noqa
            '/static/js/require.min.js'
        ).replace(
            'https://cdnjs.cloudflare.com/ajax/libs/jquery/2.0.3/jquery.min.js',  # noqa
            '/static/js/jquery.min.js')
        self.write(content)
        self.finish()


class Custom404(web.RequestHandler):

    """Render our 404 template"""

    def prepare(self):
        raise web.HTTPError(404)


# -----------------------------------------------------------------------------
# Default handler URL mapping
# -----------------------------------------------------------------------------

handlers = [
    (r'/components/(.*)', web.StaticFileHandler,
     dict(path=component_path)),
    (r'/ipython-static/(.*)', web.StaticFileHandler,
     dict(path=ipython_static_path)),
    ('/(.*)', LocalFileHandler),
    (r'.*', Custom404),
]
