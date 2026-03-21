from playwright.sync_api import sync_playwright
import json
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    page.goto("https://www.linkedin.com/login")
    
    print("🔐 Please login manually in the browser window...")
    print("⏳ You have 60 seconds to complete login + any security checks...")
    
    # Wait for you to login manually
    page.wait_for_url("**/feed/**", timeout=60000)
    
    # Save cookies
    cookies = context.cookies()
    with open("linkedin_cookies.json", "w") as f:
        json.dump(cookies, f)
    
    print("✅ Session saved to linkedin_cookies.json!")
    browser.close()