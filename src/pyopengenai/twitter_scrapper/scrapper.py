import json
import re

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pydantic import BaseModel
from typing import List, Dict
import logging
import time


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Tweet(BaseModel):
    text: str
    timestamp: str


class TwitterContent(BaseModel):
    tweets: List[Tweet] = []
    page_source: str = ""


class TwitterScraper:
    def __init__(self, chromedriver_path="/usr/local/bin/chromedriver", headless=True):
        self.chromedriver_path = chromedriver_path
        self.headless = headless
        self.driver = None
        self.username = None
        self.password = None

    def _setup_driver(self):
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--start-maximized")
        service = Service(self.chromedriver_path)
        return webdriver.Chrome(service=service, options=chrome_options)

    def login_to_twitter(self, username, password):
        self.driver = self._setup_driver()
        self.driver.get("https://x.com/login")
        self.username = username
        self.password = password

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

    def get_home_page_content(self,num_tweets=2):
        if not self.driver:
            raise Exception("You must login first using login_to_twitter method")

        # Scroll down a few times to load more tweets
        page_content = ""

        # Scroll down a few times to load more tweets
        for _ in range(num_tweets):
            page_content += self.driver.page_source
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//article[@data-testid='tweet']"))
            )
        with open("home_page_tweets.txt","w") as f:
            f.write(f'{page_content}')

        tweets= self.get_tweets_from_text(self.username,page_content)

        return TwitterContent(
            tweets=tweets,
            page_source=page_content
        )

    def get_tweets_from_text(self,username,text):
        spans = re.findall('<span(.*?)>\s*(.*?)\s*</span>', text, re.DOTALL)
        spans = [_[1] for _ in spans]
        tweets = []
        isp = []
        start = False
        for span in spans:
            if span and span[0] == '@':
                start = True
                isp = []
            if start:
                if 'span' in span:
                    start = False
                    tweets.append("".join(isp))
                else:
                    if username not in span:
                        isp.append(span)
        return [Tweet(text = t,timestamp = "") for t in tweets]

    def get_user_tweets(self, username: str, num_tweets: int = 2):
        if not self.driver:
            raise Exception("You must login first using login_to_twitter method")

        self.driver.get(f"https://x.com/{username}")



        # # Wait for tweets to load
        # WebDriverWait(self.driver, 10).until(
        #     EC.presence_of_element_located((By.XPATH, f'{username}'))
        # )
        time.sleep(1)

        page_content = ""

        # Scroll down a few times to load more tweets
        for _ in range(num_tweets):
            page_content += self.driver.page_source
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//article[@data-testid='tweet']"))
            )

        tweets = self.get_tweets_from_text(username = username,
                                  text = page_content)

        return TwitterContent(
            tweets=tweets,
            page_source=self.driver.page_source
        )

    def parse_saved_html(self, content: str) -> List[str]:
        soup = BeautifulSoup(content, 'html.parser')

        tweet_spans = soup.find_all('span', class_='css-1jxf684 r-bcqeeo r-1ttztb7 r-qvutc0 r-poiln3')

        tweets = []
        for span in tweet_spans:
            tweet_text = span.get_text(strip=True)
            if tweet_text:
                tweets.append(tweet_text)

        return tweets

    def _extract_tweets(self, limit: int = None) -> TwitterContent:
        tweet_elements = self.driver.find_elements(By.XPATH, "//div[@data-testid='tweet']")

        if limit:
            tweet_elements = tweet_elements[:limit]

        tweets = []
        for tweet in tweet_elements:
            try:
                text_element = tweet.find_element(By.XPATH, ".//div[@data-testid='tweetText']")
                time_element = tweet.find_element(By.XPATH, ".//time")
                tweets.append(Tweet(
                    text=text_element.text,
                    timestamp=time_element.get_attribute('datetime')
                ))
            except Exception as e:
                logger.error(f"Error extracting tweet: {e}")

        return TwitterContent(
            tweets=tweets,
            page_source=self.driver.page_source
        )

    def cleanup(self):
        if self.driver:
            self.driver.quit()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

def get_tweets(num_tweets=5):
    with TwitterScraper(headless=False) as scraper:
        scraper.login_to_twitter("skarandom","SK99@pass")
        return [x.text for x in scraper.get_home_page_content(num_tweets).tweets]

# Usage example
if __name__ == "__main__":
    print(get_tweets(2))