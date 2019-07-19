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
from mojo.canvas import Canvas
from mojo.drawingTools import *
import Helpers

class TextCenter():

    def __init__(self, interface):
        self.ui = interface
        self.windowWidth, self.windowHeight = 800, 600
        self.w = Window((self.windowWidth, self.windowHeight), "Text Center", minSize = (200, 200))

        self.inverse = 0
        self.scale = .4

        self.horizontalMode = 0
        self.w.horizontalMode_checkBox = CheckBox((10, -20, 150, -0),  
            "Horizontal Mode", 
            value = self.horizontalMode,
            sizeStyle = "small",
            callback = self._horizontalMode_checkBox_callback)

        self.w.canvas = Canvas((0, 60, -0, -20), delegate = self)

        Helpers.setDarkMode(self.w, self.ui.darkMode)
        self.w.bind('resize', self.windowDidResize)
        self.w.open()

    def windowDidResize(self, sender):
        _, _, self.windowWidth, self.windowHeight = sender.getPosSize()
        self.w.canvas.update()

    def _horizontalMode_checkBox_callback(self, sender):
        self.horizontalMode = sender.get()
        self.w.canvas.update()

    def keyDown(self, info):
        if info.characters() == "i":
            self.inverse = abs(self.inverse - 1)
            self.w.canvas.update()

    def draw(self):
        try:
            save()

            if self.inverse:
                fill(0)
                rect(0, 0, 10000, 10000)

            scale(self.scale, self.scale)
            translate(100, ((self.windowHeight-80)/self.scale)-500)

            width = 0
            
            for i in range(5):
                fill(None)
                stroke(0)
                rect(0, 0, 400, 400)
                translate(400, 0)
                width += 400

            restore()
        except Exception as e:
            print(e)