# models.py
import requests
from datetime import datetime
from typing import List, Dict, Optional

class User:
    def __init__(self, user_id: int, username: str, email: str):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.created_at = datetime.now()
        self.posts = []

    def add_post(self, title: str, content: str) -> dict:
        if not title:  # Keep the validation for the previous example
            raise ValueError("Post title cannot be empty")
        post = {
            'id': len(self.posts) + 1,
            'title': title,
            'content': content,
            'author': self.username,
            'created_at': datetime.now()
        }
        self.posts.append(post)
        return post

    def get_posts(self) -> List[dict]:
        return self.posts.copy()

class APIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def get_user_data(self, user_id: int) -> dict:
        try:
            response = requests.get(f"{self.base_url}/users/{user_id}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError:
            return None  # Introduce error: suppress HTTPError and return None

    def create_user(self, user_data: dict) -> dict:
        response = requests.post(f"{self.base_url}/users", json=user_data)
        response.raise_for_status()
        return response.json()