from dotenv import load_dotenv
import os

load_dotenv()


class Config:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

    GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY")