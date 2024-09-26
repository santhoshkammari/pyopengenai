import os
import subprocess
import urllib.request
import zipfile

def setup_local():
    # Download Google Chrome
    chrome_url = "https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_128.0.6613.84-1_amd64.deb"
    chrome_file = "google-chrome-stable_128.0.6613.84-1_amd64.deb"
    urllib.request.urlretrieve(chrome_url, chrome_file)

    # Install Google Chrome
    subprocess.run(["sudo", "dpkg", "-i", chrome_file], check=True)

    # Download ChromeDriver
    chromedriver_url = "https://storage.googleapis.com/chrome-for-testing-public/128.0.6613.0/linux64/chromedriver-linux64.zip"
    chromedriver_zip = "chromedriver-linux64.zip"
    urllib.request.urlretrieve(chromedriver_url, chromedriver_zip)

    # Extract ChromeDriver
    with zipfile.ZipFile(chromedriver_zip, 'r') as zip_ref:
        zip_ref.extractall()

    # Make ChromeDriver executable and move it to /usr/local/bin
    chromedriver_path = "chromedriver-linux64/chromedriver"
    os.chmod(chromedriver_path, 0o755)
    subprocess.run(["sudo", "mv", chromedriver_path, "/usr/local/bin/"], check=True)

    # Clean up downloaded files
    os.remove(chrome_file)
    os.remove(chromedriver_zip)
    os.rmdir("chromedriver-linux64")

    # Print versions
    print("ChromeDriver version:")
    subprocess.run(["chromedriver", "--version"], check=True)
    print("\nGoogle Chrome version:")
    subprocess.run(["google-chrome", "--version"], check=True)
