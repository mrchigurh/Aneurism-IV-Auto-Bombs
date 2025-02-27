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

start_time = time.perf_counter()
user32 = ctypes.windll.user32
images_directory = os.path.join(os.getcwd(), "Images")

inspectIdentifier = os.path.join(images_directory, "inspect.png")
bombScreenIdentifier = os.path.join(images_directory, "bombscreen.png")
sequenceIdentifier = os.path.join(images_directory, "WireIdentify.png")
bombLeverIdentifier = os.path.join(images_directory, "bombleveridentifier.png")

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
    'Red': os.path.join(images_directory, "redwire.png"),
    'White': os.path.join(images_directory, "whitewire.png"),
    'Blue': os.path.join(images_directory, "bluewire.png"),
    'Black': os.path.join(images_directory, "blackwire.png"),
    'Green': os.path.join(images_directory, "greenwire.png"),
}
wireWords = {
    'Red': os.path.join(images_directory, "redWord.png"),
    'White': os.path.join(images_directory, "whiteWord.png"),
    'Blue': os.path.join(images_directory, "blueWord.png"),
    'Black': os.path.join(images_directory, "blackWord.png"),
    'Green': os.path.join(images_directory, "greenWord.png"),
}

last_called_time = 0
time_since_last_reset = 0
bomb_not_seen = 0

main_code_enabled = False

def getScreenshot():
    screenshot = cv2.cvtColor(np.array(pyautogui.screenshot()), cv2.COLOR_BGR2RGB)
    return screenshot

def getResult(sourceImage, needleImage):
    return cv2.matchTemplate(sourceImage, needleImage, cv2.TM_CCOEFF_NORMED)

def getBestResultPos(result):
    return cv2.minMaxLoc(result)[3]

def moveMouse(x, y):
    user32.SetCursorPos(x, y)

def find_image(images_directory, image_filename):

    image_path = os.path.join(images_directory, image_filename)

    if os.path.isfile(image_path):
        return image_path
    else:
        return

def look_for_image(needle_image_path, screenshot, threshold=0.8):
    screenshot = screenshot
    needle_image = cv2.imread(needle_image_path, cv2.IMREAD_COLOR)
    result = getResult(screenshot, needle_image)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    return max_val > threshold

def get_image_confidence(needle_image_path, screenshot=None, threshold=0.8):
    screenshot = screenshot
    needle_image = cv2.imread(needle_image_path, cv2.COLOR_BGR2RGB)
    result = getResult(screenshot, needle_image)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    return max_val

def find_image_position(screenshot, needle_image_path, threshold=0.8):
    needle_image = cv2.imread(needle_image_path, cv2.COLOR_BGR2RGB)
    result = getResult(screenshot, needle_image)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    if max_val > threshold:
        return max_loc
    return None

def press_key(key, duration=0.01):
    pydirectinput.keyDown(key)
    time.sleep(duration)
    pydirectinput.keyUp(key)

def take_screenshot_dimensions(center, width, height):
    center_x, center_y = center

    x1 = center_x - width // 2
    y1 = center_y - height // 2
    x2 = center_x + width // 2
    y2 = center_y + height // 2

    screen = pyautogui.screenshot(region=(x1, y1, width, height))

    screen_np = np.array(screen)
    screen_cv2 = cv2.cvtColor(screen_np, cv2.COLOR_BGR2RGB)

    return screen_cv2

def find_all_image_positions(screenshot, needle_image_path, threshold=0.8, min_distance=5):
    needle_image = cv2.imread(needle_image_path, cv2.IMREAD_COLOR)
    result = getResult(screenshot, needle_image)
    locations = []
    spatial_grid = {}
    grid_size = min_distance
    for y in range(result.shape[0]):
        for x in range(result.shape[1]):
            if result[y, x] >= threshold:
                grid_x, grid_y = x // grid_size, y // grid_size
                if (grid_x, grid_y) not in spatial_grid:
                    spatial_grid[(grid_x, grid_y)] = (x, y)
                    locations.append((x, y))
    return locations

def compare_lists(list1, list2):

    for i in range(len(list1)):
        if list1[i] != list2[i]:
            print(f"Mismatch at index {i}: {list1[i]} != {list2[i]}")
            return False

    return True

def colorDetection(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    height, width, _ = hsv.shape
    center_x, center_y = width // 2, height // 2
    region_size = min(width, height) // 4

    center_region = hsv[
        center_y - region_size:center_y + region_size,
        center_x - region_size:center_x + region_size
    ]

    color_ranges = {
        "Red": [(np.array([0, 100, 50]), np.array([10, 255, 255])),
                (np.array([170, 100, 50]), np.array([180, 255, 255]))],  # Two red ranges
        "Yellow": [(np.array([20, 100, 100]), np.array([30, 255, 255]))],
        "Green": [(np.array([40, 50, 50]), np.array([85, 255, 255]))],  # Adjusted to avoid blue
        "Blue": [(np.array([100, 150, 50]), np.array([130, 255, 255]))],  # Dark blue focus
        "Black": [(np.array([0, 0, 0]), np.array([180, 50, 50]))],  # Low brightness
    }

    colorRatios = {}
    for color, ranges in color_ranges.items():
        mask = sum(cv2.inRange(center_region, lower, upper) for lower, upper in ranges)
        colorRatios[color] = cv2.countNonZero(mask)

    detected_color = max(colorRatios, key=colorRatios.get)

    return detected_color if colorRatios[detected_color] > 0 else "Unknown"

def checkInspectIdentiferRecursive():
    if not main_code_enabled:
        return
    if USE_INSPECT_IDENTIFIER:
        result = look_for_image(inspectIdentifier, getScreenshot())
        if not result:
            time.sleep(.03)
            checkInspectIdentiferRecursive()

def main():
    while main_code_enabled:
        while main_code_enabled:
            checkInspectIdentiferRecursive()
            press_key('e')
            time.sleep(.01)
            screenshot = take_screenshot_dimensions(bombScreenPixelLoc, 300, 300)
            if look_for_image(bombScreenIdentifier, screenshot):
                break

        if not main_code_enabled:
            return

        wireCoordinateColors = list()
        for wireCoordinate in wireCoordinates:
            screenshot = take_screenshot_dimensions(wireCoordinate, 100, 25)
            closestColor = None
            highestConfidence = 0
            for wireColor, wireImage in wireColors.items():
                confidence = get_image_confidence(wireImage, screenshot)
                if confidence > highestConfidence:
                    highestConfidence = confidence
                    closestColor = wireColor

            if closestColor == 'Blue' or closestColor == 'Black' or closestColor == 'Green':
                closestColor = colorDetection(screenshot)

            wireCoordinateColors.append(closestColor)

        posDict = dict()
        wordCoordinateColors = list()

        for wordCoordinate in wordCoordinates:
            screenshot = take_screenshot_dimensions(wordCoordinate, 200, 50)
            closestWord = None
            highestConfidence = 0
            for wordColor, wordImage in wireWords.items():
                confidence = get_image_confidence(wordImage, screenshot)
                if confidence > highestConfidence:
                    highestConfidence = confidence
                    closestWord = wordColor

            wordCoordinateColors.append(closestWord)

        flattened_pos_list = [(wordName, pos) for wordName in posDict for pos in posDict[wordName]]
        sorted_pos_list = sorted(flattened_pos_list, key=lambda x: x[1][1], reverse=False)

        #print('WIRE COLORS:')
        #print(wireCoordinateColors)
        #print('COLOR SEQUENCE:')
        #print(wordCoordinateColors)

        result = compare_lists(wireCoordinateColors, wordCoordinateColors)
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
    global main_code_enabled
    main_code_enabled = not main_code_enabled

    if main_code_enabled:
        print('ENABLED | HOVER OVER BOMBS')
        thread = threading.Thread(target=main)
        thread.start()
    else:
        print('DISABLED')

keyboard.add_hotkey(TOGGLE_KEY, mainToggle)
keyboard.wait(END_SCRIPT_KEY)
