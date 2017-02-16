
import importlib
from os import listdir
from os.path import dirname, isfile
from math import exp

from kivy.properties import NumericProperty

from ceed.function import CeedFunc, FunctionFactory, FuncDoneException


def import_plugins():
    for name in listdir(dirname(__file__)):
        if name.startswith('_') or not name.endswith('.py'):
            continue
        name = name[:-3]
        importlib.import_module('ceed.function.plugin.{}'.format(name))


class ConstFunc(CeedFunc):

    a = NumericProperty(0.)

    def __init__(self, **kwargs):
        kwargs.setdefault('name', 'Const')
        kwargs.setdefault('description', 'y(t) = a')
        super(ConstFunc, self).__init__(**kwargs)

    def __call__(self, t):
        if self.check_done(t):
            raise FuncDoneException
        return self.a

    def get_gui_props(self, attrs={}):
        d = super(ConstFunc, self).get_gui_props(attrs)
        d ['a'] = None
        return d

    def _copy_state(self, *largs, **kwargs):
        d = super(ConstFunc, self)._copy_state(*largs, **kwargs)
        d['a'] = self.a
        return d


class LinearFunc(CeedFunc):

    m = NumericProperty(1.)

    b = NumericProperty(0.)

    def __init__(self, **kwargs):
        kwargs.setdefault('name', 'Linear')
        kwargs.setdefault('description', 'y(t) = m(t + t0) + b')
        super(LinearFunc, self).__init__(**kwargs)

    def __call__(self, t):
        if self.check_done(t):
            raise FuncDoneException
        t = (t - self._t0_global + self.t0) / self.timebase
        return self.m * t + self.b

    def get_gui_props(self, attrs={}):
        d = super(LinearFunc, self).get_gui_props(attrs)
        d ['m'] = None
        d ['b'] = None
        return d

    def _copy_state(self, *largs, **kwargs):
        d = super(LinearFunc, self)._copy_state(*largs, **kwargs)
        d['m'] = self.m
        d['b'] = self.b
        return d


class ExponantialFunc(CeedFunc):

    A = NumericProperty(1.)

    B = NumericProperty(0.)

    tau1 = NumericProperty(1.)

    tau2 = NumericProperty(1.)

    def __init__(self, **kwargs):
        kwargs.setdefault('name', 'Exp')
        kwargs.setdefault('description',
                          'y(t) = Ae-(t + t0)/tau1 + Be-(t + t0)/tau2')
        super(ExponantialFunc, self).__init__(**kwargs)

    def __call__(self, t):
        if self.check_done(t):
            raise FuncDoneException
        t = (t - self._t0_global + self.t0) / self.timebase
        return self.A * exp(t / self.tau1) + self.B * exp(t / self.tau2)

    def get_gui_props(self, attrs={}):
        d = super(ExponantialFunc, self).get_gui_props(attrs)
        d ['A'] = None
        d ['B'] = None
        d ['tau1'] = None
        d ['tau2'] = None
        return d

    def _copy_state(self, *largs, **kwargs):
        d = super(ExponantialFunc, self)._copy_state(*largs, **kwargs)
        d['A'] = self.A
        d['B'] = self.B
        d['tau1'] = self.tau1
        d['tau2'] = self.tau2
        return d

FunctionFactory.register(ConstFunc)
FunctionFactory.register(LinearFunc)
FunctionFactory.register(ExponantialFunc)
import_plugins()
