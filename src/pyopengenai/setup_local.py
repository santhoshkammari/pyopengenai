import os
import platform
import subprocess
import sys
import urllib.request
import zipfile
import shutil

import nltk


def is_windows():
    return platform.system().lower() == "windows"


def is_chrome_installed():
    if is_windows():
        return shutil.which("chrome.exe") is not None
    else:
        return shutil.which("google-chrome") is not None


def get_chrome_version():
    try:
        if is_windows():
            result = subprocess.run(
                ["reg", "query", "HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon", "/v", "version"],
                capture_output=True, text=True, check=True)
            return result.stdout.strip().split()[-1]
        else:
            result = subprocess.run(["google-chrome", "--version"], capture_output=True, text=True, check=True)
            return result.stdout.strip().split()[-1]
    except subprocess.CalledProcessError:
        return None


def install_chrome():
    if is_windows():
        chrome_url = "https://dl.google.com/chrome/install/latest/chrome_installer.exe"
        chrome_installer = "chrome_installer.exe"
        urllib.request.urlretrieve(chrome_url, chrome_installer)
        subprocess.run([chrome_installer, "/silent", "/install"], check=True)
        os.remove(chrome_installer)
    else:
        chrome_url = "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb"
        chrome_file = "google-chrome-stable_current_amd64.deb"
        urllib.request.urlretrieve(chrome_url, chrome_file)
        subprocess.run(["sudo", "dpkg", "-i", chrome_file], check=True)
        subprocess.run(["sudo", "apt-get", "install", "-f", "-y"], check=True)
        os.remove(chrome_file)

def setup_nltk():
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('corpora/stopwords')
    except LookupError:
        print("Downloading necessary NLTK data...")
        nltk.download('punkt')
        nltk.download('stopwords')

def setup_local():
    setup_nltk()
    if not is_chrome_installed():
        print("Google Chrome is not installed. Installing...")
        install_chrome()

    chrome_version = get_chrome_version()
    if not chrome_version:
        print("Failed to detect Chrome version. Please install Chrome manually.")
        return

    print(f"Detected Chrome version: {chrome_version}")
    major_version = chrome_version.split('.')[0]

    # Download ChromeDriver
    if is_windows():
        chromedriver_url = f"https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/{chrome_version}/win64/chromedriver-win64.zip"
        chromedriver_zip = "chromedriver-win64.zip"
    else:
        chromedriver_url = f"https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/{chrome_version}/linux64/chromedriver-linux64.zip"
        chromedriver_zip = "chromedriver-linux64.zip"

    print(f"Downloading ChromeDriver from: {chromedriver_url}")
    urllib.request.urlretrieve(chromedriver_url, chromedriver_zip)

    # Extract ChromeDriver
    with zipfile.ZipFile(chromedriver_zip, 'r') as zip_ref:
        zip_ref.extractall()

    # Move ChromeDriver to appropriate location
    if is_windows():
        chromedriver_path = os.path.join("chromedriver-win64", "chromedriver.exe")
        target_path = "C:\\Windows\\System32\\chromedriver.exe"
    else:
        chromedriver_path = os.path.join("chromedriver-linux64", "chromedriver")
        target_path = "/usr/local/bin/chromedriver"

    if is_windows():
        shutil.move(chromedriver_path, target_path)
    else:
        os.chmod(chromedriver_path, 0o755)
        subprocess.run(["sudo", "mv", chromedriver_path, target_path], check=True)

    # Clean up downloaded files
    os.remove(chromedriver_zip)
    if is_windows():
        shutil.rmtree("chromedriver-win64")
    else:
        shutil.rmtree("chromedriver-linux64")

    # Print versions
    print("\nChromeDriver version:")
    subprocess.run(["chromedriver", "--version"], check=True)
    print("\nGoogle Chrome version:")
    if is_windows():
        subprocess.run(["chrome.exe", "--version"], check=True)
    else:
        subprocess.run(["google-chrome", "--version"], check=True)


if __name__ == "__main__":
    if not is_windows() and os.geteuid() != 0:
        print("This script requires root privileges on Linux. Please run with sudo.")
        sys.exit(1)
    setup_local()