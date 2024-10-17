from vtkmodules.vtkFiltersExtraction import vtkExtractCellsByType
from vtkmodules.vtkCommonDataModel import VTK_TRIANGLE, VTK_LINE, VTK_VERTEX
from vtkmodules.vtkRenderingCore import (
    vtkRenderer,
    vtkRenderWindow,
    vtkGraphicsFactory,
    vtkWindowToImageFilter,
    vtkActor,
    vtkPolyDataMapper as vtkMapper,
)
from vtkmodules.vtkIOImage import vtkPNGWriter

import numpy as np
import cadquery as cq


def convert_assembly_to_vtk(assy, edge_width, color_theme):
    """
    Converts a CadQuery assembly to VTK face and edge actors so that they can be rendered.
    """
    face_actors = []
    edge_actors = []

    # Walk the assembly tree to make sure all objects are exported
    for subassy in assy.traverse():
        for shape, name, loc, col in subassy[1]:
            color = col.toTuple() if col else (0.1, 0.1, 0.1, 1.0)
            translation, rotation = loc.toTuple()

            # Override the face color if another theme has been requested
            if color_theme == "black_and_white" and not "assembly_line" in name:
                color = (2.0, 2.0, 2.0, 1.0)
            elif color_theme == "black_and_white" and "assembly_line" in name:
                color = (0.0, 0.0, 0.0, 1.0)

            # Tesselate the CQ object into VTK data
            vtk_data = shape.toVtkPolyData(1e-3, 0.1)

            # Extract faces
            extr = vtkExtractCellsByType()
            extr.SetInputDataObject(vtk_data)

            extr.AddCellType(VTK_LINE)
            extr.AddCellType(VTK_VERTEX)
            extr.Update()
            data_edges = extr.GetOutput()

            # Extract edges
            extr = vtkExtractCellsByType()
            extr.SetInputDataObject(vtk_data)

            extr.AddCellType(VTK_TRIANGLE)
            extr.Update()
            data_faces = extr.GetOutput()

            # Remove normals from edges
            data_edges.GetPointData().RemoveArray("Normals")

            # Set up the face and edge mappers and actors
            face_mapper = vtkMapper()
            face_actor = vtkActor()
            face_actor.SetMapper(face_mapper)
            edge_mapper = vtkMapper()
            edge_actor = vtkActor()
            edge_actor.SetMapper(edge_mapper)

            # Update the faces
            face_mapper.SetInputDataObject(data_faces)
            face_actor.SetPosition(*translation)
            face_actor.SetOrientation(*rotation)
            face_actor.GetProperty().SetColor(*color[:3])
            face_actor.GetProperty().SetOpacity(color[3])

            # Allow the caller to control the edge width
            edge_width = 1
            if "edge_width" in subassy[1].metadata:
                edge_width = subassy[1].metadata["edge_width"]

            # Choose a default of black if no edge color was chosen
            cur_edge_color = (0.0, 0.0, 0.0)
            edge_opacity = 1.0
            if "edge_color" in subassy[1].metadata:
                cur_edge_color = subassy[1].metadata["edge_color"].toTuple()[:3]
                edge_opacity = subassy[1].metadata["edge_color"].toTuple()[3]

            edge_mapper.SetInputDataObject(data_edges)
            edge_actor.SetPosition(*translation)
            edge_actor.SetOrientation(*rotation)
            edge_actor.GetProperty().SetColor(cur_edge_color[0], cur_edge_color[1], cur_edge_color[2])
            edge_actor.GetProperty().SetOpacity(edge_opacity)
            edge_actor.GetProperty().SetLineWidth(edge_width)

            # Handle all actors
            face_actors.append(face_actor)
            edge_actors.append(edge_actor)

    return face_actors, edge_actors


def setup_render_window(face_actors, edge_actors, width, height, background_color):
    """
    Sets up a VTK render window with the given actors, dimensions and background color.
    """

    # Setup offscreen rendering
    graphics_factory = vtkGraphicsFactory()
    graphics_factory.SetOffScreenOnlyMode(1)
    graphics_factory.SetUseMesaClasses(1)

    # A renderer and render window
    renderer = vtkRenderer()
    render_window = vtkRenderWindow()
    render_window.SetSize(width, height)
    render_window.SetOffScreenRendering(1)

    render_window.AddRenderer(renderer)

    # Add all the actors to the scene
    for face_actor in face_actors:
        renderer.AddActor(face_actor)
    for edge_actor in edge_actors:
        renderer.AddActor(edge_actor)

    renderer.SetBackground(
        background_color[0], background_color[1], background_color[2]
    )

    # Render the scene
    render_window.Render()

    return render_window


def setup_camera(renderer, view, zoom=1.0):
    """
    Sets up a VTK camera with the given center, distance and rotation.
    """

    # Apply different options for different views
    if view == "top":
        view_up = (0, 1, 0)
        azimuth = 0
        elevation = 0
        roll = 0
        window_center_x = 0.0
        window_center_y = 0.0
    elif view == "bottom":
        view_up = (0, 1, 0)
        azimuth = 180
        elevation = 0
        roll = 0
        window_center_x = 0.0
        window_center_y = 0.0
    elif view == "back":
        view_up = (0, 1, 0)
        azimuth = 0
        elevation = 90
        roll = 180
        window_center_x = 0.0
        window_center_y = 0.0
    elif view == "front":
        view_up = (0, 1, 0)
        azimuth = 0
        elevation = -90
        roll = 0
        window_center_x = 0.0
        window_center_y = 0.0
    elif view == "left":
        view_up = (0, 1, 0)
        azimuth = 90
        elevation = 180
        roll = 90
        window_center_x = 0.0
        window_center_y = 0.0
    elif view == "right":
        view_up = (0, 1, 0)
        azimuth = 90
        elevation = 0
        roll = -90
        window_center_x = 0.0
        window_center_y = 0.0
    elif view == "front-top-right":
        view_up = (0, 1, 0)
        azimuth = 45
        elevation = -45
        roll = -55
        window_center_x = -0.05
        window_center_y = -0.05
    elif view == "front-top-left":
        view_up = (0, 1, 0)
        azimuth = -45
        elevation = -45
        roll = 55
        window_center_x = 0.1
        window_center_y = -0.2
    elif view == "front-bottom-right":
        view_up = (0, 1, 0)
        azimuth = -45
        elevation = -135
        roll = -125
        window_center_x = -0.05
        window_center_y = 0.05
    elif view == "front-bottom-left":
        view_up = (0, 1, 0)
        azimuth = 45
        elevation = -135
        roll = 125
        window_center_x = 0.1
        window_center_y = -0.1
    elif view == "back-top-right":
        view_up = (0, 1, 0)
        azimuth = 135
        elevation = 135
        roll = 125
        window_center_x = 0.1
        window_center_y = -0.1
    elif view == "back-top-left":
        view_up = (0, 1, 0)
        azimuth = -135
        elevation = 135
        roll = -125
        window_center_x = -0.1
        window_center_y = -0.1
    elif view == "back-bottom-left":
        view_up = (0, 1, 0)
        azimuth = 135
        elevation = 45
        roll = -55
        window_center_x = -0.1
        window_center_y = -0.2
    elif view == "back-bottom-right":
        view_up = (0, 1, 0)
        azimuth = -135
        elevation = 45
        roll = 55
        window_center_x = 0.1
        window_center_y = 0.1

    # Set the camera up for the requested view
    camera = renderer.GetActiveCamera()
    camera.ParallelProjectionOn()
    camera.SetViewUp(*view_up)
    camera.Zoom(zoom)
    camera.Azimuth(azimuth)
    camera.Elevation(elevation)
    camera.Roll(roll)
    camera.SetWindowCenter(window_center_x, window_center_y)

    # Set the clipping range
    camera.SetClippingRange(-10000.0, 10000.0)


def save_render_window_to_png(render_window, filename):
    """
    Saves the scene in a render window to a PNG file on disk.
    """
    # Export a PNG of the scene
    windowToImageFilter = vtkWindowToImageFilter()
    windowToImageFilter.SetInput(render_window)
    windowToImageFilter.Update()

    writer = vtkPNGWriter()
    writer.SetFileName(filename)
    writer.SetInputConnection(windowToImageFilter.GetOutputPort())
    writer.Write()

    return None


def export_assembly_png(self, options, file_path):
    """
    Renders a CadQuery assembly to a PNG file.
    """

    # Create some defaults for renders if there are no options
    if options is None:
        options = {}
        options["width"] = 800
        options["height"] = 600
        options["background_color"] = (0.8, 0.8, 0.8)
        options["view"] = "front-top-right"
        options["zoom"] = 1.0
    if "width" not in options:
        options["width"] = 800
    if "height" not in options:
        options["height"] = 600
    if "background_color" not in options:
        options["background_color"] = (0.8, 0.8, 0.8)
    if "view" not in options:
        options["view"] = "front-top-right"
    if "zoom" not in options:
        options["zoom"] = 1.0
    if "edge_color" not in options:
        options["edge_color"] = (0.0, 0.0, 0.0)
    if "edge_width" not in options:
        options["edge_width"] = 1
    if "color_theme" not in options:
        options["color_theme"] = "default"

    # Convert the assembly to VTK actors that can be rendered
    face_actors, edge_actors = convert_assembly_to_vtk(self,
                                                       options["edge_width"],
                                                       options["color_theme"])

    # Variables for the render window
    width = options["width"]
    height = options["height"]
    background_color = options["background_color"]

    # Override colors for a given theme
    if "color_theme" in options:
        if options["color_theme"] == "black_and_white":
            background_color = (1.0, 1.0, 1.0)

    render_window = setup_render_window(
        face_actors, edge_actors, width, height, background_color
    )

    # View that was requested of the assembly
    view = options["view"]

    # Center and fit the assembly using the camera
    setup_camera(render_window.GetRenderers().GetFirstRenderer(),
                 view,
                 options["zoom"])

    # Save the render window to a PNG file
    save_render_window_to_png(render_window, file_path)


# Path the function into the Assembly class
cq.Assembly.exportPNG = export_assembly_png
