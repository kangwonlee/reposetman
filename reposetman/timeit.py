import time


def timeit(method):
    """
    Decorator to measure time of a method

    ref: https://medium.com/pythonhive/python-decorator-to-measure-the-execution-time-of-methods-fa04cb6bb36d
    """

    def timed(*args, **kw):
        print("@timeit : starting %r " % method.__name__)
        t_start_sec = time.time()
        # function to measure
        result = method(*args, **kw)
        t_end_sec = time.time()

        print("%r %g (sec)" % (method.__name__, (t_end_sec - t_start_sec)))

        return result

    return timed
