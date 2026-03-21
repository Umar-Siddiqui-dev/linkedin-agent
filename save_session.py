from playwright.sync_api import sync_playwright
import json
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 800}
    )
    page = context.new_page()

    # Go to LinkedIn
    page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
    
    print("🔐 Login manually in the browser window...")
    print("✅ After logging in successfully, come back here and press ENTER")
    
    input("Press ENTER after you are fully logged in and can see your feed...")

    # Save cookies
    cookies = context.cookies()
    with open("linkedin_cookies.json", "w") as f:
        json.dump(cookies, f)

    # Also save storage state (more reliable)
    context.storage_state(path="linkedin_state.json")
    
    print(f"✅ Saved {len(cookies)} cookies to linkedin_cookies.json")
    print("✅ Saved storage state to linkedin_state.json")
    browser.close()