from pathlib import Path

import pyautogui
import time
import logging
import pytesseract
from PIL import Image

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def open_huggingchat():
    # Press the Windows key to open the Ubuntu search
    logger.info("Opening Ubuntu search...")
    pyautogui.press('win')
    time.sleep(0.025)
    # Type "HuggingChat"
    logger.info("Typing 'HuggingChaHuggt' in the search bar...")
    pyautogui.write('HuggingChat')
    logger.info("Pressing Enter to open HuggingChat...")
    pyautogui.press('enter')
    time.sleep(2)


def close_huggingfacechat():
    logger.info("Closing HuggingChat...")
    pyautogui.hotkey('alt', 'f4')

    logger.info("HuggingChat has been opened and closed successfully.")

def get_chat_request(query):
    logger.info("Typing query in HuggingChat...")
    pyautogui.write(query)
    pyautogui.press('enter')

    logger.info("Waiting for the response to complete...")
    while True:
        try:
            # Look for the "Stop generating" button
            stop_button = pyautogui.locateOnScreen('stop_generating_button.png', confidence=0.9)
            if stop_button is None:
                # If the button is not found, wait a bit more to ensure it's really gone
                time.sleep(1)
                # Check one more time to be sure
                stop_button = pyautogui.locateOnScreen('stop_generating_button.png', confidence=0.9)
                if stop_button is None:
                    logger.info("Response generation completed.")
                    break
            time.sleep(0.5)  # Short delay before checking again
        except pyautogui.ImageNotFoundException:
            # If the image is not found, assume generation is complete
            logger.info("Response generation completed.")
            break

    logger.info("Response received.")

def open_huggingchat_and_request_joke():
    try:
        open_huggingchat()
        get_chat_request("tell me a joke of 10000 words")
        close_huggingfacechat()
        exit()





        # Capture the screen area where the response is displayed
        # You'll need to adjust these coordinates based on your screen resolution and where the response appears
        screenshot = pyautogui.screenshot(region=(100, 200, 800, 400))  # Example coordinates, adjust as needed

        # Use OCR to extract text from the screenshot
        joke_text = pytesseract.image_to_string(screenshot)

        logger.info("Joke received from HuggingChat:")
        print(joke_text)

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    # Add a small delay before starting to ensure the script doesn't interfere with any current user actions
    logger.info("Starting in 3 seconds. Please don't move the mouse or use the keyboard.")
    time.sleep(3)
    open_huggingchat_and_request_joke()