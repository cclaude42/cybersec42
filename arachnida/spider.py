#!/usr/bin/env python3
import argparse
import requests
import shutil
from urllib.parse import urlparse
from html.parser import HTMLParser
from pathlib import Path


# Globals
VALID_MIME_TYPES = ("jpg", "jpeg", "png", "gif", "bmp")
seen = set()


# Utils
def get_tag(tag, attrs):
    for k, v in attrs:
        if k == tag:
            return v
    return None

def get_filetype(url):
    head = requests.head(url)
    content_type = head.headers.get("content-type")
    return content_type.split("/")[1]

def is_valid_type(type):
    return type in VALID_MIME_TYPES

def get_savepath(url, savedir, filetype):
    filename = Path(url.split('/')[-1])
    savepath = Path(savedir) / filename.stem

    n = 1
    while savepath.exists():
        savepath = Path(savedir) / f"{filename.stem}-{n}"
        n += 1

    return f"{str(savepath)}.{filetype}"

def download_image(url, savedir, filetype):
    savepath = get_savepath(url, savedir, filetype)
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(savepath, "wb") as f:
            shutil.copyfileobj(response.raw, f)
        print(f"{url} : image downloaded.")
    else:
        print(f"{url} : could not download image.")


# Recurse logic
def recurse_parser(url, savedir, depth):
    if depth:
        try:
            response = requests.get(url)
            parser = HandleLink(url, savedir, depth)
            parser.feed(response.text)
        except:
            pass

class HandleLink(HTMLParser):
    def __init__(self, url, savedir, depth):
        super(HandleLink, self).__init__()
        self.url = url
        self.savedir = savedir
        self.depth = depth

    def handle_starttag(self, tag, attrs):
        # Link logic
        if tag == "a":
            # Retrieve href tag
            href = get_tag("href", attrs)
            if not href or not href.startswith(("/", "./", "../")):
                return
            # Conditionally recurse
            if href.startswith(("./", "../")):
                url = self.url + href
            elif href.startswith(("//")):
                scheme = urlparse(self.url).scheme
                url = f"{scheme}:" + href
            elif href.startswith(("/")):
                scheme = urlparse(self.url).scheme
                root = urlparse(self.url).hostname
                url = f"{scheme}://{root}" + href
            else:
                return
            url = url.split("?")[0]
            if not url in seen:
                seen.add(url)
                recurse_parser(url, self.savedir, self.depth - 1)
        # Image logic
        elif tag == "img":
            # Retrieve src tag
            img = get_tag("src", attrs)
            if not img:
                return
            # Handle relative path
            if img.startswith(("./", "../")):
                url = self.url + img
            elif img.startswith(("//")):
                scheme = urlparse(self.url).scheme
                url = f"{scheme}:" + img
            elif img.startswith(("/")):
                scheme = urlparse(self.url).scheme
                root = urlparse(self.url).hostname
                url = f"{scheme}://{root}" + img
            else:
                url = img
            url = url.split("?")[0]
            # Conditionally download image
            filetype = get_filetype(url)
            if is_valid_type(filetype) and not url in seen:
                seen.add(url)
                download_image(url, self.savedir, filetype)


# Argument parser
parser = argparse.ArgumentParser(
    prog='spider',
    description='Extract images from a website recursively',
    epilog='*bottom text*'
)

parser.add_argument('url', help="the url to crawl")
parser.add_argument('-r', dest="recursive", action='store_true', required=False, help='download images recursively')
parser.add_argument('-l', dest="depth", metavar='N', type=int, default=5, required=False, help='an integer for the accumulator')
parser.add_argument('-p', dest="savedir", metavar='PATH', type=str, default="./data/", required=False, help='path to save images')


# Main
if __name__ == "__main__":
    args = parser.parse_args()

    response = requests.get(args.url)

    Path(args.savedir).mkdir(parents=True, exist_ok=True)
    if args.recursive:
        recurse_parser(args.url, args.savedir, args.depth)
    else:
        recurse_parser(args.url, args.savedir, 1)
