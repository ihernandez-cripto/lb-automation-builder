import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")
OCI_STORAGE_BUCKET_URL = os.getenv(
    "OCI_STORAGE_BUCKET_URL", 
    "https://objectstorage.us-ashburn-1.oraclecloud.com/n/mytenant/b/lb-configs/o/"
)