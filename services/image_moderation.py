import requests
import os
from dotenv import load_dotenv

load_dotenv()

MODERATECONTENT_API_KEY = os.getenv("MODERATECONTENT_API_KEY")

def is_inappropriate_image_by_url(image_url: str) -> bool:
    try:
        response = requests.get(
            "https://api.moderatecontent.com/moderate/",
            params={"key": MODERATECONTENT_API_KEY, "url": image_url}
        )
        result = response.json()
        rating = result.get("rating_label", "unknown")
        return rating in ["adult", "racy", "violent"]
    except Exception as e:
        print("Moderation API error:", e)
        return False  # безопасно по умолчанию
