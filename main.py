import pyautogui
import cv2
import time
import keyboard
import os
import numpy as np
import ctypes
import pydirectinput
import threading
import configparser

ConfigParser = configparser.ConfigParser()
config = configparser.ConfigParser()
config.read('config.ini')

# CONFIG
USE_INSPECT_IDENTIFIER = config.getboolean('settings', 'use_bomb_identifier')
TOGGLE_KEY = config.get('settings', 'start_keybind')
END_SCRIPT_KEY = config.get('settings', 'end_script_keybind')

# Code

mainCodeEnabled = False

start_time = time.perf_counter()
user32 = ctypes.windll.user32
imagesDirectory = os.path.join(os.getcwd(), "Images")

inspectIdentifier = os.path.join(imagesDirectory, "inspect.png")
bombScreenIdentifier = os.path.join(imagesDirectory, "bombscreen.png")
sequenceIdentifier = os.path.join(imagesDirectory, "WireIdentify.png")
bombLeverIdentifier = os.path.join(imagesDirectory, "bombleveridentifier.png")

bombScreenPixelLoc = (1219, 253)

positions = {
    "bombscreen": (1208, 250)
}
wireCoordinates = [
    (640, 489),
    (640, 538),
    (640, 587),
    (640, 650),
    (640, 690)
]
wordCoordinates = [
    (1195, 725),
    (1195, 753),
    (1195, 781),
    (1195, 802),
    (1195, 830)
]
wireColors = {
    'Red': os.path.join(imagesDirectory, "redwire.png"),
    'White': os.path.join(imagesDirectory, "whitewire.png"),
    'Blue': os.path.join(imagesDirectory, "bluewire.png"),
    'Black': os.path.join(imagesDirectory, "blackwire.png"),
    'Green': os.path.join(imagesDirectory, "greenwire.png"),
}
wireWords = {
    'Red': os.path.join(imagesDirectory, "redWord.png"),
    'White': os.path.join(imagesDirectory, "whiteWord.png"),
    'Blue': os.path.join(imagesDirectory, "blueWord.png"),
    'Black': os.path.join(imagesDirectory, "blackWord.png"),
    'Green': os.path.join(imagesDirectory, "greenWord.png"),
}

def getScreenshot():
    screenshot = cv2.cvtColor(np.array(pyautogui.screenshot()), cv2.COLOR_BGR2RGB)
    return screenshot

def getResult(sourceImage, needleImage):
    return cv2.matchTemplate(sourceImage, needleImage, cv2.TM_CCOEFF_NORMED)

def getBestResultPos(result):
    return cv2.minMaxLoc(result)[3]

def moveMouse(x, y):
    user32.SetCursorPos(x, y)

def findImage(imagesDirectory, imageFilename):
    imagePath = os.path.join(imagesDirectory, imageFilename)

    if os.path.isfile(imagePath):
        return imagePath
    else:
        return

def lookForImage(needleImagePath, screenshot, threshold=0.8):
    screenshot = screenshot
    needleImage = cv2.imread(needleImagePath, cv2.IMREAD_COLOR)
    result = getResult(screenshot, needleImage)
    minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(result)
    return maxVal > threshold

def getImageConfidence(needleImagePath, screenshot=None, threshold=0.8):
    screenshot = screenshot
    needleImage = cv2.imread(needleImagePath, cv2.COLOR_BGR2RGB)
    result = getResult(screenshot, needleImage)
    minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(result)
    return maxVal

def findImagePosition(screenshot, needleImagePath, threshold=0.8):
    needleImage = cv2.imread(needleImagePath, cv2.COLOR_BGR2RGB)
    result = getResult(screenshot, needleImage)
    minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(result)
    if maxVal > threshold:
        return maxLoc
    return None

def pressKey(key, duration=0.01):
    pydirectinput.keyDown(key)
    time.sleep(duration)
    pydirectinput.keyUp(key)

def takeScreenshotDimensions(center, width, height):
    centerX, centerY = center

    x1 = centerX - width // 2
    y1 = centerY - height // 2
    x2 = centerX + width // 2
    y2 = centerY + height // 2

    screen = pyautogui.screenshot(region=(x1, y1, width, height))

    screenNp = np.array(screen)
    screenCv2 = cv2.cvtColor(screenNp, cv2.COLOR_BGR2RGB)

    return screenCv2

def findAllImagePositions(screenshot, needleImagePath, threshold=0.8, minDistance=5):
    needleImage = cv2.imread(needleImagePath, cv2.IMREAD_COLOR)
    result = getResult(screenshot, needleImage)
    locations = []
    spatialGrid = {}
    gridSize = minDistance
    for y in range(result.shape[0]):
        for x in range(result.shape[1]):
            if result[y, x] >= threshold:
                gridX, gridY = x // gridSize, y // gridSize
                if (gridX, gridY) not in spatialGrid:
                    spatialGrid[(gridX, gridY)] = (x, y)
                    locations.append((x, y))
    return locations

def compareLists(list1, list2):
    for i in range(len(list1)):
        if list1[i] != list2[i]:
            print(f"Mismatch at index {i}: {list1[i]} != {list2[i]}")
            return False
    return True

def colorDetection(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    height, width, _ = hsv.shape
    centerX, centerY = width // 2, height // 2
    regionSize = min(width, height) // 4

    centerRegion = hsv[
        centerY - regionSize:centerY + regionSize,
        centerX - regionSize:centerX + regionSize
    ]

    colorRanges = {
        "Red": [(np.array([0, 100, 50]), np.array([10, 255, 255])),
                (np.array([170, 100, 50]), np.array([180, 255, 255]))],  # Two red ranges
        "Yellow": [(np.array([20, 100, 100]), np.array([30, 255, 255]))],
        "Green": [(np.array([40, 50, 50]), np.array([85, 255, 255]))],  # Adjusted to avoid blue
        "Blue": [(np.array([100, 150, 50]), np.array([130, 255, 255]))],  # Dark blue focus
        "Black": [(np.array([0, 0, 0]), np.array([180, 50, 50]))],  # Low brightness
    }

    colorRatios = {}
    for color, ranges in colorRanges.items():
        mask = sum(cv2.inRange(centerRegion, lower, upper) for lower, upper in ranges)
        colorRatios[color] = cv2.countNonZero(mask)

    detectedColor = max(colorRatios, key=colorRatios.get)

    return detectedColor if colorRatios[detectedColor] > 0 else "Unknown"

def checkInspectIdentifierRecursive():
    if not mainCodeEnabled:
        return
    if USE_INSPECT_IDENTIFIER:
        result = lookForImage(inspectIdentifier, getScreenshot())
        if not result:
            time.sleep(.03)
            checkInspectIdentifierRecursive()


def main():
    while mainCodeEnabled:
        while mainCodeEnabled:
            checkInspectIdentifierRecursive()
            pressKey('e')
            time.sleep(.01)
            screenshot = takeScreenshotDimensions(bombScreenPixelLoc, 300, 300)
            if lookForImage(bombScreenIdentifier, screenshot):
                break

        if not mainCodeEnabled:
            return

        wireCoordinateColors = list()
        for wireCoordinate in wireCoordinates:
            screenshot = takeScreenshotDimensions(wireCoordinate, 100, 25)
            closestColor = None
            highestConfidence = 0
            for wireColor, wireImage in wireColors.items():
                confidence = getImageConfidence(wireImage, screenshot)
                if confidence > highestConfidence:
                    highestConfidence = confidence
                    closestColor = wireColor

            if closestColor == 'Blue' or closestColor == 'Black' or closestColor == 'Green':
                closestColor = colorDetection(screenshot)

            wireCoordinateColors.append(closestColor)

        posDict = dict()
        wordCoordinateColors = list()

        for wordCoordinate in wordCoordinates:
            screenshot = takeScreenshotDimensions(wordCoordinate, 200, 50)
            closestWord = None
            highestConfidence = 0
            for wordColor, wordImage in wireWords.items():
                confidence = getImageConfidence(wordImage, screenshot)
                if confidence > highestConfidence:
                    highestConfidence = confidence
                    closestWord = wordColor

            wordCoordinateColors.append(closestWord)

        flattenedPosList = [(wordName, pos) for wordName in posDict for pos in posDict[wordName]]
        sortedPosList = sorted(flattenedPosList, key=lambda x: x[1][1], reverse=False)

        #print('WIRE COLORS:')
        #print(wireCoordinateColors)
        #print('COLOR SEQUENCE:')
        #print(wordCoordinateColors)

        result = compareLists(wireCoordinateColors, wordCoordinateColors)
        # print(result)
        if result:
            moveMouse(1359, 792)
            pydirectinput.mouseDown(button='left')
            time.sleep(.05)
            pydirectinput.mouseUp(button='left')
            time.sleep(.05)
            moveMouse(956, 12)
            pydirectinput.mouseDown(button='left')
            time.sleep(.05)
            pydirectinput.mouseUp(button='left')
        else:
            moveMouse(956, 12)
            pydirectinput.mouseDown(button='left')
            time.sleep(.05)
            pydirectinput.mouseUp(button='left')

def mainToggle():
    global mainCodeEnabled
    mainCodeEnabled = not mainCodeEnabled

    if mainCodeEnabled:
        print('ENABLED | HOVER OVER BOMBS')
        thread = threading.Thread(target=main)
        thread.start()
    else:
        print('DISABLED')


keyboard.add_hotkey(TOGGLE_KEY, mainToggle)
keyboard.wait(END_SCRIPT_KEY)
