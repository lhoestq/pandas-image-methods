from functools import partial, wraps

import pandas as pd


def wrap_method(func):
    @wraps(func)
    def wrapped(self, *args, **kwargs):
        if hasattr(self.data, "map_partitions"):
            token = kwargs.get("_func", func).__name__
            series = self.data.map_partitions(partial(self.pil_method, func=func, args=args, kwargs=kwargs), meta=self._meta, token=token)
            series._meta_nonempty = self._meta_nonempty
            return series
        return func(self, *args, **kwargs)
    return wrapped


def init():
    from dask.dataframe.extensions import make_array_nonempty

    @make_array_nonempty.register(pd.core.dtypes.dtypes.NumpyEADtype)
    def _(dtype):
        return dtype.construct_array_type()._array_nonempty
