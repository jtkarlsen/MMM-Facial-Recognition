import json
import urllib
import requests
import sys
import time
import subprocess
from datetime import datetime, timedelta
import RPi.GPIO as GPIO
from picamera import PiCamera
import traceback

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
    # print 'taking picture'
    camera.capture('image.jpg')
    return


def facial_recognition():
    # print 'Starting facial recognition'
    global last_lookup
    last_lookup = datetime.now()

    capture_picture()
    faces = detect_faces()
    # print faces
    identities = identify_faces(faces)
    # print identities
    names = get_identity_names(identities)
    # print names
    push_to_mirror(names, len(faces))


def detect_faces():
    # print 'detecting faces'
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
        # print 'Exception in detecting faces'
        # print traceback.print_exc()
        return []


def identify_faces(faces):
    # print 'identifying faces'
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
        # print 'Exception in identifying faces'
        # print traceback.print_exc()
        return []


def get_identity_names(identities):
    # print 'getting names'
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
    return distance


def set_user_present():
    global user_is_present
    user_is_present = True
    subprocess.call(['./image_on.sh'])


def set_user_not_present():
    global user_is_present
    user_is_present = False
    subprocess.call(['./image_off.sh'])


def could_turn_off():
    last_detection_delta = datetime.now() - last_detection
    if last_detection_delta.total_seconds() > 10:
        set_user_not_present()


def loop_de_loop():
    global last_detection
    set_user_not_present()
    while True:
        if distance() < 130:
            last_detection = datetime.now()
            if not user_is_present:
                set_user_present()

            if is_time_for_lookup():
                time.sleep(0.5)
                facial_recognition()

        elif user_is_present:
            could_turn_off()
        time.sleep(1)


loop_de_loop()