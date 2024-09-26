import json
from textwrap import indent

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pydantic import BaseModel
from typing import List
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TwitterContent(BaseModel):
    tweets: List[str] = []
    page_source: str = ""


class TwitterScraper:
    def __init__(self, chromedriver_path="/usr/local/bin/chromedriver", headless=False,
                 scroll_count=5):
        self.chromedriver_path = chromedriver_path
        self.headless = headless
        self.driver = None
        self.scroll_count = scroll_count

    def _setup_driver(self):
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--start-maximized")
        return webdriver.Chrome(self.chromedriver_path, options=chrome_options)

    def login_to_twitter(self, username, password):
        self.driver = self._setup_driver()
        self.driver.get("https://twitter.com/login")

        # Wait for the username field and enter the username
        username_field = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, "text"))
        )
        username_field.send_keys(username)
        self.driver.find_element(By.XPATH, "//span[text()='Next']").click()

        # Wait for the password field and enter the password
        password_field = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, "password"))
        )
        password_field.send_keys(password)
        self.driver.find_element(By.XPATH, "//span[text()='Log in']").click()

        # Wait for the home page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@data-testid='primaryColumn']"))
        )

    def get_home_page_content(self):
        if not self.driver:
            raise Exception("You must login first using login_to_twitter method")

        # Scroll down a few times to load more tweets
        for _ in range(self.scroll_count):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

        # Extract tweets
        tweets = self.driver.find_elements(By.XPATH, "//div[@data-testid='tweetText']")
        tweet_texts = [tweet.text for tweet in tweets]

        return TwitterContent(
            tweets=tweet_texts,
            page_source=self.driver.page_source
        )

    def cleanup(self):
        if self.driver:
            self.driver.quit()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()


# Usage example
if __name__ == "__main__":
    with TwitterScraper(scroll_count=5) as scraper:
        scraper.login_to_twitter("skarandom", "SK99@pass")
        content = scraper.get_home_page_content()
        print(f"Number of tweets fetched: {len(content.tweets)}")
        with open("tweets.json","w") as f:
            json.dump(content.tweets,f,indent = 4)
        with open("tweets_ps.txt","w") as f:
            f.write(f'{content.page_source}')
