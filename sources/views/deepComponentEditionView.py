"""
Copyright 2019 Black Foundry.

This file is part of Robo-CJK.

Robo-CJK is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Robo-CJK is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Robo-CJK.  If not, see <https://www.gnu.org/licenses/>.
"""
from imp import reload
from vanilla import *
from vanilla.dialogs import askYesNo
from defconAppKit.windows.baseWindow import BaseWindowController

from AppKit import *

from mojo.UI import OpenGlyphWindow, AllGlyphWindows, CurrentGlyphWindow, PostBannerNotification
from mojo.roboFont import *
from mojo.canvas import *
from mojo.events import addObserver, removeObserver
from lib.cells.colorCell import RFColorCell
# from fontTools.pens import cocoaPen

import os
import json
# import Quartz

from utils import files
from utils import git
from views import tableDelegate
from views import mainCanvas
from utils import interpolations
from resources import deepCompoMasters_AGB1_FULL

reload(files)
reload(git)
reload(mainCanvas)
reload(deepCompoMasters_AGB1_FULL)
reload(interpolations)

from utils import decorators
reload(decorators)
refreshMainCanvas = decorators.refreshMainCanvas

class CanvasGroup(Group):

    def __init__(self, posSize, RCJKI, controller):
        super(CanvasGroup, self).__init__(posSize)
        self.RCJKI = RCJKI
        self.c = controller

        
        self.mainCanvas = Canvas((0,0,-0,-0), 
            delegate=self.c.canvasDrawer,
            canvasSize=(5000, 5000),
            hasHorizontalScroller=False, 
            hasVerticalScroller=False)

        self.extremsList = PopUpButton((0, 0, 200, 20), 
            [], 
            sizeStyle = 'small',
            callback = self.extremsListCallback)

        self.dcOffsetXTextBox = TextBox((35, -20, 15, 20), "x:", sizeStyle = 'small')
        self.dcOffsetYTextBox = TextBox((85, -20, 15, 20), "y:", sizeStyle = 'small')


        self.dcOffsetXEditText = EditText((50, -20, 50, 20), 
            self.c.deepComponentTranslateX,
            sizeStyle = "small",
            callback = self.dcOffsetXEditTextCallback,
            continuous = False)

        self.dcOffsetXEditText.getNSTextField().setBordered_(False)
        self.dcOffsetXEditText.getNSTextField().setDrawsBackground_(False)

        
        self.dcOffsetYEditText = EditText((100, -20, 50, 20), 
            self.c.deepComponentTranslateY,
            sizeStyle = "small",
            callback = self.dcOffsetYEditTextCallback,
            continuous = False)

        self.dcOffsetYEditText.getNSTextField().setBordered_(False)
        self.dcOffsetYEditText.getNSTextField().setDrawsBackground_(False)

        self.colorPicker = ColorWell((0,-20,20,20),
                callback=self.colorPickerCallback, 
                color=NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, 0))


    def extremsListCallback(self, sender):
        char = sender.getItem()
        self.c.controller.setExtremDCGlyph(char)

    @refreshMainCanvas
    def dcOffsetXEditTextCallback(self, sender):
        try:
            self.c.deepComponentTranslateX = int(sender.get())
        except:
            sender.set(self.c.deepComponentTranslateX)

    @refreshMainCanvas
    def dcOffsetYEditTextCallback(self, sender):
        try:
            self.c.deepComponentTranslateY = int(sender.get())
        except:
            sender.set(self.c.deepComponentTranslateY)

    def colorPickerCallback(self, sender):
        if self.RCJKI.currentGlyph is None: return
        color = sender.get()
        r = color.redComponent()
        g = color.greenComponent()
        b = color.blueComponent()
        a = color.alphaComponent()
    
        self.RCJKI.currentGlyph.markColor = (r, g, b, a)
        self.c.controller.updateGlyphSetList()

class SliderGroup(Group):

    def __init__(self, posSize, RCJKI, controller, axis):
        super(SliderGroup, self).__init__(posSize)
        self.axis = axis
        self.RCJKI = RCJKI
        self.c = controller
        self.lock = False

        slider = SliderListCell(minValue = 0, maxValue = 1000)
        self.slidersValuesList = []
        self.slidersList = List((0, 0, -0, -20),
            self.slidersValuesList,
            columnDescriptions = [
                                    {"title": "Layer", "editable": False, "width": 0},
                                    
                                    {"title": "Values", "cell": slider, "width": 410},
                                    {"title": "Image", "editable": False, "cell": ImageListCell(), "width": 160}, 
                                    # {"title": "Axis", "cell": PopUpButtonListCell(["Proportion Axis", "Control Axis", "Localisation Axis"]), "binding": "selectedValue", "width": 100}
                                    # {"title": "Lock", "cell": checkbox, "width": 20},
                                   # {"title": "YValue", "cell": slider, "width": 250},
                                    
                                    ],
            editCallback = self.slidersListEditCallback,
            doubleClickCallback = self.sliderListDoubleClickCallback,
            drawFocusRing = False,
            allowsMultipleSelection = False,
            rowHeight = 145.0,
            showColumnTitles = False
            )

        # self.addNLIButton = Button((-300, -20, 100, 20),
        #     'NLI',
        #     # callback = self.addNLIButtonCallback
        #     )
        self.addLayerButton = Button((-200, -20, 100, 20), 
            "+",
            callback = self.addLayerButtonCallback
            )
        self.removeLayerButton = Button((-100, -20, 100, 20), 
            "-",
            callback = self.removeLayerButtonCallback
            )

    def slidersListEditCallback(self, sender):
        sel = sender.getSelection()
        if not sel: return
        if self.lock: return
        self.lock = True
        layersInfo = sender.get()
        layerInfo = layersInfo[sel[0]]

        selectedLayerName = layerInfo["Layer"]
        image = layerInfo["Image"]
        # lock = layerInfo["Lock"]
        value = layerInfo["Values"]

        axis = layerInfo.get("Axis", " ")

        # print(axis)
        layer = self.RCJKI.currentFont.getLayer(selectedLayerName)[self.RCJKI.currentGlyph.name]
        print(layer.lib["Axis"])
        # print(axis)
        # layer.lib['Axis'] = self.axis
        # layer.update()
        # print('\t', layer.lib.keys())
        # YValue = layerInfo["YValue"]

        # changed = False
        # # if lock:
        #     if Value != self.slidersValuesList[sel[0]]["Value"]:
        #         YValue = XValue
        #         changed = True

        #     elif YValue != self.slidersValuesList[sel[0]]["YValue"]:
        #         XValue = YValue
        #         changed = True

        # if lock != self.slidersValuesList[sel[0]]["Lock"]:
            # changed = True 


        self.RCJKI.layersInfos[selectedLayerName] = value
        self.slidersValuesList[sel[0]]["Values"] = value
        # self.slidersValuesList[sel[0]]["YValue"] = YValue 
        # self.slidersValuesList[sel[0]]["Lock"] = lock

        #if changed:
        # d = {'Layer': selectedLayerName,
        #     'Image': image,
        #     'Values': value
        #     # 'YValue': YValue,
        #     # 'Lock': lock
        #     }
        # layers = [e if i != sel[0] else d for i, e in enumerate(layersInfo)]
        # sender.set(layers)
        # sender.setSelection(sel)

        # layerInfo["NLI"] = "NLI"
        self.RCJKI.currentGlyph = self.RCJKI.currentFont[self.c.selectedDeepComponentGlyphName]
        self.RCJKI.deepComponentGlyph = self.RCJKI.getDeepComponentGlyph()
        self.c.canvasGroup.mainCanvas.update()
        self.lock = False

    def sliderListDoubleClickCallback(self, sender):
        sel = sender.getSelection()
        if not sel: return
        layerName = sender.get()[sel[0]]['Layer']
        self.RCJKI.currentGlyph = self.RCJKI.currentFont.getLayer(layerName)[self.RCJKI.currentGlyph.name]
        self.RCJKI.openGlyphWindow(self.RCJKI.currentGlyph)


    # @refreshMainCanvas
    def addLayerButtonCallback(self, sender):
        g = self.RCJKI.currentGlyph
        f = self.RCJKI.currentFont
        if len(f.getLayer("foreground")[g.name]):
            newGlyphLayer = list(filter(lambda l: not len(g.getLayer(l.name)), f.layers))[0]
            f.getLayer(newGlyphLayer.name).insertGlyph(g.getLayer("foreground"))
            self.RCJKI.currentGlyph = f.getLayer(newGlyphLayer.name)[g.name]
            self.slidersValuesList.append({'Layer': newGlyphLayer.name,
                                        'Image': None,
                                        'Values': 0,
                                        # 'Axis': ' ',
                                        # 'YValue': 0
                                        })
            self.RCJKI.currentGlyph.lib["Axis"] = self.axis
            print(self.RCJKI.currentGlyph.lib["Axis"])
            self.RCJKI.currentGlyph.update()
        else:

            self.RCJKI.currentGlyph = f.getLayer("foreground")[g.name]
            if self.selectedGlyphName in self.RCJKI.DCFonts2Fonts[self.RCJKI.currentFont]:
                self.RCJKI.currentGlyph.appendGlyph(self.RCJKI.DCFonts2Fonts[self.RCJKI.currentFont][self.selectedGlyphName])

        self.RCJKI.openGlyphWindow(self.RCJKI.currentGlyph)
        self.c.setSliderList()
        self.c.updateImageSliderList()
        self.c.canvasGroup.mainCanvas.update()
        # self.RCJKI.updateViews()
        # self.setSliderList()

    # @refreshMainCanvas
    def removeLayerButtonCallback(self, sender):
        sel = self.slidersList.getSelection()
        if not sel:
            PostBannerNotification("Error", "No selected layer")
            return

        layerName = self.slidersValuesList[sel[0]]['Layer']
        self.RCJKI.currentFont.getLayer(layerName)[self.RCJKI.currentGlyph.name].clear()

        self.slidersValuesList.pop(sel[0])
        del self.RCJKI.layersInfos[layerName]

        self.RCJKI.deepComponentGlyph = self.RCJKI.getDeepComponentGlyph()

        self.slidersList.set(self.slidersValuesList)
        self.c.canvasGroup.mainCanvas.update()


class DeepComponentEditionWindow(BaseWindowController):

    def __init__(self, controller):
        super(DeepComponentEditionWindow, self).__init__()
        self.controller = controller
        self.RCJKI = self.controller.RCJKI
        self.RCJKI.allFonts = []
        self.selectedGlyph = None
        self.RCJKI.layersInfos = {}

        self.lock = False

        self.w = Window((200, 0, 800, 800), 
                'Deep Component Edition', 
                minSize = (300,300), 
                maxSize = (2500,2000))

        self.w.fontsList = List((0,0,200,85),
                [],
                selectionCallback = self.fontsListSelectionCallback,
                drawFocusRing = False)

        self.w.glyphSetList = List((0,85,200,230),
                [],
                columnDescriptions = [
                                {"title": "#", "width" : 20, 'editable':False},
                                {"title": "Char", "width" : 30, 'editable':False},
                                {"title": "Name", "width" : 80, 'editable':False},
                                {"title": "MarkColor", "width" : 30, 'editable':False}
                                ],
                selectionCallback = self.glyphSetListSelectionCallback,
                doubleClickCallback = self.glyphSetListdoubleClickCallback,
                # editCallback = self.glyphSetListEditCallback,
                showColumnTitles = False,
                drawFocusRing = False)

        self.delegate = tableDelegate.TableDelegate.alloc().initWithMaster(self, "_deepComponentsEdition_glyphs", self.w.glyphSetList)
        tableView = self.w.glyphSetList.getNSTableView()
        tableView.setDelegate_(self.delegate)

        self.w.deepComponentsSetList = List((0, 315, 200, 200),
                [],
                columnDescriptions = [
                                {"title": "#", "width" : 20, 'editable':False},
                                {"title": "Char", "width" : 30, 'editable':False},
                                {"title": "Name", "width" : 80, 'editable':False},
                                {"title": "MarkColor", "width" : 30, 'editable':False}
                                ],
                selectionCallback = self.deepComponentsSetListSelectionCallback,
                doubleClickCallback = self.deepComponentsSetListDoubleClickCallback,
                # editCallback = self.glyphSetListEditCallback,
                showColumnTitles = False,
                drawFocusRing = False
            )

        self.w.saveLocalFontButton = Button((0,-60,200,20), 
            'Save', 
            callback=self.saveLocalFontButtonCallback)

        self.w.pushBackButton = Button((0,-40,200,20), 
            'Push', 
            callback=self.pushBackButtonCallback)

        self.w.pullMasterGlyphsButton = Button((0,-20,200,20), 
            'Pull', 
            callback=self.pullMasterGlyphsButtonCallback)


        self.deepComponentTranslateX = 0
        self.deepComponentTranslateY = 0

        self.canvasDrawer = mainCanvas.MainCanvas(self.RCJKI, self)
        
        self.canvasGroup = CanvasGroup((0, 0,-0,-0), self.RCJKI, self)

        # self.canvasDrawer = mainCanvas.MainCanvas(self.RCJKI, self)
        # self.canvasGroup.mainCanvas = Canvas((0,0,-0,-0), 
        #     delegate=self.canvasDrawer,
        #     canvasSize=(5000, 5000),
        #     hasHorizontalScroller=False, 
        #     hasVerticalScroller=False)

        # self.canvasGroup.extremsList = PopUpButton((0, 0, 200, 20), 
        #     [], 
        #     sizeStyle = 'small',
        #     callback = self.extremsListCallback)

        # self.canvasGroup.dcOffsetXTextBox = TextBox((35, -20, 15, 20), "x:", sizeStyle = 'small')
        # self.canvasGroup.dcOffsetYTextBox = TextBox((85, -20, 15, 20), "y:", sizeStyle = 'small')


        # self.canvasGroup.dcOffsetXEditText = EditText((50, -20, 50, 20), 
        #     self.deepComponentTranslateX,
        #     sizeStyle = "small",
        #     callback = self.dcOffsetXEditTextCallback,
        #     continuous = False)

        # self.canvasGroup.dcOffsetXEditText.getNSTextField().setBordered_(False)
        # self.canvasGroup.dcOffsetXEditText.getNSTextField().setDrawsBackground_(False)

        
        # self.canvasGroup.dcOffsetYEditText = EditText((100, -20, 50, 20), 
        #     self.deepComponentTranslateY,
        #     sizeStyle = "small",
        #     callback = self.dcOffsetYEditTextCallback,
        #     continuous = False)

        # self.canvasGroup.dcOffsetYEditText.getNSTextField().setBordered_(False)
        # self.canvasGroup.dcOffsetYEditText.getNSTextField().setDrawsBackground_(False)

        # slider = SliderListCell(minValue = 0, maxValue = 1000)
        # checkbox = CheckBoxListCell()


        self.slidersGroup = Group((0, 0, -0, -0))
        self.slidersSegmentedButtonsItems = [
                            "Proportion Axis",
                            "Control Axis",
                            "Localisation Axis",
                            ]
        self.slidersGroup.segmentedButton = SegmentedButton((0, 0, -0, 20),
            [dict(title=e, width=600/len(self.slidersSegmentedButtonsItems)) for e in self.slidersSegmentedButtonsItems],
            callback = self.sliderGroupSegmentedButtonCallback
            )
        self.slidersGroup.segmentedButton.set(0)

        for index, item in enumerate(self.slidersSegmentedButtonsItems):
            name = item.split(" ")[0]
            sliderGroup = SliderGroup((0, 20, -0, -0), self.RCJKI, self, item)
            setattr(self.slidersGroup, name, sliderGroup)
            getattr(self.slidersGroup, name).show(index == 0)
            if not index:
                self.enableSliderGroup = sliderGroup

        # self.slidersValuesList = []
        # self.slidersGroup.proportion.slidersList = List((0, 0, -0, -20),
        #     self.slidersValuesList,
        #     columnDescriptions = [
        #                             {"title": "Layer", "editable": False, "width": 0},
                                    
        #                             {"title": "Values", "cell": slider, "width": 410},
        #                             {"title": "Image", "editable": False, "cell": ImageListCell(), "width": 60}, 
        #                             {"title": "Axis", "cell": PopUpButtonListCell(["Proportion Axis", "Control Axis", "Localisation Axis"]), "binding": "selectedValue", "width": 100}
        #                             # {"title": "Lock", "cell": checkbox, "width": 20},
        #                            # {"title": "YValue", "cell": slider, "width": 250},
                                    
        #                             ],
        #     editCallback = self.slidersListEditCallback,
        #     doubleClickCallback = self.sliderListDoubleClickCallback,
        #     drawFocusRing = False,
        #     allowsMultipleSelection = False,
        #     rowHeight = 50.0,
        #     showColumnTitles = False
        #     )

        # self.slidersGroup.proportion.addNLIButton = Button((-300, -20, 100, 20),
        #     'NLI',
        #     callback = self.addNLIButtonCallback)
        # self.slidersGroup.proportion.addLayerButton = Button((-200, -20, 100, 20), 
        #     "+",
        #     callback = self.addLayerButtonCallback)
        # self.slidersGroup.proportion.removeLayerButton = Button((-100, -20, 100, 20), 
        #     "-",
        #     callback = self.removeLayerButtonCallback)

        # self.canvasGroup.colorPicker = ColorWell((200,-260,20,20),
        #         callback=self.colorPickerCallback, 
        #         color=NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, 0))


        paneDescriptors = [
            dict(view=self.canvasGroup, identifier="pane1"),
            dict(view=self.slidersGroup, identifier="pane2", size=240),
        ]
        self.w.splitView = SplitView((200, 0, -0, -0), 
                            paneDescriptors,
                            isVertical = False,
                            dividerStyle = "thin",
                            )
        

        self.dummyCell = NSCell.alloc().init()
        self.dummyCell.setImage_(None)

        self.observer()

        self.w.bind('close', self.windowCloses)
        self.w.bind('became main', self.windowBecameMain)
        self.w.open()

    def observer(self, remove=False):
        if not remove:
            addObserver(self, "glyphAdditionContextualMenuItems", "glyphAdditionContextualMenuItems")
            return
        removeObserver(self, "glyphAdditionContextualMenuItems")

    def glyphAdditionContextualMenuItems(self, info):
        info['additionContextualMenuItems'].append(("Import layer from next master", self.importLayerFromNextMaster))

    def importLayerFromNextMaster(self, sender):
        font = None
        for f in self.RCJKI.DCFonts2Fonts.keys():
            if f == self.RCJKI.currentFont: continue
            font = f 
        glyph = self.RCJKI.currentGlyph
        name = glyph.name
        glyph.prepareUndo()
        glyph.clear()
        glyph.appendGlyph(font[name].getLayer(glyph.layer.name))
        glyph.performUndo()
        glyph.update()

    def UpdateDCOffset(self):
        self.canvasGroup.dcOffsetXEditText.set(self.deepComponentTranslateX)
        self.canvasGroup.dcOffsetYEditText.set(self.deepComponentTranslateY)

    # @refreshMainCanvas
    # def dcOffsetXEditTextCallback(self, sender):
    #     try:
    #         self.deepComponentTranslateX = int(sender.get())
    #     except:
    #         sender.set(self.deepComponentTranslateX)

    # @refreshMainCanvas
    # def dcOffsetYEditTextCallback(self, sender):
    #     try:
    #         self.deepComponentTranslateY = int(sender.get())
    #     except:
    #         sender.set(self.deepComponentTranslateY)

    # def addNLIButtonCallback(self, sender):
    #     self.RCJKI.deepComponentEditionController.makeNLIPaths(reset=True)

    # def addLayerButtonCallback(self, sender):
    #     g = self.RCJKI.currentGlyph
    #     f = self.RCJKI.currentFont
    #     if len(f.getLayer("foreground")[g.name]):
    #         newGlyphLayer = list(filter(lambda l: not len(g.getLayer(l.name)), f.layers))[0]
    #         f.getLayer(newGlyphLayer.name).insertGlyph(g.getLayer("foreground"))
    #         self.RCJKI.currentGlyph = f.getLayer(newGlyphLayer.name)[g.name]
    #         self.slidersValuesList.append({'Layer': newGlyphLayer.name,
    #                                     'Image': None,
    #                                     'Values': 0,
    #                                     # 'Axis': ' ',
    #                                     # 'YValue': 0
    #                                     })
    #     else:

    #         self.RCJKI.currentGlyph = f.getLayer("foreground")[g.name]
    #         if self.selectedGlyphName in self.RCJKI.DCFonts2Fonts[self.RCJKI.currentFont]:
    #             self.RCJKI.currentGlyph.appendGlyph(self.RCJKI.DCFonts2Fonts[self.RCJKI.currentFont][self.selectedGlyphName])

    #     self.RCJKI.openGlyphWindow(self.RCJKI.currentGlyph)
    #     self.updateImageSliderList()
    #     self.RCJKI.updateViews()
    #     # self.setSliderList()

    # @refreshMainCanvas
    # def removeLayerButtonCallback(self, sender):
    #     sel = self.slidersGroup.proportion.slidersList.getSelection()
    #     if not sel:
    #         PostBannerNotification("Error", "No selected layer")
    #         return

    #     layerName = self.slidersValuesList[sel[0]]['Layer']
    #     self.RCJKI.currentFont.getLayer(layerName)[self.RCJKI.currentGlyph.name].clear()

    #     self.slidersValuesList.pop(sel[0])
    #     del self.RCJKI.layersInfos[layerName]

    #     self.RCJKI.deepComponentGlyph = self.RCJKI.getDeepComponentGlyph()

    #     self.slidersGroup.proportion.slidersList.set(self.slidersValuesList)

    @refreshMainCanvas
    def saveLocalFontButtonCallback(self, sender):
        self.RCJKI.deepComponentEditionController.saveSubsetFonts()
     
    @refreshMainCanvas   
    def pullMasterGlyphsButtonCallback(self, sender):
        self.controller.pullDCMasters()

    @refreshMainCanvas
    def pushBackButtonCallback(self, sender):
        self.controller.pushDCMasters()

    def windowBecameMain(self, sender):
        self.updateImageSliderList()

    def sliderGroupSegmentedButtonCallback(self, sender):
        i = sender.get()
        for index, item in enumerate(self.slidersSegmentedButtonsItems):
            name = item.split(" ")[0]
            enable = index == i
            group = getattr(self.slidersGroup, name)
            group.show(enable)
            if enable:
                self.enableSliderGroup = group
                self.setSliderList()

    def updateImageSliderList(self):
        return
        slidersValuesList = []
        for item in self.enableSliderGroup.slidersValuesList:

            layerName = item["Layer"]
            g = self.RCJKI.currentFont[self.RCJKI.currentGlyph.name].getLayer(layerName)
            emDimensions = self.RCJKI.project.settings['designFrame']['em_Dimension']
            pdfData = self.RCJKI.getLayerPDFImage(g, emDimensions)

            d = {'Layer': layerName,
                'Image': NSImage.alloc().initWithData_(pdfData),
                'Values': item["Values"],
                # 'Axis': item['Axis']
                # 'Lock': item["Lock"]
                }

            slidersValuesList.append(d)
        self.enableSliderGroup.slidersValuesList = slidersValuesList
        self.w.enableSliderGroup.slidersList.set(slidersValuesList)

    def setSliderList(self):
        # self.RCJKI.layersInfos = {}
        # self.enableSliderGroup.slidersValuesList = []
        # layers = [(l.name, l) for l in list(filter(lambda l: len(self.RCJKI.currentFont[self.RCJKI.currentGlyph.name].getLayer(l.name)), self.RCJKI.currentFont.layers))]
        # for l in layers:
        #     layerName, layer = l
        #     if layerName == "foreground": continue
        #     g = self.RCJKI.currentFont[self.RCJKI.currentGlyph.name].getLayer(layerName)
        #     emDimensions = self.RCJKI.project.settings['designFrame']['em_Dimension']
        #     pdfData = self.RCJKI.getLayerPDFImage(g, emDimensions)
        #     print(layer.lib.keys())
        #     d = {'Layer': layerName,
        #         'Image': NSImage.alloc().initWithData_(pdfData),
        #         'Values': 0,
        #         'Axis': self.RCJKI.currentFont.getLayer(layerName)[self.RCJKI.currentGlyph.name].lib.get("Axis", " ")
        #         # 'Lock': 1
        #         }

        #     self.enableSliderGroup.slidersValuesList.append(d)
        #     self.RCJKI.layersInfos[layerName] = 0
        # self.enableSliderGroup.slidersList.set(self.enableSliderGroup.slidersValuesList)


        self.RCJKI.layersInfos = {}
        enableSliderGroup = self.enableSliderGroup
        # enableSliderName = self.enableSliderGroup.axis

        self.enableSliderGroup.slidersValuesList = []
        layers = [(l.name, l) for l in list(filter(lambda l: len(self.RCJKI.currentFont[self.RCJKI.currentGlyph.name].getLayer(l.name)), self.RCJKI.currentFont.layers))]
        for l in layers:
            layerName, layer = l
            if layerName == "foreground": continue
            axis = self.RCJKI.currentFont.getLayer(layerName)[self.RCJKI.currentGlyph.name].lib.get("Axis", " ")
            # print(axis)
            if axis != self.enableSliderGroup.axis: continue
            
            g = self.RCJKI.currentFont[self.RCJKI.currentGlyph.name].getLayer(layerName)
            emDimensions = self.RCJKI.project.settings['designFrame']['em_Dimension']
            pdfData = self.RCJKI.getLayerPDFImage(g, emDimensions)
            # print(layer.lib.keys())
            d = {'Layer': layerName,
                'Image': NSImage.alloc().initWithData_(pdfData),
                'Values': 0,
                # 'Axis': axis
                # 'Lock': 1
                }

            self.enableSliderGroup.slidersValuesList.append(d)
            self.RCJKI.layersInfos[layerName] = 0
        self.enableSliderGroup.slidersList.set(self.enableSliderGroup.slidersValuesList)

    # def slidersListEditCallback(self, sender):
    #     sel = sender.getSelection()
    #     if not sel: return
    #     if self.lock: return
    #     self.lock = True
    #     layersInfo = sender.get()
    #     layerInfo = layersInfo[sel[0]]

    #     selectedLayerName = layerInfo["Layer"]
    #     image = layerInfo["Image"]
    #     # lock = layerInfo["Lock"]
    #     value = layerInfo["Values"]

    #     axis = layerInfo.get("Axis", " ")

    #     print(axis)
    #     layer = self.RCJKI.currentFont.getLayer(selectedLayerName)[self.RCJKI.currentGlyph.name]
    #     layer.lib['Axis'] = axis
    #     layer.update()
    #     print('\t', layer.lib.keys())
    #     # YValue = layerInfo["YValue"]

    #     # changed = False
    #     # # if lock:
    #     #     if Value != self.slidersValuesList[sel[0]]["Value"]:
    #     #         YValue = XValue
    #     #         changed = True

    #     #     elif YValue != self.slidersValuesList[sel[0]]["YValue"]:
    #     #         XValue = YValue
    #     #         changed = True

    #     # if lock != self.slidersValuesList[sel[0]]["Lock"]:
    #         # changed = True 

    #     self.RCJKI.layersInfos[selectedLayerName] = value
    #     self.slidersValuesList[sel[0]]["Values"] = value
    #     # self.slidersValuesList[sel[0]]["YValue"] = YValue 
    #     # self.slidersValuesList[sel[0]]["Lock"] = lock

    #     #if changed:
    #     # d = {'Layer': selectedLayerName,
    #     #     'Image': image,
    #     #     'Values': value
    #     #     # 'YValue': YValue,
    #     #     # 'Lock': lock
    #     #     }
    #     # layers = [e if i != sel[0] else d for i, e in enumerate(layersInfo)]
    #     # sender.set(layers)
    #     # sender.setSelection(sel)

    #     # layerInfo["NLI"] = "NLI"
    #     self.RCJKI.currentGlyph = self.RCJKI.currentFont[self.selectedDeepComponentGlyphName]
    #     self.RCJKI.deepComponentGlyph = self.RCJKI.getDeepComponentGlyph()
    #     self.w.mainCanvas.update()
    #     self.lock = False

    # def sliderListDoubleClickCallback(self, sender):
    #     sel = sender.getSelection()
    #     if not sel: return
    #     layerName = sender.get()[sel[0]]['Layer']
    #     self.RCJKI.currentGlyph = self.RCJKI.currentFont.getLayer(layerName)[self.RCJKI.currentGlyph.name]
    #     self.RCJKI.openGlyphWindow(self.RCJKI.currentGlyph)

    def fontsListSelectionCallback(self, sender):
        sel = sender.getSelection()
        if not sel:
            self.RCJKI.currentFont = None
            self.w.glyphSetList.setSelection([])
            self.w.glyphSetList.set([])
            self.selectedGlyph = None
            return
        self.RCJKI.currentFont = self.RCJKI.fonts2DCFonts[self.RCJKI.allFonts[sel[0]][self.controller.fontsList[sel[0]]]]
        self.controller.updateGlyphSetList()

    @refreshMainCanvas
    def glyphSetListSelectionCallback(self, sender):
        sel = sender.getSelection()
        if not sel: return
        self.selectedGlyphName = sender.get()[sel[0]]['Name']
        self.controller.updateDeepComponentsSetList(self.selectedGlyphName)
        self.deepComponentTranslateX, self.deepComponentTranslateY = 0, 0
        self.canvasGroup.dcOffsetXEditText.set(self.deepComponentTranslateX)
        self.canvasGroup.dcOffsetYEditText.set(self.deepComponentTranslateY)

    def glyphSetListdoubleClickCallback(self, sender):
        sel = sender.getSelection()
        if not sel: return
        selectedGlyphName = sender.get()[sel[0]]['Name']
        self.RCJKI.openGlyphWindow(self.RCJKI.DCFonts2Fonts[self.RCJKI.currentFont][selectedGlyphName])

    @refreshMainCanvas
    def deepComponentsSetListSelectionCallback(self, sender):
        sel = sender.getSelection()
        if not sel: return
        # self.RCJKI.deepComponentEditionController.makeNLIPaths()

        self.selectedDeepComponentGlyphName = sender.get()[sel[0]]['Name']

        self.controller.updateExtemeList(self.selectedDeepComponentGlyphName)
        if self.selectedDeepComponentGlyphName in self.RCJKI.currentFont:
            self.RCJKI.currentGlyph = self.RCJKI.currentFont[self.selectedDeepComponentGlyphName]

            if self.RCJKI.currentGlyph.markColor is None:
                r, g, b, a = 0, 0, 0, 0
            else: 
                r, g, b, a = self.RCJKI.currentGlyph.markColor
            self.canvasGroup.colorPicker.set(NSColor.colorWithCalibratedRed_green_blue_alpha_(r, g, b, a))
        else:
            self.RCJKI.currentGlyph = None
        self.setSliderList()

        self.RCJKI.deepComponentGlyph = self.RCJKI.getDeepComponentGlyph()

        self.deepComponentTranslateX, self.deepComponentTranslateY = 0, 0
        self.canvasGroup.dcOffsetXEditText.set(self.deepComponentTranslateX)
        self.canvasGroup.dcOffsetYEditText.set(self.deepComponentTranslateY) 

    # def extremsListCallback(self, sender):
    #     char = sender.getItem()
    #     self.controller.setExtremDCGlyph(char)

    def deepComponentsSetListDoubleClickCallback(self, sender):
        if not sender.getSelection(): return
        
        if self.selectedDeepComponentGlyphName not in self.RCJKI.currentFont:
            self.RCJKI.currentGlyph = self.RCJKI.currentFont.newGlyph(self.selectedDeepComponentGlyphName)
            self.RCJKI.currentGlyph.width = self.RCJKI.project.settings['designFrame']['em_Dimension'][0]
        self.RCJKI.openGlyphWindow(self.RCJKI.currentGlyph)

    # def colorPickerCallback(self, sender):
    #     if self.RCJKI.currentGlyph is None: return
    #     color = sender.get()
    #     r = color.redComponent()
    #     g = color.greenComponent()
    #     b = color.blueComponent()
    #     a = color.alphaComponent()
    
    #     self.RCJKI.currentGlyph.markColor = (r, g, b, a)
    #     self.controller.updateGlyphSetList()

    def windowCloses(self, sender):
        # askYesNo('Do you want to save fonts?', "Without saving you'll loose unsaved modification", alertStyle = 2, parentWindow = None, resultCallback = self.yesnocallback)
        if CurrentGlyphWindow() is not None:
            CurrentGlyphWindow().close()
        self.RCJKI.currentGlyphWindow = None
        self.RCJKI.deepComponentEditionController.interface = None
        self.RCJKI.deepComponentGlyph =  None
        self.observer(True)

    def yesnocallback(self, yes):
        if yes:
            self.RCJKI.deepComponentEditionController.saveSubsetFonts()

    def tableView_dataCellForTableColumn_row_(self, tableView, tableColumn, row, designStep, glist):
        self.RCJKI.tableView_dataCellForTableColumn_row_(tableView, tableColumn, row, self.w, glist, designStep, self.RCJKI.DCFonts2Fonts[self.RCJKI.currentFont])
