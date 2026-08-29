"""Client for querying a Microsoft Fabric semantic model via the Power BI REST API."""

from __future__ import annotations

import base64
import json
import os

import requests
from azure.identity import InteractiveBrowserCredential

POWER_BI_SCOPE = "https://analysis.windows.net/powerbi/api/.default"
EXECUTE_QUERIES_URL = (
    "https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/executeQueries"
)

# Well-known public client ID (Azure PowerShell) pre-consented for the Power BI API
# scope in most tenants, so an interactive login works without registering your own
# Azure AD app. Override with AZURE_CLIENT_ID if your tenant blocks it.
DEFAULT_CLIENT_ID = "1950a258-227b-4e31-a9cf-717495945fc2"

SCHEMA_TABLES_DAX = "EVALUATE INFO.VIEW.TABLES()"
SCHEMA_COLUMNS_DAX = "EVALUATE INFO.VIEW.COLUMNS()"
SCHEMA_MEASURES_DAX = "EVALUATE INFO.VIEW.MEASURES()"


class FabricSemanticModelClient:
    """Executes DAX queries against a Fabric/Power BI semantic model (dataset)."""

    def __init__(self, workspace_id: str, dataset_id: str):
        self.workspace_id = workspace_id
        self.dataset_id = dataset_id
        self._client_id = os.environ.get("AZURE_CLIENT_ID", DEFAULT_CLIENT_ID)
        self._tenant_id = os.environ.get("AZURE_TENANT_ID", "organizations")
        self._credential = InteractiveBrowserCredential(client_id=self._client_id, tenant_id=self._tenant_id)
        self._token = None

    @property
    def is_signed_in(self) -> bool:
        return self._token is not None and self._token.expires_on > _now()

    @property
    def signed_in_user(self) -> str | None:
        if not self.is_signed_in:
            return None
        claims = _decode_jwt_claims(self._token.token)
        return (
            claims.get("name")
            or claims.get("preferred_username")
            or claims.get("upn")
            or claims.get("unique_name")
        )

    def sign_in(self) -> None:
        """Explicitly triggers the interactive browser sign-in (opens a browser window)."""
        self._get_token()

    def sign_out(self) -> None:
        """Drops the current token and credential so the next sign-in starts fresh."""
        self._token = None
        self._credential = InteractiveBrowserCredential(client_id=self._client_id, tenant_id=self._tenant_id)

    def _get_token(self) -> str:
        if self._token is None or self._token.expires_on <= _now():
            self._token = self._credential.get_token(POWER_BI_SCOPE)
        return self._token.token

    def execute_dax(self, dax_query: str) -> list[dict]:
        """Runs a DAX query and returns the result rows as a list of dicts."""
        url = EXECUTE_QUERIES_URL.format(workspace_id=self.workspace_id, dataset_id=self.dataset_id)
        headers = {
            "Authorization": f"Bearer {self._get_token()}",
            "Content-Type": "application/json",
        }
        body = {
            "queries": [{"query": dax_query}],
            "serializerSettings": {"includeNulls": True},
        }
        response = requests.post(url, headers=headers, json=body, timeout=60)
        if not response.ok:
            raise FabricQueryError(response.status_code, response.text)

        payload = response.json()
        results = payload["results"][0]
        if "error" in results:
            raise FabricQueryError(200, str(results["error"]))
        tables = results["tables"]
        return tables[0]["rows"] if tables else []

    def get_tables(self) -> list[dict]:
        return self.execute_dax(SCHEMA_TABLES_DAX)

    def get_columns(self) -> list[dict]:
        return self.execute_dax(SCHEMA_COLUMNS_DAX)

    def get_measures(self) -> list[dict]:
        return self.execute_dax(SCHEMA_MEASURES_DAX)


class FabricQueryError(RuntimeError):
    def __init__(self, status_code: int, message: str):
        super().__init__(f"Fabric query failed ({status_code}): {message}")
        self.status_code = status_code


def _now() -> float:
    import time

    return time.time()


def _decode_jwt_claims(token: str) -> dict:
    """Decodes a JWT's payload for display purposes (no signature verification)."""
    try:
        payload_b64 = token.split(".")[1]
        padded = payload_b64 + "=" * (-len(payload_b64) % 4)
        return json.loads(base64.urlsafe_b64decode(padded))
    except Exception:
        return {}
