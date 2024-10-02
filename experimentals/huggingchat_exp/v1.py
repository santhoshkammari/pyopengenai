import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class HuggingFaceChatOpener:
    def __init__(self, chromedriver_path="/usr/local/bin/chromedriver", headless=False):
        self.chromedriver_path = chromedriver_path
        self.headless = headless
        self.driver = None

    def setup_driver(self):
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--start-maximized")

        self.driver = webdriver.Chrome(self.chromedriver_path, options=chrome_options)

    def open_huggingface_chat(self):
        if not self.driver:
            self.setup_driver()

        url = "https://huggingface.co/chat/"
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            logger.info("Successfully opened Hugging Face Chat page.")
            return True
        except Exception as e:
            logger.error(f"An error occurred while opening Hugging Face Chat: {str(e)}")
            return False

    def cleanup(self):
        if self.driver:
            self.driver.quit()
            logger.info("Browser closed.")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()


if __name__ == "__main__":
    with HuggingFaceChatOpener(headless=False) as chat_opener:
        success = chat_opener.open_huggingface_chat()
        if success:
            input("Press Enter to close the browser...")