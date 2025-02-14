# -*- coding: utf-8 -*-
#   Copyright 2017 Edoardo Pasca
#   Copyright 2018 Richard Smith
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import numpy
import vtk
from ccpi.viewer import (ALT_KEY, CONTROL_KEY, CROSSHAIR_ACTOR, CURSOR_ACTOR, HELP_ACTOR, HISTOGRAM_ACTOR,
                         LINEPLOT_ACTOR, OVERLAY_ACTOR, SHIFT_KEY, SLICE_ACTOR, SLICE_ORIENTATION_XY,
                         SLICE_ORIENTATION_XZ, SLICE_ORIENTATION_YZ)
from ccpi.viewer.CILViewerBase import CILViewerBase
from ccpi.viewer.utils import colormaps
from ccpi.viewer.utils import CameraData


class CILInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):

    def __init__(self, callback):
        vtk.vtkInteractorStyleTrackballCamera.__init__(self)
        self._viewer = callback
        self.AddObserver('MouseWheelForwardEvent', self.mouseInteraction, 1.0)
        self.AddObserver('MouseWheelBackwardEvent', self.mouseInteraction, 1.0)
        self.AddObserver('KeyPressEvent', self.OnKeyPress, 1.0)
        self.AddObserver('LeftButtonPressEvent', self.OnLeftMouseClick)
        self.AddObserver('LeftButtonReleaseEvent', self.OnLeftMouseRelease)
        #self.AddObserver('RightButtonPressEvent', self.OnRightMousePress, -0.5)
        #self.AddObserver('RightButtonReleaseEvent', self.OnRightMouseRelease, -0.5)

    def GetSliceOrientation(self):
        return self._viewer.sliceOrientation

    def GetDimensions(self):
        return self._viewer.img3D.GetDimensions()

    def GetActiveSlice(self):
        return self._viewer.getActiveSlice()

    def SetActiveSlice(self, sliceno):
        self._viewer.setActiveSlice(sliceno)

    def UpdatePipeline(self, resetcamera=False):
        self._viewer.updatePipeline(resetcamera)

    def GetSliceActorNo(self):
        return self._viewer.sliceActorNo

    def SetSliceOrientation(self, orientation):
        self._viewer.sliceOrientation = orientation

    def SetActiveCamera(self, camera):
        self._viewer.ren.SetActiveCamera(camera)

    def Render(self):
        self._viewer.renWin.Render()

    def GetKeyCode(self):
        return self.GetInteractor().GetKeyCode()

    def SetKeyCode(self, keycode):
        self.GetInteractor().SetKeyCode(keycode)

    def GetControlKey(self):
        return self.GetInteractor().GetControlKey()

    def GetShiftKey(self):
        return self.GetInteractor().GetShiftKey()

    def GetAltKey(self):
        return self.GetInteractor().GetAltKey()

    def GetEventPosition(self):
        return self.GetInteractor().GetEventPosition()

    def GetActiveCamera(self):
        return self._viewer.ren.GetActiveCamera()

    def SetDecimalisation(self, value):
        decimate = self._viewer.decimate
        decimate.SetTargetReduction(value)
        if not decimate.GetInput() is None:
            decimate.Update()

    def SetEventActive(self, event):
        self._viewer.event.On(event)

    def SetEventInactive(self, event):
        self._viewer.event.Off(event)

    def GetViewerEvent(self, event):
        return self._viewer.event.isActive(event)

    def SetInitialLevel(self, level):
        self._viewer.InitialLevel = level

    def GetInitialLevel(self):
        return self._viewer.InitialLevel

    def SetInitialWindow(self, window):
        self._viewer.InitialWindow = window

    def GetInitialWindow(self):
        return self._viewer.InitialWindow

    def HideActor(self, actorno, delete=False):
        self._viewer.hideActor(actorno, delete)

    def ShowActor(self, actorno):
        self._viewer.showActor(actorno)

    def UpdateImageSlice(self):
        self._viewer.imageSlice.Update()
        self.Render()

    def mouseInteraction(self, interactor, event):
        shift = interactor.GetShiftKey()
        advance = 1
        if shift:
            advance = 10

        if event == 'MouseWheelForwardEvent':
            maxSlice = self._viewer.img3D.GetExtent()[self.GetSliceOrientation() * 2 + 1]
            # print (self.GetActiveSlice())
            if (self.GetActiveSlice() + advance <= maxSlice):
                self.SetActiveSlice(self.GetActiveSlice() + advance)
                self.UpdatePipeline()
        else:
            minSlice = self._viewer.img3D.GetExtent()[self.GetSliceOrientation() * 2]
            if (self.GetActiveSlice() - advance >= minSlice):
                self.SetActiveSlice(self.GetActiveSlice() - advance)
                self.UpdatePipeline()

    def OnLeftMouseClick(self, interactor, event):
        self.SetDecimalisation(0.8)
        self.OnLeftButtonDown()

    def OnLeftMouseRelease(self, interactor, event):
        self.SetDecimalisation(0.0)
        self.OnLeftButtonUp()

    def OnRightMousePress(self, interactor, event):
        ctrl = interactor.GetControlKey()
        alt = interactor.GetAltKey()
        shift = interactor.GetShiftKey()
        # print (alt, ctrl,shift)
        if alt and not (ctrl and shift):
            self.SetEventActive("WINDOW_LEVEL_EVENT")
        if not (alt and ctrl and shift):
            self.SetEventActive("ZOOM_EVENT")

    def OnRightMouseRelease(self, interactor, event):
        ctrl = interactor.GetControlKey()
        alt = interactor.GetAltKey()
        shift = interactor.GetShiftKey()

        # print (alt, ctrl,shift)
        if alt and not (ctrl and shift):
            self.SetEventInactive("WINDOW_LEVEL_EVENT")
        if not (alt and ctrl and shift):
            self.SetEventInactive("ZOOM_EVENT")

    def ToggleSliceInterpolation(self):
        # toggle interpolation of image slice
        is_interpolated = self._viewer.imageSlice.GetProperty().GetInterpolationType()
        if is_interpolated:
            self._viewer.imageSlice.GetProperty().SetInterpolationTypeToNearest()
        else:
            self._viewer.imageSlice.GetProperty().SetInterpolationTypeToLinear()
        self._viewer.updatePipeline()

    def SetVolumeClipping(self, clipping_on):
        if hasattr(self._viewer, 'planew') and self._viewer.clipping_plane_initialised:
            self._viewer.planew.SetEnabled(clipping_on)
            self._viewer.getRenderer().Render()
        else:
            # Doesn't exist and turn it off do nothing else:
            if clipping_on:
                planew = self.CreateClippingPlane()
                planew.On()

    def ToggleVolumeClipping(self):
        viewer = self._viewer
        viewer.imageSlice.VisibilityOff()
        # clip a volume render if available
        if hasattr(self._viewer, 'planew') and self._viewer.clipping_plane_initialised:
            is_enabled = viewer.planew.GetEnabled()
            self.SetVolumeClipping(not is_enabled)
        else:
            self.SetVolumeClipping(True)
        viewer.updatePipeline()

    def ToggleSliceVisibility(self):
        # toggle visibility of the slice
        if self._viewer.imageSlice.GetVisibility():
            self._viewer.imageSlice.VisibilityOff()
        else:
            self._viewer.imageSlice.VisibilityOn()
        self._viewer.updatePipeline()

    def SetVolumeVisibility(self, visibility):
        if not visibility:
            self._viewer.volume.VisibilityOff()
            self._viewer.light.SwitchOff()
        else:
            self._viewer.volume.VisibilityOn()
            self._viewer.light.SwitchOn()

    def ToggleVolumeVisibility(self):
        # toggle visibility of the volume render
        if not self._viewer.volume_render_initialised:
            self._viewer.installVolumeRenderActorPipeline()

        self.SetVolumeVisibility(not self._viewer.volume.GetVisibility())

        self._viewer.updatePipeline()

    def AutoWindowLevelOnVolumeRange(self, update_slice=True):
        '''Auto-adjusts window-level for the slice, based on the 5 and 95th percentiles of the whole image volume.'''
        cmin, cmax = self._viewer.getImageMapRange((5., 95.), method="scalar")
        window, level = self._viewer.getSliceWindowLevelFromRange(cmin, cmax)

        self._viewer.imageSlice.GetProperty().SetColorLevel(level)
        self._viewer.imageSlice.GetProperty().SetColorWindow(window)

        if update_slice:
            self.UpdateImageSlice()

    def OnKeyPress(self, interactor, _):
        if interactor.GetKeyCode() == "x":
            self.SetSliceOrientation(SLICE_ORIENTATION_YZ)
            self.UpdatePipeline(resetcamera=True)
        elif interactor.GetKeyCode() == "y":
            self.SetSliceOrientation(SLICE_ORIENTATION_XZ)
            self.UpdatePipeline(resetcamera=True)
        elif interactor.GetKeyCode() == "z":
            self.SetSliceOrientation(SLICE_ORIENTATION_XY)
            self.UpdatePipeline(resetcamera=True)
        elif interactor.GetKeyCode() == "a":
            self._viewer.autoWindowLevelOnSliceRange()
        elif interactor.GetKeyCode() == "h":
            self.DisplayHelp()
        elif interactor.GetKeyCode() == "r":
            filename = "current_render"
            self.SaveRender(filename)
        elif interactor.GetKeyCode() == "v":
            self.ToggleVolumeVisibility()
        elif interactor.GetKeyCode() == "s":
            self.ToggleSliceVisibility()
        elif interactor.GetKeyCode() == "i":
            self.ToggleSliceInterpolation()
        elif interactor.GetKeyCode() == "c" and self._viewer.volume_render_initialised:
            self.ToggleVolumeClipping()
        else:
            print("Unhandled event %s" % interactor.GetKeyCode())

    def CreateClippingPlane(self):
        viewer = self._viewer
        planew = vtk.vtkImplicitPlaneWidget2()

        rep = vtk.vtkImplicitPlaneRepresentation()
        world_extent = self.GetImageWorldExtent()
        extent = [0, world_extent[0], 0, world_extent[1], 0, world_extent[2]]
        rep.SetWidgetBounds(*extent)
        planew.SetRepresentation(rep)
        planew.SetInteractor(viewer.getInteractor())

        rep.SetNormalToCamera()
        rep.SetOutlineTranslation(False)  # this means user can't move bounding box

        plane = vtk.vtkPlane()
        # should be in the focal point
        cam = self.GetActiveCamera()
        foc = cam.GetFocalPoint()
        plane.SetOrigin(*foc)

        proj = cam.GetDirectionOfProjection()
        proj = [x + 0.3 for x in list(proj)]
        plane.SetNormal(*proj)
        rep.SetPlane(plane)
        rep.UpdatePlacement()

        viewer.volume.GetMapper().AddClippingPlane(plane)
        viewer.volume.Modified()
        viewer.plane = plane
        viewer.planew = planew
        planew.AddObserver('InteractionEvent', self.update_clipping_plane, 0.5)
        self._viewer.clipping_plane_initialised = True

        return planew

    def update_clipping_plane(self, interactor, event):
        # event translator should you want to filter events
        # event_translator = planew.GetEventTranslator()
        # pevent = event_translator.GetTranslation(event)
        planew = self._viewer.planew
        viewer = self._viewer
        rep = planew.GetRepresentation()
        plane = vtk.vtkPlane()
        rep.GetPlane(plane)

        viewer.volume.GetMapper().RemoveAllClippingPlanes()
        viewer.volume.GetMapper().AddClippingPlane(plane)
        viewer.volume.Modified()
        viewer.getRenderer().Render()

    def DisplayHelp(self):
        help_actor = self._viewer.helpActor
        slice_actor = self._viewer.imageSlice

        if help_actor.GetVisibility():
            help_actor.VisibilityOff()
            slice_actor.VisibilityOn()
            self.ShowActor(1)
            self.Render()
            return

        font_size = 24

        # Create the text mappers and the associated Actor2Ds.

        # The font and text properties (except justification) are the same for
        # each multi line mapper. Let's create a common text property object
        multiLineTextProp = vtk.vtkTextProperty()
        multiLineTextProp.SetFontSize(font_size)
        multiLineTextProp.SetFontFamilyToArial()
        multiLineTextProp.BoldOn()
        multiLineTextProp.ItalicOn()
        multiLineTextProp.ShadowOn()
        multiLineTextProp.SetLineSpacing(1.3)

        # The text is on multiple lines and center-justified (both horizontal and
        # vertical).
        textMapperC = vtk.vtkTextMapper()
        textMapperC.SetInput("Mouse Interactions:\n"
                             "\n"
                             "  - Slice: Mouse Scroll\n"
                             "  - Zoom: Right Mouse + Move Up/Down\n"
                             "  - Pan: Middle Mouse Button + Move or Shift + Left Mouse + Move\n"
                             "  - Adjust Camera: Left Mouse + Move\n"
                             "  - Rotate: Ctrl + Left Mouse + Move\n"
                             "\n"
                             "Keyboard Interactions:\n"
                             "\n"
                             "h: Display this help\n"
                             "x:  YZ Plane\n"
                             "y:  XZ Plane\n"
                             "z:  XY Plane\n"
                             "r:  Save render to current_render.png\n"
                             "s:  Toggle visibility of slice\n"
                             "v:  Toggle visibility of volume render\n"
                             "c:  Activates volume render clipping plane widget\n"
                             "a:  Whole image Auto Window/Level\n")
        tprop = textMapperC.GetTextProperty()
        tprop.ShallowCopy(multiLineTextProp)
        tprop.SetJustificationToLeft()
        tprop.SetVerticalJustificationToCentered()
        tprop.SetColor(0, 1, 0)

        help_actor.SetMapper(textMapperC)
        help_actor.VisibilityOn()
        slice_actor.VisibilityOff()
        self.HideActor(1)

        self.Render()

    def SaveRender(self, filename):
        self._viewer.saveRender(filename)

    # Coordinate conversion ----------------------------

    def world2imageCoordinate(self, world_coordinates):
        """
        Convert from the world or global coordinates to image coordinates
        :param world_coordinates: (x,y,z)
        :return: rounded to next integer (x,y,z) in image coorindates eg. slice index
        """

        dims = self.GetInputData().GetDimensions()
        self.log(dims)
        spac = self.GetInputData().GetSpacing()
        orig = self.GetInputData().GetOrigin()

        return [round((world_coordinates[i]) / spac[i] - orig[i]) for i in range(3)]

    def world2imageCoordinateFloat(self, world_coordinates):
        """
        Convert from the world or global coordinates to image coordinates
        :param world_coordinates: (x,y,z)
        :return: float (x,y,z) in image coorindates eg. slice index
        """

        dims = self.GetInputData().GetDimensions()
        self.log(dims)
        spac = self.GetInputData().GetSpacing()
        orig = self.GetInputData().GetOrigin()

        return [(world_coordinates[i]) / spac[i] - orig[i] for i in range(3)]

    def image2world(self, image_coordinates):

        spac = self.GetInputData().GetSpacing()
        orig = self.GetInputData().GetOrigin()

        return [(image_coordinates[i]) * spac[i] + orig[i] for i in range(3)]

    def GetImageWorldExtent(self):
        """
        Compute and return the maximum extent of the image in the rendered world
        """
        return self.image2world(self.GetInputData().GetExtent()[1::2])

    def GetInputData(self):
        return self._viewer.img3D


class CILViewer(CILViewerBase):
    '''Simple 3D Viewer based on VTK classes'''

    def __init__(self, dimx=600, dimy=600, renWin=None, iren=None, ren=None, debug=False):
        CILViewerBase.__init__(self, dimx=dimx, dimy=dimy, ren=ren, renWin=renWin, iren=iren, debug=debug)
        '''creates the rendering pipeline'''

        self.setInteractorStyle(CILInteractorStyle(self))

        self.sliceActorNo = 0
        # Render decimation
        self.decimate = vtk.vtkDecimatePro()

        # Setup the slice histogram:
        self.sliceIA = vtk.vtkImageAccumulate()
        self.histogramPlotActor.SetPosition2(0.98, 0.98)
        self.histogramPlotActor.SetPosition(0., 0.)
        self.addActor(self.histogramPlotActor)
        self.histogramPlotActor.VisibilityOff()  # Off by default

        # Help text
        self.ren.AddActor(self.helpActor)

        # These may be optionally set by the user:
        self.volume_colormap_limits = None

        self.volume_colormap_name = 'viridis'
        self.volume_render_initialised = False
        self.clipping_plane_initialised = False

    def createPolyDataActor(self, polydata):
        '''returns an actor for a given polydata'''

        self.decimate.SetInputData(polydata)
        self.decimate.SetTargetReduction(0.0)
        self.decimate.Update()

        mapper = vtk.vtkPolyDataMapper()
        if vtk.VTK_MAJOR_VERSION <= 5:
            mapper.SetInput(polydata)
        else:
            mapper.SetInputConnection(self.decimate.GetOutputPort())
        # actor
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        return actor

    def setPolyDataActor(self, actor):
        '''displays the given polydata'''

        self.hideActor(1, delete=True)
        self.ren.AddActor(actor)

        self.actors[len(self.actors) + 1] = [actor, True]
        self.iren.Initialize()
        self.renWin.Render()

    def displayPolyData(self, polydata):
        self.setPolyDataActor(self.createPolyDataActor(polydata))

    def hideActor(self, actorno, delete=False):
        '''Hides an actor identified by its number in the list of actors'''
        try:
            if self.actors[actorno][1]:
                self.ren.RemoveActor(self.actors[actorno][0])
                self.actors[actorno][1] = False

            if delete:
                self.actors = {}
                self.renWin.Render()

        except KeyError as ke:
            print("Warning Actor not present")

    def showActor(self, actorno, actor=None):
        '''Shows hidden actor identified by its number in the list of actors'''
        try:
            if not self.actors[actorno][1]:
                self.ren.AddActor(self.actors[actorno][0])
                self.actors[actorno][1] = True
                return actorno
        except KeyError as ke:
            # adds it to the actors if not there already
            if actor != None:
                self.ren.AddActor(actor)
                self.actors[len(self.actors) + 1] = [actor, True]
                return len(self.actors)

    def addActor(self, actor):
        '''Adds an actor to the render'''
        return self.showActor(0, actor)

    def setInput3DData(self, imageData):
        self.img3D = imageData

        # Have to overwrite old volume and clipping planes if they
        # were previously created:
        if self.volume_render_initialised:
            if self.clipping_plane_initialised:
                # Have to create new clipping plane so that camera
                # position is adjusted appropriately for new volume.
                # Note: just removing old plane is not sufficient.
                self.style.CreateClippingPlane()
                self.planew.SetEnabled(False)
                self.volume.GetMapper().RemoveAllClippingPlanes()
                self.clipping_plane_initialised = False

            # Have to remove old volume and install pipeline
            # with new volume:
            self.ren.RemoveVolume(self.volume)
            self.installVolumeRenderActorPipeline()

        # Reset slice visibility and orientation:
        self.imageSlice.VisibilityOn()
        self.style.SetSliceOrientation(SLICE_ORIENTATION_XY)

        # Reset camera to initial orientation
        # i.e. reset any rotation of the slice and volume
        self.resetCameraToDefault()

        # Install pipeline with new image:
        self.installPipeline()

        # needs an extra nudge to turn the slice visibility on:
        self.updatePipeline()
        # Note, this includes adjusting the camera once the new image is loaded,
        # so the camera settings have been changed.

        # Save default camera settings for this image:
        self.saveDefaultCamera()

    def setInputData(self, imageData):
        '''alias of setInput3DData'''
        return self.setInput3DData(imageData)

    def setInputAsNumpy(self, numpyarray):
        if (len(numpy.shape(numpyarray)) == 3):
            doubleImg = vtk.vtkImageData()
            shape = numpy.shape(numpyarray)
            doubleImg.SetDimensions(shape[0], shape[1], shape[2])
            doubleImg.SetOrigin(0, 0, 0)
            doubleImg.SetSpacing(1, 1, 1)
            doubleImg.SetExtent(0, shape[0] - 1, 0, shape[1] - 1, 0, shape[2] - 1)
            doubleImg.AllocateScalars(vtk.VTK_DOUBLE, 1)

            for i in range(shape[0]):
                for j in range(shape[1]):
                    for k in range(shape[2]):
                        doubleImg.SetScalarComponentFromDouble(i, j, k, 0, numpyarray[i][j][k])

            # rescale to appropriate VTK_UNSIGNED_SHORT
            stats = vtk.vtkImageAccumulate()
            stats.SetInputData(doubleImg)
            stats.Update()
            iMin = stats.GetMin()[0]
            iMax = stats.GetMax()[0]
            scale = vtk.VTK_UNSIGNED_SHORT_MAX / (iMax - iMin)

            shiftScaler = vtk.vtkImageShiftScale()
            shiftScaler.SetInputData(doubleImg)
            shiftScaler.SetScale(scale)
            shiftScaler.SetShift(iMin)
            shiftScaler.SetOutputScalarType(vtk.VTK_UNSIGNED_SHORT)
            shiftScaler.Update()
            self.img3D = shiftScaler.GetOutput()

    def installPipeline(self):
        # Reset the viewer when loading a new data source
        try:
            N = self.ren.GetActors().GetNumberOfItems()
            i = 0
            while i < N:
                actor = self.ren.GetActors().GetNextActor()
                self.ren.RemoveActor(actor)
                i += 1
        except TypeError as te:
            print(te)
            print(self.ren.GetActors())

        self.installSliceActorPipeline()
        # self.installVolumeRenderActorPipeline()

        self.ren.ResetCamera()
        self.ren.Render()

        self.adjustCamera()

        self.iren.Initialize()
        self.renWin.Render()

    def saveDefaultCamera(self):
        ''' Saves the default camera settings for a particular
        loaded 3D image.'''
        self.default_camera_data = CameraData(self.getCamera())

    def resetCameraToDefault(self):
        ''' resets to the default camera settings for the current
        loaded 3D image'''
        if hasattr(self, 'default_camera_data'):
            self.adjustCamera(resetcamera=True)
            CameraData.CopyDataToCamera(self.default_camera_data, self.getCamera())

    def installVolumeRenderActorPipeline(self):
        # volume render
        volumeMapper = vtk.vtkSmartVolumeMapper()
        #volumeMapper = vtk.vtkFixedPointVolumeRayCastMapper()
        self.volume_mapper = volumeMapper
        volumeProperty = vtk.vtkVolumeProperty()

        self.volume_property = volumeProperty
        self.volume_mapper.SetInputData(self.img3D)

        # The volume holds the mapper and the property and
        # can be used to position/orient the volume.
        volume = vtk.vtkVolume()
        volume.SetMapper(volumeMapper)
        volume.SetProperty(volumeProperty)
        self.volume = volume

        # set defaults for opacity and colour mapping:
        color_percentiles = (5., 95.)
        scalar_opacity_percentiles = (80., 99.)
        gradient_opacity_percentiles = (80., 99.)
        max_opacity = 0.1

        self.setVolumeColorPercentiles(*color_percentiles, update_pipeline=False)
        self.setScalarOpacityPercentiles(*scalar_opacity_percentiles, update_pipeline=False)
        self.setGradientOpacityPercentiles(*gradient_opacity_percentiles, update_pipeline=False)
        self.setMaximumOpacity(max_opacity)

        # define colors and opacity with default values
        colors, opacity = self.getColorOpacityForVolumeRender()

        self.volume_property.SetColor(colors)

        self._setDefaultScalarOpacityFunction()

        if self.getVolumeRenderOpacityMethod() == 'scalar':
            self.volume_property.SetScalarOpacity(opacity)
        else:
            # currently this is not relevant, but in the future one may want to do
            # something fancier
            # see also https://www.kitware.com/new-in-paraview-5-9-volume-rendering-with-a-separate-opacity-array/
            self.volume_property.SetGradientOpacity(opacity)

        self.volume_property.ShadeOn()
        self.volume_property.SetInterpolationTypeToLinear()

        self.ren.AddVolume(self.volume)
        self.volume_render_initialised = True
        self.volume.VisibilityOff()
        self.addHeadlight()

    def addHeadlight(self):
        if not hasattr(self, 'light'):
            lgt = vtk.vtkLight()
            lgt.SetLightTypeToHeadlight()
            lgt.SwitchOff()
            self.getRenderer().AddLight(lgt)
            self.light = lgt

    def getVolumeRenderOpacityMethod(self):
        if not hasattr(self, '_vol_render_opacity_method'):
            self._vol_render_opacity_method = "gradient"
        return self._vol_render_opacity_method

    def setVolumeRenderOpacityMethod(self, method='gradient'):
        '''
        Parameters
        ----------
        method: string: 'scalar' or 'gradient'
            method for setting opacity of the volume render            
        '''
        if method in ['scalar', 'gradient']:
            self._vol_render_opacity_method = method
            # self.updateVolumePipeline()
            #This is a hack #TODO: fix update pipeline in case where we change opacity method
            if self.volume_render_initialised:
                planes = self.volume.GetMapper().GetClippingPlanes()
                self.ren.RemoveVolume(self.volume)
                self.volume_render_initialised = False
                self.style.ToggleVolumeVisibility()
                # add existing clipping plane to new volume
                if planes is not None:
                    plane = planes.GetItem(0)
                    self.volume.GetMapper().AddClippingPlane(plane)
                    self.volume.Modified()

    def setMaximumOpacity(self, max, update_pipeline=True):
        '''
        Parameters
        ----------
        max_opacity: float in [0,1]
            representing the maximum rendered opacity
        update_pipeline: bool
            whether to immediately update the pipeline with this new
            setting
        '''
        self.maximum_opacity = max
        if update_pipeline:
            self.updateVolumePipeline()

    def getMaximumOpacity(self):
        '''
        Returns
        ----------
        max_opacity: float in [0,1]
            representing the maximum rendered opacity
        '''
        return self.maximum_opacity

    def setGradientOpacityPercentiles(self, min, max, update_pipeline=True):
        '''
        Parameters
        -----------
        min, max: float, default: (80., 99.)
            the percentiles on the image gradient values that the 
            opacity will be mapped to if setVolumeRenderOpacityMethod
            has been set to 'gradient'.
        update_pipeline: bool
            whether to immediately update the pipeline with this new
            setting
        '''
        go_min, go_max = self.getImageMapRange((min, max), 'gradient')
        self.setGradientOpacityRange(go_min, go_max, update_pipeline)

    def getGradientOpacityPercentiles(self):
        '''
        Returns
        -----------
        min, max: float, default: (80., 99.)
            the percentiles on the image gradient values that the 
            opacity will be mapped to if setVolumeRenderOpacityMethod
            has been set to 'gradient'.
        '''
        go_min, go_max = self.getGradientOpacityRange()
        value_min, value_max = self.getImageMapWholeRange('gradient')
        min_percentage = (go_min - value_min) / (value_max - value_min) * 100
        max_percentage = (go_max - value_min) / (value_max - value_min) * 100
        return min_percentage, max_percentage

    def setScalarOpacityPercentiles(self, min, max, update_pipeline=True):
        '''
        min, max: float, default: (80., 99.)
            the percentiles on the image values that the 
            opacity will be mapped to if setVolumeRenderOpacityMethod
            has been set to 'scalar'.
        '''
        so_min, so_max = self.getImageMapRange((min, max), 'scalar')
        self.setScalarOpacityRange(so_min, so_max, update_pipeline)

    def getScalarOpacityPercentiles(self):
        '''
        Returns
        -----------
        min, max: float, default: (80., 99.)
            the percentiles on the image values that the 
            opacity will be mapped to if setVolumeRenderOpacityMethod
            has been set to 'scalar'.
        '''
        so_min, so_max = self.getScalarOpacityRange()
        value_min, value_max = self.getImageMapWholeRange('scalar')
        min_percentage = (so_min - value_min) / (value_max - value_min) * 100
        max_percentage = (so_max - value_min) / (value_max - value_min) * 100
        return min_percentage, max_percentage

    def setVolumeColorPercentiles(self, min, max, update_pipeline=True):
        '''
        Parameters
        -----------
        min, max: int, default: (85., 95.)
            the percentiles on the image values upon which the colours will be mapped to
        '''
        cmin, cmax = self.getImageMapRange((min, max), 'scalar')
        self.setVolumeColorRange(cmin, cmax, update_pipeline)

    def getVolumeColorPercentiles(self):
        '''
        Returns
        -----------
        min, max: int, default: (85., 95.)
            the percentiles on the image values upon which the colours will be mapped to
        '''
        cmin, cmax = self.getVolumeColorRange()
        value_min, value_max = self.getImageMapWholeRange('scalar')
        min_percentage = (cmin - value_min) / (value_max - value_min) * 100
        max_percentage = (cmax - value_min) / (value_max - value_min) * 100
        return min_percentage, max_percentage

    def setGradientOpacityRange(self, min, max, update_pipeline=True):
        '''
        Parameters
        -----------
        min, max: float, default: (80., 99.)
            the upper and lower image gradient values that the 
            opacity will be mapped to if setVolumeRenderOpacityMethod
            has been set to 'gradient'.
        update_pipeline: bool
            whether to immediately update the pipeline with this new
            setting
        '''
        self.gradient_opacity_limits = (min, max)
        if update_pipeline:
            self.updateVolumePipeline()

    def getGradientOpacityRange(self):
        '''
        Returns
        -----------
        (min, max): tuple, default: (80., 99.)
            the upper and lower image gradient values that the 
            opacity will be mapped to if setVolumeRenderOpacityMethod
            has been set to 'gradient'.
        '''
        return self.gradient_opacity_limits

    def setScalarOpacityRange(self, min, max, update_pipeline=True):
        '''
        Parameters
        -----------
        min, max: float, default: (80., 99.)
            the upper and lower image values that the 
            opacity will be mapped to if setVolumeRenderOpacityMethod
            has been set to 'scalar'.
        update_pipeline: bool
            whether to immediately update the pipeline with this new
            setting
        '''
        self.scalar_opacity_limits = (min, max)
        if update_pipeline:
            self.updateVolumePipeline()

    def getScalarOpacityRange(self):
        '''
        Returns
        -----------
        (min, max): tuple, default: (80., 99.)
            the upper and lower image values that the 
            opacity will be mapped to if setVolumeRenderOpacityMethod
            has been set to 'scalar'.
        '''
        return self.scalar_opacity_limits

    def setVolumeColorRange(self, min, max, update_pipeline=True):
        '''
        Parameters
        -----------
        min, max: float, default: the raw value of the 80. percentile for min, and the raw value of the 99. percentile for max.
            the upper and lower image values that the 
            color will be mapped to.
        update_pipeline: bool
            whether to immediately update the pipeline with this new
            setting
        '''
        self.volume_colormap_limits = (min, max)
        if update_pipeline:
            self.updateVolumePipeline()

    def getVolumeColorRange(self):
        '''
        Returns
        -----------
        (min, max): tuple, default: (80., 99.)
            the upper and lower image values that the 
            color will be mapped to.
        '''
        return self.volume_colormap_limits

    def setVolumeColorMapName(self, cmap='viridis'):
        '''set the volume color map name
        Parameters
        ----------
        cmap: string, default: 'viridis'
            with one of ['viridis', 'plasma', 'magma', 'inferno'],
            or matplotlib's cmaps if available
        '''
        self.volume_colormap_name = cmap
        self.updateVolumePipeline()

    def getVolumeColorMapName(self):
        '''get the volume color map name'''
        return self.volume_colormap_name

    def _setDefaultScalarOpacityFunction(self):
        # used inside viewer, not for user
        self.default_scalar_opacity = self.volume_property.GetScalarOpacity()

    def _getDefaultScalarOpacityFunction(self):
        # used inside viewer, not for user
        return self.default_scalar_opacity

    def getColorOpacityForVolumeRender(self, color_num=255):
        '''
        Defines the color and opacity tables
        
        Parameters
        ----------
        color_num: int, default: 255 
            number of colors in the map
        '''

        colors = colormaps.CILColorMaps.get_color_transfer_function(self.getVolumeColorMapName(),
                                                                    self.volume_colormap_limits)

        method = self.getVolumeRenderOpacityMethod()

        if method == 'scalar':
            omin, omax = self.scalar_opacity_limits
        else:
            omin, omax = self.gradient_opacity_limits

        # mapping values in the image or gradient to the opacity:
        x = self.getMappingArray(color_num, method)
        opacity = colormaps.CILColorMaps.get_opacity_transfer_function(x, colormaps.relu, omin, omax,
                                                                       self.maximum_opacity)

        return colors, opacity

    def getMappingArray(self, color_num, method):
        '''
        generates array of color_num values between min and max values in 
        image or image gradient (depending on method).
        '''
        ia = self.getImageHistogramStatistics(method)
        x = numpy.linspace(ia.GetMinimum(), ia.GetMaximum(), num=color_num)
        return x

    def installSliceActorPipeline(self):
        self.voi.SetInputData(self.img3D)

        extent = [i for i in self.img3D.GetExtent()]
        for i in range(len(self.slicenos)):
            self.slicenos[i] = round((extent[i * 2 + 1] + extent[i * 2]) / 2)
        extent[self.sliceOrientation * 2] = self.getActiveSlice()
        extent[self.sliceOrientation * 2 + 1] = self.getActiveSlice()

        self.voi.SetVOI(extent[0], extent[1], extent[2], extent[3], extent[4], extent[5])

        self.voi.Update()

        self.ia.SetInputData(self.voi.GetOutput())
        self.ia.Update()

        self.style.AutoWindowLevelOnVolumeRange(update_slice=False)
        self.InitialLevel = self.getSliceColorLevel()
        self.InitialWindow = self.getSliceColorWindow()

        self.imageSliceMapper.SetInputConnection(self.voi.GetOutputPort())
        self.imageSlice.Update()

        self.imageSlice.GetProperty().SetColorLevel(self.InitialLevel)
        self.imageSlice.GetProperty().SetColorWindow(self.InitialWindow)
        self.imageSlice.GetProperty().SetInterpolationTypeToNearest()
        self.imageSlice.GetProperty().SetOpacity(0.99)

        self.imageSlice.Update()

        self.ren.AddActor(self.imageSlice)

    def updatePipeline(self, resetcamera=False):
        self.hideActor(self.sliceActorNo)

        extent = [i for i in self.img3D.GetExtent()]
        extent[self.sliceOrientation * 2] = self.getActiveSlice()
        extent[self.sliceOrientation * 2 + 1] = self.getActiveSlice()
        self.voi.SetVOI(extent[0], extent[1], extent[2], extent[3], extent[4], extent[5])

        self.voi.Update()
        self.ia.Update()

        self.imageSliceMapper.SetOrientation(self.sliceOrientation)
        self.imageSlice.Update()

        no = self.showActor(self.sliceActorNo, self.imageSlice)
        self.sliceActorNo = no

        self.updateVolumePipeline()
        self.updateSliceHistogram()

        self.adjustCamera(resetcamera)

        self.renWin.Render()

    def updateVolumePipeline(self):
        if self.volume_render_initialised and self.volume.GetVisibility():
            # define colors and opacity with default values
            colors, opacity = self.getColorOpacityForVolumeRender()

            self.volume_property.SetColor(colors)

            # Update whether we use our calculated opacity as the scalar or gradient opacity
            if self.getVolumeRenderOpacityMethod() == 'gradient':
                # Also return the scalar opacity to its default value:
                # If we don't do this then the gradient opacity changes depending on what the
                # user set for the scalar opacity - not sure we want this:
                self.volume_property.SetScalarOpacity(self._getDefaultScalarOpacityFunction())
                self.volume_property.DisableGradientOpacityOff()
                self.volume_property.SetGradientOpacity(opacity)

            elif self.getVolumeRenderOpacityMethod() == 'scalar':
                self.volume_property.DisableGradientOpacityOn()
                self.volume_property.SetScalarOpacity(opacity)

            self.renWin.Render()

    def adjustCamera(self, resetcamera=False):
        self.ren.ResetCameraClippingRange()

        if resetcamera:
            self.ren.ResetCamera()

    def updateSliceHistogram(self):
        irange = self.voi.GetOutput().GetScalarRange()
        self.sliceIA.SetInputData(self.voi.GetOutput())
        self.sliceIA.IgnoreZeroOn()

        #use 255 bins
        delta = irange[1] - irange[0]
        nbins = 255
        self.sliceIA.SetComponentSpacing(delta / nbins, 0, 0)
        self.sliceIA.SetComponentExtent(0, nbins - 1, 0, 0, 0, 0)
        self.sliceIA.Update()

        self.histogramPlotActor.AddDataSetInputConnection(self.sliceIA.GetOutputPort())
        self.histogramPlotActor.SetXRange(irange[0], irange[1])
        self.histogramPlotActor.SetYRange(self.sliceIA.GetOutput().GetScalarRange())

    def remove_clipping_plane(self):
        if self.volume_render_initialised and self.clipping_plane_initialised:
            self.volume.GetMapper().RemoveAllClippingPlanes()

            # Now remove planew from the cil_viewer
            del self.planew
            del self.plane
            self.clipping_plane_initialised = False

            self.getRenderer().Render()
            self.updatePipeline()
