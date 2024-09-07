from datetime import datetime
from typing import Dict

from dotenv import load_dotenv

from fastapi import APIRouter, HTTPException, status, Depends, Query

from app.database import database
from app.auth_bearer import JWTBearer
from .schemas import TickerTracking


load_dotenv()
router = APIRouter()



@router.get("/get_ticker_tracking", tags=["notify"])
async def get_ticker_tracking(token_data: Dict = Depends(JWTBearer())):
    records = await database.fetch(
        """
        SELECT *
        FROM users.user_notification
        WHERE user_id = $1 AND notification_type = 'ticker_tracking' AND active = true
        """, token_data.get("user_id")
    )

    return {"status": status.HTTP_200_OK, "records": records}


@router.get("/get_ticker_tracking_history", tags=["notify"])
async def get_ticker_tracking_history(token_data: Dict = Depends(JWTBearer())):
    notifications_id = await database.fetch(
        """
        SELECT id
        FROM users.user_notification
        WHERE user_id = $1 AND notification_type = 'ticker_tracking' AND active = true
        """, token_data.get("user_id")
    )

    notifications_merged = [not_id.get('id') for not_id in notifications_id]
    placeholders = ','.join(f"${i + 1}" for i in range(len(notifications_merged)))

    ticker_tracking_history = await database.fetch(
        f"""
        SELECT active_name, date, percent, day_percent
        FROM users.notification
        WHERE type IN ({placeholders})
        ORDER BY date DESC 
        LIMIT 10;
        """, *notifications_merged
    )

    return {"status": status.HTTP_200_OK, "ticker_tracking_history": ticker_tracking_history}


@router.delete("/delete_ticker_tracking", tags=["notify"])
async def delete_ticker_tracking(tt_id: int = Query(None), token_data: Dict = Depends(JWTBearer())):
    if tt_id is None:
        return {"status": "error", "message": "No ticker tracking id"}

    try:
        await database.execute(
            """
            UPDATE users.user_notification
            SET active = false
            WHERE user_id = $1 AND id = $2
            """, token_data.get("user_id"), tt_id
        )
    except:
        return {"status": "error", "message": "Ticker tracking not found"}

    return {"status": status.HTTP_200_OK, "message": "Ticker tracking deleted"}


@router.post("/set_ticker_tracking", tags=["notify"])
async def set_ticker_tracking(tt_params: TickerTracking, token_data: Dict = Depends(JWTBearer())):
    status_to_add = await database.fetch(
        """
            WITH notification_count AS (
                SELECT COUNT(*) AS count
                FROM users.user_notification
                WHERE user_id = $1 AND notification_type = 'ticker_tracking' AND active = true
            )
            SELECT 
                CASE 
                    WHEN p.status = true THEN nc.count < 3
                    ELSE nc.count < 1
                END AS allowed_to_add
            FROM users.premium p
            CROSS JOIN notification_count nc
            WHERE p.user_id = $1;
        """, token_data.get("user_id")
    )

    condition = f"{tt_params.ticker_name}:{tt_params.time_period}_min"

    if not status_to_add[0].get("allowed_to_add"):
        return {"status": status.HTTP_403_FORBIDDEN, "message": "Ticker tracking not allowed!"}

    try:
        await database.execute(
            """
            INSERT INTO users.user_notification (user_id, notification_type, notify_time, condition, created) 
            VALUES ($1, 'last_impulse', NULL, $2, $3)
            """, token_data.get("user_id"), condition, datetime.now()
        )
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error arose while adding new notification. Condition 1"
        )

    return {"Success": status.HTTP_200_OK}