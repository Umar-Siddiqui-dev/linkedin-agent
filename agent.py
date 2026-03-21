import time
import random
import os
import json
import calendar
from groq import Groq
from playwright.sync_api import sync_playwright
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ─── CONFIG ───────────────────────────────────────────
GROQ_API_KEY = os.environ["GROQ_API_KEY"]

# ─── DAY THEMES (No Sunday) ───────────────────────────
DAY_THEMES = {
    "Monday":    "motivational story or personal experience related to coding, office life, career, or tech journey",
    "Tuesday":   "technical explanation of a backend concept in NestJS or Node.js with practical examples",
    "Wednesday": "software architecture or system design concept explained clearly with real world use cases",
    "Thursday":  "frontend development topic, or web security and performance optimization technique",
    "Friday":    "advanced database concept, query optimization, or data modeling technique",
    "Saturday":  "building with AI, creating agents, automation, or practical LLM use cases for developers",
}

# ─── GET TODAY'S THEME ────────────────────────────────
def get_todays_theme():
    day = calendar.day_name[datetime.now().weekday()]
    if day not in DAY_THEMES:
        print(f"📅 Today is {day} — No post scheduled for Sunday. Exiting.")
        return None, None
    theme = DAY_THEMES[day]
    print(f"📅 Today is {day}")
    print(f"🎯 Theme: {theme}")
    return day, theme

# ─── GENERATE POST ────────────────────────────────────
def generate_post():
    day, theme = get_todays_theme()

    if not day:
        return None

    client = Groq(api_key=GROQ_API_KEY)

    is_technical = day not in ["Monday"]
    dm_instruction = "- End with this line before hashtags: '💬 Have questions or working on something similar? DM me — happy to help.'" if is_technical else ""
    tone_instruction = (
        "Share a personal, vulnerable, real story or experience. Be human and inspiring."
        if not is_technical else
        "Explain clearly with a practical example or analogy. Teach something useful."
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{
            "role": "system",
            "content": """You are a senior software engineer and LinkedIn content creator.
You write posts that feel genuinely human — never robotic, never generic.
Every post you write must be on a DIFFERENT and FRESH topic.
Never repeat the same idea twice. Be creative and specific."""
        }, {
            "role": "user",
            "content": f"""Today is {day}.

Your job:
1. First, PICK a fresh and specific topic related to: {theme}
2. Then write a LinkedIn post about that topic

Post requirements:
- Start with a bold, curiosity-driven hook (no emojis in first line)
- {tone_instruction}
- Conversational tone — write like a real person, not a textbook
- Under 280 words
- Use short paragraphs and line breaks for readability
- End with a question that invites comments
{dm_instruction}
- Add 8-10 relevant hashtags at the very bottom
- NEVER start with clichés like 'In today's world', 'As a developer', 'In this post'
- NEVER write the same topic twice — be specific and original every time"""
        }]
    )

    post = response.choices[0].message.content
    print("✅ Post generated!\n")
    print("─" * 50)
    print(post)
    print("─" * 50)
    return post

# ─── POST TO LINKEDIN ─────────────────────────────────
def post_to_linkedin(content):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            slow_mo=50
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()

        try:
            # ─── LOAD COOKIES ─────────────────────────
            print("🍪 Loading LinkedIn session...")

            cookies_json = os.environ.get("LINKEDIN_COOKIES", "")

            if cookies_json:
                # Running on GitHub Actions
                cookies = json.loads(cookies_json)
                print("✅ Cookies loaded from environment!")
            elif os.path.exists("linkedin_cookies.json"):
                # Running locally
                with open("linkedin_cookies.json", "r") as f:
                    cookies = json.load(f)
                print("✅ Cookies loaded from file!")
            else:
                print("⚠️ No cookies found! Run save_session.py first.")
                return

            context.add_cookies(cookies)

            # ─── GO TO FEED ───────────────────────────
            print("🏠 Navigating to LinkedIn feed...")
            page.goto("https://www.linkedin.com/feed/",
                      wait_until="domcontentloaded",
                      timeout=60000)
            time.sleep(random.uniform(3, 5))

            print(f"📍 Current URL: {page.url}")

            # Check if session expired
            if "login" in page.url or "authwall" in page.url:
                print("⚠️ Session expired! Run save_session.py again to refresh cookies.")
                return

            # ─── OPEN POST EDITOR ─────────────────────
            print("✍️ Opening post editor...")
            page.click('[aria-label="Start a post"]', timeout=15000)
            time.sleep(random.uniform(2, 3))

            # ─── TYPE POST ────────────────────────────
            print("⌨️ Typing post...")
            time.sleep(3)

            post_area = page.locator('[data-artdeco-is-focused]').first
            if not post_area.is_visible():
                post_area = page.locator('.ql-editor').first
            if not post_area.is_visible():
                post_area = page.locator('[contenteditable="true"]').first

            post_area.click()
            time.sleep(2)

            # Type character by character to trigger LinkedIn's input detection
            for char in content:
                page.keyboard.type(char)
                time.sleep(0.01)

            time.sleep(3)

            # ─── WAIT FOR POST BUTTON ─────────────────
            print("⏳ Waiting for Post button to enable...")
            page.wait_for_selector(
                'button.share-actions__primary-action:not([disabled])',
                timeout=15000
            )

            # ─── CLICK POST ───────────────────────────
            print("📤 Publishing post...")
            page.locator('button.share-actions__primary-action').click()
            time.sleep(random.uniform(3, 5))

            print("✅ Successfully posted to LinkedIn!")

        except Exception as e:
            print(f"❌ Error: {e}")
            page.screenshot(path="error_screenshot.png")
            print("📸 Screenshot saved — open error_screenshot.png to see what happened")

        finally:
            browser.close()

# ─── MAIN ─────────────────────────────────────────────
if __name__ == "__main__":
    print(f"🤖 LinkedIn Agent started at {datetime.now()}")
    content = generate_post()

    if content:
        post_to_linkedin(content)
    else:
        print("😴 No post today — enjoy your Sunday!")

    print(f"🏁 Agent finished at {datetime.now()}")