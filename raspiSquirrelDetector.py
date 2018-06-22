# Raspberry Pi Squirrel Detector
# Squirrel Detection performed with the Microsoft Azure Custom Vision Service: http://customvision.ai
# Motion detection code adapted from the blog of Ron Ostafichuk: 
# http://www.ostafichuk.com/raspberry-pi-projects/python-picamera-motion-detection/

# Required for remote debugging
# import ptvsd
# ptvsd.enable_attach("my_secret", address = ('192.168.10.224', 3000))
# print('Attach debugger now...')
# ptvsd.wait_for_attach()

# Imports
import io
import os
import logging
import json
import tweepy
import time
import numpy as np
from datetime import datetime
from picamera import PiCamera
from azure.cognitiveservices.vision.customvision.prediction import prediction_endpoint
from azure.cognitiveservices.vision.customvision.prediction.prediction_endpoint import models

# Constants
path = '/home/pi/raspiSquirrelDetector/'
width = 1024            # Image Width
height = 768            # Image Height
colorThreshold = 30     # Color value change to be considered motion
pixelThreshold = width * height * .0175   # Number of pixels changed to be considered motion

# Initialize logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.FileHandler(path + 'raspiSquirrelDetector.log','w')
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logging.info('{0} Logger initialized'.format(datetime.now()))

# Load secrects
with open(path + 'auth.json') as authFile:
    secrets = json.load(authFile)
logging.info('{0} Secrets loaded'.format(datetime.now()))

# Initialize camera
camera = PiCamera()
camera.resolution = (1024,768)
logging.info('{0} Camera initialized'.format(datetime.now()))

# Initialize Custom Vision predictor
projectId = secrets['project_id']
predictKey = secrets['predict_key']
predictor = prediction_endpoint.PredictionEndpoint(predictKey)
logging.info('{0} Predictor initialized'.format(datetime.now()))

# Initialize Twitter
auth = tweepy.OAuthHandler(secrets['consumer_key'], secrets['consumer_secret'])
auth.set_access_token(secrets['access_token'], secrets['access_token_secret'])
twitter = tweepy.API(auth)
logging.info('{0} Twitter initialized'.format(datetime.now()))

# Initialize in-memory stream
stream = io.BytesIO()
step = 1            # use this to toggle where the image gets saved
numImages = 1       # count number of images processed
captureCount = 0    # flag used to begin a sequence capture
logging.info('{0} Image stream initialized'.format(datetime.now()))

# Function to call the predictor endpoint and check if the captured image contains a squirrel and tweet out if it sees one
def checkForSquirrel(fileStr):
    with open(fileStr, 'rb') as imageFile:
        imageBytes = imageFile.read()
        imageFile.close()

    results = predictor.predict_image(projectId, imageBytes)

    for pred in results.predictions:
        if pred.tag_name == 'Squirrel':
            if pred.probability > .8:
                status = 'Squirrel!'
                twitter.update_with_media(fileStr, status)
            elif pred.probability > .5:
                status = 'Might be a squirrel!'
                twitter.update_with_media(fileStr, status)
            else:
                status = 'Not a squirrel!'
            logging.info('{0} {1} Probability: {2:.5f}%'.format(datetime.now(), status, pred.probability * 100))
            print('{0} {1} Probability: {2:.5f}%'.format(datetime.now(), status, pred.probability * 100))

    time.sleep(10)  # Wait 10 seconds after checking an image

# Begin monitoring
print('Begin monitoring')
logging.info('{0} Begin monitoring'.format(datetime.now()))
try:
    while colorThreshold > 0:
        if step == 1:
            stream.seek(0)
            camera.capture(stream, 'rgba', True)    # use video port for high speed
            data1 = np.fromstring(stream.getvalue(), dtype=np.uint8)
            step = 2
        else:
            stream.seek(0)
            camera.capture(stream, 'rgba', True)
            data2 = np.fromstring(stream.getvalue(), dtype=np.uint8)
            step = 1
        numImages = numImages + 1

        if numImages > 4:  # ignore first few images because if the camera is not quite ready it will register as motion right away
            # look for motion unless we are in save mode
            if captureCount <= 0:
                # not capturing, test for motion
                data3 = np.abs(data1 - data2)  # get difference between 2 successive images
                numTriggers = np.count_nonzero(data3 > colorThreshold) / 4 / colorThreshold # there are 4 times the number of pixels due to rgba

                if numTriggers > pixelThreshold:
                    logging.info('{0} Motion detected!'.format(datetime.now()))
                    captureCount = 1 # Number of images to capture
                    
                    d = path + time.strftime("capture/%Y%m%d") # make sure directory exists for today
                    if not os.path.exists(d):
                        os.makedirs(d)
            else:
                fileStr = path + time.strftime("capture/%Y%m%d/%Y%m%d-%H%M%S.jpg",time.localtime())
                camera.capture(fileStr,'jpeg',use_video_port=True, quality=92)
                captureCount = captureCount-1
                logging.info('{0} Image captured: {1}'.format(datetime.now(), fileStr))
                checkForSquirrel(fileStr)

except Exception as e:
    print('[Error: {0}]'.format(e))
    logging.error('{0} [Error: {0}]'.format(e))

finally:
    camera.close()
    print('Program terminated.')
    logging.info('{0} Program terminated'.format(datetime.now()))
