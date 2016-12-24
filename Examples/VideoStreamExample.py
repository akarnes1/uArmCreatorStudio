import sys
sys.path.append("../")

import numpy             as np
import cv2
from time                import sleep  # Used only for waiting for robot in CoordCalibrations

from Logic import Video
from Logic import Robot
from Logic.Resources    import TrackableObject, MotionPath, Function
from Logic.Vision import PlaneTracker
from Logic.Vision       import Vision

from PyQt5              import QtCore, QtWidgets, QtGui

cascadePath  = "../Resources"


def startCalibration(vision, trackable, robot):
       #---------------------------------------------------------------------------------
       #startCalibration
       #Start tracking the robots marker

       rbMarker = trackable

       vision.endAllTrackers()
       vision.addTarget(rbMarker)

       # Set the robot to the home position, set the speed, and other things for the calibration
       robot.setActiveServos(all=True)
       robot.setSpeed(10)

       # Move the robot up a certain offset from the ground coordinate
       zLower = float(round(groundCoords[2] + 2.0, 2))
       robot.setPos(x=robot.home["x"], y=robot.home["y"], z=zLower)
       sleep(1)


       # Generate a large set of points to test the robot, and put them in testCoords
       testCoords    = []

       # Test the z on 3 xy points
       zTest = int(round(zLower, 0))  # Since range requires an integer, round zLower just for this case
       for x in range(  -20, 20, 4): testCoords += [[x,  15,    11]]  # Center of XYZ grid
       for y in range(    8, 24, 4): testCoords += [[ 0,  y,    11]]
       for z in range(zTest, 19, 1): testCoords += [[ 0, 15,     z]]

       for x in range(  -20, 20, 4): testCoords += [[x,  15,    17]]  # Center of XY, top z
       for y in range(   12, 24, 4): testCoords += [[ 0,  y,    17]]



       direction  = int(1)
       for y in range(12, 25, 2):
           for x in range(-20 * direction, 20 * direction, 2 * direction):
               testCoords += [[x, y, zTest]]
           direction *= -1
       print(testCoords)
       return testCoords

def endCalibration(robot, vision, errors, newCalibrations, testCoords):

    # Return the robot to home and turn off tracking
    vision.endAllTrackers()
    # robot.setPos(**robot.home)

    print(len(newCalibrations["ptPairs"]))

def getPoint(robot, vision, rbMarker, currentPoint, errors, newCalibrations, coord):
    # Here we update the GUI element for telling the user how many valid points have been tested, and progress
    successCount = len(newCalibrations["ptPairs"])
    recFailCount = len(newCalibrations["failPts"])

    # Get variables that will be used
    print("GUI| Testing point ", coord)

    # Move the robot to the coordinate
    robot.setPos(x=coord[0], y=coord[1], z=coord[2])
    vision.waitForNewFrames(3)

    # Now that the robot is at the desired position, get the avg location
    frameAge, marker = vision.getObjectLatestRecognition(rbMarker)

    if marker is None or not frameAge < 2:
        print("GUI| Marker was not recognized.")
        newCalibrations['failPts'].append(coord)
        print('heihei', newCalibrations)
        return

    newCalibrations["ptPairs"].append([marker.center, coord])
    timer = singleShot()

#---------------------------------------------------------------------------------------------
# Create a VideoStream and start a video-retrieval thread
vStream = Video.VideoStream()
vStream.startThread()
vStream.setNewCamera(0)


historyLen = 60
planeTracker   = PlaneTracker(25.0, historyLen)

vision = Vision(vStream, cascadePath)  # Performs computer vision tasks, using images from vStream

#page2
robot = Robot.Robot()
robot.setUArm('/dev/ttyUSB0')
#wait for getCoords can get value
coord = robot.getCoords();
robot.setActiveServos(servo0=False)

key = None
while coord ==[0, 0, 0]:
    coord = robot.getCoords()
    print(coord)

input("Press Enter to continue...")

robot.setActiveServos(all=False)
samples = 10
sumCoords = np.float32([0, 0, 0])
for i in range(0, samples):
    coord = robot.getCoords()
    sumCoords += np.float32(coord)
groundCoords = list(map(float, sumCoords / samples))
print("groundCoords", groundCoords)
robot.setPos(z=groundCoords[2] + .5)
robot.setActiveServos(servo0=False)

# Play video until the user presses "q"
key = None
step = 1
trackable = TrackableObject("Robot Marker")
currentPoint = 0

while not key == ord("q"):
    # Request the latest frame from the VideoStream
    frame = vStream.getFilteredFrame()

    # If the camera has started up, then show the frame
    if frame is not None:
        if step:
            h, w, _  = frame.shape
            rect = (333, 103, 406, 238)

            trackable.addNewView(image      = frame,
                                 rect       = rect,
                                 pickupRect = [0, 0, h, w],
                                height     = 0)
            target = planeTracker.createTarget(trackable.getViews()[0])

            vision.addTarget(trackable)
            step = 0


            # Begin testing every coordinate in the testCoords array, and recording the results into newCalibrations

    testCoords = startCalibration(vision, trackable, robot)

    getPoint(robot, vision, trackable, currentPoint, [], {"ptPairs": [], "failPts": []}, coord)

    if currentPoint >= len(testCoords):
        endCalibration(robot, vision, rbMark, errors, newCalibrations, testCoords)
    coord = testCoords[currentPoint]
    currentPoint += 1
    print(currentPoint)

    cv2.imshow("frame", frame)
    key = cv2.waitKey(10)
