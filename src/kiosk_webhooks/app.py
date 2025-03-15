from flask import Flask, request
import json
import hashlib
import hmac
import requests
from urllib.parse import urljoin
from os import environ
from dotenv import load_dotenv

from waitress import serve

import logging

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler()],
)

log = logging.getLogger(__name__)

app = Flask(__name__)


load_dotenv()

SECRET = environ.get("SECRET", "")
IMMICH_URL = environ.get("IMMICH_URL", "")
IMMICH_API_KEY = environ.get("IMMICH_API_KEY", "")
ALBUM_ID = environ.get("ALBUM_ID", "")

HEADERS = {"Content-Type": "application/json", "X-Api-Key": IMMICH_API_KEY}


def verify_signature(payload_body, secret_token, signature_header) -> bool:
    """
    Verify if the webhook signature is valid

    Args:
        payload_body: The raw request payload body
        secret_token: The shared secret token used to sign the payload
        signature_header: The signature header from the request

    Returns:
        bool: True if signature is valid, False otherwise
    """
    if not signature_header:
        return False
    hash_object = hmac.new(
        secret_token.encode("utf-8"), msg=payload_body, digestmod=hashlib.sha256
    )
    expected_signature = "sha256=" + hash_object.hexdigest()
    if not hmac.compare_digest(expected_signature, signature_header):
        return False
    return True


def api_call(endpoint: str, method: str, data: dict) -> dict:
    """
    Make an API call to the Immich server

    Args:
        endpoint: The API endpoint to call
        method: The HTTP method to use (GET, POST, PUT, etc)
        data: The request payload data

    Returns:
        dict: The JSON response from the API call, or empty dict on error
    """
    url = urljoin(IMMICH_URL, endpoint)
    try:
        response = requests.request(method, url, json=data, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        log.error(f"API call failed: {e}")
        return {}
    return {}


def add_to_album(album_id, asset_id) -> dict:
    """
    Add an asset to an album in Immich

    Args:
        album_id: The ID of the album to add the asset to
        asset_id: The ID of the asset to add

    Returns:
        dict: The API response from adding the asset, or empty dict on error
    """
    try:
        res = api_call(f"api/albums/{album_id}/assets", "PUT", {"ids": [asset_id]})
        return res
    except Exception as e:
        log.error(f"Failed to add asset to album: {e}")
        return {}


@app.route("/webhook", methods=["POST"])
def webhook():
    """
    Webhook endpoint that verifies the request signature, processes then prints the payload

    The signature (if provided) is verified against the shared secret token. If verification fails,
    returns an error response. If successful, the payload is processed and logged.

    Returns:
        tuple: Response message and status code
            - ("Payload received!", 200) for successful requests
            - ("Error", 500) for invalid/missing signatures
            - ("Error", 400) for invalid JSON payload
    """
    secret_header = request.headers.get("X-Kiosk-Signature-256")
    log.debug("secret_header", secret_header)

    if secret_header is not None:
        verify = verify_signature(request.get_data(), SECRET, secret_header)
        if verify == False:
            log.error("Invalid signature")
            return "Erro", 500

    data = request.get_json()
    print(json.dumps(data, indent=4))
    return "Payload received!", 200


@app.route("/add-to-album", methods=["POST"])
def album():
    """
    Endpoint to add assets to an album

    Expects a JSON payload containing a list of assets with IDs.
    Adds each asset to the configured album.

    Returns:
        tuple: Response message and status code
            - ("Added to album", 200) for successful requests
            - ("Missing asset ID", 400) if assets list is missing
    """
    data = request.get_json()
    assets = data.get("assets")

    if assets is None:
        return "Missing asset ID", 400

    for asset in assets:
        assetID = asset.get("id")

        if assetID is None:
            log.error("Invalid asset ID")
            continue

        try:
            add_to_album(ALBUM_ID, assetID)

        except Exception as e:
            log.error(f"Failed to add asset to album: {e}")
            return f"Failed to add asset to album: {e}", 500

    log.info("Assets added to album")
    return "Added to album", 200


if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=6000)
