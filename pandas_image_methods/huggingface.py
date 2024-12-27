import json

import pyarrow.pandas_compat

def init():
    _cm = pyarrow.pandas_compat.construct_metadata

    def construct_metadata(columns_to_convert, *args, **kwargs):
        result = _cm(columns_to_convert, *args, **kwargs)
        result["huggingface"] = json.dumps({
            "info": {
                "features": {
                    column.name: column.array.feature
                    for column in columns_to_convert
                    if hasattr(column.array, "feature")
                }
            }
        }).encode("utf-8")
        return result

    pyarrow.pandas_compat.construct_metadata = construct_metadata
