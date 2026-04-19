from __future__ import annotations

import os
import json
import httpx
import google.auth
from google.oauth2 import service_account
from google.auth.transport.requests import Request as GoogleAuthRequest
from src.config import FIREBASE_PROJECT_ID, FIREBASE_LOCATION, DATA_CONNECT_SERVICE_ID, DATA_CONNECT_CONNECTOR_ID

class FirebaseDataConnectClient:
    def __init__(self):
        self.project_id = FIREBASE_PROJECT_ID
        self.location = FIREBASE_LOCATION
        self.service_id = DATA_CONNECT_SERVICE_ID
        self.connector_id = DATA_CONNECT_CONNECTOR_ID
        self.base_url = f"https://firebasedataconnect.googleapis.com/v1beta/projects/{self.project_id}/locations/{self.location}/services/{self.service_id}/connectors/{self.connector_id}"
        self.client = httpx.AsyncClient()

    async def get_auth_token(self) -> str:
        try:
            credentials_json = os.environ.get("FIREBASE_CREDENTIALS_JSON")
            if credentials_json:
                info = json.loads(credentials_json)
                credentials = service_account.Credentials.from_service_account_info(
                    info, scopes=["https://www.googleapis.com/auth/cloud-platform"]
                )
            else:
                # Use default google auth (e.g. from GOOGLE_APPLICATION_CREDENTIALS)
                credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
            
            credentials.refresh(GoogleAuthRequest())
            return credentials.token
        except Exception as e:
            # If credentials are not set up yet, return empty token
            print(f"Auth error: {e}. Returning empty token.")
            return ""

    async def execute_mutation(self, mutation_name: str, variables: dict) -> dict:
        url = f"{self.base_url}:executeMutation"
        token = await self.get_auth_token()
        headers = {
            "Content-Type": "application/json"
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        payload = {
            "operationName": mutation_name,
            "variables": variables
        }

        response = await self.client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()

    async def execute_query(self, query_name: str, variables: dict) -> dict:
        url = f"{self.base_url}:executeQuery"
        token = await self.get_auth_token()
        headers = {
            "Content-Type": "application/json"
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        payload = {
            "operationName": query_name,
            "variables": variables
        }

        response = await self.client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()

    async def close(self):
        await self.client.aclose()


# Global client instance
firebase_client = FirebaseDataConnectClient()

async def get_db() -> FirebaseDataConnectClient:
    return firebase_client

def init_db() -> None:
    pass