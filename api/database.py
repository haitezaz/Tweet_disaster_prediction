"""
Firebase Database Initialization
Initializes Firebase Admin SDK and provides utilities.
"""

from __future__ import annotations

from api.firebase_db import get_firebase_db
from src.utils.logger import get_logger

logger = get_logger(__name__)


def init_db() -> None:
	"""Initialize Firestore database"""
	try:
		db = get_firebase_db()
		if db.health_check():
			logger.info("firestore.initialized_successfully")
		else:
			logger.warning("firestore.health_check_failed")
	except Exception as exc:
		logger.error("firestore.initialization_failed", exc_info=True)
		raise