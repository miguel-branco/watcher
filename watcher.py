import ast
import _ast
import sys
import time


def parse_expr(expr):
    """Supports expressions of type <variable> or <object>.<vvariable> (with arbitrary nesting).
    Returns list of identifiers.

    e.g. 
    >>> parse_expr('self.foo')
    ('self', 'foo')
    >>> parse_expr('foo)
    ('foo', )
    """
    try:
        e = ast.parse(expr)
    except Exception:
        raise ValueError('invalid expression')
    if not isinstance(e, _ast.Module):
        raise ValueError('invalid expression')
    b = e.body
    if len(b) != 1:
        raise ValueError('invalid expression')
    e = b[0]
    if not isinstance(e, _ast.Expr):
        raise ValueError('invalid expression')
    v = e.value
    if isinstance(v, _ast.Name):
        return (v.id, )
    elif isinstance(v, _ast.Attribute):
        ids = []
        while v:
            if isinstance(v, _ast.Attribute):
                ids.insert(0, v.attr)
                v = v.value
            elif isinstance(v, _ast.Name):
                ids.insert(0, v.id)
                v = None
            else:
                raise ValueError('invalid expression')
        return tuple(ids)
    else:
        raise ValueError('invalid expression')


class Watcher(object):

    def __init__(self, steps_delta=None, time_delta=None, dump_new=True):
        if steps_delta is None and time_delta is None:
            raise ValueError('steps_delta or time_delta must be set')

        self.__steps_delta = steps_delta    # Number of stepts (i.e. code lines) executed between re-checking variables
        self.__time_delta = time_delta      # Time elapsed between re-checking variables
        self.__dump_new = dump_new          # If set, forces new objects to be dumped even if out of cycle

        self.__watches = {}         # Store watches added by the user.
                                    # Key is line number.
                                    # Value is a list of expressions.

        self.__enabled = set()      # Set of all line numbers that have been enabled already.

        self.__objects = {}         # Store (references to) objects being watched.
                                    # Key is tuple with line number and expression.
                                    # Value is the object.

        self.__prev_frame = None    # Keep pointers to previously executed frame.
        self.__prev_lineno = -1     # Useful because processing happens *after* a line has been executed,
                                    # so that we get any values defined in that line.

        self.__stepno = -1
        self.__prev_time = time.time()

    def watch(self, expr, lineno):
        self.__watches.setdefault(lineno, [])
        e = parse_expr(expr)
        self.__watches[lineno].append(e)

    def __save_object(self, frame, lineno, expr):
        if expr[0] in frame.f_locals:
            obj = frame.f_locals[expr[0]]
        else:
            obj = frame.f_globals[expr[0]]
        self.__objects[(lineno, expr)] = obj
        return obj

    def dump_value(self, lineno, expr, value):
        print '(%d, %s) -> %s' % (lineno, expr, value)

    def __dump(self, lineno, expr, obj):
        v = obj
        for id in expr[1:]:
            v = getattr(v, id)
        self.dump_value(lineno, expr, v)

    def dump_all_values(self):
        for (lineno, expr), obj in self.__objects.items():
            self.__dump(lineno, expr, obj)

    def __check_variables(self):
        done = False
        if self.__steps_delta is not None and (self.__stepno % self.__steps_delta) == 0:
            self.dump_all_values()
            done = True
        if not done and self.__time_delta is not None:
            now = time.time()
            if (now - self.__prev_time) > self.__time_delta:
                self.dump_all_values()
                done = True
                self.__prev_time = now
        return done

    def trace_command(self, frame, event, arg):
        new_objects = []

        self.__stepno += 1

        if event != 'line':
            self.__check_variables()
            self.__prev_frame = frame
            self.__prev_lineno = frame.f_lineno
            return self.trace_command

        if self.__prev_lineno in self.__watches and self.__prev_lineno not in self.__enabled:
            # Just finished executing for the first time a line that has a watch

            if frame.f_back == self.__prev_frame.f_back:
                # We are still in the same frame since the current frame and the previous frame have the same parent

                for expr in self.__watches[self.__prev_lineno]:
                    # Read the object from the current frame, since it might have been defined in the previous frame.
                    obj = self.__save_object(frame, self.__prev_lineno, expr)
                    new_objects.append((self.__prev_lineno, expr, obj))

            else:
                # The code jumped somewhere else.
                # This could happen if the user had highlighted variable 'foo' in the statement "return foo"

                for expr in self.__watches[self.__prev_lineno]:
                    # Read the object from the previous frame, since it had to be defined by then.
                    obj = self.__save_object(self.__prev_frame, lineno, expr)
                    new_objects.append((self.__prev_lineno, expr, obj))

            self.__enabled.add(self.__prev_lineno)    # Mark line as enabled

        dumped = self.__check_variables()
        if not dumped and self.__dump_new and new_objects:
            # Wasn't the moment to dump, but we have new objects
            for lineno, expr, obj in new_objects:
                self.__dump(lineno, expr, obj)

        self.__prev_frame = frame
        self.__prev_lineno = frame.f_lineno

        # When all watches have been enabled, move to faster tracer
        return self.trace_command if len(self.__enabled) != len(self.__watches) else self.fast_trace_command

    def fast_trace_command(self, frame, event, arg):
        self.__check_variables()
        self.__prev_frame = frame
        self.__prev_lineno = frame.f_lineno
        return self.trace_command        

    def start(self):
        sys.settrace(watcher.trace_command)

    def stop(self):
        sys.settrace(None)

watcher = Watcher(time_delta=.2)

# Remember that line numbers start at 1
watcher.watch('x.foo', 13)
watcher.watch('a', 16)

watcher.start()
import userscript
watcher.stop()

# Dump once more to get the final values
watcher.dump_all_values()