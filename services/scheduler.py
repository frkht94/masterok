from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from db.database import SessionLocal
from models.user import User
from models.payment import Payment
from datetime import datetime, timedelta
import pytz

def promote_masters_job():
    db: Session = SessionLocal()
    try:
        now = datetime.utcnow()

        # Получаем все активные платежи
        active_payments = db.query(Payment).filter(
            Payment.is_active == True,
            Payment.start_date <= now,
            Payment.end_date >= now,
            Payment.status == "paid"
        ).all()

        # Собираем очередь кандидатов
        queue = []

        for payment in active_payments:
            user = payment.user
            if not user or user.user_type != "master":
                continue

            if user.promote_today_used is None:
                user.promote_today_used = 0

            if user.promote_today_used < payment.times_per_day:
                queue.append((user, payment))

        # Сортировка по времени последнего подъёма — кто дольше не поднимался, тот выше
        queue.sort(key=lambda item: item[0].last_promoted_at or datetime.min)

        promoted_ids = []

        for user, payment in queue:
            user.last_promoted_at = now
            user.promote_today_used += 1
            user.is_promoted = True
            promoted_ids.append(user.id)

        db.commit()
        print(f"✅ Продвинуто мастеров: {len(promoted_ids)} | ID: {promoted_ids}")

    except Exception as e:
        print("❌ Ошибка в promote_masters_job:", str(e))
    finally:
        db.close()

def reset_daily_promotions():
    db: Session = SessionLocal()
    try:
        db.query(User).filter(User.user_type == "master").update({
            User.promote_today_used: 0
        })
        db.commit()
        print("♻️ Сброшен дневной счётчик продвижений")
    except Exception as e:
        print("❌ Ошибка в reset_daily_promotions:", str(e))
    finally:
        db.close()

def start_scheduler():
    scheduler = BackgroundScheduler(timezone=pytz.timezone("Asia/Almaty"))
    scheduler.add_job(promote_masters_job, IntervalTrigger(minutes=15))
    scheduler.add_job(reset_daily_promotions, CronTrigger(hour=0, minute=0))
    scheduler.start()
    print("🕒 Планировщик APScheduler запущен")
