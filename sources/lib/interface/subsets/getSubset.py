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

from vanilla import *
from vanilla.dialogs import message
from mojo.glyphPreview import GlyphPreview
from mojo.roboFont import *
from mojo.UI import AccordionView
from AppKit import NSColor
import shutil
from imp import reload

import os, json, subprocess, datetime, Helpers, getpass, time

reload(Helpers)
from Helpers import makepath, GitHelper, unique, deepolation , normalizeUnicode

class GetSubset_Sheet():

    def __init__(self, interface):
        self.ui = interface
        self.w = Sheet((200, 250), self.ui.w)

        self.w.deepComponents_textBox = TextBox((10, 10, -10, 20), 
            "Deep Components", 
            sizeStyle = "regular", 
            alignment = "center")

        
        # self.w.radioGroup = RadioGroup((10, 40, -10, 20), 
        #     ["Editor", "Instantiator"],
        #     isVertical = False,
        #     sizeStyle="small",
        #     callback = self._radioGroup_callback)

        self.w.searchBox = SearchBox((10, 70, -10, 20),
            placeholder = "Char/Name",
            sizeStyle = "small",
            callback = self._searchBox_callback)
        # self.w.searchBox.show(0)

        self.w.GlyphPreview = GlyphPreview((0, 105, -0, -30))

        self.selectedGlyph = None
        self.selectedGlyphName = None

        self.w.closeButton = Button((10, -30, 30, -10), 
            "X",
            callback = self._closeButtonCallback,
            sizeStyle = "small")

        self.w.getSubset_Button = Button((50, -30, -10, -10), 
            "Get Mini Font", 
            callback = self._getSubset_Button_callback,
            sizeStyle = "small")

        # deepCompoEditorData_path = "/Users/gaetanbaehr/Documents/BlackFoundry/TYPE/OTHER/git/TestRoboCJK2/settings/TEMP_deepComponentAxisCompo2charsAGB1_FULL_Edit.json"
        # self.deepCompoEditorData = json.load(open(deepCompoEditorData_path, "r"))
        
        # self.selectedSubsetOption = self.deepCompoEditorData

        Helpers.setDarkMode(self.w, self.ui.darkMode)

        self.w.open()

    def _closeButtonCallback(self, sender):
        self.w.close()

    # def _radioGroup_callback(self, sender):
    #     self.w.searchBox.show(1)
    #     if not sender.get():
    #         self.selectedSubsetOption = self.deepCompoEditorData
    #     else:
    #         self.selectedSubsetOption = self.ui.glyphCompositionData

    def _searchBox_callback(self, sender):
        string = sender.get()
        if not string: return
        try:
            if string.startswith("uni"):
                self.selectedGlyphName = string

            elif len(string) == 1:
                self.selectedGlyphName = "uni"+normalizeUnicode(hex(ord(string))[2:].upper())

            self.selectedGlyph = self.ui.font[self.selectedGlyphName]
        except:
            self.selectedGlyph = None
            self.selectedGlyphName = None

        self.w.GlyphPreview.setGlyph(self.selectedGlyph)

    def _getSubset_Button_callback(self, sender):
        # if self.selectedSubsetOption is None:
        #     message("Warning there is no seleted option")
        #     return

        if self.selectedGlyphName is None:
            message("Warning there is no chosen glyph")
            return

        if self.ui.designStep == 1:
            GetSubset(self.ui, self.selectedGlyphName, self.ui.deepComponentExtremsData, self)
            self.ui.collapse = 1
            self.ui.getSubset_UI()

class GetSubset():

    def __init__(self, interface, characterName, database, controller):
        self.ui = interface
        self.characterName = characterName
        self.database = database
        self.c = controller
        self.rdir = self.ui.projectPath
        self.makeSubsets()

    def writeJsonFile(self, name):
        path = os.path.join(self.rdir, f"resources/{name}.json")
        makepath(path)
        myFile = open(path, 'w')
        d = json.dumps(getattr(self, name), indent=4, separators=(',', ':'))
        myFile.write(d)
        myFile.close()

    def makeSubsets(self):
        f = self.ui.font
        if 'temp' in f.path:
            message("ERROR: you are tring to get mini font over a mini font")
            return
        
        git = GitHelper(self.rdir)
        if not git.pull(): return
        user = git.user()

        fontsPaths = [font.path for font in self.ui.fonts.values()]

        dt = datetime.datetime.today()
        stamp = str(dt.year) + str(dt.month) + str(dt.day) + "_" + str(''.join(user[:-1].decode('utf-8').split(' ')))

        WIPPath = os.path.join(self.rdir, "resources/WIP_DCEditor.json")
        makepath(WIPPath)

        if not os.path.exists(WIPPath):
            self.WIP_DCEditor = {}  
            self.writeJsonFile("WIP_DCEditor")

        self.WIP_DCEditor = json.load(open(WIPPath, "r"))

        if self.characterName in self.WIP_DCEditor:
            message("This glyph is lock, please choose another one")
            return

        self.Fonts_Link = {}
        fontsLinkPath = os.path.join(self.rdir, "Temp/Fonts_Link.json")
        makepath(fontsLinkPath)

        self.Fonts_Link["font2storage"] = {}
        self.Fonts_Link["linkFontsName"] = {}

        # print(self.characterName)
        # print(self.database)
        # print(self.database[chr(int(self.characterName[3:],16))])
        mini_glyphSet = ["uni"+normalizeUnicode(hex(ord(char))[2:].upper()) for variants in self.database[chr(int(self.characterName[3:],16))] for char in variants]        

        self.WIP_DCEditor[stamp] = mini_glyphSet

        self.writeJsonFile("WIP_DCEditor")
 
        fontsList = []
        fonts = {}
        font2Storage = {}

        for fontName, font in self.ui.fonts.items():
            ######### UFO #########
            familyName, styleName = font.info.familyName, font.info.styleName

            tempFont = NewFont(familyName = "Temp %s"%familyName, styleName = styleName, showInterface = False)
            tempFont.info.unitsPerEm = 1000

            for name in mini_glyphSet:
                tempFont.newGlyph(name)
                tempFont[name] = font[name]

            tempFont.glyphOrder = mini_glyphSet

            tempFontName = "temp-%s-%s"%(stamp, tempFont.info.styleName)
            tempPath = os.path.join(self.rdir, "Temp/%s.ufo" % tempFontName)
            makepath(tempPath)
            tempFont.save(tempPath)

            ######### STORAGE UFO ########
            storageFont = self.ui.font2Storage[font]
            familyName, styleName = font.info.familyName, font.info.styleName

            tempStorageGlyphSet = list(filter(lambda x: x.startswith(self.characterName[3:]), storageFont.keys()))
            storageTempFont = NewFont(familyName = "Storage Temp %s"%familyName, styleName = styleName, showInterface = False)
            storageTempFont.info.unitsPerEm = 1000

            ########################################
            ######## WRITE STORAGE FONT LIB ########
            ########################################

            for name in tempStorageGlyphSet:
                glyph = storageFont[name]

                storageTempFont.newGlyph(name)
                storageTempFont[name] = glyph

                for layer in glyph.layers:
                    if layer.layerName not in [layer.name for layer in storageTempFont.layers]:
                        storageTempFont.newLayer(layer.layerName)
                        storageTempFont.getLayer(layer.layerName).insertGlyph(layer)

                if "deepComponentsGlyph" in storageFont.lib:
                    if "deepComponentsGlyph" not in storageTempFont.lib:
                        storageTempFont.lib['deepComponentsGlyph'] = {}
                    for k, v in storageFont.lib['deepComponentsGlyph'].items():
                        storageTempFont.lib['deepComponentsGlyph'][k] = v

            storageTempFont.glyphOrder = tempStorageGlyphSet

            storageTempFontName = "storageTemp-%s-%s"%(stamp, storageTempFont.info.styleName)

            self.Fonts_Link["linkFontsName"][tempFontName] = fontName
            self.Fonts_Link["linkFontsName"][storageTempFontName] = storageFont.path.split("/")[-1][:-4]

            self.Fonts_Link["font2storage"][tempFontName] = storageTempFontName

            storageTempPath = os.path.join(self.rdir, "Temp/%s.ufo" % storageTempFontName)
            makepath(storageTempPath)
            storageTempFont.save(storageTempPath)

            fonts[tempFontName] = tempFont
            fontsList.append(tempFontName)
            font2Storage[tempFont] = storageTempFont

        self.ui.fontList = fontsList
        self.ui.fonts = fonts
        self.ui.font2Storage = font2Storage

        self.ui.font = fonts[fontsList[0]]

        self.ui.glyphsSetDict = {font: [dict(Name = name, Char = chr(int(name[3:],16)) if name.startswith('uni') else "") for name in font.lib['public.glyphOrder']] for font in self.ui.fonts.values()}

        open(fontsLinkPath, "w").write(json.dumps(self.Fonts_Link))

        if not git.commit('TO DO: ' + stamp): return
        git.push()

        stop = time.time()

        self.c.w.close()

        self.ui._setUI()

        self.ui.glyph = None
        self.ui.updateViews()

        
        # self.ui.w.fontsGroup.fonts_list.setSelection([0])
        # self.ui.w.fontsGroup.injectBack.show(True)
        # self.ui.w.fontsGroup.getSubset.show(False)
