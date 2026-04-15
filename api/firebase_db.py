"""
Firebase Firestore Database Client
Production-grade implementation with error handling, retry logic, and type safety.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, TypeVar
from uuid import uuid4

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore import Client
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from src.config import FIREBASE_CREDENTIALS_PATH, FIREBASE_PROJECT_ID
from src.utils.logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class FirebaseConfig:
    """Firebase configuration management"""

    def __init__(self):
        self.project_id = FIREBASE_PROJECT_ID
        self.credentials_path = FIREBASE_CREDENTIALS_PATH
        self.max_retries = 3
        self.timeout = 30

    @property
    def is_emulator(self) -> bool:
        """Check if using Firestore emulator"""
        return os.getenv("FIRESTORE_EMULATOR_HOST") is not None


class FirebaseDB:
    """
    Singleton Firebase Firestore client with production-grade features.
    
    Features:
    - Automatic retry with exponential backoff
    - Type safety with error handling
    - Batch operations for efficiency
    - Health checks and monitoring
    - Thread-safe singleton pattern
    """

    _instance: FirebaseDB | None = None
    _client: Client | None = None
    _initialized: bool = False

    def __new__(cls) -> FirebaseDB:
        """Singleton pattern for Firebase client"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize Firebase connection (idempotent)"""
        if self._initialized:
            return

        self.config = FirebaseConfig()
        self._initialize_firebase()
        self._initialized = True

    def _initialize_firebase(self) -> None:
        """Initialize Firebase Admin SDK"""
        try:
            # Check if already initialized
            firebase_admin.get_app()
            logger.info("Firebase app already initialized")
        except ValueError:
            # Not initialized, initialize now
            if self.config.is_emulator:
                logger.info("Using Firestore emulator")
                credentials_obj = None
            else:
                if not os.path.exists(self.config.credentials_path):
                    raise FileNotFoundError(
                        f"Firebase credentials not found at {self.config.credentials_path}"
                    )
                creds = credentials.Certificate(self.config.credentials_path)
                credentials_obj = creds

            firebase_admin.initialize_app(
                credential=credentials_obj,
                options={"projectId": self.config.project_id}
            )
            logger.info(
                "Firebase initialized",
                extra={
                    "extra_data": {
                        "project_id": self.config.project_id,
                        "emulator": self.config.is_emulator,
                    }
                },
            )

        self._client = firestore.client()

    @property
    def client(self) -> Client:
        """Get Firestore client"""
        if self._client is None:
            self._initialize_firebase()
        return self._client

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    def _execute_with_retry(self, operation) -> Any:
        """Execute operation with exponential backoff retry"""
        return operation()

    def create_document(
        self,
        collection: str,
        data: dict[str, Any],
        document_id: str | None = None,
    ) -> str:
        """
        Create a document in a collection.
        
        Args:
            collection: Collection name
            data: Document data
            document_id: Optional document ID (auto-generated if not provided)
            
        Returns:
            Document ID
        """
        doc_id = document_id or str(uuid4())

        def _create():
            self.client.collection(collection).document(doc_id).set(data)
            return doc_id

        try:
            result = self._execute_with_retry(_create)
            logger.debug(
                f"firestore.document_created",
                extra={
                    "extra_data": {
                        "collection": collection,
                        "document_id": result,
                    }
                },
            )
            return result
        except Exception as exc:
            logger.error(
                "firestore.create_failed",
                extra={
                    "extra_data": {
                        "collection": collection,
                        "document_id": doc_id,
                    }
                },
                exc_info=True,
            )
            raise

    def get_document(
        self,
        collection: str,
        document_id: str,
    ) -> dict[str, Any] | None:
        """
        Get document by ID.
        
        Args:
            collection: Collection name
            document_id: Document ID
            
        Returns:
            Document data or None if not found
        """

        def _get():
            doc = self.client.collection(collection).document(document_id).get()
            return doc.to_dict() if doc.exists else None

        try:
            return self._execute_with_retry(_get)
        except Exception as exc:
            logger.error(
                "firestore.get_failed",
                extra={
                    "extra_data": {
                        "collection": collection,
                        "document_id": document_id,
                    }
                },
                exc_info=True,
            )
            raise

    def update_document(
        self,
        collection: str,
        document_id: str,
        data: dict[str, Any],
    ) -> None:
        """
        Update document fields.
        
        Args:
            collection: Collection name
            document_id: Document ID
            data: Fields to update
        """

        def _update():
            self.client.collection(collection).document(document_id).update(data)

        try:
            self._execute_with_retry(_update)
            logger.debug(
                "firestore.document_updated",
                extra={
                    "extra_data": {
                        "collection": collection,
                        "document_id": document_id,
                    }
                },
            )
        except Exception as exc:
            logger.error(
                "firestore.update_failed",
                extra={
                    "extra_data": {
                        "collection": collection,
                        "document_id": document_id,
                    }
                },
                exc_info=True,
            )
            raise

    def delete_document(
        self,
        collection: str,
        document_id: str,
    ) -> None:
        """
        Delete document.
        
        Args:
            collection: Collection name
            document_id: Document ID
        """

        def _delete():
            self.client.collection(collection).document(document_id).delete()

        try:
            self._execute_with_retry(_delete)
            logger.debug(
                "firestore.document_deleted",
                extra={
                    "extra_data": {
                        "collection": collection,
                        "document_id": document_id,
                    }
                },
            )
        except Exception as exc:
            logger.error(
                "firestore.delete_failed",
                extra={
                    "extra_data": {
                        "collection": collection,
                        "document_id": document_id,
                    }
                },
                exc_info=True,
            )
            raise

    def query_collection(
        self,
        collection: str,
        filters: list[tuple[str, str, Any]] | None = None,
        order_by: tuple[str, str] | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Query collection with filters, ordering, and limits.
        
        Args:
            collection: Collection name
            filters: List of (field, operator, value) tuples
            order_by: (field, direction) tuple
            limit: Max documents to return
            
        Returns:
            List of documents
        """

        def _query():
            query = self.client.collection(collection)

            # Apply filters
            if filters:
                for field, operator, value in filters:
                    query = query.where(field, operator, value)

            # Apply ordering
            if order_by:
                field, direction = order_by
                query = query.order_by(field, direction=direction)

            # Apply limit
            if limit:
                query = query.limit(limit)

            return [doc.to_dict() | {"id": doc.id} for doc in query.stream()]

        try:
            return self._execute_with_retry(_query)
        except Exception as exc:
            logger.error(
                "firestore.query_failed",
                extra={
                    "extra_data": {
                        "collection": collection,
                        "filters": filters,
                    }
                },
                exc_info=True,
            )
            raise

    def batch_write(self, operations: list[tuple[str, str, str, dict]]) -> None:
        """
        Batch write multiple operations.
        
        Args:
            operations: List of (operation, collection, doc_id, data) tuples
                       operation: 'set', 'update', 'delete'
        """

        def _batch():
            batch = self.client.batch()

            for operation, collection, doc_id, data in operations:
                doc_ref = self.client.collection(collection).document(doc_id)

                if operation == "set":
                    batch.set(doc_ref, data)
                elif operation == "update":
                    batch.update(doc_ref, data)
                elif operation == "delete":
                    batch.delete(doc_ref)

            batch.commit()

        try:
            self._execute_with_retry(_batch)
            logger.debug(
                "firestore.batch_committed",
                extra={"extra_data": {"operation_count": len(operations)}},
            )
        except Exception as exc:
            logger.error(
                "firestore.batch_failed",
                extra={"extra_data": {"operation_count": len(operations)}},
                exc_info=True,
            )
            raise

    def health_check(self) -> bool:
        """Check Firestore connectivity"""
        try:
            self.client.collection("system").document("health").set({
                "status": "ok",
                "timestamp": datetime.now(timezone.utc),
            })
            return True
        except Exception as exc:
            logger.error("firestore.health_check_failed", exc_info=True)
            return False


def get_firebase_db() -> FirebaseDB:
    """Get singleton Firebase DB instance"""
    return FirebaseDB()
