watcher
=======

Watch Python variables live.

Dumps contents of variables being watched "live" to the console.
(To change the dump behavior, inherit from `Watcher` and override the `dump_value`.)

# Usage and Explanation

```
watcher = Watcher(time_delta=.2)

# Remember that line numbers start at 1
watcher.watch('x.foo', 13)
watcher.watch('a', 16)

watcher.start()
import userscript
watcher.stop()

# Dump once more to get the final values
watcher.dump_all_values()
```

The example above creates the watcher and sets the time between dumps of variable contents to .2 seconds.
(You can also use `steps_delta` to specify the number of Python lines to execute between every dump.)

Then, it adds two watchs:
* for expression `x.foo` defined on line `13` (see file `userscript.py`)
* for expression `a` defined on line `16` (see same file)

The watcher is started, the script to watch is imported (i.e. executed on import), then the watcher is stopped.
Finally, `dump_all_values()` is called to print the final values of the variables being watched.

# How?

Implemented using Python's debugger framework (refer to `sys.settrace`).

The implementation is *slow* and, technically, it is not *live* since the Python code is interrupted for the debugger code to execute. 
 