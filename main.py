import os
import json
from collections import defaultdict
import uuid

from pagexml.parser import parse_pagexml_file
from pagexml.helper.pagexml_helper import get_custom_tags

import pandas as pd

# FOLDER = "data/"
PREFIX = "https://id.amsterdamtimemachine.nl/ark:/81741/amsterdam-diaries/"

METADATA_DIARIES = "data/metadata_diaries.csv"
METADATA_ENTRIES = "data/metadata_entries.csv"


region2textualbody = defaultdict(list)

name2archive_uri = {
    "Verzetsmuseum Amsterdam": "https://www.verzetsmuseum.org/",
    "Stadsarchief Amsterdam": "https://archief.amsterdam/",
    "Atria": "https://atria.nl/",
    "Crescas Joods Educatief Centrum": "https://www.crescas.nl/",
}

tagtype2resource = {
    "structure": {
        "id": PREFIX + "tags/entities/" + "structure",
        "type": "skos:Concept",
        "label": "Structure",
    },
    "date": {
        "id": PREFIX + "tags/entities/" + "date",
        "type": "skos:Concept",
        "label": "Date",
    },
    "person": {
        "id": PREFIX + "tags/entities/" + "person",
        "type": "skos:Concept",
        "label": "Person",
    },
    "place": {
        "id": PREFIX + "tags/entities/" + "place",
        "type": "skos:Concept",
        "label": "Place",
    },
    "organization": {
        "id": PREFIX + "tags/entities/" + "organization",
        "type": "skos:Concept",
        "label": "Organization",
    },
    "add": {
        "id": PREFIX + "tags/entities/" + "add",
        "type": "skos:Concept",
        "label": "Add",
    },
    "unclear": {
        "id": PREFIX + "tags/entities/" + "unclear",
        "type": "skos:Concept",
        "label": "Unclear",
    },
    "blackening": {
        "id": PREFIX + "tags/entities/" + "blackening",
        "type": "skos:Concept",
        "label": "Blackening",
    },
    "speech": {
        "id": PREFIX + "tags/entities/" + "speech",
        "type": "skos:Concept",
        "label": "Speech",
    },
    "abbrev": {
        "id": PREFIX + "tags/entities/" + "abbrev",
        "type": "skos:Concept",
        "label": "Abbrev",
    },
    "gap": {
        "id": PREFIX + "tags/entities/" + "gap",
        "type": "skos:Concept",
        "label": "Gap",
    },
    "sic": {
        "id": PREFIX + "tags/entities/" + "sic",
        "type": "skos:Concept",
        "label": "Sic",
    },
}
#

regiontype2resource = {
    "heading": {
        "id": PREFIX + "tags/regions/" + "heading",
        "type": "skos:Concept",
        "label": "Heading",
    },
    "paragraph": {
        "id": PREFIX + "tags/regions/" + "paragraph",
        "type": "skos:Concept",
        "label": "Paragraph",
    },
    "caption": {
        "id": PREFIX + "tags/regions/" + "caption",
        "type": "skos:Concept",
        "label": "Caption",
    },
    "visual": {
        "id": PREFIX + "tags/regions/" + "visual",
        "type": "skos:Concept",
        "label": "Visual",
    },
    "marginalia": {
        "id": PREFIX + "tags/regions/" + "marginalia",
        "type": "skos:Concept",
        "label": "Marginalia",
    },
    "page-number": {
        "id": PREFIX + "tags/regions/" + "page-number",
        "type": "skos:Concept",
        "label": "Page number",
    },
}


def generate_metadata(csv_diaries, csv_entries):

    df_diaries = pd.read_csv(csv_diaries)
    df_entries = pd.read_csv(csv_entries)

    resources = []

    # books
    for _, r in df_diaries.iterrows():

        # Organization
        archive = {
            # "@id": ?
            "@type": "ArchiveOrganization",
            "name": r["archive_name"],
        }

        # Collection
        collection = {
            # "@id": ?
            "@type": ["Collection", "ArchiveComponent"],
            "name": r["archive_collection"],
            "holdingArchive": archive,
        }

        # Diary
        book = {
            "@context": {"@vocab": "https://schema.org/"},
            "@id": f"{PREFIX}diaries/{r.identifier}",
            "@type": "Book",
            "author": {
                "@id": r.author_URI,
                "@type": "Person",
                "name": r["author"],
            },
            "about": {
                "@id": r.about_URI,
                "@type": "Person",
                "name": r["about"],
            },
            "name": r["name"],
            "isPartOf": collection,
            # "keywords": r["keywords"].replace(";", ","),
            "description": r.description if not pd.isna(r.description) else [],
            "temporalCoverage": str(r.year).replace("-", "/"),
            # "dateCreated": #TODO
        }

        resources.append(book)

        # entries
        for _, e in df_entries[df_entries["diary"] == r.identifier].iterrows():

            # Regions
            regions = []
            textualbodies = []
            for region in e["regions"].split("\n"):
                region = region.replace(" ", "#")
                regions.append(region)
                textualbodies += region2textualbody[region]

            # Entry
            entry = {
                "@context": {
                    "@vocab": "https://schema.org/",
                    "text": {
                        "@id": "https://schema.org/text",
                        "@type": "@id",
                        "@container": "@list",
                    },
                },
                "@id": f"{PREFIX}entries/{e.identifier}",
                "@type": "Manuscript",
                "isPartOf": {
                    "@id": book["@id"],
                    "@type": "Book",
                    "name": book["name"],
                },  # shallow
                "name": e["name"],
                "dateCreated": e.date,
                "text": textualbodies,
            }

            # Entry annotation
            entry_annotation = {
                "@context": [
                    "http://www.w3.org/ns/anno.jsonld",
                ],
                "id": f"{PREFIX}annotations/entries/{e.identifier}-annotation",
                "motivation": "classifying",
                "type": "Annotation",
                "body": [entry],
                "target": {"type": "oa:List", "items": regions},
            }

            resources.append(entry_annotation)

    return resources


def parse_pagexml(pagexml_file_path, region2textualbody=region2textualbody):

    annotations = []

    page = parse_pagexml_file(pagexml_file_path)
    scan_uri = f"{pagexml_file_path}-scan"

    # TODO: these are not unique
    base_filename = os.path.basename(pagexml_file_path)

    for region in page.text_regions:

        region_id = f"{base_filename}#{region.id}"
        target_id = f"{region_id}-target"

        region_type = region.types.difference(
            {"physical_structure_doc", "pagexml_doc", "text_region"}
        )
        if not region_type:
            region_type = ""
        else:
            region_type = region_type.pop()
            region_type_resource = regiontype2resource[region_type]

        # region2text[region.id] = {"coords": region.coords, "lines": []}

        region_annotation = {
            "@context": [
                "http://www.w3.org/ns/anno.jsonld",
                "http://iiif.io/api/extension/text-granularity/context.json",
            ],
            "id": f"{PREFIX}annotations/regions/{region_id}",
            "type": "Annotation",
            "textGranularity": "region",
            "items": [],
            "body": [
                {
                    "type": "SpecificResource",
                    "source": region_type_resource,
                    "purpose": "tagging",
                },
            ],
            "target": {
                "id": f"{PREFIX}annotations/regions/{target_id}",
                "type": "SpecificResource",
                "source": scan_uri,
                "selector": [
                    {
                        "type": "FragmentSelector",
                        "value": f"xywh={region.coords.x},{region.coords.y},{region.coords.w},{region.coords.h}",
                    },
                ],
            },
        }
        annotations.append(region_annotation)

        for line in region.lines:
            # region2text[region.id]["lines"].append()

            line_id = f"{region_id}-{line.id}"
            body_id = f"{line_id}-body"

            region2textualbody[region_id].append(body_id)

            line_annotation = {
                "@context": [
                    "http://www.w3.org/ns/anno.jsonld",
                    "http://iiif.io/api/extension/text-granularity/context.json",
                ],
                "id": f"{PREFIX}annotations/lines/{line_id}",
                "type": "Annotation",
                "textGranularity": "line",
                "body": [
                    {
                        "id": f"{PREFIX}annotations/lines/{body_id}",
                        "type": "TextualBody",
                        "value": line.text,
                        "purpose": "supplementing",
                    },
                ],
                "target": {
                    "type": "SpecificResource",
                    "source": scan_uri,
                    "selector": [
                        {
                            "type": "FragmentSelector",
                            "value": f"xywh={line.coords.x},{line.coords.y},{line.coords.w},{line.coords.h}",
                        },
                    ],
                },
            }
            region_annotation["items"].append(line_id)
            annotations.append(line_annotation)

    return annotations


def make_entity_annotation(tag, identifier="", prefix="", filename=""):

    if not identifier:
        identifier = uuid.uuid4()

        if prefix:
            identifier = f"{prefix}{identifier}"

    # TODO: these are not unique
    base_filename = os.path.basename(filename)

    source = f"{base_filename}#{tag['region_id']}-{tag['line_id']}-body"

    annotation = {
        "@context": "http://www.w3.org/ns/anno.jsonld",
        "id": identifier,
        "type": "Annotation",
        "body": [
            {
                "type": "SpecificResource",
                "source": tagtype2resource[tag["type"]],
                # "value": tag["type"],
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


def main():

    # Text (from pagexml)
    textual_annotations = []
    for root, dirs, files in os.walk("data/export_job_8701885/"):
        for file in sorted(files):
            if file.endswith(".xml") and file not in ("metadata.xml", "mets.xml"):
                filepath = os.path.join(root, file)

                textual_annotations += parse_pagexml(filepath)

    with open("rdf/textual_annotations.jsonld", "w") as outfile:
        json.dump(textual_annotations, outfile, indent=4)

    # Metadata
    resources = generate_metadata(METADATA_DIARIES, METADATA_ENTRIES)

    with open("rdf/metadata.jsonld", "w") as outfile:
        json.dump(resources, outfile, indent=4)

    # Annotations
    entity_annotations = []
    for root, dirs, files in os.walk("data/export_job_8701885/"):
        for file in sorted(files):
            if file.endswith(".xml") and file not in ("metadata.xml", "mets.xml"):
                filepath = os.path.join(root, file)

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

                tags = get_custom_tags(page)

                for tag in tags:
                    entity_annotations.append(
                        make_entity_annotation(
                            tag, prefix=PREFIX + "annotations/", filename=filepath
                        )
                    )

    with open("rdf/entity_annotations.jsonld", "w") as outfile:
        json.dump(entity_annotations, outfile, indent=4)


if __name__ == "__main__":
    main()
