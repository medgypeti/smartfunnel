
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time

# Instagram login credentials
USERNAME = "the_smart_funnel"
PASSWORD = "Firescan2024+"

# Instagram target profile
TARGET_PROFILE = "https://www.instagram.com/antoineblanco99/"

def login_instagram(driver):
    # Open Instagram login page
    driver.get("https://www.instagram.com/accounts/login/")
    time.sleep(3)
    
    # Accept cookies if the button is present
    try:
        cookies_btn = driver.find_element(By.XPATH, "//button[text()='Only allow essential cookies']")
        cookies_btn.click()
    except:
        pass

    time.sleep(2)
    
    # Enter username and password to log in
    username_input = driver.find_element(By.NAME, "username")
    password_input = driver.find_element(By.NAME, "password")
    
    username_input.send_keys(USERNAME)
    password_input.send_keys(PASSWORD)
    
    # Submit the form
    login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
    login_button.click()

    # Wait for login process
    time.sleep(5)

def get_last_10_posts(driver):
    # Go to the target profile
    driver.get(TARGET_PROFILE)
    time.sleep(5)
    
    # Scroll down to load more posts (adjust depending on how many posts are initially loaded)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)

    # Get post links (only fetching the first 10)
    posts = driver.find_elements(By.XPATH, "//article//a[contains(@href, '/p/')]")[:10]

    post_data = []
    
    # Extract post ID and caption
    for post in posts:
        post_url = post.get_attribute('href')
        post_id = post_url.split("/")[-2]  # Post ID from URL

        # Open the post in a new tab and extract caption
        driver.execute_script("window.open(arguments[0]);", post_url)
        driver.switch_to.window(driver.window_handles[1])
        time.sleep(2)

        try:
            caption = driver.find_element(By.XPATH, "//div[contains(@class, 'C4VMK')]/span").text
        except:
            caption = "No caption"
        
        post_data.append({
            'post_id': post_id,
            'caption': caption
        })

        # Close the post tab and switch back to the main profile
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
    
    return post_data

def main():
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode (no GUI)
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Create driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        # Login to Instagram
        login_instagram(driver)
        
        # Extract last 10 posts' IDs and captions
        posts = get_last_10_posts(driver)
        
        # Print or return extracted data
        for post in posts:
            print(f"Post ID: {post['post_id']}, Caption: {post['caption']}")
    
    finally:
        # Close the browser
        driver.quit()

if __name__ == "__main__":
    main()


# import asyncio
# import random
# from playwright.async_api import async_playwright
# from bs4 import BeautifulSoup

# async def scrape_instagram(account, username, password):
#     async with async_playwright() as p:
#         # Launch the browser without a proxy
#         browser = await p.chromium.launch(headless=False, args=["--start-maximized"])

#         context = await browser.new_context(
#             user_agent=f"Mozilla/5.0 (Windows NT {random.randint(7, 10)}.0; Win64; x64) AppleWebKit/{random.randint(500, 600)}.{random.randint(0, 10)} (KHTML, like Gecko) Chrome/{random.randint(58, 80)}.0.{random.randint(2000, 4000)}.110 Safari/{random.randint(500, 600)}.36",
#             viewport={'width': 1280, 'height': 800},
#         )
        
#         page = await context.new_page()

#         # Simulate human-like delay
#         async def human_like_delay(min_sec=1, max_sec=3):
#             await page.wait_for_timeout(random.randint(min_sec * 1000, max_sec * 1000))

#         # Go to Instagram login page
#         await page.goto("https://www.instagram.com/accounts/login/", wait_until='networkidle')

#         # Add a random delay to mimic human behavior
#         await human_like_delay()

#         # Fill in the username and password fields
#         await page.fill("input[name='username']", username)
#         await human_like_delay()
#         await page.fill("input[name='password']", password)

#         # Simulate scrolling behavior
#         await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")

#         # Add another random delay
#         await human_like_delay()

#         # Click the login button
#         await page.click("button[type='submit']")

#         # Wait for the page to load after login
#         await page.wait_for_load_state('networkidle')

#         # Go to the Instagram account page
#         await page.goto(f"https://www.instagram.com/{account}/", wait_until='networkidle')

#         # Wait for posts to load
#         await page.wait_for_selector('article')

#         # Simulate some scrolling to make the bot behavior less obvious
#         for _ in range(3):
#             await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
#             await human_like_delay(2, 5)

#         # Get the page content
#         content = await page.content()
#         soup = BeautifulSoup(content, 'lxml')

#         # Find posts
#         posts = soup.find_all('article')[0].find_all('div', {'role': 'presentation'})[:10]

#         results = []
#         for post in posts:
#             try:
#                 post_data = {
#                     "image_url": post.find('img')['src'],
#                     "caption": post.find('div', {'class': 'C4VMK'}).find('span').text,
#                     "likes": post.find('div', {'class': 'Nm9Fw'}).text.split(' ')[0],
#                     "date": post.find('time')['datetime'],
#                     "post_url": post.find('a')['href']
#                 }
#                 results.append(post_data)
#             except Exception as e:
#                 print(f"Error parsing post: {e}")

#         await browser.close()
#         return results

# if __name__ == "__main__":
#     account = "antoineblanco99"
#     username = "the_smart_funnel"
#     password = "Firescan2024+"
#     results = asyncio.run(scrape_instagram(account, username, password))
#     for post in results:
#         print(post)
