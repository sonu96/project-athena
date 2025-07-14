"""
Google Cloud Platform configuration and client initialization
"""

import os
from typing import Optional
from google.cloud import firestore, bigquery, secretmanager, logging as cloud_logging
from google.cloud.exceptions import GoogleCloudError
from .settings import settings


class GCPConfig:
    """Manages GCP service clients and configuration"""
    
    def __init__(self):
        self._firestore_client: Optional[firestore.Client] = None
        self._bigquery_client: Optional[bigquery.Client] = None
        self._secret_manager_client: Optional[secretmanager.SecretManagerServiceClient] = None
        self._logging_client: Optional[cloud_logging.Client] = None
        
        # Set credentials if provided
        if settings.google_application_credentials:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.google_application_credentials
    
    @property
    def firestore_client(self) -> firestore.Client:
        """Get or create Firestore client"""
        if not self._firestore_client:
            try:
                self._firestore_client = firestore.Client(
                    project=settings.gcp_project_id,
                    database=settings.firestore_database
                )
            except GoogleCloudError as e:
                raise Exception(f"Failed to initialize Firestore client: {e}")
        return self._firestore_client
    
    @property
    def bigquery_client(self) -> bigquery.Client:
        """Get or create BigQuery client"""
        if not self._bigquery_client:
            try:
                self._bigquery_client = bigquery.Client(
                    project=settings.gcp_project_id
                )
            except GoogleCloudError as e:
                raise Exception(f"Failed to initialize BigQuery client: {e}")
        return self._bigquery_client
    
    @property
    def secret_manager_client(self) -> secretmanager.SecretManagerServiceClient:
        """Get or create Secret Manager client"""
        if not self._secret_manager_client:
            try:
                self._secret_manager_client = secretmanager.SecretManagerServiceClient()
            except GoogleCloudError as e:
                raise Exception(f"Failed to initialize Secret Manager client: {e}")
        return self._secret_manager_client
    
    @property
    def logging_client(self) -> cloud_logging.Client:
        """Get or create Cloud Logging client"""
        if not self._logging_client:
            try:
                self._logging_client = cloud_logging.Client(
                    project=settings.gcp_project_id
                )
                # Set up the logging handler
                self._logging_client.setup_logging(log_level=settings.log_level)
            except GoogleCloudError as e:
                raise Exception(f"Failed to initialize Cloud Logging client: {e}")
        return self._logging_client
    
    def get_secret(self, secret_id: str, version: str = "latest") -> str:
        """Retrieve a secret from Secret Manager"""
        try:
            name = f"projects/{settings.gcp_project_id}/secrets/{secret_id}/versions/{version}"
            response = self.secret_manager_client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            raise Exception(f"Failed to retrieve secret {secret_id}: {e}")
    
    def close_all_clients(self):
        """Close all GCP client connections"""
        # Most GCP clients handle connection pooling automatically
        # This method is here for explicit cleanup if needed
        self._firestore_client = None
        self._bigquery_client = None
        self._secret_manager_client = None
        self._logging_client = None


# Global GCP configuration instance
gcp_config = GCPConfig()