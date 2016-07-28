"""
This software was designed by Alexander Thiel
Github handle: https://github.com/apockill
Email: Alex.D.Thiel@Gmail.com


The software was designed originaly for use with a robot arm, particularly uArm (Made by uFactory, ufactory.cc)
It is completely open source, so feel free to take it and use it as a base for your own projects.

If you make any cool additions, feel free to share!


License:
    This file is part of uArmCreatorStudio.
    uArmCreatorStudio is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    uArmCreatorStudio is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with uArmCreatorStudio.  If not, see <http://www.gnu.org/licenses/>.
"""
import json
import os
import cv2   # For image saving
import numpy as np
from collections  import namedtuple
from Logic.Global import printf, ensurePathExists
__author__ = "Alexander Thiel"



"""
This module holds the types of objects that can be created, loaded, and saved through ObjectManager
"""

class Resource:
    """
    A resource is any object that can save and load itself, and be used in conjunction with ObjectManager.
    """

    def __init__(self, name, loadFromDirectory=None):
        self.name        = name
        self.loadSuccess = False
        self.dataJson    = {}

        if loadFromDirectory is not None:
            self.loadSuccess = self._load(loadFromDirectory)

    def save(self, directory):
        ensurePathExists(directory)

        # Long form (human readable:
        json.dump(self.dataJson, open(directory + "data.txt", 'w'), sort_keys=False, separators=(',', ': '))

    def _load(self, directory):
        """
        Loading should only be done once, during ObjectManager initialization
        :param directory:
        :return:
        """
        # Check if the directory exists (just in case)
        if not os.path.isdir(directory):
            printf("ERROR: Could not find directory", directory)
            return False


        # Try to load the data.txt json
        dataFile   = directory + "\data.txt"
        try:
            loadedData = json.load( open(dataFile))
            self.dataJson = loadedData
        except IOError:
            printf("ERROR: Data file ", dataFile, " was not found!")
            return False
        except ValueError:
            printf("ERROR: Object in ", directory, " is corrupted!")
            return False
        return True


    # In case I ever decide to make plain "Resource" objects, this is useful
    def getAttribute(self, attribute):
        return self.dataJson[attribute]

    def setAttribute(self, attribute):
        self.dataJson[attribute] = attribute


class MotionPath(Resource):
    """
        A motionpath is a recording of the robots movement, that is basically a huge list of lists, where each list
        includes the time, gripper status, and angles of the robot. The motionPath is then played back by a function
        in RobotVision.py.

        motionPath data looks like this [[time, gripper, angleA, angleB, angleC, angleD], [...], [...], ...]
    """

    def __init__(self, name, loadFromDirectory=None):
        super(MotionPath, self).__init__(name, loadFromDirectory)

    def getMotionPath(self):
        return self.dataJson["motionPath"]

    def setMotionPath(self, newPath):
        self.dataJson["motionPath"] = newPath


class Function(Resource):
    def __init__(self, name, loadFromDirectory=None):
        # Unpacked motionPath data looks like this [time, gripper, anglea, angleb, anglec, angled]
        super(Function, self).__init__(name, loadFromDirectory)

    def getCommandList(self):
        return self.dataJson["commandList"]

    def setCommandList(self, commandList):
        self.dataJson["commandList"] = commandList


    def getDescription(self):
        return self.dataJson["description"]

    def setDescription(self, description):
        self.dataJson["description"] = description


    def getArguments(self):
        return self.dataJson["arguments"]

    def setArguments(self, argumentList):
        self.dataJson["arguments"] = argumentList


class Trackable(Resource):
    """
    Any "Trackable" should be capable of being put into a vision/tracking function and track an object or objects.
    """
    def __init__(self, name, loadFromDirectory):
        self.views = []
        super(Trackable, self).__init__(name, loadFromDirectory)

    def getViews(self):
        return self.views

    def equalTo(self, otherObjectID):
        # Test if two objects are are the same (used when seeing if something was recognized)
        # This method is overrided in TrackableGroup
        return self.name == otherObjectID


class TrackableObject(Trackable):
    View = namedtuple('View', 'name, viewID, height, pickupRect, rect, image')

    def __init__(self, name, loadFromDirectory = None):
        """
        Name: A String of the objects unique name. It must be unique for file saving and lookup purposes.

        "Views" is a list [View, View, View] of Views.
        An View is a namedTuple that looks like this:
                {
                    'image': cv2Frame,
                    'rect': (x1,y1,x2,y2),
                    'pickupRect': (x1,y1,x2,y2),
                    'height': 3
                }

        Views are used to record objects at different orientations and help aid tracking in that way.
        """
        self.__tags = []

        super(TrackableObject, self).__init__(name, loadFromDirectory)

    def save(self, directory):
        """
        Everything goes into a folder called TrackableObject OBJECTNAMEHERE

        Saves images for each View, with the format View#,
        and a data.txt folder is saved as a json, with this structure:
        {
            "Orientation_1": {
                            "rect": (0, 0, 10, 10),
                            "pickupRect": (0, 0, 10, 10),
                        },

            "Orientation_1": {
                            "rect": (0, 0, 10, 10),
                            "pickupRect": (0, 0, 10, 10),
                        },
        }
        """


        # Make sure the "objects" directory exists
        ensurePathExists(directory)


        dataJson = {"tags": self.__tags, "Orientations": {}}


        # Save images and numpy arrays as seperate folders
        for index, view in enumerate(self.views):
            # Save the image
            cv2.imwrite(directory + "Orientation_" + str(index) + "_Image.png", view.image)

            # Add any view data to the dataJson
            dataJson["Orientations"]["Orientation_" + str(index)] = {"rect":  view.rect,
                                                                     "pickupRect": view.pickupRect,
                                                                     "height":     view.height}

        json.dump(dataJson, open(directory + "data.txt", 'w'), sort_keys=False, indent=3, separators=(',', ': '))

    def _load(self, directory):
        # Should only be called during initialization

        # Check if the directory exists (just in case)
        if not os.path.isdir(directory):
            printf("ERROR: Could not find directory", directory)
            return False


        # Try to load the data.txt json
        dataFile = directory + "\data.txt"
        try:
            loadedData = json.load( open(dataFile))

        except IOError:
            printf("ERROR: Data file ", dataFile, " was not found!")
            return False
        except ValueError:
            printf("ERROR: Object in ", directory, " is corrupted!")
            return False

        # For each view, load the image associated with it, and build the appropriate view
        orientationData = loadedData["Orientations"]
        for key in orientationData:
            imageFile = directory + '\\' + key + "_Image.png"
            image     = cv2.imread(imageFile)

            if image is None:
                printf("ERROR: Image File ", imageFile, " was unable to be loaded!")
                return False

            self.addNewView(image      = image,
                            rect       = orientationData[key]["rect"],
                            pickupRect = orientationData[key]["pickupRect"],
                            height     = orientationData[key]["height"])


        for tag in loadedData["tags"]:
            self.addTag(tag)
        return True


    def addNewView(self, image, rect, pickupRect, height):
        newView = self.View(name   = self.name, viewID      = len(self.views),
                            height =    height, pickupRect  =      pickupRect,
                            rect   =      rect, image       =           image)
        self.views.append(newView)

    def addTag(self, tagString):
        # Make sure there's never duplicates
        if tagString not in self.__tags:
            self.__tags.append(tagString)

    def removeTag(self, tagString):
        self.__tags.remove(tagString)


    def getIcon(self, maxWidth, maxHeight):
        # Create an icon of a cropped image of the 1st View, and resize it to the parameters.
        # if drawPickupRect is True, it will also overlay the position of the robots pickup area for the object

        #  Get the full image and crop it
        fullImage = self.views[0].image.copy()
        rect      = self.views[0].rect
        image     = fullImage[rect[1]:rect[3], rect[0]:rect[2]]

        # Draw the pickupArea on it before resizing
        # if drawPickupRect and self.views[0].pickupRect is not None:
        x0, y0, x1, y1  = self.views[0].pickupRect
        quad            = np.int32([[x0, y0], [x1, y0], [x1, y1], [x0, y1]])


        cv2.polylines(image, [quad], True, (255, 255, 255), 2)


        #  Resize it to fit within maxWidth and maxHeight
        # Keep Width within maxWidth
        height, width, _ = image.shape

        if width > maxWidth:
            image = cv2.resize(image, (maxWidth, int(float(maxWidth) / width * height)))

        # Keep Height within maxHeight
        height, width, _ = image.shape
        if height > maxHeight:
            image = cv2.resize(image, (int(float(maxHeight) / height * width), maxHeight))



        return image.copy()

    def getTags(self):
        return self.__tags


class TrackableGroupObject(Trackable):
    """
    A group of TrackableObjects that works just like any other Trackable and can be used for detection purposes.
    EqualTo will look to see if the said TrackableObject is inside of the group

    GetViews returns every view of every object in the group, and is how the trackableGroup is tracked.

    self.name is the Group name
    """


    def __init__(self, name, members):
        super(TrackableGroupObject, self).__init__(name, None)
        self.__members = members  # List of Trackable objects that belong to the group
        self.__memberIDs = [obj.name for obj in self.__members]

    def getViews(self):
        views = []
        for obj in self.__members:
            views += obj.getViews()

        return views

    def getMembers(self):
        return self.__members

    def equalTo(self, otherObjectID):
        return otherObjectID in self.__memberIDs
