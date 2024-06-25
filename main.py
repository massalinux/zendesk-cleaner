import json
import time
import zipfile

import requests
import os
import pytz
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

SUBDOMAIN = os.getenv("ZENDESK_SUBDOMAIN")
EMAIL = os.getenv("ZENDESK_EMAIL")
API_TOKEN = os.getenv("ZENDESK_API_TOKEN")
BASE_URL = f"https://{SUBDOMAIN}.zendesk.com/api/v2"
AUTH = (f"{EMAIL}/token", API_TOKEN)
MAX_UPDATED_AT = datetime.now(pytz.utc) - timedelta(
    days=os.getenv("MAX_UPDATED_AT", 365 * 3)
)
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "./data")
RESTING_TIME = os.getenv("RESTING_TIME", 60)
DEBUG = os.getenv("DEBUG", False)


class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return json.JSONEncoder.default(self, o)


class Ticket:
    id: int
    requester_id: int
    ticket_dir: str
    requester_email = ""
    ticket_json = ""
    comments_json = ""
    attachments = []

    def __init__(self, ticket_response, download_directory):
        self.id = ticket_response["id"]
        self.ticket_json = ticket_response
        self.requester_id = ticket_response["requester_id"]
        self.attachments = []
        self.requester_email = self.get_user_email()
        self.create_ticket_dir(download_directory)
        self.update_ticket_comments()

    def create_ticket_dir(self, directory):
        self.ticket_dir = os.path.join(directory, str(self.id))
        os.makedirs(self.ticket_dir, exist_ok=True)

    def get_user_email(self):
        response = requests.get(f"{BASE_URL}/users/{self.requester_id}", auth=AUTH)
        data = response.json()
        return data["user"]["email"]

    def update_ticket_comments(self):
        params = {
            "include_inline_images": "true",
        }
        response = requests.get(
            f"{BASE_URL}/tickets/{self.id}/comments", params=params, auth=AUTH
        )
        data = response.json()
        self.comments_json = data

        for comment in data["comments"]:
            for attachment in comment["attachments"]:
                self.attachments.append(attachment["content_url"])

    def save(self):
        ticket_json = json.dumps(self.__dict__, cls=DateTimeEncoder)
        with open(os.path.join(self.ticket_dir, f"{self.id}-ticket.json"), "w") as f:
            f.write(ticket_json)

        for attachment in self.attachments:
            response = requests.get(attachment, auth=AUTH)
            filename = attachment.split("/")[-1]
            with open(os.path.join(self.ticket_dir, filename), "wb") as f:
                f.write(response.content)
            with zipfile.ZipFile(
                os.path.join(self.ticket_dir, f"{filename}.zip"), "w"
            ) as zipf:
                zipf.write(f.name, "w", zipfile.ZIP_DEFLATED, 9)
            os.remove(f.name)

    def delete(self):
        response = requests.delete(f"{BASE_URL}/tickets/{self.id}", auth=AUTH)
        if response.status_code != 204:
            print(response.status_code)
            print(response.text)
            raise Exception(f"Failed to delete ticket {self.id}")


def run():
    params = {
        "query": f'type:ticket status:closed updated<{MAX_UPDATED_AT.strftime("%Y-%m-%d")}',
        "sort_by": "updated_at",
        "sort_order": "asc",
    }
    response = requests.get(f"{BASE_URL}/search.json", params=params, auth=AUTH)
    data = response.json()
    for result in data["results"]:
        ticket_date = result["updated_at"] = datetime.strptime(
            result["updated_at"], "%Y-%m-%dT%H:%M:%S%z"
        )
        if ticket_date < MAX_UPDATED_AT:
            ticket = Ticket(result, DOWNLOAD_DIR)
            ticket.save()
            # ticket.delete()
            log(f"Ticket {ticket.id} archived")


def init_download_dir():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def check_envs():
    envs = [
        "ZENDESK_SUBDOMAIN",
        "ZENDESK_EMAIL",
        "ZENDESK_API_TOKEN",
    ]
    for env in envs:
        if not os.getenv(env):
            raise Exception(f"{env} is not set")


def log(message: str):
    if DEBUG:
        print(f"{message}")


if __name__ == "__main__":
    check_envs()
    init_download_dir()
    while True:
        run()
        log("Resting....")
        time.sleep(RESTING_TIME)
