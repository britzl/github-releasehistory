#!/usr/bin/env python

from datetime import datetime
from datetime import timedelta
import requests
import argparse
import sys

ap = argparse.ArgumentParser()
ap.add_argument("-o", "--owner", required=True, help="name of the owner")
ap.add_argument("-r", "--repo", required=False, help="name of the repository")
ap.add_argument("-a", "--age", required=False, help="max age of releases (days)")
ap.add_argument("-t", "--token", required=False, help="authentication token")
ap.add_argument("-f", "--file", required=True, help="file to write results to")
args = vars(ap.parse_args())


def log(s):
    sys.stdout.write(s)
    sys.stdout.flush()


def github(url, token):
    return requests.get(url, headers={"Authorization": "token %s" % (token)})


def get_releases(owner, repo, token):
    return github("https://api.github.com/repos/%s/%s/releases" % (owner, repo), token)


def get_latest_release_date(owner, repo, token):
    response = github("https://api.github.com/repos/%s/%s/releases" % (owner, repo), token)
    if response.status_code != 200:
        print("Unable to get latest release date")
        return None

    releases = response.json()
    if len(releases) == 0:
        return None

    published_at = releases[0]["published_at"]
    return datetime.strptime(published_at, '%Y-%m-%dT%H:%M:%SZ')


def list_repositories(owner, token):
    repos = []
    url = "https://api.github.com/users/%s/repos?page=1" % (owner)
    while url:
        response = github(url, token)
        if response.status_code != 200:
            print("Unable to list repositories (%d)" % (response.status_code))
            url = None
        else:
            url = response.links.get("next", {}).get("url")
            for repo in response.json():
                repos.append(repo["name"])
    return repos


owner = args["owner"]
repo = args["repo"]
age = args["age"]
token = args["token"]
file = args["file"]

repos = None
if repo is None:
    repos = list_repositories(owner, token)
else:
    repos = [repo]

max_releaseage = None
if age is None:
    max_releaseage = datetime.min
else:
    max_releaseage = datetime.now() - timedelta(days=int(age))

with open(file, "w") as out:
    log("Parsing %d repositories...\n" % (len(repos)))
    for repo in repos:
        log("  %s" % (repo))
        latest_release_date = get_latest_release_date(owner, repo, token)
        if latest_release_date and latest_release_date >= max_releaseage:
            log(" - found releases\n")
            out.write("# %s\n" % (repo))
            response = get_releases(owner, repo, token)

            if response.status_code != 200:
                print("Unable to get releases for %s" % (repo))
                exit(1)

            for release in response.json():
                name = release["name"]
                body = release["body"].replace("\r\n", "  \r\n")
                published_at = release["published_at"]
                prerelease = release["prerelease"]
                author = release["author"]["login"]
                release_date = datetime.strptime(published_at, '%Y-%m-%dT%H:%M:%SZ')
                if release_date >= max_releaseage:
                    out.write("## %s [%s released %d-%02d-%02d]\n%s\n\n" % (name, author, release_date.year, release_date.month, release_date.day, body))
            out.write("\n")
        else:
            log(" - no releases found\n")
