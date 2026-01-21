import os


class Config:
    DB_URL = "sqlite:///birdbrain.db"
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    AUTH_DIR = os.path.join(os.getcwd(), "auth_storage")

    @staticmethod
    def get_auth_path(username: str) -> str:
        os.makedirs(Config.AUTH_DIR, exist_ok=True)
        return os.path.join(Config.AUTH_DIR, f"{username}_state.json")
