import base64
import inspect
from functools import partialmethod
from io import BytesIO

import numpy as np
import pandas as pd
import PIL.Image
import pyarrow as pa
from pandas._typing import Dtype
from pandas.api.extensions import ExtensionArray

from . import huggingface


huggingface.init()
PIL.Image.init()
_IMAGE_COMPRESSION_FORMATS = list(set(PIL.Image.OPEN.keys()) & set(PIL.Image.SAVE.keys()))


def _image_to_bytes(image: "PIL.Image.Image") -> bytes:
    """Convert a PIL Image object to bytes using native compression if possible, otherwise use PNG/TIFF compression."""
    buffer = BytesIO()
    if image.format in _IMAGE_COMPRESSION_FORMATS:
        format = image.format
    else:
        format = "PNG" if image.mode in ["1", "L", "LA", "RGB", "RGBA"] else "TIFF"
    image.save(buffer, format=format)
    return buffer.getvalue()


def _encode_pil_image(image: "PIL.Image.Image") -> dict:
    return {"bytes": _image_to_bytes(image), "path": getattr(image, "filename", "") or None}


def _decode_pil_image(encoded_image: dict) -> "PIL.Image.Image":
    return PIL.Image.open(BytesIO(encoded_image["bytes"])) if encoded_image["bytes"] else PIL.Image.open(encoded_image["path"])


class ImageArray(ExtensionArray):
    _pa_type = pa.struct({"bytes": pa.binary(), "path": pa.string()})

    def __init__(self, data: np.ndarray) -> None:
        self.data = data

    @property
    def dtype(self):
        return pd.core.dtypes.dtypes.NumpyEADtype("object")

    @property
    def feature(self):
        return {"_type": "Image"}

    @classmethod
    def _from_sequence_of_strings(cls, strings, *, dtype: Dtype | None = None, copy: bool = False):
        a = np.empty(len(strings), dtype=object)
        a[:] = [PIL.Image.open(path) if path is not None else None for path in strings]
        return cls(a)

    @classmethod
    def _from_sequence_of_images(cls, images, *, dtype: Dtype | None = None, copy: bool = False):
        a = np.empty(len(images), dtype=object)
        a[:] = images
        return cls(a)

    @classmethod
    def _from_sequence_of_encoded_images(cls, encoded_images, *, dtype: Dtype | None = None, copy: bool = False):
        a = np.empty(len(encoded_images), dtype=object)
        a[:] = [_decode_pil_image(encoded_image) if encoded_image is not None else None for encoded_image in encoded_images]
        return cls(a)

    @classmethod
    def _from_sequence(cls, scalars, *, dtype: Dtype | None = None, copy: bool = False):
        if len(scalars) == 0:
            return cls(np.array([], dtype=object))
        if isinstance(scalars[0], str):
            return cls._from_sequence_of_strings(scalars, dtype=dtype, copy=copy)
        if isinstance(scalars[0], dict) and set(scalars[0]) == {"bytes", "path"}:
            return cls._from_sequence_of_encoded_images(scalars, dtype=dtype, copy=copy)
        elif isinstance(scalars[0], PIL.Image.Image):
            return cls._from_sequence_of_images(scalars, dtype=dtype, copy=copy)
        raise TypeError()

    def __eq__(self, value: object) -> bool:
        return self.data == value.data

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, item) -> "PIL.Image.Image | ImageArray":
        if isinstance(item, int):
            return self.data[item]
        return type(self)(self.data[item])

    def copy(self) -> "ImageArray":
        return ImageArray(self.data.copy())

    def __arrow_array__(self, type=None):
        return pa.array([_encode_pil_image(image) if image is not None else None for image in self.data], type=type or self._pa_type)

    def _formatter(self, boxed=False):
        return lambda x: f"<PIL.Image.Image size={x.shape[0]}x{x.shape[1]}>" if isinstance(x, np.ndarray) else str(x)


class PILMethods:

    def __init__(self, data: pd.Series) -> None:
        self.data = data

    def open(self):
        return pd.Series(ImageArray._from_sequence(self.data))

    def enable(self):
        return pd.Series(ImageArray._from_sequence_of_images(self.data))

    def _apply(self, *args, _func, **kwargs):
        if not isinstance(self.data.array, ImageArray):
            raise Exception("You need to enable PIL methods first, using for example: df['image'] = df['image'].pil.enable()")
        out = [_func(x, *args, **kwargs) for x in self.data]
        try:
            return pd.Series(type(self.data.array)._from_sequence(out))
        except TypeError:
            return pd.Series(out)

    @staticmethod
    def html_formatter(x):
        with BytesIO() as buffer:
            PIL.Image.fromarray(x.astype(np.uint8())).save(buffer, 'jpeg')
            return f'<img style="max-height: 100px;", src="data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}">'

for _name, _func in inspect.getmembers(PIL.Image.Image, predicate=inspect.isfunction):
    if not _name.startswith("_") and _name not in ["open", "save", "load"]:
        setattr(PILMethods, _name, partialmethod(PILMethods._apply, _func=_func))


_sts = pd.Series.to_string
def _new_sts(self, *args, **kwargs):
    return _sts(self, *args, **kwargs) + (", PIL methods enabled" if isinstance(self.array, ImageArray) else "")
    
pd.Series.to_string = _new_sts
