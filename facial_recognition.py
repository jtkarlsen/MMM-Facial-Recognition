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
import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

# Logging
logging.basicConfig(filename='facial_recognition.log', level=logging.DEBUG)

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
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

detect_params = urllib.urlencode({
    'returnFaceId': 'true'
})

# Vars
face_base_url = 'https://northeurope.api.cognitive.microsoft.com/face/v1.0/'
emotion_base_url = 'https://westus.api.cognitive.microsoft.com/emotion/v1.0/recognize'
face_subscription_key = os.getenv("FACE_API_KEY")
emotion_subscription_key = os.getenv("EMOTION_API_KEY")
last_face_lookup = datetime.now() - timedelta(seconds=60)
last_emotion_lookup = datetime.now() - timedelta(seconds=60)
last_detection = datetime.now()
user_is_present = False
lights_on = False
monitor_on = False


def capture_picture():
    image_name = "./faces/" + datetime.now().strftime("%Y-%m-%dT%H:%M:%S") + ".jpg"
    logging.debug('Taking picture ' + image_name)
    camera.capture(image_name)
    return image_name


def facial_recognition():
    logging.debug('Starting facial recognition')
    global last_face_lookup
    last_face_lookup = datetime.now()

    image_name = capture_picture()
    faces = detect_faces(image_name)
    logging.debug('Faces:')
    logging.debug(faces)
    if len(faces) > 0:
        identities = identify_faces(faces)
        logging.debug('Identities:')
        logging.debug(identities)
        names = get_identity_names(identities)
        logging.debug('Names:')
        logging.debug(names)
        push_identities_to_mirror(names, len(faces))


def detect_faces(image_name):
    headers = {
        'Content-Type': 'application/octet-stream',
        'Ocp-Apim-Subscription-Key': face_subscription_key,
    }
    url = face_base_url + 'detect?' + detect_params
    data = open(image_name, 'rb').read()
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
        'Ocp-Apim-Subscription-Key': face_subscription_key,
    }
    url = face_base_url + 'identify'
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
        'Ocp-Apim-Subscription-Key': face_subscription_key,
    }
    url = face_base_url + 'persongroups/beboere/persons/' + identity
    response = requests.get(url, params=None, headers=headers)
    return response.json()['name']


def push_identities_to_mirror(names, detection_count):
    data = {}
    data['type'] = 'identity'
    data['names'] = names
    data['faces'] = detection_count
    push_to_mirror(data)


def push_emotion_to_mirror(emotion):
    data = {}
    data['type'] = 'emotion'
    data['emotion'] = emotion
    push_to_mirror(data)


def push_to_mirror(data):
    logging.debug('pushing to mirror')
    logging.debug(data)
    try:
        print json.dumps(data)
    except Exception:
        logging.error(traceback.print_exc())
        pass
    sys.stdout.flush()


def is_time_for_face_lookup():
    if (datetime.now() - last_face_lookup).total_seconds() > 15:
        return True
    else:
        return False


def is_time_for_emotion_lookup():
    if (datetime.now() - last_emotion_lookup).total_seconds() > 20:
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
    if distance < 150:
        logging.debug('Distance: '+str(distance))
    return distance


def turn_on_monitor():
    global monitor_on
    if not monitor_on:
        logging.debug("Turning on monitor")
        monitor_on = True
        subprocess.call(['./modules/facial_recognition/image_on.sh'])


def turn_off_monitor():
    global monitor_on
    if monitor_on:
        logging.debug("Turning off monitor")
        monitor_on = False
        subprocess.call(['./modules/facial_recognition/image_off.sh'])


def turn_on():
    logging.debug('Turn on')
    global user_is_present
    user_is_present = True
    turn_on_lights()
    turn_on_monitor()


def turn_off():
    global user_is_present
    user_is_present = False
    seconds_since_last_detection = (
        datetime.now() - last_detection).total_seconds()
    if seconds_since_last_detection > 300:
        turn_off_monitor()
    if seconds_since_last_detection > 15:
        turn_off_lights()


def turn_on_lights():
    global lights_on
    if not lights_on:
        logging.debug("Turning on light")
        lights_on = True
        arduino.write("white")


def turn_off_lights():
    global lights_on
    if lights_on:
        logging.debug("Turning off light")
        lights_on = False
        arduino.write("black")


def get_emotion():
    logging.debug('Starting emotion')
    global last_emotion_lookup
    last_emotion_lookup = datetime.now()
    image_name = capture_picture()
    headers = {
        'Content-Type': 'application/octet-stream',
        'Ocp-Apim-Subscription-Key': emotion_subscription_key,
    }
    data = open(image_name, 'rb').read()
    response = requests.post(emotion_base_url, data=data, headers=headers)
    try:
        emotion = response.json()
        push_emotion_to_mirror(emotion)
    except IndexError:
        logging.debug('Exception when detecting emotion')
        logging.error(traceback.print_exc())
        return []


def loop_de_loop():
    global user_is_present
    global last_detection
    turn_off()
    user_is_present = True
    user_present_count = 0
    while True:
        if distance() < 130:
            if user_present_count > 5:
                last_detection = datetime.now()
                if not user_is_present:
                    turn_on()
                if is_time_for_face_lookup():
                    time.sleep(0.5)
                    facial_recognition()
            if user_present_count > 15:
                if is_time_for_emotion_lookup():
                    get_emotion()
            user_present_count += 1
        else:
            user_present_count = 0
            turn_off()
        time.sleep(0.05)


logging.info('Starting application')
loop_de_loop()
