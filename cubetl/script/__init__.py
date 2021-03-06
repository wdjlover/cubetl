import logging
from cubetl.core import Node, ContextProperties
import cubetl
import sys
import inspect
from inspect import isclass
import traceback
from cubetl.core.context import Context

# Get an instance of a logger
logger = logging.getLogger(__name__)


class Script(Node):

    script = None
    refs = {}

    def __init__(self):
        super(Script, self).__init__()
        self.refs = {}

    def process(self, ctx, m):

        # TODO: Cache code?

        try:
            e_locals = { "m": m, "ctx": ctx, "props": ctx.props, "var": ctx.var, "refs": self.refs, "logger": logger }
            e_globals = ctx._globals
            exec (self.code, e_locals, e_globals)
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logger.error("Error in script %s" % self)
            #print self.code
            #raise Exception('Error evaluating script at %s:\n%s' % (self, ("".join(traceback.format_exception_only(exc_type, exc_value)))) )
            raise

        yield m


class Function(Node):

    def __init__(self, function):
        super().__init__()
        self.function = function

    def process(self, ctx, m):

        # TODO: Cache code?
        self.function(ctx, m)
        yield m


class ContextScript(ContextProperties):

    #def after_properties_set(self):
    code = None

    def load_properties(self, ctx):

        try:
            e_locals = { "ctx": ctx, "props": ctx.props, "var": ctx.var, "logger": logger }
            e_globals = ctx._globals
            exec (self.code, e_locals, e_globals)
        except (Exception) as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            #logger.error("Error evaluating script")
            raise Exception('Error evaluating script at %s: %s' % (self, ("".join(traceback.format_exception_only(exc_type, exc_value)))) )
            #raise


class Eval(Node):
    """
    Note that evaluation is done via ctx.interpolate(), and so
    requires expressions to be delimited by ${}.
    """

    def __init__(self, eval=None):

        super().__init__()

        self.eval = eval or []

    def initialize(self, ctx):
        super(Eval, self).initialize(ctx)

        if (hasattr(self, "mappings")):
            raise Exception ("%s config contains a mappings element which is not allowed (use 'eval' element)" % self)


    @staticmethod
    def process_evals(ctx, m, evals, data = {}):

        # Accept a single dict as eval (convert to list)
        if (isinstance(evals, dict)):
            evals = [ evals ]

        if (len(evals) == 0):
            if (m != data):
                m.update(data)

        else:

            for evalitem in evals:

                if isinstance(evalitem, dict):
                    m.update(evalitem)
                    return

                elif ("value" in evalitem):
                    try:
                        m[evalitem["name"]] = ctx.interpolate(m, evalitem["value"], data)
                    except Exception as e:
                        if "except" in evalitem:
                            m[evalitem["name"]] = ctx.interpolate(m, evalitem["except"], data)
                        else:
                            raise
                else:
                    print(evalitem)
                    if evalitem["name"] in data:
                        m[evalitem["name"]] = data[evalitem["name"]]
                    else:
                        if (not "default" in evalitem):
                            logging.warn("Mapping with no value and no default: %s" % evalitem)
                        #m[evalitem["name"]] = None

                if ("default" in evalitem):
                    if (not m[evalitem["name"]]):
                        m[evalitem["name"]] = ctx.interpolate(data, evalitem["default"])


    def process(self, ctx, m):

        Eval.process_evals(ctx, m, self.eval)

        yield m


class Delete(Node):
    """
    Note that evaluation is done via ctx.interpolate(), and so
    requires expressions to be delimited by ${}.
    """

    def __init__(self, fields):

        super().__init__()

        self.fields = fields

    def process(self, ctx, m):
        for field in self.fields:
            try:
                m.pop(field)
            except:
                pass

        yield m

