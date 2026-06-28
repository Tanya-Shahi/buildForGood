import logging
from sqlalchemy.orm import Session
from app.models.user import User

logger = logging.getLogger("TrustEngine")

class TrustEngine:
    # We keep scores between 0.1 and 1.0 (where 1.0 is full trust).
    # We never drop to 0.0 to prevent divide-by-zero errors in ML models later.
    MAX_SCORE = 1.0
    MIN_SCORE = 0.1
    
    # Penalties hit hard, rewards build slowly.
    FALSE_FLAG_PENALTY = 0.3
    VERIFIED_REWARD = 0.1

    @staticmethod
    def penalize_user(db: Session, reporter_id: int):
        """Drops the user's trust score heavily for a false report."""
        user = db.query(User).filter(User.id == reporter_id).first()
        if user:
            new_score = max(TrustEngine.MIN_SCORE, user.reputation_score - TrustEngine.FALSE_FLAG_PENALTY)
            user.reputation_score = new_score
            db.commit()
            logger.warning(f"User {user.username} penalized for fake report. New Trust: {round(new_score, 2)}")
            return new_score
        return None

    @staticmethod
    def reward_user(db: Session, reporter_id: int):
        """Slightly boosts trust when a report is verified by NGOs or corroboration."""
        user = db.query(User).filter(User.id == reporter_id).first()
        if user:
            new_score = min(TrustEngine.MAX_SCORE, user.reputation_score + TrustEngine.VERIFIED_REWARD)
            user.reputation_score = new_score
            db.commit()
            logger.info(f"User {user.username} rewarded for verified report. New Trust: {round(new_score, 2)}")
            return new_score
        return None