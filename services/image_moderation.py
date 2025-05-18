import requests

MODERATECONTENT_API_KEY = "afa77977-0cb9-4d73-b2be-7f1b2d5331a0"  # Замени на свой API-ключ

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
        return False  # По умолчанию считаем изображение безопасным
