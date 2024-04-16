import pandas as pd


from SPARQLWrapper import SPARQLWrapper, JSON
from shapely import wkt


ANNOTATION_IDENTIFIERS = (
    "data/ATM-Diaries Annotaties Linking 2024-03-14 - annotations_20240314.csv"
)


def query_wikidata(uri, endpoint="https://query.wikidata.org/sparql", cache=dict()):

    if uri in cache:
        return cache[uri]

    q = """
    SELECT DISTINCT ?uri ?uriLabel ?uriDescription ?latitude ?longitude WHERE {
        ?uri wdt:P31 [] .
    
        OPTIONAL {
            ?uri p:P625 ?coordinate.
            ?coordinate ps:P625 ?coord.
            ?coordinate psv:P625 ?coordinate_node.
            ?coordinate_node wikibase:geoLongitude ?longitude.
            ?coordinate_node wikibase:geoLatitude ?latitude.  
            }
        
        VALUES ?uri { <URIHIER> }

        SERVICE wikibase:label { bd:serviceParam wikibase:language "nl,en". }
    }
    """.replace(
        "URIHIER", uri
    )

    sparql = SPARQLWrapper(endpoint)
    sparql.setQuery(q)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    label = results["results"]["bindings"][0]["uriLabel"]["value"]
    description = (
        results["results"]["bindings"][0].get("uriDescription", {}).get("value")
    )
    latitude = results["results"]["bindings"][0].get("latitude", {}).get("value")
    longitude = results["results"]["bindings"][0].get("longitude", {}).get("value")

    cache[uri] = label, description, latitude, longitude
    return label, description, latitude, longitude


def query_adamlink(
    uri,
    endpoint="https://api.lod.uba.uva.nl/datasets/ATM/ATM-KG/services/ATM-KG/sparql",
    cache=dict(),
):

    if uri in cache:
        return cache[uri]

    q = """
    prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    prefix schema: <https://schema.org/>
    prefix geo: <http://www.opengis.net/ont/geosparql#>
    PREFIX bif: <http://www.openlinksw.com/schemas/bif#>
    SELECT ?uri ?label ?description ?geometryWKT ?longitude ?latitude WHERE {
        ?uri a [] ;
            rdfs:label ?label .

        OPTIONAL {
            ?uri schema:description ?description .
        }

        OPTIONAL {
            # Address
            ?uri schema:geoContains/geo:asWKT ?geometry .
            BIND(bif:st_x(?geometry) AS ?longitude)
            BIND(bif:st_y(?geometry) AS ?latitude)
        }

        OPTIONAL {
            # Street / Building
            ?uri geo:hasGeometry/geo:asWKT ?geometryWKT .
            # No geof function here?
        }

        VALUES ?uri { <URIHIER> }
    }
    """.replace(
        "URIHIER", uri
    )

    sparql = SPARQLWrapper(endpoint)
    sparql.setQuery(q)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    label = results["results"]["bindings"][0]["label"]["value"]
    description = results["results"]["bindings"][0].get("description", {}).get("value")
    geometryWKT = results["results"]["bindings"][0].get("geometryWKT", {}).get("value")
    latitude = results["results"]["bindings"][0].get("latitude", {}).get("value")
    longitude = results["results"]["bindings"][0].get("longitude", {}).get("value")

    if geometryWKT:
        geometry = wkt.loads(geometryWKT)
        latitude = geometry.centroid.y
        longitude = geometry.centroid.x

    cache[uri] = label, description, latitude, longitude
    return label, description, latitude, longitude


def main(annotations_file):

    df = pd.read_csv(annotations_file)

    cache = dict()

    for index, row in df.iterrows():

        if pd.isna(row["uri"]):
            continue
        elif pd.notna(row["label"]):
            continue

        uri = row["uri"]
        if "wikidata" in uri:
            label, description, latitude, longitude = query_wikidata(uri, cache=cache)
        elif "adamlink" in uri:
            label, description, latitude, longitude = query_adamlink(uri, cache=cache)

        df.at[index, "label"] = label
        df.at[index, "description"] = description
        df.at[index, "latitude"] = round(float(latitude), 6) if latitude else latitude
        df.at[index, "longitude"] = (
            round(float(longitude), 6) if longitude else longitude
        )

    # Save!
    df.to_csv(annotations_file, index=False)


if __name__ == "__main__":
    main(ANNOTATION_IDENTIFIERS)
