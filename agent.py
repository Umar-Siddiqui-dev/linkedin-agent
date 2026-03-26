import os
import calendar
import requests
from groq import Groq
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ─── CONFIG ───────────────────────────────────────────
GROQ_API_KEY          = os.environ["GROQ_API_KEY"]
LINKEDIN_ACCESS_TOKEN = os.environ["LINKEDIN_ACCESS_TOKEN"]

# ─── DAY THEMES (No Sunday) ───────────────────────────
DAY_THEMES = {
    "Monday":    "motivational story or personal experience related to coding, office life, career, or tech journey",
    "Tuesday":   "technical explanation of a backend concept in NestJS or Node.js with practical examples",
    "Wednesday": "software architecture or system design concept explained clearly with real world use cases",
    "Thursday":  "frontend React/Next JS development topic, or web security and performance optimization technique with practicle examples",
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

# ─── GET LINKEDIN PROFILE URN ─────────────────────────
def get_profile_urn(token):
    resp = requests.get(
        "https://api.linkedin.com/v2/userinfo",
        headers={"Authorization": f"Bearer {token}"}
    )
    if resp.status_code != 200:
        raise Exception(f"Failed to fetch profile URN: {resp.status_code} {resp.text}")
    data = resp.json()
    urn = f"urn:li:person:{data['sub']}"
    print(f"👤 Profile URN: {urn}")
    return urn

# ─── POST TO LINKEDIN ─────────────────────────────────
def post_to_linkedin(content):
    token = LINKEDIN_ACCESS_TOKEN

    print("🔐 Authenticating with LinkedIn API...")
    urn = get_profile_urn(token)

    payload = {
        "author": urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": content
                },
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }

    print("📤 Publishing post via LinkedIn API...")
    resp = requests.post(
        "https://api.linkedin.com/v2/ugcPosts",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        },
        json=payload
    )

    if resp.status_code == 201:
        post_id = resp.headers.get("x-restli-id", "unknown")
        print(f"✅ Successfully posted to LinkedIn!")
        print(f"🔗 Post ID: {post_id}")
    else:
        print(f"❌ Failed to post: {resp.status_code}")
        print(f"📋 Response: {resp.text}")
        raise Exception(f"LinkedIn API error: {resp.status_code}")

# ─── MAIN ─────────────────────────────────────────────
if __name__ == "__main__":
    print(f"🤖 LinkedIn Agent started at {datetime.now()}")
    content = generate_post()

    if content:
        post_to_linkedin(content)
    else:
        print("😴 No post today — enjoy your Sunday!")

    print(f"🏁 Agent finished at {datetime.now()}")