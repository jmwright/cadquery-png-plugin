
import cadquery as cq
from cadquery_png_plugin.plugin import export_assembly_png

def test_assembly_to_png_export():
    """
    Tests to make sure that a sample assembly can be exported
    to PNG.
    """

    # Create a sample assembly
    assy = cq.Assembly(cq.Workplane().box(1, 1, 1))
    # assy.add(cq.Workplane().box(1, 1, 1))
    # assy.add(cq.Workplane().box(1, 1, 1).translate((1, 1, 1)))

    # Export the assembly to a PNG file
    assy.exportPNG(assy, {}, "test.png")

    # assert False