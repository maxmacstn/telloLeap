"""
tellopy sample using joystick and video palyer

 - you can use PS3/PS4/XONE joystick to controll DJI Tello with tellopy module
 - you must install mplayer to replay the video
 - Xbox One Controllers were only tested on Mac OS with the 360Controller Driver.
    get it here -> https://github.com/360Controller/360Controller'''
"""

import time
import sys
import tellopy
import pygame
import pygame.locals
import Leap, sys, time
from Leap import CircleGesture, KeyTapGesture, ScreenTapGesture, SwipeGesture
from subprocess import Popen, PIPE



class JoystickPS3:
    # d-pad
    UP = 4  # UP
    DOWN = 6  # DOWN
    ROTATE_LEFT = 7  # LEFT
    ROTATE_RIGHT = 5  # RIGHT

    # bumper triggers
    TAKEOFF = 11  # R1
    LAND = 10  # L1
    # UNUSED = 9 #R2
    # UNUSED = 8 #L2

    # buttons
    FORWARD = 12  # TRIANGLE
    BACKWARD = 14  # CROSS
    LEFT = 15  # SQUARE
    RIGHT = 13  # CIRCLE

    # axis
    LEFT_X = 0
    LEFT_Y = 1
    RIGHT_X = 2
    RIGHT_Y = 3
    LEFT_X_REVERSE = 1.0
    LEFT_Y_REVERSE = -1.0
    RIGHT_X_REVERSE = 1.0
    RIGHT_Y_REVERSE = -1.0
    DEADZONE = 0.1


class JoystickPS4:
    # d-pad
    UP = -1  # UP
    DOWN = -1  # DOWN
    ROTATE_LEFT = -1  # LEFT
    ROTATE_RIGHT = -1  # RIGHT

    # bumper triggers
    TAKEOFF = 5  # R1
    LAND = 4  # L1
    # UNUSED = 7 #R2
    # UNUSED = 6 #L2

    # buttons
    FORWARD = 3  # TRIANGLE
    BACKWARD = 1  # CROSS
    LEFT = 0  # SQUARE
    RIGHT = 2  # CIRCLE

    # axis
    LEFT_X = 0
    LEFT_Y = 1
    RIGHT_X = 2
    RIGHT_Y = 3
    LEFT_X_REVERSE = 1.0
    LEFT_Y_REVERSE = -1.0
    RIGHT_X_REVERSE = 1.0
    RIGHT_Y_REVERSE = -1.0
    DEADZONE = 0.08


class JoystickXONE:
    # d-pad
    UP = 0  # UP
    DOWN = 1  # DOWN
    ROTATE_LEFT = 2  # LEFT
    ROTATE_RIGHT = 3  # RIGHT

    # bumper triggers
    TAKEOFF = 9  # START
    LAND = 8  # LAND
    # UNUSED = 7 #RT
    # UNUSED = 6 #LT
    AUTODEMO = 5  # RB
    # UNUSED = 4 #LB




    # buttons
    FORWARD = 14  # Y
    BACKWARD = 11  # A
    LEFT = 13  # X
    RIGHT = 12  # B

    # axis
    LEFT_X = 0
    LEFT_Y = 1
    RIGHT_X = 2
    RIGHT_Y = 3
    LEFT_X_REVERSE = 1.0
    LEFT_Y_REVERSE = -1.0
    RIGHT_X_REVERSE = 1.0
    RIGHT_Y_REVERSE = -1.0
    DEADZONE = 0.09


class LeapMotionListener(Leap.Listener):

    def on_connect(self, controller):
        print "Connected"


    #def on_frame(self, controller):
    #    print "Frame available"

prev_flight_data = None
video_player = None


def handler(event, sender, data, **args):
    global prev_flight_data
    global video_player
    drone = sender
    if event is drone.EVENT_FLIGHT_DATA:
        if prev_flight_data != str(data):
            print(data)
            prev_flight_data = str(data)

    else:
        print('event="%s" data=%s' % (event.getname(), str(data)))


def update(old, new, max_delta=0.3):
    if abs(old - new) <= max_delta:
        res = new
    else:
        res = 0.0
    return res


def autoDemo(drone):
    drone.forward(50)
    time.sleep(1)
    drone.forward(0)
    time.sleep(0.5)

    drone.left(50)
    time.sleep(1)
    drone.left(0)
    time.sleep(0.5)

    drone.backward(50)
    time.sleep(1)
    drone.backward(0)
    time.sleep(0.5)

    drone.right(50)
    time.sleep(1)
    drone.right(0)
    time.sleep(0.5)

    drone.flip_forward()
    time.sleep(3)

def printLeapInfo(frame):
    finger_names = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky']
    bone_names = ['Metacarpal', 'Proximal', 'Intermediate', 'Distal']
    state_names = ['STATE_INVALID', 'STATE_START', 'STATE_UPDATE', 'STATE_END']
    
    # Get hands
    for hand in frame.hands:

        handType = "Left hand" if hand.is_left else "Right hand"

        print ("  %s, id %d, position: %s" % (
            handType, hand.id, hand.palm_position))

        # Get the hand's normal vector and direction
        normal = hand.palm_normal
        direction = hand.direction

        # Calculate the hand's pitch, roll, and yaw angles
        print ("  pitch: %f degrees, roll: %f degrees, yaw: %f degrees" % (
            direction.pitch * Leap.RAD_TO_DEG,
            normal.roll * Leap.RAD_TO_DEG,
            direction.yaw * Leap.RAD_TO_DEG))

        # Get arm bone
        arm = hand.arm
        print ("  Arm direction: %s, wrist position: %s, elbow position: %s" % (
            arm.direction,
            arm.wrist_position,
            arm.elbow_position))

        # Get fingers
        for finger in hand.fingers:

            print ("    %s finger, id: %d, length: %fmm, width: %fmm" % (
                finger_names[finger.type],
                finger.id,
                finger.length,
                finger.width))

            # Get bones
            for b in range(0, 4):
                bone = finger.bone(b)
                print ("      Bone: %s, start: %s, end: %s, direction: %s" % (
                    bone_names[bone.type],
                    bone.prev_joint,
                    bone.next_joint,
                    bone.direction))

    # Get tools
    for tool in frame.tools:

        print("  Tool id: %d, position: %s, direction: %s" % (
            tool.id, tool.tip_position, tool.direction))

    # Get gestures
    for gesture in frame.gestures():
        if gesture.type == Leap.Gesture.TYPE_CIRCLE:
            circle = CircleGesture(gesture)

            # Determine clock direction using the angle between the pointable and the circle normal
            if circle.pointable.direction.angle_to(circle.normal) <= Leap.PI/2:
                clockwiseness = "clockwise"
            else:
                clockwiseness = "counterclockwise"

            # Calculate the angle swept since the last frame
            swept_angle = 0
            if circle.state != Leap.Gesture.STATE_START:
                previous_update = CircleGesture(controller.frame(1).gesture(circle.id))
                swept_angle =  (circle.progress - previous_update.progress) * 2 * Leap.PI

            print("  Circle id: %d, %s, progress: %f, radius: %f, angle: %f degrees, %s" % (
                    gesture.id, state_names[gesture.state],
                    circle.progress, circle.radius, swept_angle * Leap.RAD_TO_DEG, clockwiseness))

        if gesture.type == Leap.Gesture.TYPE_SWIPE:
            swipe = SwipeGesture(gesture)
            print("  Swipe id: %d, state: %s, position: %s, direction: %s, speed: %f" % (
                    gesture.id, state_names[gesture.state],
                    swipe.position, swipe.direction, swipe.speed))

        if gesture.type == Leap.Gesture.TYPE_KEY_TAP:
            keytap = KeyTapGesture(gesture)
            print("  Key Tap id: %d, %s, position: %s, direction: %s" % (
                    gesture.id, state_names[gesture.state],
                    keytap.position, keytap.direction ))

        if gesture.type == Leap.Gesture.TYPE_SCREEN_TAP:
            screentap = ScreenTapGesture(gesture)
            print("  Screen Tap id: %d, %s, position: %s, direction: %s" % (
                    gesture.id, state_names[gesture.state],
                    screentap.position, screentap.direction ))

    if not (frame.hands.is_empty and frame.gestures().is_empty):
        print ("")


def main():
    pygame.init()
    pygame.joystick.init()
    windowSize = width, height = 800, 600
    screen = pygame.display.set_mode(windowSize)
    font = pygame.font.Font("OpenSans-Regular.ttf", 24)
    LEAPDEADZONE = 0.1
    leapenable = True


    buttons = None
    try:
        js = pygame.joystick.Joystick(0)
        js.init()
        js_name = js.get_name()
        print('Joystick name: ' + js_name)
        if js_name in ('Wireless Controller', 'Sony Computer Entertainment Wireless Controller'):
            buttons = JoystickPS4
        elif js_name in ('PLAYSTATION(R)3 Controller', 'Sony PLAYSTATION(R)3 Controllerwww'):
            buttons = JoystickPS3
        elif js_name == 'Xbox One Wired Controller' or js_name == "Controller (Wireless Gamepad F710)" or js_name == "Logitech Cordless RumblePad 2":
            buttons = JoystickXONE
    except pygame.error:
        pass

    if buttons is None:
        print('Joystick not detected')


    drone = tellopy.Tello()
    drone.connect()
    drone.start_video()
    drone.subscribe(drone.EVENT_FLIGHT_DATA, handler)
    # drone.subscribe(drone.EVENT_VIDEO_FRAME, handler)

    #init leap motion controller
    listener = LeapMotionListener()
    leapController = Leap.Controller()

    # Have the sample listener receive events from the controller
    leapController.add_listener(listener)





    speed = 100
    throttle = 0.0
    yaw = 0.0
    pitch = 0.0
    roll = 0.0

    try:
        while 1:
            # loop with pygame.event.get() is too much tight w/o some sleep
            time.sleep(0.01)
            #time.sleep(0.5)
            joystickControl = False

            for e in pygame.event.get():

                print(e)

                #Handle Joystick control
                if e.type == pygame.locals.JOYAXISMOTION:
                    joystickControl = True
                    print(e.value)
                    # ignore small input values (Deadzone)
                    if -buttons.DEADZONE <= e.value and e.value <= buttons.DEADZONE:
                        e.value = 0.0
                    if e.axis == buttons.LEFT_Y:
                        throttle = update(
                            throttle, e.value * buttons.LEFT_Y_REVERSE)
                        drone.set_throttle(throttle)
                    if e.axis == buttons.LEFT_X:
                        yaw = update(yaw, e.value * buttons.LEFT_X_REVERSE)
                        drone.set_yaw(yaw)
                    if e.axis == buttons.RIGHT_Y:
                        pitch = update(pitch, e.value *
                                       buttons.RIGHT_Y_REVERSE)
                        drone.set_pitch(pitch)
                    if e.axis == buttons.RIGHT_X:
                        roll = update(roll, e.value * buttons.RIGHT_X_REVERSE)
                        drone.set_roll(roll)

                elif e.type == pygame.locals.JOYHATMOTION:
                    joystickControl = True

                    if e.value[0] < 0:
                        drone.counter_clockwise(speed)
                    if e.value[0] == 0:
                        drone.clockwise(0)
                    if e.value[0] > 0:
                        drone.clockwise(speed)
                    if e.value[1] < 0:
                        drone.down(speed)
                    if e.value[1] == 0:
                        drone.up(0)
                    if e.value[1] > 0:
                        drone.up(speed)
                elif e.type == pygame.locals.JOYBUTTONDOWN:
                    joystickControl = True

                    if e.button == buttons.LAND:
                        drone.land()
                    elif e.button == buttons.UP:
                        drone.up(speed)
                    elif e.button == buttons.DOWN:
                        drone.down(speed)
                    elif e.button == buttons.ROTATE_RIGHT:
                        drone.clockwise(speed)
                    elif e.button == buttons.ROTATE_LEFT:
                        drone.counter_clockwise(speed)
                    elif e.button == buttons.FORWARD:
                        drone.forward(speed)
                    elif e.button == buttons.BACKWARD:
                        drone.backward(speed)
                    elif e.button == buttons.RIGHT:
                        drone.right(speed)
                    elif e.button == buttons.LEFT:
                        drone.left(speed)
                elif e.type == pygame.locals.JOYBUTTONUP:
                    joystickControl = True

                    if e.button == buttons.TAKEOFF:
                        drone.takeoff()
                    elif e.button == buttons.UP:
                        drone.up(0)
                    elif e.button == buttons.DOWN:
                        drone.down(0)
                    elif e.button == buttons.ROTATE_RIGHT:
                        drone.clockwise(0)
                    elif e.button == buttons.ROTATE_LEFT:
                        drone.counter_clockwise(0)
                    elif e.button == buttons.FORWARD:
                        drone.forward(0)
                    elif e.button == buttons.BACKWARD:
                        drone.backward(0)
                    elif e.button == buttons.RIGHT:
                        drone.right(0)
                    elif e.button == buttons.LEFT:
                        drone.left(0)
                    elif e.button == buttons.AUTODEMO:  # Autonomous flight for demo
                        print("Auto Demo")
                        autoDemo(drone)


                #handle Keyboard press
                elif e.type == pygame.locals.KEYDOWN:
                    joystickControl = True

                    if e.key == pygame.K_w:
                        drone.up(speed)
                    elif e.key == pygame.K_s:
                        drone.down(speed)
                    if e.key == pygame.K_d:
                        drone.clockwise(speed)
                    if e.key == pygame.K_a:
                        drone.counter_clockwise(speed)
                    if e.key == pygame.K_UP:
                        drone.forward(speed)
                    if e.key == pygame.K_DOWN:
                        drone.backward(speed)
                    if e.key == pygame.K_LEFT:
                        drone.left(speed)
                    if e.key == pygame.K_RIGHT:
                        drone.right(speed)
                    if e.key == pygame.K_RETURN:
                        drone.takeoff()
                    elif e.key == pygame.K_SPACE:
                        leapenable = not leapenable

                elif e.type == pygame.locals.KEYUP:
                    joystickControl = True

                    if e.key == pygame.K_w:
                        drone.up(0)
                    elif e.key == pygame.K_s:
                        drone.down(0)
                    if e.key == pygame.K_d:
                        drone.clockwise(0)
                    if e.key == pygame.K_a:
                        drone.counter_clockwise(0)
                    if e.key == pygame.K_UP:
                        drone.forward(0)
                    if e.key == pygame.K_DOWN:
                        drone.backward(0)
                    if e.key == pygame.K_LEFT:
                        drone.left(0)
                    if e.key == pygame.K_RIGHT:
                        drone.right(0)


                if e.type == pygame.QUIT:
                    drone.quit()
                    exit(1)
                    leapController.remove_listener(listener)


            frame = leapController.frame()
            hand = frame.hands[0]
            handPitch = hand.direction.pitch
            handYaw = hand.direction.yaw
            handRoll = hand.palm_normal.roll


            if frame.hands.is_empty:
                handPitch = 0
                handYaw = 0
                handRoll = 0



            # make sure that the value that came from sensor didn't exceed the limit
            if abs(handPitch) > 1 or abs(handPitch) < LEAPDEADZONE:
                handPitch = 0.0

            if abs(handYaw) > 1 or abs(handYaw) < LEAPDEADZONE:
                handYaw = 0.0

            if abs(handRoll) > 1 or abs(handRoll) < LEAPDEADZONE:
                handRoll = 0.0

            if leapenable and not joystickControl:
                # if e.axis == buttons.LEFT_Y:
                #     throttle = update(
                #         throttle, e.value * buttons.LEFT_Y_REVERSE)
                #     drone.set_throttle(throttle)
                yaw = update(yaw, handYaw  )
                drone.set_yaw(yaw)

                pitch = update(pitch,handPitch * -1 )
                drone.set_pitch(pitch)

                roll = update(roll, handRoll * -1 )
                drone.set_roll(roll)
            
            # printLeapInfo(frame)
                        
            screen.fill((255, 255, 255))



            text_drone_sta = font.render("Drone" + str(drone.state), True, (0, 128, 0))
            screen.blit(text_drone_sta, (20, 10))

            text_hand_roll = font.render('roll : ' + str(roll) , True, (0, 128, 0))
            screen.blit(text_hand_roll, (20, 40))

            text_hand_pitch = font.render('pitch : ' + str(pitch) , True, (0, 128, 0))
            screen.blit(text_hand_pitch, (20, 60))

            text_hand_yaw = font.render('yaw : ' + str(yaw) , True, (0, 128, 0))
            screen.blit(text_hand_yaw, (20, 80))

            text_leap_enable = font.render("Leap motion enable: "+ str(leapenable), True, (0, 128, 0))
            screen.blit(text_leap_enable, (20, 100))


            #text_drone_info = font.render(str(drone), True, (0, 128, 0))
            #screen.blit(text_drone_sta, (20, 20))


            text = font.render(str(e), True, (0, 128, 0))
            screen.blit(text, (20, 120))
            pygame.display.flip()



    except KeyboardInterrupt as e:
        print(e)
    except Exception as e:
        print(e)

    drone.quit()
    exit(1)


if __name__ == '__main__':
    main()
