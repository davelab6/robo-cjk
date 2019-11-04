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

from defconAppKit.controls.glyphCollectionView import GlyphCollectionView

import os
import json
# import Quartz
import copy

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

class DeepComponentInstantiationWindow(BaseWindowController):

    def __init__(self, controller):
        super(DeepComponentInstantiationWindow, self).__init__()
        self.controller = controller
        self.RCJKI = self.controller.RCJKI
        self.RCJKI.allFonts = []
        self.selectedGlyph = None
        self.RCJKI.layersInfos = {}
        self.tempDeepComponent = None

        self.lock = False

        self.w = Window((200, 0, 800, 800), 
                'Deep Component Instantiation', 
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

        self.delegate = tableDelegate.TableDelegate.alloc().initWithMaster(self, "_deepComponentsInstantiation_glyphs", self.w.glyphSetList)
        tableView = self.w.glyphSetList.getNSTableView()
        tableView.setDelegate_(self.delegate)

        self.w.glyphCompositionList = List((0, 315, 200, 123),
                [],
                columnDescriptions = [
                                # {"title": "#", "width" : 20, 'editable':False},
                                {"title": "Char", "width" : 30, 'editable':False},
                                {"title": "Name", "width" : 150, 'editable':False},
                                # {"title": "MarkColor", "width" : 30, 'editable':False}
                                ],
                selectionCallback = self.glyphCompositionListSelectionCallback,
                # doubleClickCallback = self.glyphSetListdoubleClickCallback,
        #         # editCallback = self.glyphSetListEditCallback,
                showColumnTitles = False,
                drawFocusRing = False
            )

        self.w.keyVariantList = List((0, 438, 200, 123),
                [],
                columnDescriptions = [
                                # {"title": "#", "width" : 20, 'editable':False},
                                {"title": "Char", "width" : 30, 'editable':False},
                                {"title": "Name", "width" : 150, 'editable':False},
                                # {"title": "MarkColor", "width" : 30, 'editable':False}
                                ],
                selectionCallback = self.keyVariantListSelectionCallback,
        #         doubleClickCallback = self.deepComponentsSetListDoubleClickCallback,
        #         # editCallback = self.glyphSetListEditCallback,
                showColumnTitles = False,
                drawFocusRing = False
            )

        segmentedItems = ["Frozen Deep Components", "New Deep Component"]
        self.w.dcSegmentedButton = SegmentedButton((200, -240, -0, 20),
                [dict(title=e, width=600/len(segmentedItems)) for e in segmentedItems],
                callback = self.dcSegmentedButtonCallback
                )
        self.w.dcSegmentedButton.set(0)

        self.w.frozenDCGroup = Group((200, -220, -0, -0))
        self.w.newDCGroup = Group((200, -220, -0, -0))
        self.w.newDCGroup.show(0)
        self.DCGroups = [
                        self.w.frozenDCGroup,
                        self.w.newDCGroup
                        ]
        self.w.frozenDCGroup.frozenDCList = GlyphCollectionView((0, -0, -0, -0),
            selectionCallback = self.frozenDCListSelectionCallback)

        # self.w.deepComponentsSetList = List((0, 315, 200, 200),
        #         [],
        #         columnDescriptions = [
        #                         {"title": "#", "width" : 20, 'editable':False},
        #                         {"title": "Char", "width" : 30, 'editable':False},
        #                         {"title": "Name", "width" : 80, 'editable':False},
        #                         {"title": "MarkColor", "width" : 30, 'editable':False}
        #                         ],
        #         selectionCallback = self.deepComponentsSetListSelectionCallback,
        #         doubleClickCallback = self.deepComponentsSetListDoubleClickCallback,
        #         # editCallback = self.glyphSetListEditCallback,
        #         showColumnTitles = False,
        #         drawFocusRing = False
        #     )

        self.w.saveLocalFontButton = Button((0,-60,200,20), 
            'Save', 
            callback=self.saveLocalFontButtonCallback
            )

        self.w.pushBackButton = Button((0,-40,200,20), 
            'Push', 
            callback=self.pushBackButtonCallback
            )

        self.w.pullMasterGlyphsButton = Button((0,-20,200,20), 
            'Pull', 
            # callback=self.pullMasterGlyphsButtonCallback
            )

        

        self.canvasDrawer = mainCanvas.MainCanvas(self.RCJKI, self)
        self.w.mainCanvas = Canvas((200,0,-0,-240), 
            delegate=self.canvasDrawer,
            canvasSize=(5000, 5000),
            hasHorizontalScroller=False, 
            hasVerticalScroller=False)

        # self.w.extremsList = PopUpButton((200, 0, 200, 20), 
        #     [], 
        #     sizeStyle = 'small',
        #     callback = self.extremsListCallback)

        # self.w.dcOffsetXTextBox = TextBox((235, -260, 15, 20), "x:", sizeStyle = 'small')
        # self.w.dcOffsetYTextBox = TextBox((285, -260, 15, 20), "y:", sizeStyle = 'small')

        # self.deepComponentTranslateX = 0
        # self.w.dcOffsetXEditText = EditText((250, -260, 50, 20), 
        #     self.deepComponentTranslateX,
        #     sizeStyle = "small",
        #     callback = self.dcOffsetXEditTextCallback,
        #     continuous = False)

        # self.w.dcOffsetXEditText.getNSTextField().setBordered_(False)
        # self.w.dcOffsetXEditText.getNSTextField().setDrawsBackground_(False)

        # self.deepComponentTranslateY = 0
        # self.w.dcOffsetYEditText = EditText((300, -260, 50, 20), 
        #     self.deepComponentTranslateY,
        #     sizeStyle = "small",
        #     callback = self.dcOffsetYEditTextCallback,
        #     continuous = False)

        # self.w.dcOffsetYEditText.getNSTextField().setBordered_(False)
        # self.w.dcOffsetYEditText.getNSTextField().setDrawsBackground_(False)

        slider = SliderListCell(minValue = 0, maxValue = 1000)
        # checkbox = CheckBoxListCell()
        self.slidersValuesList = []
        self.w.newDCGroup.slidersList = List((0, -00, -0, -20),
            self.slidersValuesList,
            columnDescriptions = [
                                    {"title": "Layer", "editable": False, "width": 0},
                                    
                                    {"title": "Values", "cell": slider},
                                    {"title": "Image", "editable": False, "cell": ImageListCell(), "width": 60}, 
                                    # {"title": "NLI", "cell": PopUpButtonListCell(["NLI", "Reset NLI", "Update NLI"]), "binding": "selectedValue", "width": 100}
                                    # {"title": "Lock", "cell": checkbox, "width": 20},
                                   # {"title": "YValue", "cell": slider, "width": 250},
                                    
                                    ],
            editCallback = self.slidersListEditCallback,
            # doubleClickCallback = self.sliderListDoubleClickCallback,
            drawFocusRing = False,
            allowsMultipleSelection = False,
            rowHeight = 50.0,
            showColumnTitles = False
            )
        self.w.newDCGroup.addDCInstance = Button((-150, -20, -0, -0),
            "add",
            callback = self.addDCInstanceCallback)

        # self.w.addNLIButton = Button((-300, -20, 100, 20),
        #     'NLI',
        #     callback = self.addNLIButtonCallback)
        # self.w.addLayerButton = Button((-200, -20, 100, 20), 
        #     "+",
        #     callback = self.addLayerButtonCallback)
        # self.w.removeLayerButton = Button((-100, -20, 100, 20), 
        #     "-",
        #     callback = self.removeLayerButtonCallback)

        # self.w.colorPicker = ColorWell((200,-260,20,20),
        #         callback=self.colorPickerCallback, 
        #         color=NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, 0))

        

        # self.dummyCell = NSCell.alloc().init()
        # self.dummyCell.setImage_(None)

        # self.observer()


        self.w.bind('close', self.windowCloses)
        # self.w.bind('became main', self.windowBecameMain)
        self.w.open()

    

    @refreshMainCanvas
    def glyphSetListSelectionCallback(self, sender):
        sel = sender.getSelection()
        if not sel: return

        self.selectedChar = sender.get()[sel[0]]['Char']
        self.selectedGlyphName = sender.get()[sel[0]]['Name']    
        self.RCJKI.currentGlyph = self.RCJKI.currentFont[self.selectedGlyphName]


        if self.selectedGlyphName in self.RCJKI.collab._userLocker(self.RCJKI.user).glyphs['_deepComponentsInstantiation_glyphs']:
            self.currentGlyphComposition = None
            if self.selectedChar:
                self.currentGlyphComposition = [dict(Char = c, Name = files.normalizeUnicode(hex(ord(c))[2:].upper())) for c in self.RCJKI.char2DC[self.selectedChar]]
                self.w.glyphCompositionList.set(self.currentGlyphComposition)


                # ----- ADD DCINFOS IN CURRENTGLYPH LIB
                
                self.setCurrentGlyphLib()
                self.controller.getDeepComponentsInstances()
                # print(self.RCJKI.currentGlyph.lib["DeepComponentsInfos"])

        else:
            self.w.glyphCompositionList.set([])
            self.w.glyphCompositionList.setSelection([])

        # self.controller.getDeepComponentsInstances()
        # self.controller.updateDeepComponentsSetList(self.selectedGlyphName)

        # self.deepComponentTranslateX, self.deepComponentTranslateY = 0, 0
        # self.w.dcOffsetXEditText.set(self.deepComponentTranslateX)
        # self.w.dcOffsetYEditText.set(self.deepComponentTranslateY)
        # self.w.mainCanvas.update()

    def setCurrentGlyphLib(self):
        if "DeepComponentsInfos" not in self.RCJKI.currentGlyph.lib:
            self.RCJKI.currentGlyph.lib["DeepComponentsInfos"]=[]
            for e in self.currentGlyphComposition:
                name = e["Name"]
                char = e["Char"]
                dcFont = self.RCJKI.fonts2DCFonts[self.RCJKI.currentFont]
                # print(self.getDCVariant(char, dcFont))
                self.RCJKI.currentGlyph.lib["DeepComponentsInfos"].append(
                    dict(
                        DeepComponentName = self.getDCVariant(char, dcFont)[0]["Name"],
                        DeepComponentInstance = {}
                        )
                    # {self.getDCVariant(char, dcFont)[0]["Name"]:{}}
                    )

    def getDCVariant(self, selectedKey, dcFont):
        selectedKeyCode = files.normalizeUnicode(hex(ord(selectedKey))[2:].upper())
        DCV = list(filter(lambda n: selectedKeyCode in n.split('_'), dcFont.keys()))
        return [dict(Char = chr(int(n.split("_")[1],16)), Name = n) for n in sorted(DCV)]

    @refreshMainCanvas
    def glyphCompositionListSelectionCallback(self, sender):
        sel = sender.getSelection()
        if not sel: 
            self.w.keyVariantList.set([])
            return

        

        selectedKey = sender.get()[sel[0]]['Char']
        self.selectedKeyName = sender.get()[sel[0]]['Name']
        script = self.controller.script
        dcFont = self.RCJKI.fonts2DCFonts[self.RCJKI.currentFont]

        DCVariants = self.getDCVariant(selectedKey, dcFont)



        # if "DeepComponentsInfos" not in self.RCJKI.currentGlyph.lib:
        #     self.RCJKI.currentGlyph.lib["DeepComponentsInfos"]=[]
        # lib = self.RCJKI.currentGlyph.lib["DeepComponentsInfos"]

        # defaultDC = [getDCVariant(e["Char"])[0]["Name"] for e in sender.get()]
        
        # for i, name in enumerate(defaultDC):
        #     print([list(e.keys())[0][:-3] for e in lib])
        #     if name[:-3] not in [list(e.keys())[0][:-3] for e in lib]:
        #         print(name[:-3])
        #         lib.insert(i, {name:{}})
        # print(self.RCJKI.currentGlyph.lib["DeepComponentsInfos"])


        # DCVariants = [dict(Char = v[0], Name = files.unicodeName(v[0])) for v in deepCompoMasters_AGB1_FULL.deepCompoMasters[script][selectedKey]]
        # DCVariants = [dict(Char = v[0], Name = files.unicodeName(v[0])) for v in deepCompoMasters_AGB1_FULL.deepCompoMasters[script][selectedKey]]
        self.w.keyVariantList.set(DCVariants)
        for i, e in enumerate(DCVariants):
            if not "DeepComponentsInfos" in self.RCJKI.currentGlyph.lib: continue
            if e["Name"] == self.RCJKI.currentGlyph.lib["DeepComponentsInfos"][sel[0]]["DeepComponentName"]:
                self.w.keyVariantList.setSelection([i])

    def keyVariantListSelectionCallback(self, sender):
        sel = sender.getSelection()
        if not sel: 
            self.w.frozenDCGroup.frozenDCList.set([])
            self.w.newDCGroup.slidersList.set([])
            return

        selectedName = sender.get()[sel[0]]['Name']
        dcFont = self.RCJKI.fonts2DCFonts[self.RCJKI.currentFont]

        # lib = self.RCJKI.currentGlyph.lib["DeepComponentsInfos"]
        glyphCompositionSel = self.w.glyphCompositionList.getSelection()[0]

        # print(lib[glyphCompositionSel]["DeepComponentName"])
        if 'DeepComponentsInfos' in self.RCJKI.currentGlyph.lib:
            self.RCJKI.currentGlyph.lib["DeepComponentsInfos"][glyphCompositionSel]["DeepComponentName"] = selectedName
            # print(self.RCJKI.currentGlyph.lib["DeepComponentsInfos"])

        # if "DeepComponentsInfos" not in self.RCJKI.currentGlyph.lib:
        #     self.RCJKI.currentGlyph.lib["DeepComponentsInfos"]=[]
        # lib = self.RCJKI.currentGlyph.lib["DeepComponentsInfos"]

        # print(selectedName)
        # item = {selectedName:{}}
        # print("------LIB------")
        # print(lib[sel[0]])
        # print("------LIB------")
        # lib[sel[0]] = item

        # self.RCJKI.currentGlyph.lib["DeepComponentsInfos"] = lib
        # print(self.RCJKI.currentGlyph.lib["DeepComponentsInfos"])
        # # if "DeepComponentsInfos" not in self.RCJKI.currentGlyph.lib:
        #     # self.RCJKI.currentGlyph.lib["DeepComponentsInfos"]=[]
        # print(sender.get())
        # for i, e in enumerate(sender.get()):
        #     print([list(e.keys())[0] for e in lib])
        #     if e["Name"] not in [list(e.keys())[0] for e in lib]:
        #         lib.insert(i, {e["Name"]:{}})
        #     # self.RCJKI.currentGlyph.lib["DeepComponentsInfos"].append({e["Name"]:{}})
        # self.RCJKI.currentGlyph.lib["DeepComponentsInfos"] = lib
        # print(self.RCJKI.currentGlyph.lib["DeepComponentsInfos"])

        self.selectedDeepComponentGlyph = dcFont[selectedName]
        self.getFrozenDC()
        self.setSliderList()

        self.controller.getDeepComponentsInstances()

    def getFrozenDC(self):
        tempFDC = NewFont(showUI = False)
        DCGlyphsList = []
        for FDC, layersInfos in self.selectedDeepComponentGlyph.lib["DeepComponents"].items():
            tempFDC.newGlyph(FDC)
            tempFDC[FDC].appendGlyph(interpolations.deepolation(RGlyph(), self.selectedDeepComponentGlyph, layersInfos))
            tempFDC[FDC].width = self.RCJKI.project.settings['designFrame']['em_Dimension'][0]
            DCGlyphsList.append(tempFDC[FDC])

        self.w.frozenDCGroup.frozenDCList.set(DCGlyphsList)

    def setSliderList(self):
        self.RCJKI.layersInfos = {}
        self.slidersValuesList = []

        layers = [l.name for l in list(filter(lambda l: len(self.selectedDeepComponentGlyph.getLayer(l.name)), self.RCJKI.fonts2DCFonts[self.RCJKI.currentFont].layers))]
        for layerName in layers:
            if layerName == "foreground": continue
            value = 0

            self.slidersValuesList.append(self.getSlidersInfos(layerName, value))
            self.RCJKI.layersInfos[layerName] = value
        self.w.newDCGroup.slidersList.set(self.slidersValuesList)

    def getSlidersInfos(self, layerName, value):
        g = self.selectedDeepComponentGlyph.getLayer(layerName)
        emDimensions = self.RCJKI.project.settings['designFrame']['em_Dimension']
        pdfData = self.RCJKI.getLayerPDFImage(g, emDimensions)

        d = {'Layer': layerName,
            'Image': NSImage.alloc().initWithData_(pdfData),
            'Values': value,
            # 'NLI': 'NLI'
            }
        return d


    @refreshMainCanvas
    def saveLocalFontButtonCallback(self, sender):
        self.RCJKI.deepComponentInstantiationController.saveSubsetFonts()

    @refreshMainCanvas
    def pushBackButtonCallback(self, sender):
        self.controller.pushDCMasters()

    @refreshMainCanvas
    def slidersListEditCallback(self, sender):
        sel = sender.getSelection()
        if not sel: return

        self.w.frozenDCGroup.frozenDCList.setSelection([])
        # if self.lock: return
        # self.lock = True
        layersInfo = sender.get()
        layerInfo = layersInfo[sel[0]]

        selectedLayerName = layerInfo["Layer"]
        image = layerInfo["Image"]
        value = layerInfo["Values"]

        self.RCJKI.layersInfos[selectedLayerName] = value
        self.slidersValuesList[sel[0]]["Values"] = value

        offset = [0, 0]
        if self.tempDeepComponent:
            offset =  self.tempDeepComponent[2]
        layersInfos = {layerInfo["Layer"]:layerInfo["Values"] for layerInfo in layersInfo}
        # self.tempDeepComponent = interpolations.deepolation(RGlyph(), self.selectedDeepComponentGlyph, layersInfos)
        self.tempDeepComponent = [self.selectedDeepComponentGlyph, layersInfos, offset]
        self.canvasDrawer.TempDCIGlyph = interpolations.deepolation(RGlyph(), self.selectedDeepComponentGlyph, layersInfos)
        self.canvasDrawer.TempDCIGlyph.moveBy((offset[0], offset[1]))

        # self.RCJKI.currentGlyph = self.RCJKI.currentFont[self.selectedDeepComponentGlyphName]
        # self.RCJKI.deepComponentGlyph = self.RCJKI.getDeepComponentGlyph()
        # self.w.mainCanvas.update()
        # self.lock = False
    @refreshMainCanvas
    def addDCInstanceCallback(self, sender):
        # print(self.RCJKI.layersInfos)
        # print(self.selectedDeepComponentGlyph.lib["DeepComponents"])

        # name = "DC_"
        i = 0
        while True:
            name = "DC_%s"%str(i).zfill(2)
            if name not in self.selectedDeepComponentGlyph.lib["DeepComponents"].keys():
                break
            i+=1

        self.selectedDeepComponentGlyph.lib["DeepComponents"][name] = copy.deepcopy(self.RCJKI.layersInfos)
        self.selectedDeepComponentGlyph.update()
        self.getFrozenDC()

        self.w.frozenDCGroup.frozenDCList.setSelection([-1])
        self.controller.getDeepComponentsInstances()

    @refreshMainCanvas
    def frozenDCListSelectionCallback(self, sender):
        sel = sender.getSelection()
        if not sel:
            return
        glyph = sender.get()[sel[0]]
        name = glyph.name

        # instance = {name:(0, 0)}
        instance = dict(Name = name, offset = (0, 0))
        glyphCompositionSel = self.w.glyphCompositionList.getSelection()[0]
        self.RCJKI.currentGlyph.lib["DeepComponentsInfos"][glyphCompositionSel]["DeepComponentInstance"] = instance
        # self.RCJKI.currentGlyph.lib["DeepComponentsInfos"][glyphCompositionSel][self.selectedKeyName] = instance
        self.RCJKI.currentGlyph.update()

        self.RCJKI.layersInfos = {}
        self.slidersValuesList = []
        for layerName, value in self.selectedDeepComponentGlyph.lib["DeepComponents"][name].items():
            self.slidersValuesList.append(self.getSlidersInfos(layerName, value))
            self.RCJKI.layersInfos[layerName] = value
        self.w.newDCGroup.slidersList.set(self.slidersValuesList)

        self.controller.getDeepComponentsInstances()

    @refreshMainCanvas
    def glyphSetListdoubleClickCallback(self, sender):
        sel = sender.getSelection()
        if not sel:
            return
        if not self.RCJKI.currentGlyph.width:
            self.RCJKI.currentGlyph.width = self.RCJKI.project.settings['designFrame']['em_Dimension'][0]
            self.RCJKI.currentGlyph.update()
        # print(self.RCJKI.currentGlyph.width)
        

    def fontsListSelectionCallback(self, sender):
        sel = sender.getSelection()
        if not sel:
            self.RCJKI.currentFont = None
            self.w.glyphSetList.setSelection([])
            self.w.glyphSetList.set([])
            self.selectedGlyph = None
            return
        self.RCJKI.currentFont = self.RCJKI.allFonts[sel[0]][self.controller.fontsList[sel[0]]]
        # print(self.RCJKI.currentFont)
        self.controller.updateGlyphSetList()
        self.controller.getDeepComponentsInstances()

    @refreshMainCanvas
    def dcSegmentedButtonCallback(self, sender):
        for i, g in enumerate(self.DCGroups):
            g.show(i==sender.get())
        self.tempDeepComponent = None
        self.canvasDrawer.TempDCIGlyph = None

    def windowCloses(self, sender):
        # askYesNo('Do you want to save fonts?', "Without saving you'll loose unsaved modification", alertStyle = 2, parentWindow = None, resultCallback = self.yesnocallback)
        if CurrentGlyphWindow() is not None:
            CurrentGlyphWindow().close()
        self.RCJKI.currentGlyphWindow = None
        self.RCJKI.deepComponentInstantiationController.interface = None
        self.RCJKI.deepComponentGlyph =  None
        # self.observer(True)


    def tableView_dataCellForTableColumn_row_(self, tableView, tableColumn, row, designStep, glist):
        self.RCJKI.tableView_dataCellForTableColumn_row_(tableView, tableColumn, row, self.w, glist, designStep, self.RCJKI.currentFont)

