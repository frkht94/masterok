from sqlalchemy.orm import Session
from models.user import User
from models.payment import Payment
from sqlalchemy import and_
from datetime import datetime, timedelta
import random

def reset_daily_counters(db: Session):
    """Сброс ежедневных счетчиков мастеров."""
    masters = db.query(User).filter(User.is_promoted == True).all()
    for master in masters:
        master.promote_today_used = 0
    db.commit()


def promote_masters(db: Session):
    """Поднимает мастеров в топ по очереди в рамках лимита и города."""
    now = datetime.utcnow()
    cities = db.query(User.city).filter(User.user_type == "master", User.is_promoted == True).distinct()

    for city_obj in cities:
        city = city_obj.city
        masters = db.query(User).filter(
            User.user_type == "master",
            User.city == city,
            User.is_promoted == True,
            User.promote_today_used < User.promote_times_per_day,
            User.promotion_expiration > now
        ).order_by(User.last_promoted_at.asc().nullsfirst()).all()

        if masters:
            # Берём первого в очереди
            master = masters[0]
            master.last_promoted_at = now
            master.promote_today_used += 1
            db.commit()
