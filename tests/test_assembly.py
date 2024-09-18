import tempfile
import os
import cadquery as cq
import cadquery_png_plugin.plugin


def test_assembly_to_png_export_default_options():
    """
    Tests to make sure that a sample assembly can be exported
    to PNG.
    """

    # Generate a temporary directory to put the PNG file in
    tempdir = tempfile.mkdtemp()
    file_path = os.path.join(tempdir, "test.png")

    # Create a sample assembly
    box_1 = cq.Workplane().box(10, 10, 10)
    box_2 = cq.Workplane().box(3, 3, 3)
    box_3 = cq.Workplane().box(3, 3, 3)
    cyl_1 = cq.Workplane("XZ").cylinder(3.0, 1.5)
    assy = cq.Assembly(name="assy")
    assy.add(box_1, name="box_1", color=cq.Color(1, 0, 0, 1))
    assy.add(
        box_2,
        name="box_2",
        loc=cq.Location(cq.Vector(-3.0, 3.0, 6.5)),
        color=cq.Color(0, 1, 0, 1),
    )
    assy.add(
        box_3,
        name="box_3",
        loc=cq.Location(cq.Vector(3.0, -3.0, -6.5)),
        color=cq.Color(0, 1, 0, 1),
    )
    assy.add(
        cyl_1,
        name="cyl_1",
        loc=cq.Location(cq.Vector(0.0, -6.5, 0.0)),
        color=cq.Color(0, 1, 0, 1),
    )

    # Add parts to the assembly
    assy.exportPNG(options=None, file_path=file_path)

    # Make sure that the file was created
    assert os.path.exists(file_path)
