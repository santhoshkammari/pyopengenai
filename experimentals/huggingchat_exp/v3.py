from pathlib import Path

import pyautogui
import time
import logging
import pytesseract
from PIL import Image

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def open_huggingchat():
    logger.info("Opening Ubuntu search...")
    pyautogui.press('win')
    time.sleep(0.025)
    logger.info("Typing 'HuggingChaHuggt' in the search bar...")
    pyautogui.write('HuggingChat')
    logger.info("Pressing Enter to open HuggingChat...")
    pyautogui.press('enter')
    time.sleep(2)


def close_huggingfacechat():
    logger.info("Closing HuggingChat...")
    pyautogui.hotkey('alt', 'f4')
    logger.info("HuggingChat has been opened and closed successfully.")


def wait_till_response_completed():
    logger.info("Waiting for the response to complete...")
    screen_width, screen_height = pyautogui.size()
    region = (screen_width // 2, screen_height // 2, screen_width // 2, screen_height // 2)
    while True:
        screenshot = pyautogui.screenshot(region=region)  # Adjust these coordinates as needed
        text = pytesseract.image_to_string(screenshot)
        if "stop generating" not in text.lower():
            break
        time.sleep(1)


def write_and_hit_enter(query):
    logger.info("Typing query in HuggingChat...")
    pyautogui.write(query)
    pyautogui.press('enter')


def get_chat_request(query):
    write_and_hit_enter(query)
    wait_till_response_completed()

def open_huggingchat_and_request_joke():
    try:
        open_huggingchat()
        get_chat_request("tell me about narendra modi in very shor paragraph")
        close_huggingfacechat()
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    # Add a small delay before starting to ensure the script doesn't interfere with any current user actions
    logger.info("Starting in 3 seconds. Please don't move the mouse or use the keyboard.")
    open_huggingchat_and_request_joke()