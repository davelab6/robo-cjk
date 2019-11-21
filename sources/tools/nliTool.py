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
from mojo.events import BaseEventTool, installTool
from AppKit import *

from mojo.extensions import ExtensionBundle

import os
from imp import reload

from utils import points
reload(points)

cwd = os.getcwd()
rdir = os.path.abspath(os.path.join(cwd, os.pardir))

toolbarIcon = NSImage.alloc().initByReferencingFile_(os.path.join(rdir, "RoboCJK/resources/NLITool_ToolbarIcon.pdf"))

class NliTool(BaseEventTool):

    def __init__(self, RCJKI):
        super(NliTool, self).__init__()
        self.RCJKI = RCJKI
        self.targetPoint = []

    def getToolbarIcon(self):
        return toolbarIcon

    def getToolbarTip(self):
        return "NLI Tool"

    def becomeActive(self):
        self.RCJKI.activeNLI = True
        self.RCJKI.updateViews()

    def becomeInactive(self):
        self.RCJKI.activeNLI = False
        self.RCJKI.updateViews()

    def mouseDown(self, ploc, clickcount):
        # if self.RCJKI.currentGlyph.name not in self.RCJKI.pathsGlyphs: return
        # print(ploc)
        if self.RCJKI.currentGlyph.layerName == 'foreground': return
        # best = [None]
        # dist = [999999999.0]

        # print(self.RCJKI.currentGlyph.layerName)
        x, y = ploc
        # print(self.RCJKI.currentGlyph.lib["NLIPoints"])
        for ci, c in enumerate(self.RCJKI.currentGlyph.lib["NLIPoints"]):
            for pi, ps in enumerate(c):
                for i, p in enumerate(ps):
                    px, py = p
                    if abs(px-x) < 10 and abs(py-y) < 10:
                        self.targetPoint = [ci, pi, i]
                        return
        # self.ploc = self.pointClickedOnGlyph(ploc, self.RCJKI.pathsGlyphs[self.RCJKI.currentGlyph.name]['paths_'+self.RCJKI.currentGlyph.layerName], best, dist)

    def mouseDragged(self, ploc, delta):
        if not self.targetPoint: return
        dx, dy = delta

        ci, pi, p = self.targetPoint

        nli = self.RCJKI.currentGlyph.lib["NLIPoints"]

        x, y = nli[ci][pi][p]

        nli[ci][pi][p] = [x + dx, y - dy]

        self.RCJKI.currentGlyph.lib["NLIPoints"] = nli
        
        # mouseDraggedPos = points.Point(*ploc)
        # pmoved = self.RCJKI.pathsGlyphs[self.RCJKI.currentGlyph.name]['paths_'+self.RCJKI.currentGlyph.layerName][self.ploc.cont][self.ploc.seg][self.ploc.idx]
        # pmoved.x = mouseDraggedPos.x
        # pmoved.y = mouseDraggedPos.y

        self.RCJKI.updateViews()

    def mouseUp(self, info):
        self.targetPoint = []

    # def pointClickedOnGlyph(self, clickPos, glyph, best, dist):
    #     if len(glyph) == 0: return
    #     thresh = 10.0 * 10.0

    #     def update(p, cont, seg, idx):
    #         d = (points.Point(clickPos[0], clickPos[1]) - points.Point(p.x, p.y)).squaredLength()
    #         if d < dist[0]:
    #             dist[0] = d
    #             best[0] = points.PointLocation(points.Point(p), cont, seg, idx)
                
    #     for cont, contour in enumerate(glyph):
    #         for seg, segment in enumerate(contour):
    #             for idx, p in enumerate(segment.offCurve):
    #                 update(p, cont, seg, idx)
    #     if dist[0] <= thresh:
    #         return best[0]
    #     else:
    #         return None

