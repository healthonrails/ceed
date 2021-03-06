'''Ceed View App
=====================

The module that runs the :mod:`ceed.view` GUI for displaying the pixels on the
projector. This is run in a seperate process than the main server side GUI.
'''
import os
os.environ['SDL_VIDEO_MINIMIZE_ON_FOCUS_LOSS'] = '0'

from functools import partial

from base_kivy_app.app import run_app as run_cpl_app, app_error, BaseKivyApp

from kivy.lang import Builder
from kivy.graphics import Color, Point, Fbo, Rectangle, Scale, PushMatrix, \
    PopMatrix, Translate, ClearColor, ClearBuffers
from kivy.uix.widget import Widget
from kivy.graphics.opengl import glEnable, GL_DITHER, glDisable
from kivy.logger import Logger
from kivy.compat import string_types

import ceed
from ceed.function import FunctionFactoryBase, register_all_functions
from ceed.view.controller import ViewSideViewControllerBase
from ceed.view.view_widgets import ViewRootFocusBehavior
from ceed.storage.controller import DataSerializerBase, CeedDataWriterBase
from ceed.stage import StageFactoryBase
from ceed.shape import CeedPaintCanvasBehavior

if ceed.is_view_inst or __name__ == '__main__':
    from kivy.core.window import Window

__all__ = ('CeedViewApp', 'run_app')


kv = '''
<ViewRootWidget>:
    Widget:
        size: root.width, root.height
        canvas.before:
            Color:
                rgba: [0, 0, 0, 1]
            Rectangle:
                pos: self.pos
                size: self.size
        Widget:
            size: root.size
            id: display_canvas
'''


class ViewRootWidget(ViewRootFocusBehavior, Widget):
    pass


class CeedViewApp(BaseKivyApp):
    '''The app which runs the GUI.
    '''

    view_controller = None

    data_serializer = None

    function_factory = None

    stage_factory = None

    shape_factory = None

    ceed_data = None

    @classmethod
    def get_config_classes(cls):
        d = super(CeedViewApp, cls).get_config_classes()
        d['view'] = ViewSideViewControllerBase
        d['data'] = CeedDataWriterBase
        d['serializer'] = DataSerializerBase
        d['function'] = FunctionFactoryBase
        return d

    def get_config_instances(self):
        d = super(CeedViewApp, self).get_config_instances()
        d['view'] = self.view_controller
        d['data'] = self.ceed_data
        d['serializer'] = self.data_serializer
        d['function'] = self.function_factory
        return d

    def __init__(self, **kwargs):
        self.view_controller = ViewSideViewControllerBase()
        self.ceed_data = CeedDataWriterBase()
        self.data_serializer = DataSerializerBase()
        self.function_factory = FunctionFactoryBase()
        register_all_functions(self.function_factory)
        self.shape_factory = CeedPaintCanvasBehavior()
        self.stage_factory = StageFactoryBase(
            function_factory=self.function_factory,
            shape_factory=self.shape_factory)

        super(CeedViewApp, self).__init__(**kwargs)

    def init_load(self):
        pass

    def get_display_canvas(self):
        return self.root.ids.display_canvas.canvas

    def build(self):
        Builder.load_string(kv)
        widget = ViewRootWidget()
        return widget

    def get_root_pixels(self):
        widget = self.root.ids.display_canvas

        canvas_parent_index = widget.parent.canvas.indexof(widget.canvas)
        if canvas_parent_index > -1:
            widget.parent.canvas.remove(widget.canvas)

        fbo = Fbo(size=widget.size, with_stencilbuffer=True)

        with fbo:
            ClearColor(0, 0, 0, 1)
            ClearBuffers()
            Scale(1, -1, 1)
            Translate(0, -widget.height, 0)

        fbo.add(widget.canvas)
        fbo.draw()
        pixels = fbo.pixels
        fbo.remove(widget.canvas)

        if canvas_parent_index > -1:
            widget.parent.canvas.insert(canvas_parent_index, widget.canvas)
        return pixels, widget.size

    def on_start(self):
        glDisable(GL_DITHER)
        Window.clearcolor = (0, 0, 0, 1)
        # Window.minimize()
        self.root.focus = True
        Window.show_cursor = False

    def _ask_close(self, *largs, **kwargs):
        return False

    def handle_exception(self, exception, exc_info=None, event=None, obj=None,
                         level='error', *largs):
        '''Should be called whenever an exception is caught in the app.

        :parameters:

            `exception`: string
                The caught exception (i.e. the ``e`` in
                ``except Exception as e``)
            `exc_info`: stack trace
                If not None, the return value of ``sys.exc_info()``. It is used
                to log the stack trace.
            `event`: :class:`moa.threads.ScheduledEvent` instance
                If not None and the exception originated from within a
                :class:`moa.threads.ScheduledEventLoop`, it's the
                :class:`moa.threads.ScheduledEvent` that caused the execution.
            `obj`: object
                If not None, the object that caused the exception.
        '''
        if isinstance(exc_info, string_types):
            self.get_logger().error(exception)
            self.get_logger().error(exc_info)
        else:
            self.get_logger().error(exception, exc_info=exc_info)
        if obj is None:
            err = exception
        else:
            err = '{} from {}'.format(exception, obj)
        self.view_controller.handle_exception(err, exc_info)

    def get_logger(self):
        return Logger


run_app = partial(run_cpl_app, CeedViewApp)
'''The function that starts the GUI and the entry point for
the main script.
'''

if __name__ == '__main__':
    run_app()
