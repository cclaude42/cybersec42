#!/usr/bin/env python3
import argparse
from PIL import Image, ExifTags




# Argument parser
parser = argparse.ArgumentParser(
    prog='scorpion',
    description='Parse the metadata of one or more images',
    epilog='*bottom text*'
)
parser.add_argument('img', nargs='+', help="the path to the image(s)")


# Main
if __name__ == "__main__":
    args = parser.parse_args()

    for path in args.img:
        # Open image
        try:
            img = Image.open(path)
        except:
            print(f"{path} : could not open file.")
            continue

        # Look for metadata
        exif_data = img.getexif().items()
        if exif_data:
            print(f"{path} : found metadata !")
        else:
            print(f"{path} : no metadata.")
            continue

        # Print metadata
        for tag, value in exif_data:
            print(f"- {ExifTags.TAGS[tag]} : {value}")
        print()
