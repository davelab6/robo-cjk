"""
Copyright 2020 Black Foundry.

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
from vanilla import *
from vanilla.dialogs import getFile, getFolder, message
from fontParts.ui import AskString
from mojo.canvas import Canvas
import mojo.drawingTools as mjdt
from mojo.UI import CurrentGlyphWindow
from utils import files, interpolation
from AppKit import NumberFormatter, NSColor
from mojo.UI import PostBannerNotification
from mojo.extensions import getExtensionDefault, setExtensionDefault
from mojo.UI import SetCurrentLayerByName
from controllers import client
from utils import colors

import json, os
blackrobocjk_locker = "com.black-foundry.blackrobocjk_locker"

transparentColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, 1, 1, 0)

cwd = os.getcwd()
connectorPath = os.path.join(cwd, "rcjk2mysql", "Config", "connectors.cfg")
# head, tail = os.path.split(cwd)
# print("cwd", cwd)
# print("head", head)
# print("tail", tail)

getSuffix = files.getSuffix

class SelectLayerSheet():
    def __init__(self, RCJKI, controller, availableLayers):
        self.RCJKI = RCJKI
        self.availableLayers = availableLayers
        # self.parent = CurrentGlyphWindow()
        self.sheet = Sheet((300, 420), controller.controller.w)
        
        self.previewGlyph = None
        
        self.aegv =  self.RCJKI.currentGlyph.lib.get('robocjk.atomicElement.glyphVariations',{})
        self.sheet.layerList = List(
            (0, 0, -0, 80),
            [l.layer.name for l in self.availableLayers if l.layer.name not in self.aegv.values()],
            allowsMultipleSelection = False,
            selectionCallback = self.updatePreview
            )
        
        self.sheet.newAxisNameTextBox = TextBox(
            (0, 80, 100, 20), 
            'Axis Name:'
            )
        layerName = files.normalizeCode(str(len(self.aegv)), 4)
        self.sheet.newAxisNameEditText = EditText(
            (100, 80, -0, 20), 
            layerName
            )
    
        self.sheet.canvasPreview = Canvas(
            (0, 100, -0, -20), 
            canvasSize=(300, 300), 
            delegate=self
            )

        self.updatePreview(None)
        
        self.sheet.addButton = Button(
            (-150,-20, 150, 20), 
            'Add', 
            callback=self.addLayer
            )

        self.sheet.closeButton = Button(
            (-300,-20, 150, 20), 
            'Close', 
            callback=self.closeSheet
            )

        self.sheet.setDefaultButton(self.sheet.addButton)
        self.sheet.open()
        
    def addLayer(self, sender):
        newAxisName = self.sheet.newAxisNameEditText.get()
        newLayerName = self.sheet.layerList.get()[self.sheet.layerList.getSelection()[0]]

        currentGlyph = self.RCJKI.currentFont.getGlyphFromLayer(self.RCJKI.currentGlyph.name, "foreground")
        if newAxisName in currentGlyph._axes.names:
            PostBannerNotification('Impossible', "Layer name already exist")
            return
        SetCurrentLayerByName("foreground")
        currentGlyph.addGlyphVariation(newAxisName, newLayerName)
        self.RCJKI.updateListInterface()
        self.RCJKI.updateDeepComponent(update = False)
        self.sheet.close()
        
    def closeSheet(self, sender):
        self.sheet.close()
    
    def updatePreview(self, sender):
        if not self.sheet.layerList.getSelection() : return
        self.previewGlyph = None
        for l in self.availableLayers:
            if l.layer.name == self.sheet.layerList.get()[self.sheet.layerList.getSelection()[0]]:
                self.previewGlyph = l
        self.sheet.canvasPreview.update()
                
    def draw(self):
        if not self.previewGlyph: return
        mjdt.save()
        mjdt.translate(75, 95)
        mjdt.scale(.15)
        mjdt.fill(0, 0, 0, 1)
        mjdt.drawGlyph(self.previewGlyph)  
        mjdt.restore()

class SelectAtomicElementSheet():

    def __init__(self, RCJKI, atomicElementsNames):
        self.RCJKI = RCJKI
        self.atomicElementsNames = atomicElementsNames
        self.atomicElementName = None
        self.previewGlyph = None
        self.parent = CurrentGlyphWindow()
        self.parent.sheet = Sheet((300, 400), self.parent.w)
        
        self.parent.sheet.searchBox = SearchBox(
            (0, 0, -0, 20),
            callback = self.searchBoxCallback
            )
        self.parent.sheet.atomicElementList = List(
            (0, 20, -0, -220),
            self.atomicElementsNames,
            allowsMultipleSelection = False,
            selectionCallback = self.atomicElementListSelectionCallback
            )
        self.parent.sheet.atomicElementList.setSelection([])

        self.parent.sheet.canvasPreview = Canvas(
            (0, -220, -0, -20), 
            canvasSize=(300, 200), 
            delegate=self
            )
        
        self.parent.sheet.addButton = Button(
            (-150,-20, 150, 20), 
            'Add', 
            callback=self.addAtomicElement
            )
        self.parent.sheet.closeButton = Button(
            (-300,-20, 150, 20), 
            'Close', 
            callback=self.closeSheet
            )
        self.parent.sheet.setDefaultButton(self.parent.sheet.addButton)
        self.parent.sheet.open()

    def searchBoxCallback(self, sender):
        name = sender.get()
        l = files._getFilteredListFromName(self.atomicElementsNames, name)
        if not l:
            l = self.atomicElementsNamest
        self.parent.sheet.atomicElementList.set(l)
    
    def closeSheet(self, sender):
        self.parent.sheet.close()

    def atomicElementListSelectionCallback(self, sender):
        sel = sender.getSelection()
        if not sel: return
        self.atomicElementName = sender.get()[sel[0]]
        self.RCJKI.currentFont[self.atomicElementName]
        self.previewGlyph = self.RCJKI.currentFont._RFont[self.atomicElementName]
        self.parent.sheet.canvasPreview.update()
    
    def addAtomicElement(self, sender):
        if self.atomicElementName is None: return
        self.RCJKI.currentGlyph.addAtomicElementNamed(self.atomicElementName)
        self.RCJKI.updateDeepComponent(update = False)
        self.RCJKI.glyphInspectorWindow.deepComponentListItem.setList()

    def draw(self):
        if self.previewGlyph is None: return
        glyphs = self.previewGlyph.layers
        mjdt.save()
        mjdt.translate(75, 95)
        mjdt.scale(.15)
        mjdt.fill(0, 0, 0, 1/(len(glyphs)+1e-10))
        for glyph in glyphs:
            mjdt.drawGlyph(glyph)  
        mjdt.restore()

class SelectFontVariationSheet():
    def __init__(self, RCJKI, view):
        self.RCJKI = RCJKI
        self.view = view
        self.parent = CurrentGlyphWindow()
        self.parent.sheet = Sheet((300, 140), self.parent.w)
        print(self.RCJKI.currentFont.fontVariations)
        print(self.RCJKI.currentGlyph._glyphVariations.axes)
        l = [axis for axis in self.RCJKI.currentFont.fontVariations if axis not in self.RCJKI.currentGlyph._glyphVariations.axes]
        if not l: l=[""]
        popupbuttonlist = PopUpButtonListCell(l)
        self.parent.sheet.fontVariationsList = List((0, 0, -0, 20), 
            [{'AxisName':l[0]}],
            columnDescriptions = [{"title":"AxisName", "cell":popupbuttonlist, "binding": "selectedValue", "editable":True, "width":290}],
            showColumnTitles = False,
            allowsMultipleSelection = False
            )
        self.parent.sheet.addButton = Button(
            (-150,-20, 150, 20), 
            'Add', 
            callback=self.addCharacterGlyphFontVariation
            )
        self.parent.sheet.closeButton = Button(
            (-300,-20, 150, 20), 
            'Close', 
            callback=self.closeSheet
            )
        self.parent.sheet.setDefaultButton(self.parent.sheet.addButton)
        self.parent.sheet.open()
        
    def addCharacterGlyphFontVariation(self, sender):
        name = self.parent.sheet.fontVariationsList.get()[self.parent.sheet.fontVariationsList.getSelection()[0]]['AxisName']
        self.RCJKI.currentGlyph.addCharacterGlyphNamedVariationToGlyph(name)
        self.RCJKI.updateListInterface()

        source = []
        if self.RCJKI.currentGlyph._glyphVariations:
            source = [{'Axis':axis, 'PreviewValue':0} for axis in self.RCJKI.currentGlyph._glyphVariations]
        isel = len(source)
        self.RCJKI.currentGlyph.selectedSourceAxis = source[isel-1]['Axis']
        self.RCJKI.copyDCSettingsFromAnotherGlyphWindowSetUI()
        self.view.sourcesList.setSelection([isel-1])
        self.RCJKI.updateDeepComponent(update = False)
        
    def closeSheet(self, sender):
        self.parent.sheet.close()

class SelectDeepComponentSheet():

    def __init__(self, RCJKI, deepComponentsNames):
        self.RCJKI = RCJKI
        self.deepComponentsNames = deepComponentsNames
        self.parent = CurrentGlyphWindow()
        self.parent.sheet = Sheet((300, 400), self.parent.w)
        self.glyph = None

        self.parent.sheet.canvasPreview = Canvas(
            (0, -220, -0, -20), 
            canvasSize=(300, 300), 
            delegate=self
            )

        self.parent.sheet.searchBox = SearchBox(
            (0, 0, -0, 20),
            callback = self.searchBoxCallback
            )
        self.parent.sheet.deepComponentList = List(
            (0, 20, -0, -220),
            self.deepComponentsNames,
            selectionCallback = self.deepComponentListSelectionCallback,
            allowsMultipleSelection = False
            )
        if self.deepComponentsNames:
            self.getDeepComponentPreview(self.deepComponentsNames[0])
            self.deepComponentName = self.deepComponentsNames[0]
        
        self.parent.sheet.addButton = Button(
            (-150,-20, 150, 20), 
            'Add', 
            callback=self.addDeepComponentList
            )
        self.parent.sheet.closeButton = Button(
            (-300,-20, 150, 20), 
            'Close', 
            callback=self.closeSheet
            )
        self.parent.sheet.setDefaultButton(self.parent.sheet.addButton)
        self.parent.sheet.open()

    def searchBoxCallback(self, sender):
        name = sender.get()
        l = files._getFilteredListFromName(self.deepComponentsNames, name)
        if not l:
            l = self.deepComponentsNames
        self.parent.sheet.deepComponentList.set(l)

    def deepComponentListSelectionCallback(self, sender):
        sel = sender.getSelection()
        if not sel: return
        self.deepComponentName = sender.get()[sel[0]]
        self.getDeepComponentPreview(self.deepComponentName)

    def getDeepComponentPreview(self, deepComponentName):
        self.glyph = self.RCJKI.currentFont[deepComponentName]
        # self.glyph.preview.computeDeepComponents(update = False)
        self.parent.sheet.canvasPreview.update()
    
    def closeSheet(self, sender):
        self.parent.sheet.close()
    
    def addDeepComponentList(self, sender):
        self.RCJKI.currentGlyph.addDeepComponentNamed(self.deepComponentName)
        self.RCJKI.updateDeepComponent(update = False)
        self.RCJKI.glyphInspectorWindow.deepComponentListItem.setList()

    def draw(self):
        if self.glyph is None: return
        mjdt.save()
        mjdt.translate(75, 35)
        mjdt.scale(.15)
        mjdt.fill(0, 0, 0, 1)
        # # loc = {}
        # # if self.glyph.selectedSourceAxis:
        #     loc = {self.glyph.selectedSourceAxis:1}
        for atomicinstance in self.glyph.preview(forceRefresh=False):
            mjdt.drawGlyph(atomicinstance.glyph) 
        mjdt.restore()

numberFormatter = NumberFormatter()

class FontInfosSheet():

    def __init__(self, RCJKI, parentWindow, posSize):
        self.RCJKI = RCJKI
        # if not self.RCJKI.get("currentFont"): return
        # print(self.RCJKI.currentFont.designspace)
        fontvariations = []
        for axis in self.RCJKI.currentFont.designspace.get("axes", []):
            axe = dict(tag=axis["tag"], name=axis["name"], minimum=axis["minValue"], maximum=axis["maxValue"], default=axis["defaultValue"])
            fontvariations.append(axe)
        # return
        # fontvariations = self.RCJKI.currentFont.fontVariations
        if 'robocjk.defaultGlyphWidth' not in self.RCJKI.currentFont._fullRFont.lib:
            self.RCJKI.currentFont._fullRFont.lib['robocjk.defaultGlyphWidth'] = 1000
        defaultGlyphWidth = self.RCJKI.currentFont._fullRFont.lib['robocjk.defaultGlyphWidth']

        self.s = Sheet(posSize, parentWindow)
        self.s.fontVariationAxisList = List(
            (10, 10, -10, 100), 
            fontvariations,
            columnDescriptions=[{"title": "tag"}, {"title": "name"}, {"title": "minimum"}, {"title": "default"}, {"title": "maximum"}],
             
            editCallback = self.fontVariationAxisListEditCallback
            )
        self.s.addVariation = Button(
            (10, 110, 200, 20), 
            "+",
            callback = self.addVariationCallback,
            sizeStyle = 'small'
            )
        self.s.removeVariation = Button(
            (210, 110, 200, 20), 
            "-",
            callback = self.removeVariationCallback,
            sizeStyle = 'small'
            )

        self.s.defaultGlyphWidthTitle = TextBox(
            (10, 142, 150, 20),
            'Default Glyph Width',
            sizeStyle = "small"
            ) 

        self.s.defaultGlyphWidth = EditText(
            (125, 140, -10, 20),
            defaultGlyphWidth,
            sizeStyle = 'small',
            formatter = numberFormatter,
            callback = self.defaultGlyphWidthCallback
            )

        self.s.loadDataBase = Button(
            (10, 170, -10, 20),
            'Load Data Base',
            callback = self.loadDataBaseCallback,
            sizeStyle = 'small'
            )

        # self.s.exportDataBase = Button(
        #     (10, 190, 200, 20),
        #     'Export Data Base',
        #     callback = self.exportDataBaseCallback,
        #     sizeStyle = 'small'
        #     )

        self.s.closeButton = Button(
            (10, -30, -10, 20), 
            'close', 
            self.closeCallback,
            sizeStyle = 'small'
            )
        self.s.open()

    @property
    def fontAxesNames(self):
        return [x["tag"] for x in self.s.fontVariationAxisList.get()]

    @property
    def formatAxesForJSON(self):
        axes = []
        for axis in self.s.fontVariationAxisList.get():
            elem = {"name":axis["name"], "tag":axis["tag"], 
            "defaultValue":axis["default"], 'maxValue':axis["maximum"], 
            "minValue":axis["minimum"]}
            axes.append(elem)
        return axes

    def fontVariationAxisListEditCallback(self, sender):
        self.RCJKI.currentFont.designspace["axes"] = self.formatAxesForJSON
        self.RCJKI.currentFont._fullRFont.lib['robocjk.fontVariations'] = self.fontAxesNames
        self.RCJKI.currentFont.fontVariations = self.fontAxesNames

    def addVariationCallback(self, sender):
        names = self.fontAxesNames
        l = 0
        name = files.normalizeCode(files.int_to_column_id(l), 4)
        while name in names:
            l += 1
            name = files.normalizeCode(files.int_to_column_id(l), 4)

        tag = name
        for x in ["a", "e", "i", "o", "u", "y"]:
            tag = tag.replace(x,'')
        tag = tag[:4]
        elem = dict(name=name, tag=tag, minimum=0, default=0, maximum=1)
        elem_designspace = {"name": name, "tag":tag, 'defaultValue':0, "maxValue":1, "minValue":0}

        self.RCJKI.currentFont.designspace.get("axes", []).append(elem_designspace)
        self.s.fontVariationAxisList.append(elem)
        self.RCJKI.currentFont._fullRFont.lib['robocjk.fontVariations'].append(tag)
        self.RCJKI.currentFont.fontVariations.append(tag)

    def defaultGlyphWidthCallback(self, sender):
        try:
            self.RCJKI.currentFont._fullRFont.lib['robocjk.defaultGlyphWidth'] = sender.get()
            self.RCJKI.currentFont.defaultGlyphWidth = sender.get()
        except: pass

    def removeVariationCallback(self, sender):
        sel = self.s.fontVariationAxisList.getSelection()
        if not sel: return
        l = self.s.fontVariationAxisList.get()
        l.pop(sel[0])
        self.s.fontVariationAxisList.set(l)
        self.RCJKI.currentFont.designspace["axes"] = self.formatAxesForJSON
        self.RCJKI.currentFont._fullRFont.lib['robocjk.fontVariations'] = self.fontAxesNames
        self.RCJKI.currentFont.fontVariations = self.fontAxesNames

    def loadDataBaseCallback(self, sender):
        path = getFile()[0]
        if path.endswith("txt"):
            with open(path, 'r', encoding = 'utf-8') as file:
                txt = file.readlines()
            self.RCJKI.currentFont.dataBase = {}
            for line in txt:
                k, v = line.strip('\n').split(':')
                self.RCJKI.currentFont.dataBase[k] = v
        elif path.endswith("json"):
            with open(path, 'r', encoding = 'utf-8') as file:
                self.RCJKI.currentFont.dataBase = json.load(file)
                
        self.RCJKI.exportDataBase()

    # def exportDataBaseCallback(self, sender):
    #     self.RCJKI.exportDataBase()
        
    def closeCallback(self, sender):
        self.RCJKI.currentFont.fontLib.update(self.RCJKI.currentFont._fullRFont.lib.asDict())
        self.RCJKI.currentFont.updateDesignspace()
        self.RCJKI.currentFont.saveFontlib()
        self.RCJKI.currentFont.createLayersFromVariationAxis()
        self.s.close()

class NewGlyph:

    def __init__(self, RCJKI, parentWindow):
        self.RCJKI = RCJKI
        self.window = parentWindow
        self.w = Sheet((400, 100), self.window)
        self.w.inputNameTitle = TextBox((10, 10, -10, 20), 'Choose a %s name'%self.type)
        self.w.inputName = EditText((10, 40, -10, 20), '')
        self.w.applyButton = Button((200, -20, -0, -0), "Apply", callback = self.applyButtonCallback)
        self.w.cancelButton = Button((0, -20, 200, -0), "Cancel", callback = self.closeButtonCallback)
        self.w.setDefaultButton(self.w.applyButton)
        

    def dumpName(self, glyphType, sets):
        index = 0
        while True:
            name = "%s%s"%(glyphType, str(index).zfill(5))
            if not name in sets:
                return name
            index+=1

    def setWindow(self):
        self.dumpedName = self.dumpName(self.type, self.glyphset)
        self.w.inputName.set(self.dumpedName)
        self.w.open()

    def applyButtonCallback(self, sender):
        chosenName = self.w.inputName.get()
        if self.type == 'characterGlyph' and len(chosenName) == 1:
            chosenName = f"uni{ord(chosenName):04X}"
        if " " in chosenName:
            message("Warning a name shouldn't contain a space")
            return
        elif chosenName in self.glyphset:
            message("This name already exist in the font")
            return
        self.RCJKI.currentFont.newGlyph(self.type, chosenName)
        self.windowList.setSelection([])
        if self.type == 'deepComponent':
            self.windowList.set(self.RCJKI.currentFont.deepComponentSet)
        elif self.type == "characterGlyph":
            charSet = [dict(char = files.unicodeName2Char(x), name = x) for x in sorted(list(self.RCJKI.currentFont.staticCharacterGlyphSet()))]
            self.windowList.set(charSet)
        else:
            self.windowList.set(self.RCJKI.currentFont.atomicElementSet)
        self.w.close()

    def closeButtonCallback(self, sender):
        self.w.close()

class NewCharacterGlyph(NewGlyph):

    def __init__(self, *args, **kwargs):
        self.type = 'characterGlyph'
        super().__init__(*args, **kwargs)
        self.glyphset = self.RCJKI.currentFont.staticCharacterGlyphSet()
        self.windowList = self.window.characterGlyph
        self.setWindow()

class NewDeepComponent(NewGlyph):

    def __init__(self, *args, **kwargs):
        self.type = 'deepComponent'
        super().__init__(*args, **kwargs)
        self.glyphset = self.RCJKI.currentFont.staticDeepComponentSet()
        self.windowList = self.window.deepComponent
        self.setWindow()

class NewAtomicElement(NewGlyph):

    def __init__(self, *args, **kwargs):
        self.type = "atomicElement"
        super().__init__(*args, **kwargs)
        self.glyphset = self.RCJKI.currentFont.staticAtomicElementSet()
        self.windowList = self.window.atomicElement
        self.setWindow()

# class NewCharacterGlyph:

#     def __init__(self, RCJKI, parentWindow):
#         self.RCJKI = RCJKI
#         self.window = parentWindow
#         self.w = Sheet((400, 300), self.window)
#         self.w.segmentedButton = SegmentedButton(
#             (10, 10, -10, 20),
#             [dict(title = "Custom"), dict(title = "Related to deep components")],
#             callback = self.segmentedButtonCallback
#             )
#         self.w.segmentedButton.set(0)

#         self.w.custom = Group((0, 25, -0, -0))
#         self.w.custom.show(True)
#         self.w.related = Group((0, 25, -0, -0))
#         self.w.related.show(False)
#         self.groups = [self.w.custom, self.w.related]

#         self.DCSet = set(self.RCJKI.currentFont.deepComponentSet)

#         self.w.custom.remind = TextBox(
#             (10, 10, -10, 20),
#             "Glyphs names (separate with space) or characters",
#             sizeStyle = 'small'
#             )
#         self.w.custom.characterField = TextEditor(
#             (10, 30, -10, -50),
#             ""
#             )
#         self.w.custom.relatedDeepComponents = CheckBox(
#             (10, -60, -10, -10),
#             "Create related deep components",
#             value = True,
#             sizeStyle = "small"
#             )
#         self.lockNewGlyph = True
#         self.w.custom.lockNewGlyphs = CheckBox(
#             (10, -25, -10, -10),
#             "Lock new glyphs",
#             value = self.lockNewGlyph,
#             sizeStyle = "small",
#             callback = self.lockNewGlyphsCallback
#             )
#         self.w.custom.addButton = Button(
#             (-195, -30, -30, -10),
#             "Add",
#             callback = self.addButtonCallback,
#             )

#         self.w.related.deepComponentsTitle = TextBox(
#             (10, 10, -10, 20),
#             "Deep Components",
#             sizeStyle = 'small'
#             )
#         checkBoxList = CheckBoxListCell()
#         self.deepComponentList = []
#         for n in self.RCJKI.currentFont.deepComponentSet:
#             if not n.startswith("DC"): continue
#             try:
#                 int(n.split('_')[1], 16) in range(0x110000)
#             except:continue
#             cell = dict(sel = 0, char = chr(int(n.split('_')[1], 16)))
#             if cell not in self.deepComponentList:
#                 self.deepComponentList.append(cell)

#         self.w.related.searchBox = SearchBox(
#             (10, 30, 100, 20),
#             "",
#             callback = self.relatedDCSearchBox
#             )

#         self.w.related.deepComponentsList = List(
#             (10, 50, 100, -40),
#             self.deepComponentList,
#             columnDescriptions = [
#                 {"title":"sel", "cell":checkBoxList, "width":20}, 
#                 {"title":"char"}
#                 ],
#             drawFocusRing = False,
#             showColumnTitles = False,
#             editCallback = self.deepComponentsListEditCallback
#             )
#         self.w.related.characterField = TextEditor(
#             (110, 30, -10, -60),
#             "",
#             readOnly = True
#             )
#         self.w.related.addfromField = Button(
#             (110, -60, -10, -40),
#             "Add",
#             callback = self.addfromFieldCallback
#             )
#         self.w.related.lockNewGlyphs = CheckBox(
#             (10, -25, -10, -10),
#             "Lock new glyphs",
#             value = self.lockNewGlyph,
#             sizeStyle = "small",
#             callback = self.lockNewGlyphsCallback
#             )
#         self.w.related.addAllPossibleButton = Button(
#             (-225, -30, -30, -10),
#             "Add all possible characters",
#             callback = self.addAllPossibleCallback
#             )
#         self.w.closeButton = SquareButton(
#             (-30, -30, -10, -10),
#             "x",
#             callback = self.closeCallback,
#             sizeStyle = "small"
#             )
#         self.w.closeButton.getNSButton().setFocusRingType_(1)
#         self.w.closeButton.getNSButton().setBackgroundColor_(transparentColor)
#         self.w.closeButton.getNSButton().setBordered_(False)

#         self.w.open()

#     def lockNewGlyphsCallback(self, sender):
#         self.lockNewGlyph = sender.get()

#     def addGlyph(self, name, addRelatedDC=False):
#         added = set()
#         try:
#             self.RCJKI.currentFont[name]
#             return [name]
#         except:
#             self.RCJKI.currentFont.newGlyph("characterGlyph", name)
#             added.add(name)
#             if addRelatedDC and self.RCJKI.currentFont.dataBase:
#                 dcChars = self.RCJKI.currentFont.selectDatabaseKey(name[3:])
#                 DC = set(["DC_%s_00"%hex(ord(c))[2:].upper() for c in dcChars])
#                 # for name in DC:
#                 #     added.add(name)
#                 for name in DC-self.DCSet:
#                     try:
#                         self.RCJKI.currentFont[name]
#                     except:
#                         added.add(name)
#                         self.RCJKI.currentFont.newGlyph("deepComponent", name)
#             return list(added)

#     def addButtonCallback(self, sender):
#         addRelatedDC = self.w.custom.relatedDeepComponents.get()
#         txt = self.w.custom.characterField.get().split(" ")
#         glyphs = []
#         for e in txt:
#             if e.startswith("uni"):
#                 for dcname in self.addGlyph(e, addRelatedDC):
#                     glyphs.append(self.RCJKI.currentFont[dcname])
#             else:
#                 for c in e:
#                     name = files.unicodeName(c)
#                     for dcname in self.addGlyph(name, addRelatedDC):
#                         glyphs.append(self.RCJKI.currentFont[dcname])
#         # self.lockGlyphs(glyphs)
#         self.window.deepComponent.set(self.RCJKI.currentFont.deepComponentSet)
#         charSet = [dict(char = files.unicodeName2Char(x), name = x) for x in self.RCJKI.currentFont.characterGlyphSet]
#         self.window.characterGlyph.setSelection([])
#         self.window.characterGlyph.set(charSet)
#         self.w.close()

#     def lockGlyphs(self, glyphs):
#         if self.lockNewGlyph:
#             # lock = self.RCJKI.currentFont.locker.batchLock(glyphs)
#             if not self.RCJKI.currentFont.mysql:
#                 lock = self.RCJKI.currentFont.batchLockGlyphs(glyphs)
#             else:
#                 lock = self.RCJKI.currentFont.batchLockGlyphs([g.name for g in glyphs])
#             PostBannerNotification("Lock %s"%["failed", "succeeded"][lock], "")

#     def relatedDCSearchBox(self, sender):
#         char = sender.get()
#         for i, item in enumerate(self.deepComponentList):   
#             if item["char"] == char:
#                 self.w.related.deepComponentsList.setSelection([i])
#                 break

#     def deepComponentsListEditCallback(self, sender):
#         deepComponents = []
#         for i, e in enumerate(sender.get()):
#             if e["sel"]:
#                 deepComponents.append(self.deepComponentList[i]["char"])
#         characters = self.getRelatedCharacterToSelected(deepComponents) 
#         self.w.related.characterField.set(characters)

#     def addfromFieldCallback(self, sender):
#         characters = self.w.related.characterField.get()
#         glyphs = []
#         for character in characters:
#             name = files.unicodeName(character)
#             for dcname in self.addGlyph(name):
#                 glyphs.append(self.RCJKI.currentFont[dcname])
#         # self.lockGlyphs(glyphs)
#         print("-----------------")
#         print("ADDED CHARACTERS: \n%s"%characters)
#         print("-----------------")
#         self.w.close()

#     def addAllPossibleCallback(self, sender):
#         deepComponents = [e["char"] for e in self.deepComponentList]
#         characters = self.getRelatedCharacterToSelected(deepComponents)
#         glyphs = []
#         for character in characters:
#             name = files.unicodeName(character)
#             for dcname in self.addGlyph(name):
#                 glyphs.append(self.RCJKI.currentFont[dcname])
#         # self.lockGlyphs(glyphs)
#         print("-----------------")
#         print("ADDED CHARACTERS: \n%s"%characters)
#         print("-----------------")
#         self.w.close()

#     def getRelatedCharacterToSelected(self, deepComponents):
#         relatedChars = set()
#         deepComponentsSet = set(deepComponents)
#         for k, v in self.RCJKI.currentFont.dataBase.items():
#             setv = set(v)
#             if setv & deepComponentsSet:
#                 if not setv - deepComponentsSet:
#                     relatedChars.add(k)
#         return "".join(sorted(list(relatedChars)))

#     def closeCallback(self, sender):
#         self.w.close()

#     def segmentedButtonCallback(self, sender):
#         for i, g in enumerate(self.groups):
#             g.show(i == sender.get())

class Login:

    def __init__(self, RCJKI, parentWindow):
        self.RCJKI = RCJKI
        self.parentWindow = parentWindow
        self.w = Sheet((400, 200), parentWindow)

        self.w.segmentedButton = SegmentedButton(
            (10, 10, -10, 20),
            [dict(title = "mySQL"), dict(title = "Git")],
            callback = self.segmentedButtonCallback
            )
        self.w.segmentedButton.set(0)
        self.w.git = Group((0, 30, -0, -0))
        self.w.git.show(not self.RCJKI.mysql)
        self.w.mysql = Group((0, 30, -0, -0))
        self.w.mysql.show(self.RCJKI.mysql)

        self.w.git.userNameTitle = TextBox(
            (10, 10, 100, 20),
            "UserName"
            )
        self.w.git.userName = EditText(
            (90, 10, -10, 20),
            getExtensionDefault(blackrobocjk_locker+"username", "")
            )
        self.w.git.passwordTitle = TextBox(
            (10, 40, 100, 20),
            "Password"
            )
        self.w.git.password = SecureEditText(
            (90, 40, -10, 20),
            getExtensionDefault(blackrobocjk_locker+"password", "")
            )
        self.w.git.hostlockerTitle = TextBox(
            (10, 70, 100, 20),
            "HostLocker"
            )
        self.w.git.hostlocker = EditText(
            (90, 70, -10, 20),
            getExtensionDefault(blackrobocjk_locker+"hostlocker", "")
            )
        self.w.git.hostLockerPasswordTitle = TextBox(
            (10, 100, 200, 20),
            "HostLocker password optional"
            )
        self.w.git.hostLockerPassword = SecureEditText(
            (200, 100, -10, 20),
            getExtensionDefault(blackrobocjk_locker+"hostlockerpassword", "")
            )
        self.w.cancelButton = Button(
            (10, -30, 100, -10),
            "Cancel",
            callback = self.cancelCallback
            )
        self.w.closeButton = Button(
            (110, -30, -10, -10),
            "Login",
            callback = self.closeCallback
            )

        self.w.mysql.userNameTitle = TextBox(
            (10, 10, 100, 20),
            "UserName"
            )
        self.w.mysql.userName = EditText(
            (90, 10, -10, 20),
            getExtensionDefault(blackrobocjk_locker+"mysql_username", "")
            )
        self.w.mysql.passwordTitle = TextBox(
            (10, 40, 100, 20),
            "Password"
            )
        self.w.mysql.password = SecureEditText(
            (90, 40, -10, 20),
            getExtensionDefault(blackrobocjk_locker+"mysql_password", "")
            )
        self.w.mysql.hostTitle = TextBox(
            (10, 70, 100, 20),
            "Host"
            )
        self.w.mysql.host = EditText(
            (90, 70, -10, 20),
            getExtensionDefault(blackrobocjk_locker+"mysql_host", "")
            )
        # self.w.mysql.loadConnectorTitle = TextBox(
        #     (10, 70, 100, 20),
        #     "Load Connector"
        #     )
        # self.w.mysql.loadConnector = Button(
        #     (90, 70, -10, 20),
        #     "Load Connector",
        #     callback = self.loadConnectorCallback
        #     # getExtensionDefault(blackrobocjk_locker+"mysql_password", "")
        #     )

        self.w.setDefaultButton(self.w.closeButton)
        self.w.open()

    def loadConnectorCallback(self, sender):
        paths = getFile()
        path = paths[0]
        with open(path, 'r', encoding = 'utf-8') as file:
            connector = file.read()
        with open(connectorPath, 'w', encoding = 'utf-8') as file:
            file.write(connector)
        # print(connector)
        # print(self.__file__.__path__)

    def cancelCallback(self, sender):
        self.w.close()

    def closeCallback(self, sender):
        # if not self.w.git.userName.get() or not self.w.git.password.get() or not self.w.git.hostlocker.get(): return

        self.RCJKI.gitUserName = self.w.git.userName.get()
        self.RCJKI.gitPassword = self.w.git.password.get()
        self.RCJKI.gitHostLocker = self.w.git.hostlocker.get()
        self.RCJKI.gitHostLockerPassword = self.w.git.hostLockerPassword.get()

        setExtensionDefault(blackrobocjk_locker+"username", self.RCJKI.gitUserName)
        setExtensionDefault(blackrobocjk_locker+"password", self.RCJKI.gitPassword)
        setExtensionDefault(blackrobocjk_locker+"hostlocker", self.RCJKI.gitHostLocker)
        setExtensionDefault(blackrobocjk_locker+"hostlockerpassword", self.RCJKI.gitHostLockerPassword)
        self.w.close()
        
        if not self.RCJKI.mysql:
            folder = getFolder()
            if not folder: return
            self.RCJKI.projectRoot = folder[0]
            self.RCJKI.setGitEngine()
            self.RCJKI.roboCJKView.setrcjkFiles()
        else:
            self.RCJKI.mysql_userName = self.w.mysql.userName.get()
            self.RCJKI.mysql_password = self.w.mysql.password.get()
            self.RCJKI.mysql_host = self.w.mysql.host.get()
            setExtensionDefault(blackrobocjk_locker+"mysql_username", self.RCJKI.mysql_userName)
            setExtensionDefault(blackrobocjk_locker+"mysql_password", self.RCJKI.mysql_password)
            setExtensionDefault(blackrobocjk_locker+"mysql_host", self.RCJKI.mysql_host)
            try:
                self.RCJKI.client = client.Client(self.RCJKI.mysql_host, self.RCJKI.mysql_userName, self.RCJKI.mysql_password)
                # return 
            except Exception as e:
                print(e)
                message("Warning, your credentials are wrong!")
                return
            # check = self.RCJKI.client.auth_token()
            # print('check', check)
            # if check["status"] != 200:
            #     print('login response:', check)
            #     message("Warning, your credentials are wrong!")
            #     return
            check = self.RCJKI.client._auth_token
            if not check:
                print('login response:', check)
                message("Warning, your credentials are wrong!")
                return
            self.RCJKI.projects = {x["name"]:x for x in self.RCJKI.client.project_list()["data"]}
            SelectMYSQLProjectSheet(self.RCJKI, self.parentWindow)
        

    def segmentedButtonCallback(self, sender):
        for i, x in enumerate([self.w.mysql, self.w.git]):
            x.show(i == sender.get())
        self.RCJKI.mysql = not sender.get()

localisation_suffix = sorted(['', '.C_xtjk.xxxk', '.C_xxjk.xxjx', '.V_xxjx*0', '.C_xxjk.xxjk', '.C_htjk.C_xtxx.xtxx', '.A_htjx', '.E_xtjk*0.E_xtjk*0', '.C_xxxk.xxxk', '.C_hxjx.xxjx', '.A_htjk', '.C_xtjk.htxx', '.C_htjx.xxjk', '.A_xtxk', '.E_xxjx*0', '.A_xxjx.A_xxjx', '.C_xtxx.xtxx', '.A_xxxk', '_C.hxxx.hxxx', '.xtxx', '.A_xxjk', '.xtjk', '.C_hxjk.xxjx', '.V_htjk*0', '.C_htjk.hxxx', '.C_xtxx.htxx', '.E_htxx*0', '.C_htjk.xxjk', '.L_xtjk*0', '.V_xxjx*1', '.A_xtxx', '.C_htxk.xtxx', '.C_xxxx.xxxk', '.C_htjx.xtxx', '.L_htxx*0', '.E_hxjk*0', '.C_xtxk.xxxk', '.A_hxjk', '.L_hxjx*0', '.C_htxk.htxx', '.E_hxjx*0', '.V_htxx*0.V_htxx', '.C_htxk.xxxk', '.C_htjk.htxk', '.V_htxx*1', '.C_htxx.xtxx', '.A_hxxx*0', '.C_xxjx.xxxk', '.C_hxjk.xxjk', '.E_htjx*0', '.C_htjx.hxxx', '.hxjx', '.A_hxxx', '.V_xxjk*1', '.C_xtjx.xxjk', '.htjx', '.E_xtjk*0', '.E_htxx', '.C_xxxk.xxjk', '.htjk', '.xtxk', '.C_htjk.htxx', '.C_htxk.hxxx', '.A_xxjx', '.V_xxjk*0k', '.C_hxxx.hxxx', '.C_htxx.htjk', '.V_htjk*1', '.E_hxxk*0', '.V_htjx', '.C_xtjk.xxjx', '.C_xtjk.xxjk', '.V_hxxk*0', '.xtjx', '.C_xtjx.xtxx', '.htxx', '.A_hxxk', '.V_xxjk*0', '.V_xtjk*0', '.L_hxjk*0', '.V_xtxx*0', '.V_htxx*0.V_htxx*0', '.A_xtjx', '.L_xtxx*1', '.A_xtxx*0', '.C_hxjx.hxxx', '.C_xtjk.xtjk', '.C_hxjk.xxxk', '.xxjx', '.V_hxxx*0', '.E_xxjx', '.C_htxx.htxx', '.C_xtjx.xxjx', '.A_xxjk*1', '.A_xxjk_xxjk', '.E_xtxx*1', '.C_htjk.htjk', '.hxxk', '.hxjk', '.E_xtxx*0', '.C_htjx.xxjx', '.C_xxjx.xxjk', '.C_htjk.xxxk', '.L_xtxx*2', '.C_xtxk.xtxk', '.L_xxjk*0', '.A_htxx', '.C_htjk.hxjk', '.C_xtjk.xtxx', '.L_xxjx*0', '.L_htjk*0', '.V_htxx*0.A_xtxx', '.C_htjk.xxjx', '.C_htjx.htxx', '.C_htxx.hxxx', '.V_hxjk*0', '.C_xxjk.C_xxjk.xxjx', '.xxxk', '.E_xxjk*0', '.C_htjk.xtxx', '.E_xxxk*0', '.E_hxxx*0', '.A_xtjk.A_xtjx', '.L_hxxx*0', '.L_xtxx*0', '.A_xxjk*0', '\x13.C_htxx.htxx', '.L_xxxk*0', '.V_xtxx*1', '.xxjk', '.V_xxjk*0.A_xxjk', '.V_htxx*0', '.L_xtjx*0', '.L_xxjk*1', '.htxk', '.hxxx', '.C_hxxk.hxxk', '.A_xxjk.A_xxjk', '.L_htxx*1', '.C_xxjx.xxjx', '.A_xtjk', '.V_htjx*0', '.C_xtxk.xtxx', '.C_htjk.htjx', '.A_xtxk.A_xtxk', '.V_xxxk*0', '.E_htjk*0', '.C_xxjk.xxxk', '.C_hxjk.hxxx'])

class LocaliseGlyphSheet:

    def __init__(self, RCJKI, controller, parentWindow, glyphName, dependencies_glyphset = None, glyphset = None, sender = None):
        self.RCJKI = RCJKI
        self.controller = controller
        self.glyphName = glyphName
        self.databaseKeys = set(self.RCJKI.currentFont.dataBase.keys())
        self.dependencies_glyphset = dependencies_glyphset
        self.glyphset = glyphset
        self.sender = sender
        self.selectedSuffix = ""
        
        self.glyph = self.RCJKI.currentFont[self.glyphName]

        if self.glyph.type != "atomicElement":
            self.w = Sheet((500, 60+30*(len(self.glyph._deepComponents)+1)), parentWindow)
        else:
            self.w = Sheet((500, 90), parentWindow)

        existingSuffix = set([x[len(self.glyph.name):] for x in glyphset() if self.glyph.name in x])
        self.available_localisation_suffix = ["Choose suffix"]+sorted(list(set(localisation_suffix)-existingSuffix))

        self.w.glyphNameSuffix = TextBox((120, 10, -100, 20), "suffix:", sizeStyle = "small")
        self.w.glyphName = TextBox((10, 30, 150, 20), self.glyph.name)
        self.w.glyphNameExtension = PopUpButton((255, 30, -10, 20), self.available_localisation_suffix, callback = self.glyphNameExtensionCallback)
        self.w.glyphNameExtensionEditText = EditText((120, 30, 135, 20), "", callback = self.glyphNameExtensionEditTextCallback)

        if self.glyph.type != "atomicElement":
            y = 60
            for i, deepComponent in enumerate(self.glyph._deepComponents):
                try:
                    glyphName = TextBox((10, y, 150, 20), "%s %s"%(chr(int(deepComponent["name"].split('_')[1], 16)),deepComponent["name"]))
                except:
                    glyphName = TextBox((10, y, 150, 20), deepComponent["name"])
                self.availableSuffix = ["Choose suffix (optional)"]+["."+getSuffix(x) for x in dependencies_glyphset if "." in x and x.split(".")[0] == deepComponent["name"]]
                glyphNameExtension = PopUpButton((255, y, -10, 20), self.availableSuffix, callback = self.popUpButtonCallback)
                glyphNameExtensionEditText = EditText((120, y, 135, 20), '', callback = self.editTextCallback)
                setattr(self.w, deepComponent["name"]+str(i), glyphName)
                if len(self.availableSuffix)>1:
                    setattr(self.w, f"{deepComponent['name']}Extension{i}", glyphNameExtension)
                    setattr(self.w, f"{deepComponent['name']}ExtensionEditText{i}", glyphNameExtensionEditText)
                else:
                    setattr(self.w, f"{deepComponent['name']}Extension{i}", TextBox((120, y, -10, 20), "No suffix available", sizeStyle = "small"))
                y+=30

        self.w.cancelButton = Button((0, -20, 150, 20), "Cancel", callback = self.cancelButtonCallback)
        self.w.localiseGlyphButton = Button((-150, -20, -0, 20), "Localise", callback = self.localiseButtonCallback)
        self.w.setDefaultButton(self.w.localiseGlyphButton)
        self.w.open()

    def glyphNameExtensionCallback(self, sender):
        t = sender.getItem()
        if t != "Choose suffix":
            self.w.glyphNameExtensionEditText.set(t)

    def glyphNameExtensionEditTextCallback(self, sender):
        name = sender.get()
        if name in self.available_localisation_suffix:
            self.w.glyphNameExtension.set(self.available_localisation_suffix.index(name))
        if not name.startswith("."):
            name = "."+name
        dataname = "%s%s"%(chr(int(self.glyphName["name"][3:], 16)), name)
        if dataname in self.databaseKeys:
            glyphComposition = [x for x in self.RCJKI.currentFont.dataBase[dataname].split(" ") if x]
            for i, deepComponent in enumerate(self.glyph._deepComponents):
                dcchar = chr(int(deepComponent['name'].split("_")[1], 16))
                count = 0
                for x in glyphComposition:
                    if x[0] == dcchar:
                        count+=1
                if count > 1: continue
                index = None
                for j, c in enumerate(glyphComposition):
                    if c[0] == dcchar and '.' in c:
                        index = j
                        suf = c[1:]
                        if deepComponent['name']+suf in self.RCJKI.currentFont.staticDeepComponentSet():
                            suflist = getattr(self.w, f"{deepComponent['name']}Extension{i}").getItems()
                            if suf in suflist:
                                getattr(self.w, f"{deepComponent['name']}ExtensionEditText{i}").set(suf)
                                getattr(self.w, f"{deepComponent['name']}Extension{i}").set(suflist.index(suf))
                if index is not None:
                    glyphComposition = [x for i, x in enumerate(glyphComposition) if i != index]
        else:
            for i, deepComponent in enumerate(self.glyph._deepComponents):
                try:
                    getattr(self.w, f"{deepComponent['name']}ExtensionEditText{i}").set("")
                    getattr(self.w, f"{deepComponent['name']}Extension{i}").set(0)
                except:
                    getattr(self.w, f"{deepComponent['name']}Extension{i}").set("No suffix available")

    def editTextCallback(self, sender):
        if self.glyph.type != "atomicElement":
            for i, deepComponent in enumerate(self.glyph._deepComponents):
                if not hasattr(self.w, f"{deepComponent['name']}ExtensionEditText{i}"):continue
                name = getattr(self.w, f"{deepComponent['name']}ExtensionEditText{i}").get()
                popup = getattr(self.w, f"{deepComponent['name']}Extension{i}")
                suf = getattr(self.w, f"{deepComponent['name']}Extension{i}").getItems()
                if name in suf:
                    popup.set(suf.index(name))

    def popUpButtonCallback(self, sender):
        if self.glyph.type != "atomicElement":
            for i, deepComponent in enumerate(self.glyph._deepComponents):
                if not hasattr(self.w, f"{deepComponent['name']}ExtensionEditText{i}"):continue
                editText = getattr(self.w, f"{deepComponent['name']}ExtensionEditText{i}")
                popup = getattr(self.w, f"{deepComponent['name']}Extension{i}")
                name = getattr(self.w, f"{deepComponent['name']}Extension{i}").getItem()
                editText.set(name)

    def cancelButtonCallback(self, sender):
        self.w.close()

    def localiseButtonCallback(self, sender):
        self.selectedSuffix = self.w.glyphNameExtensionEditText.get()
        if self.selectedSuffix == "" or self.selectedSuffix == "Choose suffix":
            return ""
        if " " in self.selectedSuffix or "\n" in self.selectedSuffix:
            message("Warning wrong character(s) in the given suffix")
            return ""
        if not self.selectedSuffix.startswith("."):
            self.selectedSuffix = f".{self.selectedSuffix}"
        newGlyphName = self.glyph.name + self.selectedSuffix
        self.RCJKI.currentFont.duplicateGlyph(self.glyph.name, newGlyphName)
        ####
        self.RCJKI.currentFont.markGlyph(newGlyphName, colors.STATUS_COLORS[colors.CHECKING1_name], colors.CHECKING1_name)
        ####
        if not self.RCJKI.currentFont.mysql:
            self.RCJKI.currentFont.batchLockGlyphs([self.RCJKI.currentFont[newGlyphName]])
        else:
            self.RCJKI.currentFont.batchLockGlyphs([newGlyphName])
        torename = {}
        if self.glyph.type != "atomicElement":
            for i, deepComponent in enumerate(self.glyph._deepComponents):
                if not hasattr(self.w, f"{deepComponent['name']}ExtensionEditText{i}"):continue
                element = getattr(self.w, f"{deepComponent['name']}ExtensionEditText{i}")
                if element.__class__.__name__ == "TextBox": continue
                ext = element.get()
                if ext == "Choose suffix (optional)" or ext == "": continue
                if ext.startswith("."): ext = ext[1:]
                torename[i] = deepComponent["name"]+'.'+ext
                # self.RCJKI.currentFont[newGlyphName].renameDeepComponent(i, deepComponent["name"]+'.'+ext)
        for i in sorted(list(torename.keys()), reverse=True):
            self.RCJKI.currentFont[newGlyphName].renameDeepComponent(i, torename[i])
        self.w.close()
        index = sorted(list(self.glyphset(update = True))).index(newGlyphName)
        self.sender.setSelection([])
        if self.sender == self.controller.w.characterGlyph:
            self.sender.set([dict(char = files.unicodeName2Char(x), name = x) for x in sorted(list(self.glyphset()))])
        else:
            self.sender.set(sorted(list(self.glyphset())))
        self.sender.setSelection([index])

class SelectMYSQLProjectSheet:

    def __init__(self, RCJKI, parentWindow):
        self.w = Sheet((340, 230), parentWindow)
        self.RCJKI = RCJKI
        self.projectList = sorted(list(self.RCJKI.projects.keys()))
        self.w.selectProject = TextBox((10, 10, -10, 20), "Select a project", sizeStyle ="small", alignment = "center")
        self.w.projectsList = List((10, 40, -10, -60), self.projectList)
        self.w.newProjectButton = Button((10, -60, -10, -40), "new project", sizeStyle = "small", callback = self.newProjectCallback)
        self.w.openProject = Button((170, -30, -10, 20), "Open", sizeStyle = "small", callback = self.openProjectCallback)
        self.w.cancel = Button((10, -30, 160, 20), "cancel", sizeStyle = "small", callback = self.cancelProjectCallback)
        self.w.setDefaultButton(self.w.openProject)
        self.w.open()

    def newProjectCallback(self, sender):
        project_name = AskString('', value = "Choose a font name", title = "Font Name")
        repo_url = AskString('', value = "Give a valid Repository url", title = "Repository url")
        response = self.RCJKI.client.project_create(project_name, repo_url)
        print(response)
        self.RCJKI.projects = {x["name"]:x for x in self.RCJKI.client.project_list()["data"]}
        self.projectList = sorted(list(self.RCJKI.projects.keys()))
        self.w.projectsList.set(self.projectList)

    def openProjectCallback(self, sender):
        sel = self.w.projectsList.getSelection()
        if not sel:
            return
        selectedProjectName = self.projectList[sel[0]]
        self.RCJKI.currentProjectUID = self.RCJKI.projects[selectedProjectName]['uid']
        self.RCJKI.fontsList = {x["name"]:x for x in self.RCJKI.client.font_list(self.RCJKI.currentProjectUID)["data"]}
        self.RCJKI.roboCJKView.setmySQLRCJKFiles()
        self.w.close()

    def cancelProjectCallback(self, sender):
        self.w.close()

class LockController:

    def __init__(self, RCJKI, parentWindow):
        self.RCJKI = RCJKI
        self.w = Sheet((340, 230), parentWindow)
        self.w.unlock = Group((0, 30, -0, -0))
        self.w.unlock.show(False)
        self.w.lock = Group((0, 30, -0, -0))
        self.locksGroup = [self.w.lock, self.w.unlock]
        self.w.segmentedButton = SegmentedButton(
            (10, 10, -10, 20),
            [dict(title = "Lock"), dict(title = "Unlock")],
            callback = self.segmentedButtonCallback
            )
        self.w.segmentedButton.set(0)
        self.w.lock.remind = TextBox(
            (10, 10, -10, 20),
            "Glyphs names (separate with space) or characters",
            sizeStyle = 'small'
            )
        self.w.lock.field = TextEditor(
            (10, 30, -10, -40),
            ""
            )
        self.w.lock.lockButton = Button(
            (10, -30, -30, 20),
            'lock',
            callback = self.lockButtonCallback
            )
        self.w.unlock.searchBox = SearchBox(
            (10, 10, 150, 20),
            callback = self.filterListCallback
            )
        self.currentGlyphName = None
        # self.lockedList = [dict(sel = 0, name = x) for x in self.RCJKI.currentFont.locker.myLockedGlyphs]
        self.lockedList = [dict(sel = 0, name = x) for x in self.RCJKI.currentFont.currentUserLockedGlyphs()]
        self.lockedList = []
        self.w.unlock.lockedGlyphsList = List(
            (10, 30, 150, -40),
            self.lockedList,
            columnDescriptions = [dict(title = "sel", cell = CheckBoxListCell(), width = 20), dict(title = "name")],
            showColumnTitles = False,
            allowsMultipleSelection = False,
            drawFocusRing = False,
            selectionCallback = self.lockedGlyphsListSelectionCallback
            )
        self.w.unlock.canvas = Canvas(
            (160, 10, -10, -40),
            delegate = self
            )
        self.w.unlock.unlockSelectedButton = Button(
            (10, -30, 150, -10),
            "Unlock selected",
            callback = self.unlockSelectedButtonCallback
            )
        self.w.unlock.unlockAllButton = Button(
            (160, -30, 150, -10),
            "Unlock all",
            callback = self.unlockAllButtonCallback
            )
        self.w.closeButton = SquareButton(
            (-30, -30, -0, -10),
            "x",
            callback = self.closeCallback
            )
        self.w.closeButton.getNSButton().setFocusRingType_(1)
        self.w.closeButton.getNSButton().setBackgroundColor_(transparentColor)
        self.w.closeButton.getNSButton().setBordered_(False)

        if self.lockedList:
            self.w.unlock.lockedGlyphsList.setSelection([0])
            self.lockedGlyphsListSelectionCallback(self.w.unlock.lockedGlyphsList)
        else:
            self.w.unlock.lockedGlyphsList.setSelection([])

    def segmentedButtonCallback(self, sender):
        for i, group in enumerate(self.locksGroup):
            group.show(i == sender.get())
        if sender.get():
            self.resetList()

    def lockedGlyphsListSelectionCallback(self, sender):
        sel = sender.getSelection()
        if not sel:
            self.currentGlyphName = None
            return
        self.currentGlyphName = sender.get()[sel[0]]["name"]
        self.w.unlock.canvas.update()

    def lockGlyphs(self, glyphs):
        # lock = self.RCJKI.currentFont.locker.batchLock(glyphs)
        lock = self.RCJKI.currentFont.batchLockGlyphs(glyphs)
        PostBannerNotification("Lock %s"%["failed", "succeeded"][lock], "")

    def lockButtonCallback(self, sender):
        f = self.RCJKI.currentFont
        txt = self.w.lock.field.get().split()
        if not f.mysql:
            glyphs = []
            for e in txt:
                try:
                    glyphs.append(self.RCJKI.currentFont[e])
                except:
                    for c in e:
                        try: glyphs.append(self.RCJKI.currentFont[files.unicodeName(c)])
                        except: continue
            self.lockGlyphs(glyphs)
        else:
            names = [x for x in txt if x in f.staticAtomicElementSet()|f.staticDeepComponentSet()|f.staticCharacterGlyphSet()]
            f.batchLockGlyphs(names)

    def unlockSelectedButtonCallback(self, sender):
        f = self.RCJKI.currentFont
        glyphs = []
        filesToRemove = []
        if not f.mysql:
            for x in self.w.unlock.lockedGlyphsList.get():
                if x["sel"]:
                    try:    
                        glyphs.append(f[x["name"]])
                    except:
                        filesToRemove.append(x["name"])
        else:
            for x in self.w.unlock.lockedGlyphsList.get():
                if x["sel"]:
                    glyphs.append(x["name"])
        # self.RCJKI.currentFont.locker.removeFiles(filesToRemove)
        self.RCJKI.currentFont.removeLockerFiles(filesToRemove)
        if glyphs:
            self.unlockGlyphs(glyphs)
        self.resetList()

    def resetList(self):
        # self.lockedList = [dict(sel = 0, name = x) for x in self.RCJKI.currentFont.locker.myLockedGlyphs]
        self.lockedList = [dict(sel = 0, name = x) for x in self.RCJKI.currentFont.currentUserLockedGlyphs()]
        self.w.unlock.lockedGlyphsList.set(self.lockedList)
        self.w.unlock.lockedGlyphsList.setSelection([])
        self.currentGlyphName = None
        self.w.unlock.canvas.update()

    def unlockGlyphs(self, glyphs):
        # unlock = self.RCJKI.currentFont.locker.batchUnlock(glyphs)
        unlock = self.RCJKI.currentFont.batchUnlockGlyphs(glyphs)
        PostBannerNotification("Unlock %s"%["failed", "succeeded"][unlock], "")

    def unlockAllButtonCallback(self, sender):
        f = self.RCJKI.currentFont
        if not f.mysql:
            glyphs = []
            filesToRemove = []
            for x in self.w.unlock.lockedGlyphsList.get():
                try: glyphs.append(f[x["name"]])
                except: 
                    filesToRemove.append(x["name"])
            # self.RCJKI.currentFont.locker.removeFiles(filesToRemove)
            self.RCJKI.currentFont.removeLockerFiles(filesToRemove)
            self.unlockGlyphs(glyphs)
        else:
            names = [x["name"] for x in self.w.unlock.lockedGlyphsList.get()]
            f.batchUnlockGlyphs(names)
        self.resetList()        

    def filterListCallback(self, sender):
        if not sender.get():
            l = self.lockedList
        else:
            try:
                name = files.unicodeName(sender.get())
            except:
                name = str(sender.get())
            lockedNames = [x["name"] for x in self.lockedList]
            l = [dict(sel = 0, name = x) for x in files._getFilteredListFromName(lockedNames, name)]
        if not l:
            l = self.lockedList

        self.w.unlock.lockedGlyphsList.set(l)
        self.w.unlock.lockedGlyphsList.setSelection([])

    def draw(self):
        if self.currentGlyphName is None: return
        glyph = self.RCJKI.currentFont[self.currentGlyphName]
        mjdt.save()
        s = .1
        mjdt.scale(s, s)
        mjdt.translate(350, 350)
        if glyph.type != "atomicElement":
            # glyph.preview.computeDeepComponents(update = False)
            self.RCJKI.drawer.drawAxisPreview(
                glyph,
                (0, 0, 0, 1),
                s,
                (0, 0, 0, 1)
                )
        mjdt.drawGlyph(glyph)
        mjdt.restore()

    def open(self):
        self.w.open()

    def closeCallback(self, sender):
        self.w.close()

import uuid, math
from collections import defaultdict
from mojo.roboFont import *
from fontTools.ufoLib.pointPen import SegmentToPointPen, PointToSegmentPen
import colorsys
from fontTools.pens.cocoaPen import CocoaPen
# from AppKit import *

class FixGlyphCompatibility:

    def __init__(self, RCJKI, currentGlyph):
        self.RCJKI = RCJKI
        self.currentGlyph = currentGlyph
        self.defaultWidth = self.RCJKI.currentFont.defaultGlyphWidth
        self.resultGlyph = None
        self.secondGlyph = None
        self.interpo = None
        self.interpoValue = .5
        self.setStartPoint = True

        self.parent = CurrentGlyphWindow()
        self.sheetWidth, self.sheetHeight = 800, 400
        self.parent.sheet = Sheet((self.sheetWidth, self.sheetHeight), self.parent.w)

        self.parent.sheet.applyButton = Button(
            (400, -20, -0, -0),
            "Apply",
            callback = self.applyButtonCallback
            )
        self.parent.sheet.cancelButton = Button(
            (0, -20, 400, -0),
            "Cancel",
            callback = self.cancelButtonCallback
            )
        self.parent.sheet.interpoValueSlider = Slider((10, -45, 200, 20),
            minValue = 0,
            maxValue = 1,
            value = .5,
            callback = self.interpoValueSliderCallback
            )
        self.parent.sheet.setStartPointCheckBox = CheckBox((230, -45, 200, 20),
            "set Start Point",
            value = self.setStartPoint,
            sizeStyle = 'small',
            callback = self.setStartPointCheckBoxCallback
            )
        variationsAxes = self.currentGlyph.glyphVariations.axes
        self.variationsGlyphs = [self.RCJKI.currentFont._RFont.getLayer(x)[self.currentGlyph.name] for x in variationsAxes]

        self.parent.sheet.canvas = Canvas((0, 0, -0, -50), delegate = self)
        # for i, g in self.variationsGlyphs:
        #     setattr(self.parent.sheet, str(i), DrawCompatibility(self.RCJKI, self, self.currentGlyph, g))
        # self.test()
        self.secondGlyph = self.variationsGlyphs[0]
        self.displayCombination(self.secondGlyph, self.setStartPoint)
        self.variationsGlyphs.pop(0)

        self.parent.sheet.open()

    # def test(self):
    #     g1 = self.currentGlyph._RGlyph
    #     g2 = self.variationsGlyphs[0]

    #     result = self.fixGlyphsCompatibility(g1, g2)
    #     f = NewFont()
    #     f.newGlyph(g1.name)
    #     for c in result:
    #         f[g1.name].appendContour(c)

    def interpoValueSliderCallback(self, sender):
        self.interpoValue = sender.get()
        self.parent.sheet.canvas.update()

    def setStartPointCheckBoxCallback(self, sender):
        self.setStartPoint = sender.get()
        self.displayCombination(self.secondGlyph, self.setStartPoint)
        self.parent.sheet.canvas.update()

    def displayCombination(self, g2, setStartPoint = True):
        self.resultGlyph = self.fixGlyphsCompatibility(self.currentGlyph._RGlyph, g2, setStartPoint)
        self.parent.sheet.canvas.update()

    def applyButtonCallback(self, sender):
        self.secondGlyph.clearContours()
        for c in self.resultGlyph:
            self.secondGlyph.appendContour(c)
        if not len(self.variationsGlyphs):
            self.parent.sheet.close()
        else:
            self.secondGlyph = self.variationsGlyphs[0]
            self.displayCombination(self.secondGlyph, self.setStartPoint)
            self.variationsGlyphs.pop(0)

    def cancelButtonCallback(self, sender):
        if not len(self.variationsGlyphs):
            self.parent.sheet.close()
        else:
            self.secondGlyph = self.variationsGlyphs[0]
            self.displayCombination(self.secondGlyph, self.setStartPoint)
            self.variationsGlyphs.pop(0)

    def draw(self):
        if self.resultGlyph is None: return
        interpo = interpolation.interpol_glyph_glyph_ratioX_ratioY_scaleX_scaleY(self.currentGlyph._RGlyph, self.resultGlyph, self.interpoValue, self.interpoValue, 1, 1, NewFont(showUI = False))
        glyphs = [self.currentGlyph, interpo, self.resultGlyph]
        s = .24

        colors = [colorsys.hsv_to_rgb(1.0*i/len(self.currentGlyph), .7, 1) for i in range(len(self.currentGlyph))]

        totalWidth = 3 * self.defaultWidth
        tx = (self.sheetWidth/s - totalWidth)*.5
        mjdt.scale(s, s)
        mjdt.translate(tx, 300)

        lineCap = NSButtLineCapStyle
        lineJoin = NSMiterLineJoinStyle
        width = 2

        def drawGlyph(g):
            mjdt.save()
            for i, c in enumerate(g):
                pen = CocoaPen(c)
                c.draw(pen)
                path = pen.path
                path.setLineWidth_(width)
                path.setLineCapStyle_(lineCap)
                path.setLineJoinStyle_(lineJoin)
                NSColor.colorWithCalibratedRed_green_blue_alpha_(*colors[i], .7).set()
                path.fill()
                px, py = c.points[0].x, c.points[0].y
                mjdt.fill(1, 0, 0, 1)
                mjdt.oval(px-2/s, py-2/s, 4/s, 4/s)
            mjdt.restore()

        for i, glyph in enumerate(glyphs):
            if i in [0, 2]:
                drawGlyph(glyph)
            else:
                if glyph:
                    mjdt.stroke(None)
                    mjdt.fill(0, 0, 0, 1)
                    mjdt.drawGlyph(glyph)
                else:
                    mjdt.stroke(None)
                    mjdt.fill(1, 0, 0, .8)
                    mjdt.oval(0, 0, self.defaultWidth, self.defaultWidth)
            if glyph:
                mjdt.translate(glyph.width)
            else:
                mjdt.translate(self.defaultWidth)

    def fixGlyphsCompatibility(self, g1: RGlyph, g2: RGlyph, setStartPoint: bool = True) -> RGlyph:
        """
        g2 will change in order to follow the g1's structure
        ------
        Dependencies:
            import math
            from mojo.roboFont import *
            from fontTools.ufoLib.pointPen import SegmentToPointPen, PointToSegmentPen
        """
        g1 = g1.copy()
        g2 = g2.copy()

        def centerDict(g):
            d = {}
            for c in g:
                x = c.box[0] + (c.box[2] - c.box[0])*.33    
                y = c.box[1] + (c.box[3] - c.box[1])*.33    
                d[c] = (x,y)
            return d 

        g1Center = centerDict(g1)
        g2Center = centerDict(g2)

        matchingG1 = {}
        for c1 in g1Center:
            rayDict = {}
            x1, y1 = g1Center[c1]
            for c2 in g2Center:
                x2, y2 = g2Center[c2]
                w, h = abs(x2 - x1), abs(y2 - y1)
                ray = math.hypot(w,h)
                rayDict[c2] = ray
            matchingG1[c1] = rayDict

        correspondence = {}
        for c1 in matchingG1:
            minRay = min(matchingG1[c1].values())
            for c2 in matchingG1[c1]:
                if matchingG1[c1][c2] == minRay:
                    correspondence[c1] = c2

        g2.clearContours()
        for c1 in g1:
            g2.appendContour(correspondence[c1])
        g2.update()

        if setStartPoint:
            rG = RGlyph()
            for c1, c2 in zip(g1, g2):
                boxX, boxY = c1.box[2] - c1.box[0], c1.box[3] - c1.box[1]
                boxX1, boxY1 = c2.box[2] - c2.box[0], c2.box[3] - c2.box[1]
            
                offX = (c2.box[0] + boxX1*.5) - (c1.box[0] + boxX*.5)
                offY = (c2.box[1] + boxY1*.5) - (c1.box[1] + boxY*.5)
            
                refPointList = [p for p in c2.points if p.type != "offcurve"]
                curStartPoint = c1.points[0]
                
                dictDistPoint = {}
                for i, p in enumerate(refPointList):
                    x = (p.x-curStartPoint.x) - offX
                    y = (p.y-curStartPoint.y) - offY
                    dist = math.hypot(x, y)
                    dictDistPoint[i] = dist
                
                d = sorted(dictDistPoint.values())[0]
                for i in dictDistPoint:
                    if dictDistPoint[i] == d:
                        minIndexPoint = i      
                index = 0
                count = 0
                for p in c2.points:
                    if p.type != "offcurve":
                        if p == refPointList[minIndexPoint]:
                            index = count
                        count +=1

                i = index
                if i < 0:
                    i = len(c2)-1

                pen = PointToSegmentPen(rG.getPen())
                oncurve = 0
                newPointsList = []
                pointsList = list(c2.points)
                for index, p in enumerate(pointsList):
                    if p.type != "offcurve":
                        oncurve += 1
                        if oncurve == i+1:
                            newPointsList.extend(pointsList[index:])
                            newPointsList.extend(pointsList[:index])
                pen.beginPath()
                for p in newPointsList:
                    px = p.x
                    py = p.y
                    ptype = p.type if p.type !="offcurve" else None
                    pen.addPoint((px, py), ptype)
                pen.endPath()

            g2.clearContours()
            for c in rG:
                g2.appendContour(c)

        return g2


    # def fixGlyphsCompatibility(self, g1: RGlyph, g2: RGlyph, setStartPoint:bool = True) -> RGlyph:
    #     """
    #     g2 will be change in order to follow the g1's structure
    #     ------
    #     Dependencies:
    #         import uuid, math
    #         from collections import defaultdict
    #         from mojo.roboFont import *
    #         from fontTools.ufoLib.pointPen import SegmentToPointPen, PointToSegmentPen
    #     """
    #     class ContourComposition:

    #         def __init__(self, center: tuple, contour: RContour, area: int):
    #             self.center = center
    #             self.contour = contour
    #             self.area = area

    #         def distance(self, c):
    #             w, h = abs(c.center[0] - self.center[0]), abs(c.center[1] - self.center[1])
    #             return math.hypot(w, h)

    #         def __repr__(self):
    #             return f"<center: {self.center}, contour: {self.contour}, area: {self.area}>"

    #     def getCompos(g: RGlyph) -> dict:
    #         compo = {}
    #         for c in g:
    #             b0, b1, b2, b3 = c.box
    #             cx, cy = b0 + (b2 - b0)*.5, b1 + (b3 - b1)*.5
    #             area = (b2 - b0)*(b3 - b1)
    #             uniqid = uuid.uuid4()
    #             compo[uniqid] = ContourComposition((cy, cy), c, area)
    #         return compo

    #     compo1 = getCompos(g1)
    #     compo2 = getCompos(g2)

    #     resultGlyph = RGlyph()
    #     added = set()

    #     for c1 in compo1.values():
    #         match = defaultdict(list)
    #         for uniqid2, c2 in compo2.items():
    #             d = c1.distance(c2)
    #             match[d].append([uniqid2, c2.contour])

    #         m = min(list(match.keys()))
    #         print(match.keys())
    #         print(m)
    #         for uniqid, contour in match[m]:
    #             if uniqid not in added:
    #             # if set([uniqid]) - added:
    #                 added.add(uniqid)
    #                 resultGlyph.appendContour(contour)
    #             # break

    #     print("------")
    #     print(added)
    #     print("------")

    #     if setStartPoint:
    #         g = RGlyph()
    #         pen = PointToSegmentPen(g.getPen())
    #         for c1, c2 in zip(g1, resultGlyph):
    #             boxX, boxY = c1.box[2] - c1.box[0], c1.box[3] - c1.box[1]
    #             boxX1, boxY1 = c2.box[2] - c2.box[0], c2.box[3] - c2.box[1]
            
    #             offX = (c2.box[0] + boxX1*.5) - (c1.box[0] + boxX*.5)
    #             offY = (c2.box[1] + boxY1*.5) - (c1.box[1] + boxY*.5)
            
    #             refPointList = [p for p in c2.points if p.type != "offcurve"]
    #             curStartPoint = c1.points[0]
                
    #             dictDistPoint = {}
    #             for i, p in enumerate(refPointList):
    #                 x = (p.x - curStartPoint.x) - offX
    #                 y = (p.y - curStartPoint.y) - offY
    #                 dist = math.hypot(x, y)
    #                 dictDistPoint[i] = dist
                
    #             d = min(list(dictDistPoint.values()))
    #             for i, v in dictDistPoint.items():
    #                 if v == d:
    #                     minIndexPoint = i      

    #             index, count = 0, 0
    #             for p in c2.points:
    #                 if p.type != "offcurve":
    #                     if p == refPointList[minIndexPoint]:
    #                         index = count
    #                     count +=1

    #             if index < 0:
    #                 index = len(c2)-1

    #             oncurve = 0
    #             newPointsList = []
    #             pointsList = list(c2.points)
    #             for i, p in enumerate(pointsList):
    #                 if p.type != "offcurve":
    #                     oncurve += 1
    #                     if oncurve == index + 1:
    #                         newPointsList.extend(pointsList[i:])
    #                         newPointsList.extend(pointsList[:i])

    #             pen.beginPath()
    #             for p in newPointsList:
    #                 px = p.x
    #                 py = p.y
    #                 ptype = p.type if p.type !="offcurve" else None
    #                 pen.addPoint((px, py), ptype)
    #             pen.endPath()

    #         resultGlyph.clearContours()
    #         for c in g:
    #             resultGlyph.appendContour(c)

    #     return resultGlyph


# class DrawCompatibility:

#     def __init__(self, RCJKI, sheet, g1, g2):
#         self.RCJKI = RCJKI
#         self.sheet = sheet
#         self.g1 = g1
#         self.g2 = g2

