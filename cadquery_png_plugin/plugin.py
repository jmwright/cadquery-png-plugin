from math import degrees
from vtkmodules.vtkRenderingCore import (
    vtkRenderer,
    vtkRenderWindow,
    vtkGraphicsFactory,
    vtkWindowToImageFilter,
    vtkActor,
    vtkPolyDataMapper as vtkMapper,
)
from vtkmodules.vtkFiltersExtraction import vtkExtractCellsByType
from vtkmodules.vtkCommonDataModel import VTK_TRIANGLE, VTK_LINE, VTK_VERTEX
from vtkmodules.vtkIOImage import vtkPNGWriter
import cadquery as cq

def export_assembly_png(self, assy, options, filename):
    print("Exporting PNG")

    """
    Exports an assembly to a VTK object, which can then be rendered to a PNG image
    while preserving colors, rotation, etc.
    :param assy: Assembly to be exported to PNG
    :param path: Path and filename for writing the PNG data to
    :param options: Options that influence the way the PNG is rendered
    """

    face_actors = []
    edge_actors = []

    # Walk the assembly tree to make sure all objects are exported
    for subassy in assy.traverse():
        for shape, name, loc, col in subassy[1]:
            color = col.toTuple() if col else (0.1, 0.1, 0.1, 1.0)
            translation, rotation = loc.toTuple()

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
            face_actor.SetOrientation(*map(degrees, rotation))
            face_actor.GetProperty().SetColor(*color[:3])
            face_actor.GetProperty().SetOpacity(color[3])

            # Update the edges
            edge_mapper.SetInputDataObject(data_edges)
            edge_actor.SetPosition(*translation)
            edge_actor.SetOrientation(*map(degrees, rotation))
            edge_actor.GetProperty().SetColor(1.0, 1.0, 1.0)
            edge_actor.GetProperty().SetLineWidth(1)

            # Handle all actors
            face_actors.append(face_actor)
            edge_actors.append(edge_actor)

    # We need a compound assembly object so we can get the size for the camera position
    assy_compound = assy.toCompound()

    # Try to determine sane defaults for the camera position
    camera_x = 20
    camera_y = 20
    camera_z = 20
    if not options or "camera_position" not in options:
        camera_x = (
            assy_compound.BoundingBox().xmax - assy_compound.BoundingBox().xmin
        ) * 2.0
        camera_y = (
            assy_compound.BoundingBox().ymax - assy_compound.BoundingBox().ymin
        ) * 2.0
        camera_z = (
            assy_compound.BoundingBox().zmax - assy_compound.BoundingBox().zmin
        ) * 2.0

    # Handle view options that were passed in
    if options:
        width = options["width"] if "width" in options else 800
        height = options["height"] if "height" in options else 600
        camera_position = (
            options["camera_position"]
            if "camera_position" in options
            else (camera_x, camera_y, camera_z)
        )
        view_up_direction = (
            options["view_up_direction"] if "view_up_direction" in options else (0, 0, 1)
        )
        focal_point = options["focal_point"] if "focal_point" in options else (0, 0, 0)
        parallel_projection = (
            options["parallel_projection"] if "parallel_projection" in options else True
        )
        background_color = (
            options["background_color"] if "background_color" in options else (0.5, 0.5, 0.5)
        )
        clipping_range = options["clipping_range"] if "clipping_range" in options else None
    else:
        width = 800
        height = 600
        camera_position = (camera_x, camera_y, camera_z)
        view_up_direction = (0, 0, 1)
        focal_point = (0, 0, 0)
        parallel_projection = False
        background_color = (0.8, 0.8, 0.8)
        clipping_range = None

    # Setup offscreen rendering
    graphics_factory = vtkGraphicsFactory()
    graphics_factory.SetOffScreenOnlyMode(1)
    graphics_factory.SetUseMesaClasses(1)

    # A renderer and render window
    renderer = vtkRenderer()
    renderWindow = vtkRenderWindow()
    renderWindow.SetSize(width, height)
    renderWindow.SetOffScreenRendering(1)

    renderWindow.AddRenderer(renderer)

    # Add all the actors to the scene
    for face_actor in face_actors:
        renderer.AddActor(face_actor)
    for edge_actor in edge_actors:
        renderer.AddActor(edge_actor)

    renderer.SetBackground(
        background_color[0], background_color[1], background_color[2]
    )

    # Render the scene
    renderWindow.Render()

    # Set the camera as the user requested
    camera = renderer.GetActiveCamera()
    camera.SetPosition(camera_position[0], camera_position[1], camera_position[2])
    camera.SetViewUp(view_up_direction[0], view_up_direction[1], view_up_direction[2])
    camera.SetFocalPoint(focal_point[0], focal_point[1], focal_point[2])
    if parallel_projection:
        camera.ParallelProjectionOn()
    else:
        camera.ParallelProjectionOff()

    # Set the clipping range
    if clipping_range:
        camera.SetClippingRange(clipping_range[0], clipping_range[1])

    # Export a PNG of the scene
    windowToImageFilter = vtkWindowToImageFilter()
    windowToImageFilter.SetInput(renderWindow)
    windowToImageFilter.Update()

    writer = vtkPNGWriter()
    writer.SetFileName(filename)
    writer.SetInputConnection(windowToImageFilter.GetOutputPort())
    writer.Write()

# Path the function into the Assembly class
cq.Assembly.exportPNG = export_assembly_png
