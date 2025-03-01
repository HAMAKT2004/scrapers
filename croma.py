from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import base64
import requests
from datetime import datetime

# GitHub Repository Details
GITHUB_TOKEN = "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"  # Replace with your actual token
REPO_OWNER = "HAMAKT2004"
REPO_NAME = "Pricely-Data"
FILE_PATH = "flipkart.json"
BRANCH = "main"

# Scraping Parameters
MAX_PAGES = 5  # Set a lower limit for testing
MAX_PRODUCTS = 300
products_list = []

# Set up Selenium in headless mode
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Initialize WebDriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# Open Flipkart
url = "https://www.flipkart.com/search?q=mobile"
driver.get(url)
time.sleep(5)  # Allow JS to load

page_number = 1
product_counter = 0

while page_number <= MAX_PAGES and product_counter < MAX_PRODUCTS:
    print(f"📄 Scraping Page {page_number}...")

    # Extract products
    products = driver.find_elements(By.CSS_SELECTOR, "div.tUxRFH")

    for product in products:
        if product_counter >= MAX_PRODUCTS:
            print("🚫 Max products reached. Stopping.")
            break

        try:
            name = product.find_element(By.CSS_SELECTOR, "div.KzDlHZ").text.strip()
            price = product.find_element(By.CSS_SELECTOR, "div.Nx9bqj").text.strip()
            link = product.find_element(By.CSS_SELECTOR, "a.CGtC98").get_attribute("href")
            image = product.find_element(By.CSS_SELECTOR, "img.DByuf4").get_attribute("src")

            rating_element = product.find_elements(By.CSS_SELECTOR, "div.XQDdHH")
            rating = rating_element[0].text.split()[0] if rating_element else "Rating not found"

            product_data = {
                "Product Name": name,
                "Price": price,
                "Rating": rating,
                "Product Link": link,
                "Image Link": image
            }

            products_list.append(product_data)
            product_counter += 1

            print(f"✅ Scraped: {name}")

        except Exception as e:
            print(f"❌ Error extracting product: {e}")

    # Go to the next page
    try:
        next_button = driver.find_element(By.XPATH, "//span[text()='Next']/parent::a")
        next_button.send_keys(Keys.RETURN)
        time.sleep(5)  # Wait for page to load
        page_number += 1
    except Exception:
        print("🚫 No more pages to scrape.")
        break

# Close WebDriver
driver.quit()

# Upload data to GitHub
def upload_to_github():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    # Fetch the existing file SHA
    response = requests.get(url, headers=headers)
    sha = response.json().get("sha") if response.status_code == 200 else None

    # Convert data to JSON
    new_content = json.dumps(products_list, indent=4)
    encoded_content = base64.b64encode(new_content.encode()).decode()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_message = f"Updated Flipkart mobile data on {timestamp}"

    payload = {
        "message": commit_message,
        "content": encoded_content,
        "branch": BRANCH
    }
    if sha:
        payload["sha"] = sha  # Include SHA if updating

    upload_response = requests.put(url, headers=headers, json=payload)

    if upload_response.status_code in [200, 201]:
        print("✅ Successfully updated flipkart.json on GitHub!")
    else:
        print(f"❌ GitHub Update Failed: {upload_response.json()}")

upload_to_github()
