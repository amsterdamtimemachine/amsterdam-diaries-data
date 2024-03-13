import os
import json
import uuid

from pagexml.parser import parse_pagexml_file
from pagexml.helper.pagexml_helper import get_custom_tags

FOLDER = "data/"
PREFIX = "https://id.amsterdamtimemachine.nl/ark:/81741/dataset/diaries/annotations/"


def main(folder):

    annotations = []

    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith(".xml") and file not in ("metadata.xml", "mets.xml"):
                filepath = os.path.join(root, file)

                try:

                    page = parse_pagexml_file(
                        filepath,
                        custom_tags=(
                            # "structure",
                            "date",
                            "person",
                            "place",
                            "organization",
                            # "add",
                            # "unclear",
                            # "blackening",
                            "speech",
                            "abbrev",
                            # "gap",
                            # "sic",
                        ),
                    )
                except:
                    continue
                tags = get_custom_tags(page)

                for tag in tags:
                    annotations.append(
                        make_annotation(tag, prefix=PREFIX, filename=filepath)
                    )

    with open("annotations.json", "w") as f:
        json.dump(annotations, f, indent=2)


def make_annotation(tag, identifier="", prefix="", filename=""):

    if not identifier:
        identifier = uuid.uuid4()

        if prefix:
            identifier = f"{prefix}{identifier}"

    source = f"{filename}#{tag['line_id']}"

    annotation = {
        "@context": "http://www.w3.org/ns/anno.jsonld",
        "id": identifier,
        "type": "Annotation",
        "body": [
            {
                "type": "TextualBody",
                "value": tag["type"],
                "purpose": "classifying",
            },
            # {
            #     "type": "SpecificResource",
            #     "source": "https://www.example.com/",
            #     "purpose": "identifying",
            # },
        ],
        "target": {
            "type": "SpecificResource",
            "source": source,
            "selector": [
                {
                    "type": "TextQuoteSelector",
                    "exact": tag["value"],
                },
                {
                    "type": "TextPositionSelector",
                    "start": tag["offset"],
                    "end": tag["offset"] + tag["length"],
                },
            ],
        },
    }

    return annotation

    # for region in page.text_regions:
    #     region_identifier = region.id
    #     region_coords = region.coords.box
    #     region_metadata = region.metadata

    #     region_type = region.metadata.get("type", "unknown")

    #     for line in region.lines:
    #         line_identifier = line.id
    #         line_coords = line.coords.box
    #         line_metadata = line.metadata

    #         line_text = line.text

    #         # if line_identifier == "tr_1_tl_6":
    #         print(line_metadata)


if __name__ == "__main__":
    main(FOLDER)
