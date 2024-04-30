import os
import json
from collections import defaultdict
import uuid
from lxml import etree

from pagexml.parser import parse_pagexml_file
from pagexml.helper.pagexml_helper import get_custom_tags

import pandas as pd

# FOLDER = "data/"
PREFIX = "https://id.amsterdamtimemachine.nl/ark:/81741/amsterdam-diaries/"
IIIF_PREFIX = "https://images.diaries.amsterdamtimemachine.nl/iiif/"

METADATA_DIARIES = "data/metadata_diaries.csv"
METADATA_ENTRIES = "data/metadata_entries.csv"
METADATA_PERSONS = "data/metadata_persons.csv"

ANNOTATION_IDENTIFIERS = "data/annotations_linking.csv"

body2length = dict()

region2textualbody = defaultdict(list)
diary2scan = defaultdict(list)

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
    "atm_food": {
        "id": PREFIX + "tags/entities/" + "atm_food",
        "type": "skos:Concept",
        "label": "Etenswaren",
        "skos:closeMatch": [
            "http://vocab.getty.edu/aat/300254496",
            "http://data.beeldengeluid.nl/gtaa/217707",
        ],
    },
}

regiontype2resource = {
    "region": {
        "id": PREFIX + "tags/regions/" + "region",
        "type": "skos:Concept",
        "label": "Region",
    },
    "heading": {
        "id": PREFIX + "tags/regions/" + "heading",
        "type": "skos:Concept",
        "label": "Heading",
        "skos:broader": PREFIX + "tags/regions/" + "region",
    },
    "header": {
        "id": PREFIX + "tags/regions/" + "header",
        "type": "skos:Concept",
        "label": "header",
        "skos:broader": PREFIX + "tags/regions/" + "region",
    },
    "paragraph": {
        "id": PREFIX + "tags/regions/" + "paragraph",
        "type": "skos:Concept",
        "label": "Paragraph",
        "skos:broader": PREFIX + "tags/regions/" + "region",
    },
    "caption": {
        "id": PREFIX + "tags/regions/" + "caption",
        "type": "skos:Concept",
        "label": "Caption",
        "skos:broader": PREFIX + "tags/regions/" + "region",
    },
    "visual": {
        "id": PREFIX + "tags/regions/" + "visual",
        "type": "skos:Concept",
        "label": "Visual",
        "skos:broader": PREFIX + "tags/regions/" + "region",
    },
    "marginalia": {
        "id": PREFIX + "tags/regions/" + "marginalia",
        "type": "skos:Concept",
        "label": "Marginalia",
        "skos:broader": PREFIX + "tags/regions/" + "region",
    },
    "page-number": {
        "id": PREFIX + "tags/regions/" + "page-number",
        "type": "skos:Concept",
        "label": "Page number",
        "skos:broader": PREFIX + "tags/regions/" + "region",
    },
}


def getSVG(
    coordinates,
    color="#BD0032",
    opacity="0.1",
    stroke_width="1",
    stroke_color="#BD0032",
):

    points = "M "  # start at this point
    points += " L ".join(
        [f"{int(x)},{int(y)}" for x, y in coordinates]
    )  # then move from point to point
    points += " Z"  # close

    svg = etree.Element("svg", xmlns="http://www.w3.org/2000/svg")
    _ = etree.SubElement(
        svg,
        "path",
        **{
            "fill-rule": "evenodd",
            "fill": color,
            "stroke": stroke_color,
            "stroke-width": stroke_width,
            "fill-opacity": opacity,
            "d": points,
        },
    )

    return etree.tostring(svg, encoding=str)


def generate_metadata(csv_diaries, csv_entries, csv_persons, diary2scan=diary2scan):

    df_diaries = pd.read_csv(csv_diaries)
    df_entries = pd.read_csv(csv_entries)
    df_persons = pd.read_csv(csv_persons)

    resources = []

    diaryname2fileprefix = dict()

    # books
    for _, r in df_diaries.iterrows():

        diaryname2fileprefix[r["name"]] = r["file_prefix"]

        # Organization
        archive = {
            "@id": r["archive_URL"],
            "@type": "ArchiveOrganization",
            "name": r["archive_name"],
        }

        # Collection
        collection = {
            "@id": r["archive_collection_URL"],
            "@type": ["Collection", "ArchiveComponent"],
            "name": r["archive_collection_name"],
            "holdingArchive": archive,
        }

        # Diary
        book = {
            "@context": {
                "@vocab": "https://schema.org/",
                "sameAs": {"@type": "@id"},
                "url": {"@type": "@id"},
                "image": {
                    "@id": "https://schema.org/image",
                    "@type": "@id",
                    "@container": "@list",
                },
            },
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
            "temporalCoverage": r["temporalCoverage"],
            "dateCreated": r["dateCreated"],
            "identifier": r["identifier"],
            "url": r["Viewer_URI"],
            "image": diary2scan[r["folder_name"]],
        }

        if not pd.isna(r["Book_URI"]):
            book["sameAs"] = r["Book_URI"]

        resources.append(book)

        # entries
        for _, e in df_entries[
            df_entries["identifier_diary"] == r.identifier
        ].iterrows():

            # Regions
            regiontargets = []
            textualbodies = []
            for region in e["regions"].split("\n"):
                region = f"{PREFIX}annotations/regions/{region.replace('.xml ', '/')}"
                regiontargets.append(region + "-target")
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
                    "name": "https://schema.org/name",
                },
                "@id": f"{PREFIX}annotations/entries/{e.identifier}",
                "@type": "Manuscript",
                "isPartOf": {
                    "@id": book["@id"],
                    "@type": "Book",
                },  # shallow
                "text": textualbodies,
            }

            if not pd.isna(e["name"]):
                entry["name"] = e["name"]

            if not pd.isna(e["date"]):
                # if e["date"].count("-") == 1:
                #     entry["dateCreated"] = {
                #         "@type": "xsd:gYearMonth",
                #         "@value": e["date"],
                #     }
                # elif e["date"].count("-") == 2:
                #     entry["dateCreated"] = {
                #         "@type": "xsd:date",
                #         "@value": e["date"],
                #     }
                # else:
                #     entry["dateCreated"] = {
                #         "@type": "xsd:gYear",
                #         "@value": e["date"],
                #     }

                entry["dateCreated"] = {
                    "@type": "http://www.w3.org/2001/XMLSchema#date",
                    "@value": e["date"],
                }

            # Entry annotation
            entry_annotation = {
                "@context": [
                    "http://www.w3.org/ns/anno.jsonld",
                    {
                        "target": {
                            "@id": "oa:hasTarget",
                            "@type": "@id",
                            "@container": "@list",
                        }
                    },
                ],
                "id": f"{PREFIX}annotations/entries/{e.identifier}-annotation",
                "motivation": "classifying",
                "type": "Annotation",
                "body": [entry],
                # "target": {"type": "oa:List", "items": regiontargets},
                "target": regiontargets,
            }

            resources.append(entry_annotation)

    # persons
    for _, r in df_persons.iterrows():

        # uri	name	birthDate	birthPlace_uri	birthPlace_name	deathDate	deathPlace_uri	deathPlace_name	description	image	image_other

        person = {
            "@context": {"@vocab": "https://schema.org/"},
            "@id": r.uri,
            "@type": "Person",
            "name": r["name"],
        }
        if not pd.isna(r["birthDate"]):
            person["birthDate"] = r["birthDate"]

        if not pd.isna(r["birthPlace_uri"]):
            person["birthPlace"] = {
                "@id": r["birthPlace_uri"],
                "@type": "Place",
                "name": r["birthPlace_name"],
            }

        if not pd.isna(r["deathDate"]):
            person["deathDate"] = r["deathDate"]

        if not pd.isna(r["deathPlace_uri"]):
            person["deathPlace"] = {
                "@id": r["deathPlace_uri"],
                "@type": "Place",
                "name": r["deathPlace_name"],
            }

        if not pd.isna(r["description"]):
            person["description"] = r["description"]

        if not pd.isna(r["image"]):
            person["image"] = r["image"]

        # if not pd.isna(r["image_other"]):
        #     person["image_other"] = r["image_other"]

        resources.append(person)

    return resources, diaryname2fileprefix


def parse_pagexml(
    diary,
    pagexml_file_path,
    region2textualbody=region2textualbody,
    diary2scan=diary2scan,
    body2length=body2length,
):

    annotations = []

    page = parse_pagexml_file(pagexml_file_path)

    filename = os.path.basename(pagexml_file_path).split("_", 1)[1]
    scan_name = filename.replace(".xml", ".jpg")
    scan_uri = IIIF_PREFIX + scan_name

    diary2scan[diary].append(scan_uri)

    # TODO: these are not unique
    base_filename = os.path.basename(pagexml_file_path)

    for region in page.text_regions:

        region_id = f"{PREFIX}annotations/regions/{base_filename.replace('.xml', '/')}{region.id}"
        target_id = f"{region_id}-target"

        region_type = region.types.difference(
            {"physical_structure_doc", "pagexml_doc", "text_region"}
        )
        if not region_type:
            region_type = ""
            region_type_resource = regiontype2resource["region"]
        else:
            region_type = region_type.pop()
            region_type_resource = regiontype2resource[region_type]

        # region2text[region.id] = {"coords": region.coords, "lines": []}

        region_annotation = {
            "@context": [
                "http://www.w3.org/ns/anno.jsonld",
                "http://iiif.io/api/extension/text-granularity/context.json",
            ],
            "id": region_id,
            "type": "Annotation",
            "textGranularity": "block",
            "items": [],
            "body": [
                {
                    "type": "SpecificResource",
                    "source": region_type_resource,
                    "purpose": "tagging",
                },
            ],
            "target": {
                "id": target_id,
                "type": "SpecificResource",
                "source": {
                    "@id": scan_uri,
                    "type": "ImageObject",
                    "name": scan_name,
                    "contentUrl": scan_uri + "/full/max/0/default.jpg",
                    "thumbnailUrl": scan_uri + "/full/,250/0/default.jpg",
                },
                "selector": [
                    {
                        "type": "FragmentSelector",
                        "value": f"xywh={region.coords.x},{region.coords.y},{region.coords.w},{region.coords.h}",
                        "conformsTo": "http://www.w3.org/TR/media-frags/",
                    },
                    {
                        "type": "SvgSelector",
                        "value": getSVG(region.coords.points),
                        "conformsTo": "http://www.w3.org/TR/SVG/",
                    },
                ],
            },
        }

        for line in region.lines:
            # region2text[region.id]["lines"].append()

            line_id = f"{region_id}-{line.id}"
            body_id = f"{line_id}-body"

            # Needed to merge annotations later
            if line.text:
                body2length[body_id] = len(line.text)
            else:
                body2length[body_id] = 0

            region2textualbody[region_id].append(body_id)

            line_annotation = {
                "@context": [
                    "http://www.w3.org/ns/anno.jsonld",
                    "http://iiif.io/api/extension/text-granularity/context.json",
                ],
                "id": line_id,
                "type": "Annotation",
                "textGranularity": "line",
                "body": [
                    {
                        "id": body_id,
                        "type": "TextualBody",
                        "value": line.text,
                        "purpose": "supplementing",
                    },
                ],
                "target": {
                    "type": "SpecificResource",
                    "source": {
                        "@id": scan_uri,
                        "type": "ImageObject",
                        "name": scan_name,
                        "contentUrl": scan_uri + "/full/max/0/default.jpg",
                        "thumbnailUrl": scan_uri + "/full/,250/0/default.jpg",
                    },
                    "selector": [
                        {
                            "type": "FragmentSelector",
                            "value": f"xywh={line.coords.x},{line.coords.y},{line.coords.w},{line.coords.h}",
                            "conformsTo": "http://www.w3.org/TR/media-frags/",
                        },
                        {
                            "type": "SvgSelector",
                            "value": getSVG(line.coords.points),
                            "conformsTo": "http://www.w3.org/TR/SVG/",
                        },
                    ],
                },
            }
            region_annotation["items"].append(line_id)
            annotations.append(line_annotation)

        annotations.append(region_annotation)

    return annotations


def make_entity_annotation(tag, identifier="", prefix="", filename=""):

    if not identifier:
        identifier = uuid.uuid4()

        if prefix:
            identifier = f"{prefix}{identifier}"

    # TODO: these are not unique
    base_filename = os.path.basename(filename)

    source = f"{PREFIX}annotations/regions/{base_filename.replace('.xml', '/')}{tag['region_id']}-{tag['line_id']}-body"

    annotation = {
        "@context": "http://www.w3.org/ns/anno.jsonld",
        "id": identifier,
        "type": "Annotation",
        "body": [
            {
                "type": "SpecificResource",
                "source": tagtype2resource[tag["type"]],
                "purpose": "classifying",
            }
        ],
        "target": [
            {
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
            }
        ],
    }

    return annotation


def add_entity_identifier(
    annotation, identifier_df, diaryname2fileprefix, skip_tags=()
):

    annotation_id = annotation["id"]
    source = annotation["target"][0]["source"]
    tag = annotation["body"][0]["source"]["id"].replace(PREFIX + "tags/entities/", "")
    text = " ".join([t["selector"][0]["exact"] for t in annotation["target"]])
    text = text.replace("- ", "").replace("¬ ", "")

    if tag.startswith("atm_"):
        # skip
        return annotation, identifier_df
    elif tag in skip_tags:
        return annotation, identifier_df

    for diary, fileprefix in diaryname2fileprefix.items():
        if fileprefix in source:
            break

    # identifying
    identifier, identifier_type, annotation_id, identifier_df = (
        get_annotation_identifier(
            diary, source, tag, text, annotation_id, identifier_df
        )
    )

    if annotation_id:
        annotation["id"] = annotation_id

    if identifier:
        if tag == "date":
            annotation["body"].append(
                {
                    "type": "TextualBody",
                    "value": {
                        "@type": "http://www.w3.org/2001/XMLSchema#date",
                        "@value": identifier,
                    },
                    "purpose": "identifying",
                }
            )
        elif tag == "abbrev":
            annotation["body"].append(
                {
                    "type": "TextualBody",
                    "value": identifier,
                    "purpose": "identifying",
                }
            )
        else:
            annotation["body"].append(
                {
                    "type": "SpecificResource",
                    "source": {
                        "id": identifier,
                        "type": identifier_type,
                    },
                    "purpose": "identifying",
                }
            )

    return annotation, identifier_df


def merge_annotations(annotations):

    for a2, a1 in zip(reversed(annotations[1:]), reversed(annotations[:-1])):

        # Are the annotations of the same type?
        if not a1["body"][0]["source"] == a2["body"][0]["source"]:
            continue

        text_length = body2length[a1["target"][0]["source"]]

        # Is the annotation at the end of the text?
        if not a1["target"][0]["selector"][1]["end"] == text_length:
            continue

        # Is the next annotation in the next line?
        body_id_a1 = a1["target"][0]["source"]
        body_id_a2 = a2["target"][0]["source"]

        region_id_a1 = body_id_a1.rsplit("-", 2)[0]
        region_id_a2 = body_id_a2.rsplit("-", 2)[0]

        index_a1 = region2textualbody[region_id_a1].index(body_id_a1)
        index_a2 = region2textualbody[region_id_a2].index(body_id_a2)

        if not index_a2 - index_a1 == 1:
            continue

        # Is the next annotation at the start of the text?
        if not a2["target"][0]["selector"][1]["start"] == 0:
            continue

        # annotations.remove(a1)
        annotations.remove(a2)

        # Merge targets
        a1["target"] += a2["target"]
        # annotations.append(a1)

    return annotations


def get_annotation_identifier(diary, source_body, tag, text, annotation_id, df):

    # temp fix
    source = source_body.replace("-body", "")
    source_prefix, source_rest = source.rsplit("/", 1)
    source_region, source_line = source_rest.rsplit("-", 1)

    source = f"{source_prefix}/{source_line}"

    results = df.query("source == @source & tag == @tag & text == @text")

    if results.empty:
        print(f"No identifier found for: {source}, {tag}, {text}")

        # add to df
        # index,annotation,tag,source,text,uri,label,date,checken
        df_add = pd.DataFrame(
            {
                "index": [df.shape[0] + 1],
                "annotation": [annotation_id],
                "diary": [diary],
                "tag": [tag],
                "source": [source],
                "text": [text],
                "uri": [None],
                "date": [None],
                "label": [None],
                "description": [None],
                "latitude": [None],
                "longitude": [None],
                "checken": [None],
            }
        )
        df = pd.concat([df, df_add], ignore_index=True)

        return None, None, None, df
    else:
        annotation_id = results.iloc[0]["annotation"]

        identifier = (
            results.iloc[0]["uri"] if not pd.isna(results.iloc[0]["uri"]) else None
        )

        # If no uri, use date
        identifier = identifier or (
            results.iloc[0]["date"] if not pd.isna(results.iloc[0]["date"]) else None
        )

        if tag == "person":
            identifier_type = "https://schema.org/Person"
        elif tag == "place":
            identifier_type = "https://schema.org/Place"
        elif tag == "organization":
            identifier_type = "https://schema.org/Organization"
        else:
            identifier_type = None

    return identifier, identifier_type, annotation_id, df


def generate_external_data(df):

    resources = []
    cache = set()

    for _, r in df.iterrows():

        if pd.isna(r["uri"]):
            continue
        elif r["uri"] in cache:
            continue

        if r["tag"] == "person":
            resource_type = "Person"
        elif r["tag"] == "place":
            resource_type = "Place"
        elif r["tag"] == "organization":
            resource_type = "Organization"

        resource = {
            "@context": {
                "@vocab": "https://schema.org/",
                "latitude": {
                    "@type": "http://www.w3.org/2001/XMLSchema#double",
                    "@id": "https://schema.org/latitude",
                },
                "longitude": {
                    "@type": "http://www.w3.org/2001/XMLSchema#double",
                    "@id": "https://schema.org/longitude",
                },
            },
            "@id": r["uri"],
            "@type": resource_type,
        }

        if not pd.isna(r["label"]):
            resource["name"] = r["label"]

        if not pd.isna(r["description"]):
            resource["description"] = r["description"]

        if not pd.isna(r["latitude"]):
            resource["geo"] = {
                "@type": "GeoCoordinates",
                "latitude": r["latitude"],
                "longitude": r["longitude"],
            }

        cache.add(r["uri"])
        resources.append(resource)

    return resources


def main():

    # Text (from pagexml)
    textual_annotations = []
    for diary in os.listdir("data/diaries/"):
        print(diary)
        page_xml_path = os.path.join("data/diaries/", diary, "page")
        for file in sorted(os.listdir(page_xml_path)):
            if file.endswith(".xml") and file not in ("metadata.xml", "mets.xml"):
                filepath = os.path.join(page_xml_path, file)

                textual_annotations += parse_pagexml(
                    diary, filepath, region2textualbody, diary2scan, body2length
                )

    with open("rdf/textual_annotations.jsonld", "w") as outfile:
        json.dump(textual_annotations, outfile, indent=4)

    # Metadata
    resources, diaryname2fileprefix = generate_metadata(
        METADATA_DIARIES, METADATA_ENTRIES, METADATA_PERSONS, diary2scan
    )

    with open("rdf/metadata.jsonld", "w") as outfile:
        json.dump(resources, outfile, indent=4)

    # Annotations
    entity_annotations = []
    df_annotation_identifiers = pd.read_csv(ANNOTATION_IDENTIFIERS)
    for diary in os.listdir("data/diaries/"):
        page_xml_path = os.path.join("data/diaries/", diary, "page")
        for file in sorted(os.listdir(page_xml_path)):
            if file.endswith(".xml") and file not in ("metadata.xml", "mets.xml"):
                filepath = os.path.join(page_xml_path, file)

                page = parse_pagexml_file(
                    filepath,
                    custom_tags=(
                        # "structure",
                        "date",
                        "person",
                        "place",
                        "organization",
                        "add",
                        "unclear",
                        "blackening",
                        "speech",
                        "abbrev",
                        "gap",
                        "sic",
                        "atm_food",
                    ),
                )

                tags = get_custom_tags(page)

                for tag in tags:
                    entity_annotations.append(
                        make_entity_annotation(
                            tag, prefix=PREFIX + "annotations/", filename=filepath
                        )
                    )

    # Merge annotations
    entity_annotations = merge_annotations(entity_annotations)

    # Add identifiers
    new_entity_annotations = []
    for a in entity_annotations:
        a, df_annotation_identifiers = add_entity_identifier(
            a,
            df_annotation_identifiers,
            diaryname2fileprefix,
            skip_tags=("add", "unclear", "blackening", "speech", "gap", "sic"),
        )
        new_entity_annotations.append(a)

    df_annotation_identifiers.to_csv(ANNOTATION_IDENTIFIERS, index=False)

    with open("rdf/entity_annotations.jsonld", "w") as outfile:
        json.dump(new_entity_annotations, outfile, indent=4)

    external_resources = generate_external_data(df_annotation_identifiers)

    with open("rdf/external_resources.jsonld", "w") as outfile:
        json.dump(external_resources, outfile, indent=4)


if __name__ == "__main__":
    main()
