import sys
sys.path.append("../")

from Logic import Video
from Logic.Vision import PlaneTracker
from Logic.Vision import CascadeTracker
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
# planeTracker   = PlaneTracker(25.0, historyLen)
# planeTracker.addView(view)
cascadeTracker = CascadeTracker(historyLen, cascadePath)
cascadeTracker.addTarget("Face")

# Play video until the user presses "q"
key = None
while not key == ord("q"):
    # Request the latest frame from the VideoStream
    frame = vStream.getFilteredFrame()

    # If the camera has started up, then show the frame
    if frame is not None: 

        # Vision.py
        cascadeTracker.track(frame)
        cascadeTracker.drawTracked(frame)

        cv2.imshow("frame", frame)

    key = cv2.waitKey(10)

# Close the VideoStream Thread
vStream.endThread()
