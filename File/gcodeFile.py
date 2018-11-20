from DataStructures.makesmithInitFuncs import MakesmithInitFuncs

import sys
import threading
import json
import re
import math
import gzip
import io


class Line:
    def __init__(self):
        self.points = []
        self.color = None
        self.dashed = False
        self.type = None


class GCodeFile(MakesmithInitFuncs):
    isChanged = False
    canvasScaleFactor = 1  # scale from mm to pixels
    INCHES = 1.0
    MILLIMETERS = 1.0/25.4

    xPosition = 0
    yPosition = 0
    zPosition = 0
    truncate = -1 #do this to truncate after shift of home position

    lineNumber = 0  # the line number currently being processed

    absoluteFlag = 0

    prependString = "G01 "

    maxNumberOfLinesToRead = 300000

    filename = ""
    line = []
    line3D = []


    def serializeGCode(self):
        sendStr = json.dumps([ob.__dict__ for ob in self.data.gcodeFile.line])
        return sendStr

    def serializeGCode3D(self):
        sendStr = json.dumps([ob.__dict__ for ob in self.data.gcodeFile.line3D])
        return sendStr

    def loadUpdateFile(self):
        if self.data.units == "MM":
            self.canvasScaleFactor = self.MILLIMETERS
        else:
            self.canvasScaleFactor = self.INCHES

        filename = self.data.gcodeFile.filename
        # print(filename)
        del self.line[:]
        del self.line3D[:]
        if filename is "":  # Blank the g-code if we're loading "nothing"
            self.data.gcode = ""
            return False

        try:
            filterfile = open(filename, "r")
            rawfilters = filterfile.read()
            filtersparsed = re.sub(
                r"\(([^)]*)\)", "\n", rawfilters
            )  # replace mach3 style gcode comments with newline
            filtersparsed = re.sub(
                r";([^\n]*)\n", "\n", filtersparsed
            )  # replace standard ; initiated gcode comments with newline
            filtersparsed = re.sub(r"\n\n", "\n", filtersparsed)  # removes blank lines
            filtersparsed = re.sub(
                r"([0-9])([GXYZIJFTM]) *", "\\1 \\2", filtersparsed
            )  # put spaces between gcodes
            filtersparsed = re.sub(r"  +", " ", filtersparsed)  # condense space runs
            value = self.data.config.getValue("Advanced Settings", "truncate")

            if value == 1:
                digits = self.data.config.getValue("Advanced Settings", "digits")
                filtersparsed = re.sub(
                    r"([+-]?\d*\.\d{1," + digits + "})(\d*)", r"\g<1>", filtersparsed
                )  # truncates all long floats to 4 decimal places, leaves shorter floats
                self.truncate = int(digits)
            else:
                self.truncate = -1
            filtersparsed = re.split(
                "\n", filtersparsed
            )  # splits the gcode into elements to be added to the list
            filtersparsed = [
                x + " " for x in filtersparsed
            ]  # adds a space to the end of each line
            filtersparsed = [x.lstrip() for x in filtersparsed]
            filtersparsed = [x.replace("X ", "X") for x in filtersparsed]
            filtersparsed = [x.replace("Y ", "Y") for x in filtersparsed]
            filtersparsed = [x.replace("Z ", "Z") for x in filtersparsed]
            filtersparsed = [x.replace("I ", "I") for x in filtersparsed]
            filtersparsed = [x.replace("J ", "J") for x in filtersparsed]
            filtersparsed = [x.replace("F ", "F") for x in filtersparsed]
            self.data.gcode = "[]"
            self.data.gcode = filtersparsed

            filterfile.close()  # closes the filter save file
            # Find gcode indicies of z moves
            self.data.zMoves = [0]
            zList = []
            for index, line in enumerate(self.data.gcode):
                z = re.search("Z(?=.)([+-]?([0-9]*)(\.([0-9]+))?)", line)
                if z:
                    zList.append(z)
                    if len(zList) > 1:
                        if not self.isClose(
                            float(zList[-1].groups()[0]), float(zList[-2].groups()[0])
                        ):
                            self.data.zMoves.append(index - 1)
                    else:
                        self.data.zMoves.append(index)
        except:
            self.data.console_queue.put("Gcode File Error")
            self.data.ui_queue.put("Message: Cannot open gcode file.")
            self.data.gcodeFile.filename = ""
            return False
        self.updateGcode()
        self.data.gcodeFile.isChanged = True
        return True

    def isClose(self, a, b):
        return abs(a - b) <= self.data.tolerance

    def addPoint(self, x, y):
        """
        Add a point to the line currently being plotted
        """
        self.line[-1].points.append(
            #(x * self.canvasScaleFactor, y * self.canvasScaleFactor * -1.0)
            (x , y * -1.0)
        )

    def addPoint3D(self, x, y, z):
        """
        Add a point to the line currently being plotted
        """
        self.line3D[-1].points.append(
            (x, y, z)
        )


    def isNotReallyClose(self, x0, x1):
        if abs(x0 - x1) > 0.0001:
            return True
        else:
            return False

    def drawLine(self, gCodeLine, command):
        """

        drawLine draws a line using the previous command as the start point and the xy coordinates
        from the current command as the end point. The line is styled based on the command to allow
        visually differentiating between normal and rapid moves. If the z-axis depth is changed a
        circle is placed at the location of the depth change to alert the user.

        """

        if True:
            xTarget = self.xPosition
            yTarget = self.yPosition
            zTarget = self.zPosition

            x = re.search("X(?=.)(([ ]*)?[+-]?([0-9]*)(\.([0-9]+))?)", gCodeLine)
            if x:
                xTarget = float(x.groups()[0]) * self.canvasScaleFactor
                if self.absoluteFlag == 1:
                    xTarget = self.xPosition + xTarget

            y = re.search("Y(?=.)(([ ]*)?[+-]?([0-9]*)(\.([0-9]+))?)", gCodeLine)
            if y:
                yTarget = float(y.groups()[0]) * self.canvasScaleFactor
                if self.absoluteFlag == 1:
                    yTarget = self.yPosition + yTarget
            z = re.search("Z(?=.)(([ ]*)?[+-]?([0-9]*)(\.([0-9]+))?)", gCodeLine)
            if z:
                zTarget = float(z.groups()[0]) * self.canvasScaleFactor

            # Draw lines for G1 and G0
            # with self.scatterObject.canvas:
            # print "Command:"+command
            # print "#"+gCodeLine+"#"
            # print "#"+str(self.xPosition/25.4)+", "+str(self.yPosition/25.4)+" - "+str(xTarget/25.4)+", "+str(yTarget/25.4)
            if self.isNotReallyClose(self.xPosition, xTarget) or self.isNotReallyClose(
                self.yPosition, yTarget
            ):
                # Color(self.data.drawingColor[0], self.data.drawingColor[1], self.data.drawingColor[2])

                if command == "G00":
                    # draw a dashed line
                    self.line.append(Line())  # points = (), width = 1, group = 'gcode')
                    self.line[-1].type = "line"
                    self.line[-1].dashed = True
                    self.addPoint(self.xPosition, self.yPosition)
                    self.addPoint(xTarget, yTarget)

                    self.line3D.append(Line())  # points = (), width = 1, group = 'gcode')
                    self.line3D[-1].type = "line"
                    self.line3D[-1].dashed = True
                    self.addPoint3D(self.xPosition, self.yPosition, self.zPosition)
                    self.addPoint3D(xTarget, yTarget, zTarget)

                else:
                    # print "here"
                    if (
                        len(self.line3D) == 0
                        or self.line3D[-1].dashed
                        or self.line3D[-1].type != "line"
                    ):
                        self.line.append( Line() )
                        self.line[-1].type = "line"
                        self.addPoint(self.xPosition, self.yPosition)
                        self.line[-1].dashed = False

                        self.line3D.append( Line() )
                        self.line3D[-1].type = "line"
                        self.addPoint3D(self.xPosition, self.yPosition, self.zPosition)
                        self.line3D[-1].dashed = False

                    self.addPoint(xTarget, yTarget)
                    self.addPoint3D(xTarget, yTarget, zTarget)

            # If the zposition has changed, add indicators
            tol = 0.05  # Acceptable error in mm
            if abs(zTarget - self.zPosition) >= tol:
                # with self.scatterObject.canvas:
                if True:
                    if zTarget - self.zPosition > 0:
                        # Color(0, 1, 0)
                        radius = 1
                    else:
                        # Color(1, 0, 0)
                        radius = 2
                    self.line.append(Line())  # points = (), width = 1, group = 'gcode')
                    self.line[-1].type = "circle"
                    self.addPoint(self.xPosition, self.yPosition)
                    self.addPoint(radius, 0)
                    self.line[-1].dashed = False

                    self.line3D.append(Line())  # points = (), width = 1, group = 'gcode')
                    self.line3D[-1].type = "circle"
                    self.addPoint3D(self.xPosition, self.yPosition, self.zPosition)
                    self.addPoint3D(radius, 0, self.zPosition)
                    self.line3D[-1].dashed = False

            self.xPosition = xTarget
            self.yPosition = yTarget
            self.zPosition = zTarget
        # except:
        #    print "Unable to draw line on screen: " + gCodeLine

    def drawArc(self, gCodeLine, command):
        """

        drawArc draws an arc using the previous command as the start point, the xy coordinates from
        the current command as the end point, and the ij coordinates from the current command as the
        circle center. Clockwise or counter-clockwise travel is based on the command.

        """

        if True:
            xTarget = self.xPosition
            yTarget = self.yPosition
            zTarget = self.zPosition
            iTarget = 0
            jTarget = 0

            x = re.search("X(?=.)(([ ]*)?[+-]?([0-9]*)(\.([0-9]+))?)", gCodeLine)
            if x:
                xTarget = float(x.groups()[0]) * self.canvasScaleFactor
            y = re.search("Y(?=.)(([ ]*)?[+-]?([0-9]*)(\.([0-9]+))?)", gCodeLine)
            if y:
                yTarget = float(y.groups()[0]) * self.canvasScaleFactor
            i = re.search("I(?=.)(([ ]*)?[+-]?([0-9]*)(\.([0-9]+))?)", gCodeLine)
            if i:
                iTarget = float(i.groups()[0]) * self.canvasScaleFactor
            j = re.search("J(?=.)(([ ]*)?[+-]?([0-9]*)(\.([0-9]+))?)", gCodeLine)
            if j:
                jTarget = float(j.groups()[0]) * self.canvasScaleFactor

            radius = math.sqrt(iTarget ** 2 + jTarget ** 2)
            centerX = self.xPosition + iTarget
            centerY = self.yPosition + jTarget

            angle1 = math.atan2(self.yPosition - centerY, self.xPosition - centerX)
            angle2 = math.atan2(yTarget - centerY, xTarget - centerX)

            # atan2 returns results from -pi to +pi and we want results from 0 - 2pi
            if angle1 < 0:
                angle1 = angle1 + 2 * math.pi
            if angle2 < 0:
                angle2 = angle2 + 2 * math.pi

            # take into account command G1 or G2
            if int(command[1:]) == 2:
                if angle1 < angle2:
                    angle1 = angle1 + 2 * math.pi
                direction = -1
            else:
                if angle2 < angle1:
                    angle2 = angle2 + 2 * math.pi
                direction = 1

            arcLen = abs(angle1 - angle2)
            if abs(angle1 - angle2) == 0:
                arcLen = 6.28313530718

            if (
                len(self.line3D) == 0
                or self.line3D[-1].dashed
                or self.line3D[-1].type != "line"
            ):
                self.line.append(Line())  # points = (), width = 1, group = 'gcode')
                self.addPoint(self.xPosition, self.yPosition)
                self.line[-1].type = "line"
                self.line[-1].dashed = False

                self.line3D.append(Line())  # points = (), width = 1, group = 'gcode')
                self.addPoint3D(self.xPosition, self.yPosition, zTarget)
                self.line3D[-1].type = "line"
                self.line3D[-1].dashed = False


            i = 0
            while abs(i) < arcLen:
                xPosOnLine = centerX + radius * math.cos(angle1 + i)
                yPosOnLine = centerY + radius * math.sin(angle1 + i)
                zPosOnline = zTarget
                self.addPoint(xPosOnLine, yPosOnLine)
                self.addPoint3D(xPosOnLine, yPosOnLine, zTarget)
                i = i + 0.1 * direction  # this is going to need to be a direction

            self.addPoint(xTarget, yTarget)
            self.addPoint3D(xTarget, yTarget, zTarget)

            self.xPosition = xTarget
            self.yPosition = yTarget
            self.zPosition = zTarget
        # except:
        #    print "Unable to draw arc on screen: " + gCodeLine

    def clearGcode(self):
        """

        clearGcode deletes the lines and arcs corresponding to gcode commands from the canvas.

        """
        del self.line[:]
        del self.line3D[:]


    def moveLine(self, gCodeLine):

        originalLine = gCodeLine

        try:
            gCodeLine = gCodeLine.upper() + " "
            x = re.search("X(?=.)(([ ]*)?[+-]?([0-9]*)(\.([0-9]+))?)", gCodeLine)
            if x:
                q = abs(float(x.groups()[0])+self.data.gcodeShift[0])
                if self.truncate >= 0:
                    q = str(round(q, self.truncate))
                else:
                    q = str(q)

                #                 xTarget = '%f' % (float(x.groups()[0]) + self.data.gcodeShift[0]) # not used any more...
                #eNtnX = re.sub(
                #    "\-?\d\.|\d*e-",
                #    "",
                #    str(abs(float(x.groups()[0]) + self.data.gcodeShift[0])),
                #)  # strip off everything but the decimal part or e-notation exponent

                eNtnX = re.sub("\-?\d\.|\d*e-","",q,)  # strip off everything but the decimal part or e-notation exponent

                #e = re.search(
                #    ".*e-", str(abs(float(x.groups()[0]) + self.data.gcodeShift[0]))
                #)

                e = re.search(".*e-", q)

                if e:
                    fmtX = (
                        "%0%.%sf" % eNtnX
                    )  # if e-notation, use the exponent from the e notation
                else:
                    fmtX = "%0%.%sf" % len(
                        eNtnX
                    )  # use the number of digits after the decimal place
                gCodeLine = (
                    gCodeLine[0 : x.start() + 1]
                    + (fmtX % (float(x.groups()[0]) + self.data.gcodeShift[0]))
                    + gCodeLine[x.end() :]
                )

            y = re.search("Y(?=.)(([ ]*)?[+-]?([0-9]*)(\.([0-9]+))?)", gCodeLine)
            if y:
                #                 yTarget = '%f' % (float(y.groups()[0]) + self.data.gcodeShift[1]) # not used any more...
                q = abs(float(y.groups()[0])+self.data.gcodeShift[1])
                if self.truncate >= 0:
                    q = str(round(q, self.truncate))
                else:
                    q = str(q)

                #eNtnY = re.sub(
                #    "\-?\d\.|\d*e-",
                #    "",
                #    str(abs(float(y.groups()[0]) + self.data.gcodeShift[1])),
                #)
                eNtnY = re.sub("\-?\d\.|\d*e-", "", q, )

                #e = re.search(
                #    ".*e-", str(abs(float(y.groups()[0]) + self.data.gcodeShift[1]))
                #)
                e = re.search(".*e-", q )

                if e:
                    fmtY = "%0%.%sf" % eNtnY
                else:
                    fmtY = "%0%.%sf" % len(eNtnY)
                gCodeLine = (
                    gCodeLine[0 : y.start() + 1]
                    + (fmtY % (float(y.groups()[0]) + self.data.gcodeShift[1]))
                    + gCodeLine[y.end() :]
                )
            #print(gCodeLine)
            return gCodeLine
        except ValueError:
            self.data.console_queue.put("line could not be moved:")
            self.data.console_queue.put(originalLine)
            return originalLine

    def loadNextLine(self):
        """

        Load the next line of gcode

        """

        try:
            self.data.gcode[self.lineNumber] = self.moveLine(
                self.data.gcode[self.lineNumber]
            )  # move the line if the gcode has been moved
            fullString = self.data.gcode[self.lineNumber]
            #print(fullString)
        except:
            return  # we have reached the end of the file

        # if the line contains multiple gcode commands split them and execute them individually
        listOfLines = fullString.split("G")
        if len(listOfLines) > 1:  # if the line contains at least one 'G'
            for line in listOfLines:
                if len(line) > 0:  # If the line is not blank
                    # print "line:"+str(self.lineNumber)+"#G"+str(line)+"#"
                    self.updateOneLine("G" + line)  # Draw it
        else:
            # print "line:"+str(self.lineNumber)+"<"+fullString+">"
            self.updateOneLine(fullString)

        self.lineNumber = self.lineNumber + 1

    def updateOneLine(self, fullString):
        """

        Draw the next line on the gcode canvas

        """

        validPrefixList = [
            "G00",
            "G0 ",
            "G1 ",
            "G01",
            "G2 ",
            "G02",
            "G3 ",
            "G03",
            "G17",
        ]

        fullString = (
            fullString + " "
        )  # ensures that there is a space at the end of the line

        # find 'G' anywhere in string
        self.prependString = ""
        gString = fullString[fullString.find("G") : fullString.find("G") + 3]

        if gString in validPrefixList:
            self.prependString = gString

        if (
            fullString.find("G") == -1
        ):  # this adds the gcode operator if it is omitted by the program
            fullString = self.prependString + " " + fullString
            gString = self.prependString

        # print gString
        if gString == "G00" or gString == "G0 ":
            self.drawLine(fullString, "G00")

        if gString == "G01" or gString == "G1 ":
            self.drawLine(fullString, "G01")

        if gString == "G02" or gString == "G2 ":
            self.drawArc(fullString, "G02")

        if gString == "G03" or gString == "G3 ":
            self.drawArc(fullString, "G03")

        if gString == "G17":
            # Take no action, XY coordinate plane is the default
            pass

        if gString == "G18":
            self.data.console_queue.put("G18 not supported")

        if gString == "G20":
            if self.data.units != "INCHES":
                self.data.actions.updateSetting("toInches", 0) # value = doesn't matter
            self.canvasScaleFactor = self.INCHES

        if gString == "G21":
            if self.data.units != "MM":
                self.data.actions.updateSetting("toMM", 0) #value = doesn't matter
            self.canvasScaleFactor = self.MILLIMETERS

        if gString == "G90":
            self.absoluteFlag = 0

        if gString == "G91":
            self.absoluteFlag = 1

    def callBackMechanism(self):
        """
        Call the loadNextLine function in background.
        """

        for _ in range(min(len(self.data.gcode), self.maxNumberOfLinesToRead)):
            self.loadNextLine()

        tstr = json.dumps([ob.__dict__ for ob in self.data.gcodeFile.line])
        out = io.BytesIO()
        with gzip.GzipFile(fileobj=out, mode="w") as f:
            f.write(tstr.encode())
        self.data.compressedGCode = out.getvalue()

        tstr = json.dumps([ob.__dict__ for ob in self.data.gcodeFile.line3D])
        out = io.BytesIO()
        with gzip.GzipFile(fileobj=out, mode="w") as f:
            f.write(tstr.encode())
        self.data.compressedGCode3D = out.getvalue()

        self.data.console_queue.put("uncompressed:"+str(len(tstr)))
        self.data.console_queue.put("compressed:"+str(len(self.data.compressedGCode)))
        self.data.console_queue.put("compressed3D:"+str(len(self.data.compressedGCode3D)))


    def updateGcode(self):
        """
        updateGcode parses the gcode commands and calls the appropriate drawing function for the
        specified command.
        """
        # reset variables
        self.data.backgroundRedraw = False
        if (self.data.units=="INCHES"):
            scaleFactor = 1.0;
        else:
            scaleFactor = 1/25.4;
        self.xPosition = self.data.gcodeShift[0] * scaleFactor
        self.yPosition = self.data.gcodeShift[1] * scaleFactor
        self.zPosition = 0

        self.prependString = "G00 "
        self.lineNumber = 0

        self.clearGcode()

        # Check to see if file is too large to load
        if len(self.data.gcode) > self.maxNumberOfLinesToRead:
            errorText = (
                "The current file contains "
                + str(len(self.data.gcode))
                + " lines of gcode.\nrendering all "
                + str(len(self.data.gcode))
                + " lines simultaneously may crash the\n program, only the first "
                + str(self.maxNumberOfLinesToRead)
                + "lines are shown here.\nThe complete program will cut if you choose to do so unless the home position is moved from (0,0)."
            )
            self.data.console_queue.put(errorText)
            self.data.ui_queue.put("closeModals:_Notification:")
            self.data.ui_queue.put("Message: " + errorText)

        th = threading.Thread(target=self.callBackMechanism)
        th.start()


