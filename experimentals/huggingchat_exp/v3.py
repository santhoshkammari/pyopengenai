
import pyautogui
import time
import logging
import pytesseract

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


def perform_search(query):
    write_and_hit_enter(query)
    wait_till_response_completed()


def scroll_and_get_response():
    logger.info("Scrolling to capture the entire response...")
    screen_width, screen_height = pyautogui.size()
    chat_area = (int(screen_width * 0.25), 0, int(screen_width * 0.75), screen_height)

    # Scroll to top
    logger.info("Scrolling to the top...")
    pyautogui.moveTo(screen_width // 2, screen_height // 2)
    pyautogui.scroll(1000)  # Large positive value to scroll up
    time.sleep(1)  # Wait for scroll to complete

    full_text = ""
    last_text = ""
    scroll_attempts = 0
    max_scroll_attempts = 20  # Adjust this value based on expected response length

    while scroll_attempts < max_scroll_attempts:
        # Capture current view
        screenshot = pyautogui.screenshot(region=chat_area)
        current_text = pytesseract.image_to_string(screenshot)

        print(f"Current text :\n {current_text}\n")
        print("--------------------------------")

        # Append new text to full_text
        full_text += current_text.replace(last_text, "")

        # Scroll down
        pyautogui.scroll(-100)  # Negative value to scroll down
        time.sleep(1)  # Wait for scroll to complete

        # Check if we've reached the end (no new text)
        if current_text == last_text:
            break

        last_text = current_text
        scroll_attempts += 1

    logger.info("Finished capturing response.")
    return full_text

def open_huggingchat_and_request_joke():
    try:
        open_huggingchat()
        perform_search("give me python code to load wikpeda data and use some numpy operation .")
        scroll_and_get_response()
        close_huggingfacechat()
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    logger.info("Starting.. Please don't move the mouse or use the keyboard.")
    open_huggingchat_and_request_joke()