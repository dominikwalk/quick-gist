import json
import logging
from typing import NamedTuple
from typing import Optional

import requests

GITHUB_API_ENDPOINT = "https://api.github.com"


class GistContent(NamedTuple):
    description: str
    files: dict
    public: bool


class GithubApiError(Exception):
    def __init__(self, msg=""):
        logging.error(f"GithubApiError: {msg}")
        exit(1)


def _validate_github_username(username: str) -> None:
    """Validate if the given github username exists"""
    url = f"{GITHUB_API_ENDPOINT}/users/{username}"
    ret = requests.get(url.format(username))
    ret_text = ret.json()
    if ret.ok:
        username_exists = False
        if "login" in ret_text:
            if ret_text["login"] == username:
                user_exists = True
            else:
                user_exists = False
        else:
            raise GithubApiError(msg="Invalid github API response")
    else:
        if ret_text["message"] == "Not Found":
            user_exists = False
        else:
            raise GithubApiError(msg="Failed to connect to github API endpoint")
    if not user_exists:
        raise GithubApiError(msg="Username does not exist on github")
    else:
        return


def _validate_github_user_apitoken(username: str, api_token: str) -> None:
    """
    Check if the given github api token is valid and
    has the right scope(s) to work on gists
    """
    url = f"{GITHUB_API_ENDPOINT}/users/{username}"
    headers = {"Authorization": f"token {api_token}"}
    ret = requests.get(url.format(username), headers=headers)
    ret_text = ret.json()
    if ret.ok:
        if "gist" not in ret.headers["X-OAuth-Scopes"]:
            raise GithubApiError("Your token does not have the rights to access gists")
    else:
        if ret_text["message"] == "Bad credentials":
            raise GithubApiError("Bad credentials")
        else:
            raise GithubApiError("Failed to connect to github api endpoint")


def _post_github_gist(gist_content: GistContent, api_token: str) -> Optional[str]:
    """Create a new github gist from a given file list and description and return gist url"""
    # form a request URL
    url = GITHUB_API_ENDPOINT + "/gists"

    # create headers, parameters and payload
    headers = {"Authorization": f"token {api_token}"}
    params = {"scope": "gist"}
    payload = {
        "description": gist_content.description,
        "public": gist_content.public,
        "files": gist_content.files,
    }

    try:
        # try to post the github gist
        res = requests.post(
            url,
            headers=headers,
            params=params,
            data=json.dumps(payload),
        )
        status_code = res.status_code
        if status_code == 201:
            # successfully created new githib gist
            ret = json.loads(res.text)
            gist_url = ret["html_url"]
            # return github gist url
            return gist_url

        # TODO: implement other status codes
        else:
            return None
    except requests.exceptions.ConnectionError:
        GithubApiError(f"Failed to create gist (connection error)")
        return None
