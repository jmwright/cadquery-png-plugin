import tempfile
import os
import pytest
from PIL import Image
import cadquery as cq
import cadquery_png_plugin.plugin


@pytest.fixture
def sample_assembly():
    """
    Creates a basic sample assembly for testing.
    """
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
    return assy


@pytest.fixture
def nested_assembly():
    """
    Creates a nested assembly that will end up jumbled if not handled properly.
    """

    def create_beam(length, plane="XY"):
        """
        Helper method to create beams
        """
        return cq.Workplane(plane).rect(150, 28, centered=False).extrude(length)

    # Default color
    c = cq.Color("burlywood3")

    # Main assembly
    main_assy = cq.Assembly()

    # Triangle side assembly
    side_assy = cq.Assembly()
    side_assy.add(
        create_beam(1500),
        loc=cq.Location((0, 0, 0), (0, 0, 0)),
        name="vertical",
        color=c,
    )
    side_assy.add(
        create_beam(2000),
        loc=cq.Location((0, 0, 0), (-40, 0, 0)),
        name="angled",
        color=c,
    )
    side_assy.add(
        create_beam(1280),
        loc=cq.Location((0, 1280, 1500), (90, 0, 0)),
        name="top",
        color=c,
    )

    # Connection between the sides
    front_assy = cq.Assembly()
    front_assy.add(
        create_beam(2500),
        loc=cq.Location((0, 0, 0), (90, -90, -90)),
        name="bottom",
        color=c,
    )
    front_assy.add(
        create_beam(2500),
        loc=cq.Location((0, 0, 1350), (90, -90, -90)),
        name="top",
        color=c,
    )

    # 'Window' assembly
    window_assy = cq.Assembly()
    window_assy.add(
        create_beam(1200, "XZ"), loc=cq.Location(0, 0, 0), name="side left", color=c
    )
    window_assy.add(
        create_beam(1200, "XZ"), loc=cq.Location(2350, 0, 0), name="side right", color=c
    )
    window_assy.add(
        create_beam(2200, "XZ"),
        loc=cq.Location((150, -150, 0), (0, 0, 90)),
        name="top",
        color=c,
    )
    window_assy.add(
        create_beam(2200, "XZ"),
        loc=cq.Location((150, -1200, 0), (0, 0, 90)),
        name="bottom",
        color=c,
    )
    # Add the window to the front assembly
    front_assy.add(
        window_assy, loc=cq.Location((-2500, 0, 150), (-90, 0, 0)), name="window"
    )

    # Add the rest of the assemblies to the main assembly
    main_assy.add(side_assy, loc=cq.Location(-150, 0, 0), name="side left")
    main_assy.add(side_assy, loc=cq.Location(2500, 0, 0), name="side right")
    main_assy.add(front_assy, loc=cq.Location(2500, 0, 0), name="front")

    return main_assy


def test_assembly_is_not_blank():
    """
    Tests to make sure that an assembly with an object passed during instantiation
    displays something in the resulting PNG.
    """

    # Generate a temporary directory to put the PNG file in
    tempdir = tempfile.mkdtemp()
    file_path = os.path.join(tempdir, "blank_test.png")

    render_options = {
        "width": 600,  # width of the output image
        "height": 600,  # height of the output image
        "color_theme": "default",  # can also be black_and_white
        "view": "front-top-right",  # front, top, front-bottom-left, etc
        "zoom": 1.0,  # zooms in and out on the center of the model
    }

    # Create a sample assembly that should reproduce the error, if present
    box = cq.Workplane().box(10, 10, 10)
    cyl = cq.Workplane().circle(2.5).extrude(5)
    assy = cq.Assembly(box, color=cq.Color(1.0, 0.0, 0.0))
    assy.add(cyl, loc=cq.Location(0, 0, 5.0), color=cq.Color(0.0, 0.0, 1.0))

    # Export the assembly
    assy.exportPNG(options=render_options, file_path=file_path)

    # Make sure that the file was created
    assert os.path.exists(file_path)

    # Make sure that the image has the content we expect
    img = Image.open(file_path)
    rgb = img.getpixel((320, 95))
    assert rgb[0] == 0
    assert rgb[1] == 0
    assert rgb[2] == 128
    rgb = img.getpixel((440, 400))
    assert rgb[0] == 128
    assert rgb[1] == 0
    assert rgb[2] == 0


def test_assembly_to_png_export_default_options(sample_assembly):
    """
    Tests to make sure that a sample assembly can be exported
    to PNG.
    """

    # Generate a temporary directory to put the PNG file in
    tempdir = tempfile.mkdtemp()
    file_path = os.path.join(tempdir, "basic_test.png")

    # Export the assembly
    sample_assembly.exportPNG(options=None, file_path=file_path)

    # Make sure that the file was created
    assert os.path.exists(file_path)

    # Make sure that the image has the content we expect
    img = Image.open(file_path)
    rgb = img.getpixel((400, 80))
    assert rgb[0] == 0
    assert rgb[1] == 180
    assert rgb[2] == 0
    rgb = img.getpixel((320, 240))
    assert rgb[0] == 180
    assert rgb[1] == 0
    assert rgb[2] == 0


def test_nested_assembly(nested_assembly):
    """
    Tests to make sure that a more complicated nested assembly works as expected.
    """

    # Generate a temporary directory to put the PNG file in
    tempdir = tempfile.mkdtemp()
    file_path = os.path.join(tempdir, "nested_test.png")

    # Export the assembly
    render_options = {
        "width": 1200,
        "height": 1200,
        "color_theme": "default",
        "view": "front-top-right",
        "zoom": 1.0,
        "background_color": (1, 1, 1),
    }
    nested_assembly.exportPNG(options=render_options, file_path=file_path)

    # Make sure that the file was created
    assert os.path.exists(file_path)

    # Make sure that the image has the content we expect
    img = Image.open(file_path)
    rgb = img.getpixel((1000, 700))
    assert rgb[0] == 177
    assert rgb[1] == 147
    assert rgb[2] == 108
    rgb = img.getpixel((500, 820))
    assert rgb[0] == 145
    assert rgb[1] == 120
    assert rgb[2] == 88


def test_assembly_with_custom_view(sample_assembly):
    """
    Tests that passing a custom view dictionary works.
    """

    # Generate a temporary directory to put the PNG file in
    tempdir = tempfile.mkdtemp()
    file_path = os.path.join(tempdir, "custom_view_test.png")

    # Export the assembly
    render_options = {
        "width": 1200,
        "height": 1200,
        "color_theme": "default",
        "view": {
            # "view_up": (0, 1, 0),  # commented to make sure that defaults kick in
            "azimuth": -100,
            "elevation": 25,
            "roll": 25,
            "window_center_x": 0.5,
            "window_center_y": 0.5,
        },
        "zoom": 1.0,
        "background_color": (1, 1, 1),
    }
    sample_assembly.exportPNG(options=render_options, file_path=file_path)

    # Make sure that the file was created
    assert os.path.exists(file_path)

    # Make sure that the image has the content we expect
    img = Image.open(file_path)
    rgb = img.getpixel((1000, 500))
    assert rgb[0] == 255
    assert rgb[1] == 255
    assert rgb[2] == 255
    rgb = img.getpixel((400, 900))
    assert rgb[0] == 227 or rgb[0] == 228
    assert rgb[1] == 0
    assert rgb[2] == 0
    rgb = img.getpixel((550, 650))
    assert rgb[0] == 0
    assert rgb[1] == 227 or rgb[1] == 228
    assert rgb[2] == 0
