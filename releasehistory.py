#!/usr/bin/env python

from datetime import datetime
import requests
import argparse

ap = argparse.ArgumentParser()
ap.add_argument("-o", "--owner", required=True, help="name of the owner")
ap.add_argument("-r", "--repo", required=True, help="name of the repository")
args = vars(ap.parse_args())

owner = args["owner"]
repo = args["repo"]
response = requests.get("https://api.github.com/repos/%s/%s/releases" % (owner, repo))

if response.status_code != 200:
    print("Unable to get releases")
    exit(1)

for release in response.json():
    name = release["name"]
    body = release["body"].replace("\r\n", "  \r\n")
    published_at = release["published_at"]
    prerelease = release["prerelease"]
    author = release["author"]["login"]
    datetime_object = datetime.strptime(published_at, '%Y-%m-%dT%H:%M:%SZ')

    print("## %s [%s released %d-%02d-%02d]\n%s\n" % (name, author, datetime_object.year, datetime_object.month, datetime_object.day, body))
