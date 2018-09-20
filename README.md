# raspiSquirrelDetector
### State of the art squirrel detection with the Azure Custom Vision Service

This example solution uses the Azure Custom Vision Service coupled with a Raspberry Pi with Pi Camera and other open source libraries to solve a real-world problem...the detection of squirrels in my yard.

I first built a Custom Vision model on https://customvision.ai by uploading several images of squirrels plus a number of images of other items to classify as "not squirrels". 

The application on the Raspberry Pi is written in Python and performs the following tasks:

- Opens an in-memory video stream and looks for motion using a simple-motion detection algorithm taken from the blog of Ron Ostafichuk: 
http://www.ostafichuk.com/raspberry-pi-projects/python-picamera-motion-detection/
- When motion is detected, an image is captured and stored on the Pi
- The checkForSquirrel function sends the image to the Custom Vision API endpoint and interrogates the JSON response to determine if a squirrel was detected
- If the probability of the prediction is > 80%, the application sends a tweet to Twitter (using the Tweepy library) consisting of the image with the message "Squirrel!"; If the probability is > 50%, it tweets, "Might be a squirrel!"; Otherwise, it tweets nothing
- Secrets are stored in the file "auth.json"; A future version may use KeyVault

NOTE: I used the ptsvd library for remote Python debugging on the Pi from VS Code
