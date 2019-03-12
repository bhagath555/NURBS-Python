"""
.. module:: VisVTK
    :platform: Unix, Windows
    :synopsis: VTK visualization component for NURBS-Python

.. moduleauthor:: Onur Rauf Bingol <orbingol@gmail.com>

"""

from random import random
from . import vis
from . import vtk_helpers as vtkh
import numpy as np
from vtk.util.numpy_support import numpy_to_vtk
from vtk import VTK_FLOAT


class VisConfig(vis.VisConfigAbstract):
    """ Configuration class for VTK visualization module.

    This class is only required when you would like to change the visual defaults of the plots and the figure.

    The ``VisVTK`` module has the following configuration variables:

    * ``ctrlpts`` (bool): Control points polygon/grid visibility. *Default: True*
    * ``evalpts`` (bool): Curve/surface points visibility. *Default: True*
    * ``trims`` (bool): Trim curve visibility. *Default: True*
    * ``figure_size`` (list): Size of the figure in (x, y). *Default: (800, 600)*
    * ``line_width`` (int): Thickness of the lines on the figure. *Default: 1.0*
    """
    def __init__(self, **kwargs):
        super(VisConfig, self).__init__(**kwargs)
        self._bg = (  # background colors
            (0.5, 0.5, 0.5), (0.2, 0.2, 0.2), (0.25, 0.5, 0.75), (1.0, 1.0, 0.0),
            (1.0, 0.5, 0.0), (0.5, 0.0, 1.0), (0.0, 0.0, 0.0), (1.0, 1.0, 1.0)
        )
        self._bg_id = 0  # used for keeping track of the background numbering
        self.display_ctrlpts = kwargs.get('ctrlpts', True)
        self.display_evalpts = kwargs.get('evalpts', True)
        self.display_trims = kwargs.get('trims', True)
        self.figure_size = kwargs.get('figure_size', (800, 600))  # size of the render window
        self.line_width = kwargs.get('line_width', 1.0)

    def keypress_callback(self, obj, ev):
        """ VTK callback for keypress events.

        Keypress events:
            * ``e``: exit the application
            * ``p``: pick object (hover the mouse and then press to pick)
            * ``l``: change color of the picked object
            * ``f``: fly to point (click somewhere in the window and press to fly)
            * ``r``: reset the camera
            * ``s`` and ``w``: switch between solid and wireframe modes
            * ``b``: change background color
            * ``arrow keys``: pan the model

        :param obj: render window interactor
        :type obj: vtkRenderWindowInteractor
        :param ev: event name
        :type ev: str
        """
        key = obj.GetKeySym()  # pressed key (as str)
        render_window = obj.GetRenderWindow()  # vtkRenderWindow
        renderer = render_window.GetRenderers().GetFirstRenderer()  # vtkRenderer

        # Custom keypress events
        if key == 'Up':
            camera = renderer.GetActiveCamera()  # vtkCamera
            camera.Pitch(-2.5)
        if key == 'Down':
            camera = renderer.GetActiveCamera()  # vtkCamera
            camera.Pitch(2.5)
        if key == 'Left':
            camera = renderer.GetActiveCamera()  # vtkCamera
            camera.Yaw(-2.5)
        if key == 'Right':
            camera = renderer.GetActiveCamera()  # vtkCamera
            camera.Yaw(2.5)
        if key == 'b':
            if self._bg_id >= len(self._bg):
                self._bg_id = 0
            renderer.SetBackground(*self._bg[self._bg_id])
            self._bg_id += 1
        if key == 'l':
            picker = obj.GetPicker()  # vtkPropPicker
            actor = picker.GetActor()  # vtkActor
            if actor is not None:
                actor.GetProperty().SetColor(random(), random(), random())
            # print(picker.GetSelectionPoint())

        # Update render window
        render_window.Render()


class VisCurve2D(vis.VisAbstract):
    """ VTK visualization module for curves. """
    def __init__(self, config=VisConfig()):
        super(VisCurve2D, self).__init__(config=config)

    def render(self, **kwargs):
        """ Plots the curve and the control points polygon. """
        # Calling parent function
        super(VisCurve2D, self).render(**kwargs)

        # Initialize a list to store VTK actors
        vtk_actors = []

        # Start plotting
        for plot in self._plots:
            # Plot control points
            if plot['type'] == 'ctrlpts' and self.vconf.display_ctrlpts:
                # Points as spheres
                pts = np.array(plot['ptsarr'], dtype=np.float)
                # Handle 2-dimensional data
                if pts.shape[1] == 2:
                    pts = np.c_[pts, np.zeros(pts.shape[0], dtype=np.float)]
                vtkpts = numpy_to_vtk(pts, deep=False, array_type=VTK_FLOAT)
                actor1 = vtkh.create_actor_pts(pts=vtkpts, color=vtkh.create_color(plot['color']))
                vtk_actors.append(actor1)
                # Lines
                actor2 = vtkh.create_actor_polygon(pts=vtkpts, color=vtkh.create_color(plot['color']),
                                                   size=self.vconf.line_width)
                vtk_actors.append(actor2)

            # Plot evaluated points
            if plot['type'] == 'evalpts' and self.vconf.display_evalpts:
                pts = np.array(plot['ptsarr'], dtype=np.float)
                # Handle 2-dimensional data
                if pts.shape[1] == 2:
                    pts = np.c_[pts, np.zeros(pts.shape[0], dtype=np.float)]
                vtkpts = numpy_to_vtk(pts, deep=False, array_type=VTK_FLOAT)
                actor1 = vtkh.create_actor_polygon(pts=vtkpts, color=vtkh.create_color(plot['color']),
                                                   size=self.vconf.line_width * 2)
                vtk_actors.append(actor1)

        # Render actors
        vtkh.create_render_window(vtk_actors, dict(KeyPressEvent=(self.vconf.keypress_callback, 1.0)),
                                  figure_size=self.vconf.figure_size)


# VisCurve3D is an alias for VisCurve2D
VisCurve3D = VisCurve2D


class VisSurface(vis.VisAbstract):
    """ VTK visualization module for surfaces. """
    def __init__(self, config=VisConfig()):
        super(VisSurface, self).__init__(config=config)
        self._module_config['ctrlpts'] = "quads"
        self._module_config['evalpts'] = "triangles"

    def render(self, **kwargs):
        """ Plots the surface and the control points grid. """
        # Calling parent function
        super(VisSurface, self).render(**kwargs)

        # Initialize a list to store VTK actors
        vtk_actors = []

        # Start plotting
        for plot in self._plots:
            # Plot control points
            if plot['type'] == 'ctrlpts' and self.vconf.display_ctrlpts:
                vertices = [v.data for v in plot['ptsarr'][0]]
                faces = [q.data for q in plot['ptsarr'][1]]
                # Points as spheres
                pts = np.array(vertices, dtype=np.float)
                vtkpts = numpy_to_vtk(pts, deep=False, array_type=VTK_FLOAT)
                actor1 = vtkh.create_actor_pts(pts=vtkpts, color=vtkh.create_color(plot['color']))
                vtk_actors.append(actor1)
                # Quad mesh
                lines = np.array(faces, dtype=np.int)
                actor2 = vtkh.create_actor_mesh(pts=vtkpts, lines=lines, color=vtkh.create_color(plot['color']),
                                                size=self.vconf.line_width)
                vtk_actors.append(actor2)

            # Plot evaluated points
            if plot['type'] == 'evalpts' and self.vconf.display_evalpts:
                vertices = [v.data for v in plot['ptsarr'][0]]
                vtkpts = numpy_to_vtk(vertices, deep=False, array_type=VTK_FLOAT)
                faces = [t.vertex_ids_zero for t in plot['ptsarr'][1]]
                tris = np.array(faces, dtype=np.int)
                actor1 = vtkh.create_actor_tri(pts=vtkpts, tris=tris, color=vtkh.create_color(plot['color']))
                vtk_actors.append(actor1)

            # Plot trim curves
            if self.vconf.display_trims:
                if plot['type'] == 'trimcurve':
                    pts = np.array(plot['ptsarr'], dtype=np.float)
                    vtkpts = numpy_to_vtk(pts, deep=False, array_type=VTK_FLOAT)
                    actor1 = vtkh.create_actor_polygon(pts=vtkpts, color=vtkh.create_color(plot['color']))
                    vtk_actors.append(actor1)

        # Render actors
        vtkh.create_render_window(vtk_actors, dict(KeyPressEvent=(self.vconf.keypress_callback, 1.0)),
                                  figure_size=self.vconf.figure_size)


class VisVolume(vis.VisAbstract):
    """ VTK visualization module for volumes. """
    def __init__(self, config=VisConfig()):
        super(VisVolume, self).__init__(config=config)
        self._module_config['ctrlpts'] = "points"
        self._module_config['evalpts'] = "points"

    def render(self, **kwargs):
        """ Plots the volume and the control points. """
        # Calling parent function
        super(VisVolume, self).render(**kwargs)

        # Initialize a list to store VTK actors
        vtk_actors = []

        # Start plotting
        for plot in self._plots:
            # Plot control points
            if plot['type'] == 'ctrlpts' and self.vconf.display_ctrlpts:
                # Points as spheres
                pts = np.array(plot['ptsarr'], dtype=np.float)
                vtkpts = numpy_to_vtk(pts, deep=False, array_type=VTK_FLOAT)
                temp_actor = vtkh.create_actor_pts(pts=vtkpts, color=vtkh.create_color(plot['color']))
                vtk_actors.append(temp_actor)

            # Plot evaluated points
            if plot['type'] == 'evalpts' and self.vconf.display_evalpts:
                pts = np.array(plot['ptsarr'], dtype=np.float)
                vtkpts = numpy_to_vtk(pts, deep=False, array_type=VTK_FLOAT)
                temp_actor = vtkh.create_actor_pts(pts=vtkpts, color=vtkh.create_color(plot['color']))
                vtk_actors.append(temp_actor)

        # Render actors
        vtkh.create_render_window(vtk_actors, dict(KeyPressEvent=(self.vconf.keypress_callback, 1.0)),
                                  figure_size=self.vconf.figure_size)


class VisVoxel(vis.VisAbstract):
    """ VTK visualization module for voxel representation of the volumes. """
    def __init__(self, config=VisConfig()):
        super(VisVoxel, self).__init__(config=config)
        self._module_config['ctrlpts'] = "points"
        self._module_config['evalpts'] = "voxels"

    def render(self, **kwargs):
        """ Plots the volume and the control points. """
        # Calling parent function
        super(VisVoxel, self).render(**kwargs)

        # Initialize a list to store VTK actors
        vtk_actors = []

        # Start plotting
        for plot in self._plots:
            # Plot control points
            if plot['type'] == 'ctrlpts' and self.vconf.display_ctrlpts:
                # Points as spheres
                pts = np.array(plot['ptsarr'], dtype=np.float)
                vtkpts = numpy_to_vtk(pts, deep=False, array_type=VTK_FLOAT)
                temp_actor = vtkh.create_actor_pts(pts=vtkpts, color=vtkh.create_color(plot['color']))
                vtk_actors.append(temp_actor)

            # Plot evaluated points
            if plot['type'] == 'evalpts' and self.vconf.display_evalpts:
                faces = np.array(plot['ptsarr'][1], dtype=np.float)
                filled = np.array(plot['ptsarr'][2], dtype=np.int)
                grid_filled = faces[filled == 1]
                temp_actor = vtkh.create_actor_hexahedron(grid=grid_filled, color=vtkh.create_color(plot['color']))
                vtk_actors.append(temp_actor)

        # Render actors
        vtkh.create_render_window(vtk_actors, dict(KeyPressEvent=(self.vconf.keypress_callback, 1.0)),
                                  figure_size=self.vconf.figure_size)
