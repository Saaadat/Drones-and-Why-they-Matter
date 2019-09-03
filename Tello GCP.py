from djitellopy import Tello
import cv2
import numpy as np
import time
import datetime
import os
from google_vision import *
from google_bucket import *

# Speed of the drone
S = 30

# Frames per second of the pygame window display
FPS = 25
dimensions = (960, 720)


ddir = "Sessions"

if not os.path.isdir(ddir):
    os.mkdir(ddir)

ddir = "Sessions/Session {}".format(str(datetime.datetime.now()).replace(':','-').replace('.','_'))
os.mkdir(ddir)

class Tello_GCP(object):
    
    def __init__(self):
        # Init Tello object that interacts with the Tello drone
        self.tello = Tello()

        # Drone velocities between -100~100
        self.for_back_velocity = 0
        self.left_right_velocity = 0
        self.up_down_velocity = 0
        self.yaw_velocity = 0
        self.speed = 10

        self.send_rc_control = False

    def run(self):

        if not self.tello.connect():
            print("Tello not connected")
            return

        if not self.tello.set_speed(self.speed):
            print("Not set speed to lowest possible")
            return

        # In case streaming is on. This happens when we quit this program without the escape key.
        if not self.tello.streamoff():
            print("Could not stop video stream")
            return

        if not self.tello.streamon():
            print("Could not start video stream")
            return

        frame_read = self.tello.get_frame_read()

        should_stop = False
        imgCount = 0
        oSpeed = 3
        self.tello.get_battery()
        

        while not should_stop:
            self.update()

            if frame_read.stopped:
                frame_read.stop()
                break

            theTime = str(datetime.datetime.now()).replace(':','-').replace('.','_')

            frame = cv2.cvtColor(frame_read.frame, cv2.COLOR_BGR2RGB)
            frameRet = frame_read.frame

            vid = self.tello.get_video_capture()

            time.sleep(1 / FPS)

            # Listen for key presses
            k = cv2.waitKey(20)

            # Press T to take off
            if k == ord('t'):
                print("Taking Off")
                self.tello.takeoff()
                self.tello.get_battery()
                self.send_rc_control = True

            # Press L to land
            if k == ord('l'):
                print("Landing")
                self.tello.land()
                self.send_rc_control = False


            if k == ord('p'):
                print("Captured")
                cv2.imwrite("{}/tellocap{}.jpg".format(ddir,imgCount),frameRet)
                main_func("{}/tellocap{}.jpg".format(ddir,imgCount), "{}/visionapi{}.jpg".format(ddir,imgCount),50)
                upload_blob("tello-images","{}/tellocap{}.jpg".format(ddir,imgCount),"original_image/tellocap{}.jpg".format(imgCount))
                upload_blob("tello-images","{}/visionapi{}.jpg".format(ddir,imgCount),"vision_image/visionapi{}.jpg".format(imgCount))
                imgCount+=1

            frame = np.rot90(frame)

            # S & W to fly forward & back
            if k == ord('w'):
                self.for_back_velocity = int(S * oSpeed)
            elif k == ord('s'):
                self.for_back_velocity = -int(S * oSpeed)
            else:
                self.for_back_velocity = 0

            # a & d to pan left & right
            if k == ord('d'):
                self.yaw_velocity = int(S * oSpeed)
            elif k == ord('a'):
                self.yaw_velocity = -int(S * oSpeed)
            else:
                self.yaw_velocity = 0

            # Q & E to fly up & down
            if k == ord('e'):
                self.up_down_velocity = int(S * oSpeed)
            elif k == ord('q'):
                self.up_down_velocity = -int(S * oSpeed)
            else:
                self.up_down_velocity = 0

            # c & z to fly left & right
            if k == ord('c'):
                self.left_right_velocity = int(S * oSpeed)
            elif k == ord('z'):
                self.left_right_velocity = -int(S * oSpeed)
            else:
                self.left_right_velocity = 0

            # Quit the software
            if k == 27:
                should_stop = True
                break

            gray  = cv2.cvtColor(frameRet, cv2.COLOR_BGR2GRAY)



            show = "Speed: {}".format(oSpeed)
            dCol = (255,255,255)

            # Draw the distance choosen
            cv2.putText(frameRet,show,(32,664),cv2.FONT_HERSHEY_SIMPLEX,1,dCol,2)

            # Display the resulting frame
            cv2.imshow('Tello Vision',frameRet)

        # On exit, print the battery
        self.tello.get_battery()

        # When everything done, release the capture
        cv2.destroyAllWindows()
        
        # Call it always before finishing. I deallocate resources.
        self.tello.end()


    def battery(self):
        return self.tello.get_battery()[:2]

    def update(self):
        """ Update routine. Send velocities to Tello."""
        if self.send_rc_control:
            self.tello.send_rc_control(self.left_right_velocity, self.for_back_velocity, self.up_down_velocity,
                                       self.yaw_velocity)


def main():
    tello_gcp = Tello_GCP()

    # run frontend
    tello_gcp.run()


if __name__ == '__main__':
    main()
