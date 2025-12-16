import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # AniList
    ANILIST_API_URL = "https://graphql.anilist.co"
    
    # Reddit
    REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
    REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
    REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "python:ip-research-tool:v0.1 (by /u/your_username)")
    
    # Output
    REPORT_FILE = "report.csv"
    
    @classmethod
    def validate(cls):
        """Check if essential secrets are loaded."""
        missing = []
        if not cls.REDDIT_CLIENT_ID:
            missing.append("REDDIT_CLIENT_ID")
        if not cls.REDDIT_CLIENT_SECRET:
            missing.append("REDDIT_CLIENT_SECRET")
        
        if missing:
            print(f"Warning: Missing environment variables: {', '.join(missing)}. Reddit functionality may fail.")

