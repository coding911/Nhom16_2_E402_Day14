import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"  # groq-compatible open model
DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "students.json")
RATE_LIMIT_PER_MINUTE = 5
