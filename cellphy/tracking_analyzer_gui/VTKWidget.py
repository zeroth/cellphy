import vtk
# from vtk import qt
# qt.QVTKRWIBase = "QGLWidget"
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor


class VTKWidget(QVTKRenderWindowInteractor):
    def __init__(self, parent=None, **kw):
        QVTKRenderWindowInteractor.__init__(self, parent, **kw)
        """
         # create the widget
            widget = QVTKRenderWindowInteractor()
            widget.Initialize()
            widget.Start()
            # if you don't want the 'q' key to exit comment this.
            widget.AddObserver("ExitEvent", lambda o, e, a=app: a.quit())
        
            ren = vtk.vtkRenderer()
            widget.GetRenderWindow().AddRenderer(ren)
        
            cone = vtk.vtkConeSource()
            cone.SetResolution(8)
        
            coneMapper = vtk.vtkPolyDataMapper()
            coneMapper.SetInputConnection(cone.GetOutputPort())
        
            coneActor = vtk.vtkActor()
            coneActor.SetMapper(coneMapper)
        
            ren.AddActor(coneActor)

        """
        self.tracks = []
        self.Initialize()
        self.Start()
        self.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())
        self.ren = vtk.vtkRenderer()
        self.actor = vtk.vtkActor()
        self.mapper = vtk.vtkPolyDataMapper()
        self.line_poly_data = vtk.vtkPolyData()

        # all you need to reset the tracks
        self.lines_cells = vtk.vtkCellArray()
        self.points = vtk.vtkPoints()
        self.colors = vtk.vtkUnsignedCharArray()
        self.point_actors = []
        self.text_actors = []

        self.GetRenderWindow().AddRenderer(self.ren)
        self.mapper.SetInputData(self.line_poly_data)

        self.actor.SetMapper(self.mapper)

        self.actor.GetProperty().SetLineWidth(3)
        self.actor.GetProperty().SetRenderLinesAsTubes(True)

        self.ren.AddActor(self.actor)

    def add_track(self, track):
        color = track.color
        color[-1] = 255
        self.create_line(list(track.time_position_map.values()), color)
        self.tracks.append(track)

    def create_line(self, pos, color):
        _points = pos
        _color = color
        _line = vtk.vtkPolyLine()

        # we have _points
        _total_points_in_track = len(_points)
        _line.GetPointIds().SetNumberOfIds(_total_points_in_track)
        # set color to line

        self.colors.SetNumberOfComponents(4)

        for index, p in enumerate(_points):
            self.points.InsertNextPoint(p)
            _line.GetPointIds().SetId(index, self.points.GetNumberOfPoints() - 1)
            self.colors.InsertNextTuple(_color)

        self.lines_cells.InsertNextCell(_line)

    def display_points(self, time_points, track_id=None):
        self.__clear_points()
        colors = vtk.vtkNamedColors()
        track = None
        if track_id is None:
            track = self.tracks[0]
        else:
            track = self.__get_track_by_id(track_id)
            if track is None:
                return

        for t_point in time_points:
            point = track.time_position_map.get(t_point, None)
            if point is None:
                continue
            point_source = vtk.vtkSphereSource()
            point_source.SetCenter(point)
            point_source.SetRadius(0.2)
            point_mapper = vtk.vtkPolyDataMapper()
            point_mapper.SetInputConnection(point_source.GetOutputPort())
            point_actor = vtk.vtkActor()
            point_actor.SetMapper(point_mapper)
            point_actor.GetProperty().SetColor(colors.GetColor3d("Red"))
            self.ren.AddActor(point_actor)
            self.point_actors.append(point_actor)

        self.render_lines()

    def highlight_track(self, track):
        # self.display_points(list(track.time_position_map.keys()), track.track_id)
        self.__reset()
        # self.__change_opacity(track)
        for _track in self.tracks:
            if _track.track_id == track.track_id:
                color = _track.color
                color[-1] = 255
                self.create_line(list(_track.time_position_map.values()), color)
            else:
                color = _track.color
                color[-1] = 20
                self.create_line(list(_track.time_position_map.values()), color)

        self.render_lines()

    def render_lines(self):
        self.line_poly_data.GetPointData().SetScalars(self.colors)
        self.line_poly_data.SetPoints(self.points)
        self.line_poly_data.SetLines(self.lines_cells)
        self.Render()

    def __get_track_by_id(self, id):
        for t in self.tracks:
            if t.track_id == id:
                return t
        return None

    def __clear_points(self):
        for a in self.point_actors:
            self.ren.RemoveActor(a)
            del a

        for b in self.text_actors:
            self.ren.RemoveActor(b)
            del b

    def __reset(self):
        self.lines_cells = vtk.vtkCellArray()
        self.points = vtk.vtkPoints()
        self.colors = vtk.vtkUnsignedCharArray()
