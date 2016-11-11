import sys
sys.path.append("../")

from Logic import Video
from Logic.Vision import PlaneTracker
from Logic.Vision import CascadeTracker
from Logic.Vision import Vision
from Logic.Resources     import TrackableObject, MotionPath, Function
import cv2

# from RunTaskNoGUI.py
taskPath     = "../Resources\\Save Files\\test.task"
settingsPath = "..\\Resources\\Settings.txt"
cascadePath  = "../Resources"
objectsPath  = "..\\Resources\\Objects"

# Create a VideoStream and start a video-retrieval thread
vStream = Video.VideoStream()
vStream.startThread()
vStream.setNewCamera(0)

# from Vision.py
historyLen = 60
planeTracker   = PlaneTracker(25.0, historyLen)


# from Environment.py Environment __init__
vision = Vision(vStream, cascadePath)  # Performs computer vision tasks, using images from vStream
cascadeTracker = CascadeTracker(historyLen, cascadePath)
cascadeTracker.addTarget("Face")

# Play video until the user presses "q"
key = None
refPt = []
cropping = False
start = False


def click_and_crop(event, x, y, flags, param):
	# grab references to the global variables
	global refPt, cropping, start

	# if the left mouse button was clicked, record the starting
	# (x, y) coordinates and indicate that cropping is being
	# performed
	if event == cv2.EVENT_LBUTTONDOWN:
            refPt = [(x, y)]
            start = True
            # cropping = True
	elif event == cv2.EVENT_MOUSEMOVE:
            if start:
                cv2.rectangle(param, refPt[0], (x, y), (0, 255, 0), 2)

	# check to see if the left mouse button was released
	elif event == cv2.EVENT_LBUTTONUP:
            # record the ending (x, y) coordinates and indicate that
            # the cropping operation is finished
            refPt.append((x, y))
            cropping = True
            start = False 

            # draw a rectangle around the region of interest
            cv2.rectangle(param, refPt[0], refPt[1], (0, 255, 0), 2)
            # cv2.imshow("frame", param)

cv2.namedWindow("frame")

while not key == ord("q"):
    # Request the latest frame from the VideoStream
    frame = vStream.getFilteredFrame()


    cv2.setMouseCallback("frame", click_and_crop, frame)

    # If the camera has started up, then show the frame
    if frame is not None: 

        if cropping:
            # from ObjectManagerGUI.py def objectSelected
            clone = frame.copy()
            rect = (refPt[0][0], refPt[0][1], refPt[1][0],refPt[1][1])
            print("rect", rect)

            trackable = TrackableObject("")
            trackable.addNewView(frame, rect, None, None)
            target    = planeTracker.createTarget(trackable.getViews()[0])
            cropping = False

            if len(target.descrs) == 0 or len(target.keypoints) == 0:
                print("ObjectManagerGUI","Your selected object needs more detail to be tracked")
            vision.addTarget(trackable)
                


        # Vision.py
        # cascadeTracker.track(frame)
        # cascadeTracker.drawTracked(frame)

        cv2.imshow("frame", frame)

    key = cv2.waitKey(10)

    if key == ord("c"):
        roi = clone[refPt[0][1]:refPt[1][1], refPt[0][0]:refPt[1][0]]
        cv2.imshow("ROI", roi)
        cv2.waitKey(0)

# Close the VideoStream Thread
vStream.endThread()
