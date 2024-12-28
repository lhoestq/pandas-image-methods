# Pandas Image Methods

Image methods for pandas dataframes using Pillow.

Features:

* Use `PIL.Image` objects in pandas dataframes
* Call `PIL.Image` methods like `.rotate()` on a column
* Save dataframes with `PIL.Image` objects to Parquet

## Installation

```pip
pip install pandas-image-methods
```

## Usage

You can open images as `PIL.Image` objects using the `.open()` method.

Once the images are opened, you can call any [PIL Image method](https://pillow.readthedocs.io/en/stable/reference/Image.html#the-image-class):

```python
import pandas as pd
from pandas_image_methods import PILMethods

pd.api.extensions.register_series_accessor("pil")(PILMethods)

df = pd.DataFrame({"image": ["path/to/image.png"]})
df["image"] = df["image"].pil.open()
df["image"] = df["image"].pil.rotate(90)
# 0    <PIL.Image.Image size=200x200>
# Name: image, dtype: object, PIL methods enabled
```

Here is how to enable `PIL` methods for `PIL Images` created manually:

```python
df = pd.DataFrame({"image": [PIL.Image.open("path/to/image.png")]})
df["image"] = df["image"].pil.enable()
df["image"] = df["image"].pil.rotate(90)
# 0    <PIL.Image.Image size=200x200>
# Name: image, dtype: object, PIL methods enabled
```

## Save

You can save a dataset of `PIL Images` to Parquet:

```python
# Save
df = pd.DataFrame({"image": ["path/to/image.png"]})
df["image"] = df["image"].pil.open()
df.to_parquet("data.parquet")

# Later
df = pd.read_parquet("data.parquet")
df["image"] = df["image"].pil.open()
```

This doesn't just save the paths to the image files, but the actual images themselves !

Under the hood it saves dictionaries of `{"bytes": <bytes of the image file>, "path": <path or name of the image file>}`.
The images are saved as bytes using their image encoding or PNG by default. Anyone can load the Parquet data even without `pandas-image-methods` since it doesn't rely on extension types.

Note: if you created the `PIL Images` manually, don't forget to enable the `PIL` methods to enable saving to Parquet.

## Hugging Face support

Most image datasets in Parquet format on Hugging Face are compatible with `pandas-image-methods`. For example you can load the [CIFAR-100 dataset](https://huggingface.co/datasets/uoft-cs/cifar100):

```python
df = pd.read_parquet("hf://datasets/uoft-cs/cifar100/cifar100/train-00000-of-00001.parquet")
df["image"] = df["image"].pil.open()
```

Datasets created with `pandas-image-methods` and saved to Parquet are compatible with the [Dataset Viewer](https://huggingface.co/docs/hub/en/datasets-viewer) on Hugging Face and the [datasets](https://github.com/huggingface/datasets) library.

## Display in Notebooks

You can display a pandas dataframe of images in a Jupyter Notebook or on Google Colab in HTML:

```python
from IPython.display import HTML
HTML(df.head().to_html(escape=False, formatters={"image": df.image.pil.html_formatter}))
```

Example on the [julien-c/impressionists](https://huggingface.co/datasets/julien-c/impressionists) dataset for painting classification:

![output of the html formatter on Colab](https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/datasets/pandas-image-methods-html_formatter.png)
