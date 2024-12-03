# cadquery-png-plugin

*cadquery-png-plugin* is a PNG export plugin for [CadQuery](https://cadquery.readthedocs.io/en/latest/), which is a Python API for creating CAD models and assemblies. The core CadQuery library can export SVG images, but not bitmap images, such as PNG.

## Installation

This plugin has not been released on PyPI, but it can be installed via `git` and `pip`.

```bash
pip install git+https://github.com/jmwright/cadquery-png-plugin.git
```

This installation will also install other required packages such as CadQuery if the environment does not already include them.

## Usage

Below is a minimal example of this plugin being used to export a CadQuery assembly.

```python
import cadquery as cq
import cadquery_png_plugin.plugin  # This registers the plugin with CadQuery

# You can customize the render options through a dictionary
render_options = {"width": 600,  # width of the output image
                  "height": 600,  # height of the output image
                  "color_theme": "default",  # can also be black_and_white
                  "view": "front-top-right",  # front, top, front-bottom-left, etc
                  "zoom": 1.0  # zooms in and out on the center of the model
                  }

# Create a simple CadQuery assembly for an example export
box = cq.Workplane().box(10, 10, 10)
cyl = cq.Workplane().circle(2.5).extrude(5)
assy = cq.Assembly(box, color=cq.Color(1.0, 0.0, 0.0))
assy.add(cyl, loc=cq.Location(0, 0, 5.0), color=cq.Color(0.0, 0.0, 1.0))

# Do the PNG export
assy.exportPNG(options=render_options, file_path="ouptput_file.png")
```

That code results in the following image.

![Sample PNG based on the script above](sample_image.png)

## Where this Plugin is Used

An example of this plugin being used by a project in the wild can be found in the [Nimble repository](https://github.com/Wakoma/nimble/blob/c33497258f969392d91b2c30aa8d06ef7a2bd7ec/nimble_build_system/cad/renderer.py).

## Running Tests

1. Clone the repository.
```
https://github.com/jmwright/cadquery-png-plugin.git && cd cadquery-png-plugin
```

2. Install the plugin and its development dependencies.
```
pip install -e .
pip install -e .[dev]
```

3. Run the tests
```
pytest
```
