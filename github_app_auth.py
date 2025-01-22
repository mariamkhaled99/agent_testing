import os
import jwt
import time
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

GITHUB_APP_ID = os.getenv("GITHUB_APP_ID")
GITHUB_APP_PRIVATE_KEY = os.getenv("GITHUB_APP_PRIVATE_KEY")
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY")

def generate_jwt(app_id, private_key):
    # print(f"app_id: {app_id}")
    # print(f"private_key: {private_key}")
    payload = {
        "iat": int(time.time()),
        "exp": int(time.time()) + 600,
        "iss": app_id
    }
    return jwt.encode(payload, private_key, algorithm="RS256")

def get_installation_access_token(jwt, repository):
    owner, repo = repository.split("/")
    headers = {
        "Authorization": f"Bearer {jwt}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/installation",
        headers=headers
    )
    response.raise_for_status()
    installation_id = response.json()["id"]

    response = requests.post(
        f"https://api.github.com/app/installations/{installation_id}/access_tokens",
        headers=headers
    )
    response.raise_for_status()
    return response.json()["token"]

def make_graphql_request(token, query):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.post(
        "https://api.github.com/graphql",
        json={"query": query},
        headers=headers
    )
    response.raise_for_status()
    return response.json()

