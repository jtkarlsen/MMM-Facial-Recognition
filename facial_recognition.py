import json
import urllib
import requests
import sys
import time
import subprocess
from datetime import datetime, timedelta
import RPi.GPIO as GPIO
from picamera import PiCamera
import serial
import traceback
import logging

# Logging
logging.basicConfig(filename='facial_regognition.log',level=logging.DEBUG)

# Arduino
USBSerial = '/dev/ttyACM0'
baud = 9600
arduino = serial.Serial(USBSerial, baud, timeout=1)

# Camera
camera = PiCamera()
camera.brightness = 55
camera.resolution = (1024, 768)

# Range detection
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
TRIG = 23
ECHO = 24
GPIO.setup(TRIG,GPIO.OUT)
GPIO.setup(ECHO,GPIO.IN)

detect_params = urllib.urlencode({
    'returnFaceId': 'true'
})

# Vars
base_url = 'https://api.projectoxford.ai/face/v1.0/'
subscription_key = '*SECRET*'
last_lookup = datetime.now() - timedelta(seconds=60)
last_detection = datetime.now()
user_is_present = False


def capture_picture():
    logging.debug('Taking picture')
    camera.capture('image.jpg')
    return


def facial_recognition():
    logging.debug('Starting facial recognition')
    global last_lookup
    last_lookup = datetime.now()

    capture_picture()
    faces = detect_faces()
    logging.debug('Faces:')
    logging.debug(faces)
    identities = identify_faces(faces)
    logging.debug('Identities:')
    logging.debug(identities)
    names = get_identity_names(identities)
    logging.debug('Names:')
    logging.debug(names)
    push_to_mirror(names, len(faces))


def detect_faces():
    headers = {
        'Content-Type': 'application/octet-stream',
        'Ocp-Apim-Subscription-Key': subscription_key,
    }
    url = base_url + 'detect?' + detect_params
    data = open('./image.jpg', 'rb').read()
    response = requests.post(url, data=data, headers=headers)
    try:
        faces = []
        face_objects = response.json()
        for face_object in face_objects:
            faces.append(face_object['faceId'])
        return faces
    except IndexError:
        logging.debug('Exception when detecting faces')
        logging.error(traceback.print_exc())
        return []


def identify_faces(faces):
    headers = {
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': subscription_key,
    }
    url = base_url + 'identify'
    body = {
        "personGroupId": "beboere",
        "faceIds": faces,
        "maxNumOfCandidatesReturned": 1,
        "confidenceThreshold": 0.5
    }
    response = requests.post(url, data=json.dumps(body), headers=headers)
    try:
        identities = []
        identity_objects = response.json()
        for identity_object in identity_objects:
            candidates = identity_object['candidates']
            if len(candidates) > 0:
                identities.append(identity_object['candidates'][0]['personId'])
        return identities
    except Exception:
        logging.debug('Exception when identifying faces')
        logging.error(traceback.print_exc())
        return []


def get_identity_names(identities):
    names = []
    for identity in identities:
        names.append(identity_request(identity))
    return names


def identity_request(identity):
    headers = {
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': subscription_key,
    }
    url = base_url + 'persongroups/beboere/persons/' + identity
    response = requests.get(url, params=None, headers=headers)
    return response.json()['name']


def push_to_mirror(names, detection_count):
    try:
        # print(json.dumps({names: names, detection_count: detection_count}))
        print json.dumps(names)
    except Exception:
        logging.error(traceback.print_exc())
        pass
    sys.stdout.flush()


def is_time_for_lookup():
    if (datetime.now() - last_lookup).total_seconds() > 15:
        return True
    else:
        return False


def distance():
    # set Trigger to HIGH
    GPIO.output(TRIG, True)

    # set Trigger after 0.01ms to LOW
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    StartTime = time.time()
    StopTime = time.time()

    # save StartTime
    while GPIO.input(ECHO) == 0:
        StartTime = time.time()

    # save time of arrival
    while GPIO.input(ECHO) == 1:
        StopTime = time.time()

    # time difference between start and arrival
    TimeElapsed = StopTime - StartTime
    # multiply with the sonic speed (34300 cm/s)
    # and divide by 2, because there and back
    distance = (TimeElapsed * 34300) / 2
    logging.debug('Distance: '+str(distance))
    return distance


def set_user_present():
    logging.debug('User is present')
    global user_is_present
    user_is_present = True
    arduino.write("white")
    subprocess.call(['./modules/facial_recognition/image_on.sh'])


def set_user_not_present():
    logging.debug('User is NOT present')
    global user_is_present
    user_is_present = False
    arduino.write("black")
    subprocess.call(['./modules/facial_recognition/image_off.sh'])


def could_turn_off():
    if (datetime.now() - last_detection).total_seconds() > 10:
        set_user_not_present()


def loop_de_loop():
    global last_detection
    set_user_not_present()
    last_true = False
    while True:
        if distance() < 130:
            logging.debug('Distance under 130')
            if last_true:
                logging.debug('Twice')
                last_detection = datetime.now()
                if not user_is_present:
                    set_user_present()
                if is_time_for_lookup():
                    time.sleep(0.5)
                    facial_recognition()
            last_true = True
        elif user_is_present:
            last_true = False
            could_turn_off()
        time.sleep(0.5)


logging.info('Starting application')
loop_de_loop()