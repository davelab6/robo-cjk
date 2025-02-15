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
from fontTools.ufoLib.glifLib import readGlyphFromString, writeGlyphToString
from fontTools.pens.recordingPen import RecordingPen
from mojo.roboFont import *
from imp import reload
from models import glyph, component, glyphPreview
from utils import interpolation, decorators
from fontMath import mathGlyph
# reload(decorators)
# reload(interpolation)
# reload(glyph)
# reload(component)
# reload(glyphPreview)
glyphUndo = decorators.glyphUndo
import copy
Glyph = glyph.Glyph
DictClass = component.DictClass
VariationGlyphs = component.VariationGlyphs
Axes = component.Axes
from fontTools.varLib.models import VariationModel
# Deprecated key 
glyphVariationsKey = 'robocjk.glyphVariationGlyphs'

# Actual key
axesKey = 'robocjk.axes'
variationGlyphsKey = 'robocjk.variationGlyphs'
statusKey = 'robocjk.status'

class CustomMathGlyph(mathGlyph.MathGlyph):

    def __init__(self, glyph):
        super().__init__(None)
        p = mathGlyph.MathGlyphPen(self)
        glyph.drawPoints(p)
        self.anchors = [dict(anchor) for anchor in glyph.anchors]
        self.guidelines = []
        self.image = mathGlyph._expandImage(glyph.image)
        self.lib = copy.deepcopy(dict(glyph.lib))
        self.name = glyph.name
        self.unicodes = list(glyph.unicodes)
        self.width = glyph.width
        self.height = glyph.height
        self.note = glyph.note

class AtomicElement(Glyph):
    def __init__(self, name):
        super().__init__()
        self._axes = Axes()
        self._glyphVariations = VariationGlyphs()
        self.selectedSourceAxis = None
        self.name = name
        self.type = "atomicElement"
        self.previewGlyph = []
        # self.preview = glyphPreview.AtomicElementPreview(self)
        self.save()

    def _clampLocation(self, d):
        return {k: min(1, max(0, v)) for k, v in d.items()}

    def preview(self, position:dict={}, font=None, forceRefresh=True):
        locationKey = ','.join([k+':'+str(v) for k,v in position.items()]) if position else ','.join([k+':'+str(v) for k,v in self.normalizedValueToMinMaxValue(position, self).items()])
        if locationKey in self.previewLocationsStore:
            for p in self.previewLocationsStore[locationKey]:
                yield p
            return
        # if not forceRefresh and self.previewGlyph: 
        #     print('AE has previewGlyph', self.previewGlyph)
        #     return self.previewGlyph
        # if not position:
        #     position = self.getLocation()
        # print(position)
        # print("AE %s position"%self.name, position, "\n")
        position = self.normalizedValueToMinMaxValue_clamped(position, self)
        # position = self._clampLocation(position)
        # for k in position:
        #     if position[k] > 1:
        #         position[k] = 1

        locations = [{}]
        locations.extend([self.normalizedValueToMinMaxValue(x["location"], self) for x in self._glyphVariations.getList() if x["on"]])
        # print("AE %s locations"%self.name, locations, "\n")
        # print(locations,'\n')
        # locations.extend([{k:self.normalizedValueToMinMaxValue(v, self) for k, v in x["location"].items()} for x in self._glyphVariations.getList() if x["on"]])

        # self.frozenPreview = []
        self.previewGlyph = []
        if font is None:
            font = self.getParent()
        model = VariationModel(locations)
        layerGlyphs = []
        for variation in self._glyphVariations.getList():
            if not variation.get("on"): continue
            try:
                g = font._RFont.getLayer(variation["layerName"])[self.name]
            except Exception as e: 
                print(e)
                continue
            layerGlyphs.append(CustomMathGlyph(font._RFont.getLayer(variation["layerName"])[self.name]))
        resultGlyph = model.interpolateFromMasters(position, [CustomMathGlyph(self._RGlyph), *layerGlyphs])
        # resultGlyph.removeOverlap()
        # self.frozenPreview.append(resultGlyph)
        resultGlyph = self.ResultGlyph(resultGlyph)
        self.previewGlyph = [resultGlyph]
        self.previewLocationsStore[','.join([k+':'+str(v) for k,v in position.items()])] = [resultGlyph]
        yield resultGlyph
        # self.previewGlyph.append(self.ResultGlyph(resultGlyph))
        # for e in self.previewGlyph:
        #     yield e
        # return self.ResultGlyph(resultGlyph)

    @property
    def foreground(self):
        return self._RFont[self.name].getLayer('foreground')
    
    @property
    def glyphVariations(self):
        return self._glyphVariations
    
    def _initWithLib(self):
        if variationGlyphsKey not in self._RGlyph.lib.keys():
            key = dict(self._RGlyph.lib[glyphVariationsKey])
            self._axes = Axes()
            self._axes._init_with_old_format(key)
            self._glyphVariations = VariationGlyphs()
            self._glyphVariations._init_with_old_format(key, self._axes, defaultWidth = self._RGlyph.width)
        else:
            if axesKey in self._RGlyph.lib:
                self._axes = Axes(self._RGlyph.lib[axesKey])
                self._glyphVariations = VariationGlyphs(self._RGlyph.lib[variationGlyphsKey], self._axes, defaultWidth = self._RGlyph.width)
                self._status = self._RGlyph.lib.get(statusKey, 0)
            else:
                self._axes = Axes()
                self._axes._init_with_old_format(dict(self._RGlyph.lib[variationGlyphsKey]))
                self._glyphVariations = VariationGlyphs()
                self._glyphVariations._init_with_old_format(dict(self._RGlyph.lib[variationGlyphsKey]), self._axes, defaultWidth = self._RGlyph.width)
        # self._temp_set_Status_value()

    def addGlyphVariation(self, newAxisName, newLayerName):
        self._axes.addAxis({"name":newAxisName, "minValue":0, "maxValue":1})
        variation = {"location":{newAxisName:1}, "layerName":newLayerName}
        self._glyphVariations.addVariation(variation, self._axes, defaultWidth = self._RGlyph.width)

        glyph = AtomicElement(self.name)
        txt = self._RFont.getLayer(newLayerName)[self.name].dumpToGLIF()
        self.currentFont.insertGlyph(glyph, txt, newLayerName)

    def removeGlyphVariation(self, axisName):
        index = 0
        for i, x in enumerate(self._axes):
            if x.name == axisName:
                index = i
        self._glyphVariations.removeVariation(index)
        self._axes.removeAxis(index)

    def save(self):
        self.lib.clear()
        lib = RLib()
        lib[axesKey] = self._axes.getList()
        lib[variationGlyphsKey] = self._glyphVariations.getList(exception=["sourceName"])
        for i, v in enumerate(lib[variationGlyphsKey]):
            if v["width"] == self._RGlyph.width:
                del lib[variationGlyphsKey][i]["width"]
        if self._status:
            lib[statusKey] = self._status
        if 'public.markColor' in lib:
            del lib['public.markColor']
        self.lib.update(lib)
        if 'public.markColor' in self.lib:
            del self.lib['public.markColor']