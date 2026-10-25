import urllib.request
import urllib.parse
import json
import os
import sys

GRAPHDB_URL = "http://localhost:7200"
FDP_URL = "http://localhost:8085"

def get_fdp_token():
    auth_data = json.dumps({
        "email": "albert.einstein@example.com",
        "password": "password"
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{FDP_URL}/tokens",
        data=auth_data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))["token"]

def publish_to_fdp():
    print("--- Publishing Dutch Electricity Metadata to FAIR Data Point ---")
    token = get_fdp_token()
    print("Obtained FDP admin JWT token.")

    # 1. Create Catalog
    catalog_ttl = """@prefix dct: <http://purl.org/dc/terms/> .
@prefix dcat: <http://www.w3.org/ns/dcat#> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .

<> a dcat:Catalog ;
  dct:title "Dutch Utilities and Energy Catalog"@en ;
  dct:description "Catalog of regional Dutch electricity consumption and distribution datasets."@en ;
  dcat:version "1.0" ;
  dct:publisher [
    a foaf:Agent ;
    foaf:name "Coteq Netbeheer B.V."
  ] .
""".encode("utf-8")

    req = urllib.request.Request(
        f"{FDP_URL}/catalog",
        data=catalog_ttl,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "text/turtle",
            "Accept": "text/turtle"
        },
        method="POST"
    )
    
    catalog_url = None
    try:
        with urllib.request.urlopen(req) as resp:
            print("Catalog created successfully! Status:", resp.status)
            body = resp.read().decode("utf-8")
            # Parse catalog URI from body
            for line in body.splitlines():
                line = line.strip()
                if line.startswith("<http://localhost:8085/catalog/") and "a dcat:Catalog" in line:
                    catalog_url = line.split()[0].strip("<>")
                    break
            if not catalog_url:
                for line in body.splitlines():
                    if "http://localhost:8085/catalog/" in line:
                        parts = line.split()
                        for p in parts:
                            if p.startswith("<http://localhost:8085/catalog/"):
                                catalog_url = p.strip("<>;,")
                                break
            print(f"Catalog URL: {catalog_url}")
    except urllib.error.HTTPError as e:
        print(f"Catalog creation error: {e.code} - {e.read().decode('utf-8', errors='ignore')}")
        return

    if not catalog_url:
        print("Could not determine Catalog URL.")
        return

    # 2. Create Dataset inside the Catalog
    # In FDP, a dataset must reference its parent catalog or be created with dcat:theme
    dataset_ttl = f"""@prefix dct: <http://purl.org/dc/terms/> .
@prefix dcat: <http://www.w3.org/ns/dcat#> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .

<> a dcat:Dataset ;
  dct:title "Dutch Electricity Consumption Dataset - Coteq Netbeheer (2013)"@en ;
  dct:description "Tabular electricity consumption records collected by regional network manager Coteq Netbeheer B.V. for 2013 across municipalities in Overijssel, Netherlands. Transformed to 46,236 RDF triples."@en ;
  dcat:version "1.0" ;
  dcat:theme <http://eurovoc.europa.eu/670> ;
  dcat:keyword "electricity"@en, "smart meters"@en, "energy consumption"@en ;
  dct:isPartOf <{catalog_url}> ;
  dct:publisher [
    a foaf:Agent ;
    foaf:name "Coteq Netbeheer B.V."
  ] .
""".encode("utf-8")

    dataset_url = None
    req = urllib.request.Request(
        f"{FDP_URL}/dataset",
        data=dataset_ttl,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "text/turtle",
            "Accept": "text/turtle"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            print("Dataset created successfully! Status:", resp.status)
            body = resp.read().decode("utf-8")
            for line in body.splitlines():
                if "http://localhost:8085/dataset/" in line:
                    for p in line.split():
                        if p.startswith("<http://localhost:8085/dataset/"):
                            dataset_url = p.strip("<>;,")
                            break
            print(f"Dataset URL: {dataset_url}")
    except urllib.error.HTTPError as e:
        print(f"Dataset creation error: {e.code} - {e.read().decode('utf-8', errors='ignore')}")
        return

    if not dataset_url:
        print("Could not determine Dataset URL.")
        return

    # 3. Create Distribution inside the Dataset
    distribution_ttl = f"""@prefix dct: <http://purl.org/dc/terms/> .
@prefix dcat: <http://www.w3.org/ns/dcat#> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .

<> a dcat:Distribution ;
  dct:title "Coteq Electricity 2013 - RDF Turtle Distribution"@en ;
  dcat:version "1.0" ;
  dcat:mediaType "text/turtle" ;
  dcat:format "text/turtle" ;
  dcat:accessURL <http://localhost:7200/repositories/coteq-energy> ;
  dcat:downloadURL <http://localhost:7200/repositories/coteq-energy/statements> ;
  dct:isPartOf <{dataset_url}> ;
  dct:publisher [
    a foaf:Agent ;
    foaf:name "Coteq Netbeheer B.V."
  ] .
""".encode("utf-8")

    req = urllib.request.Request(
        f"{FDP_URL}/distribution",
        data=distribution_ttl,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "text/turtle",
            "Accept": "text/turtle"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            print("Distribution created successfully! Status:", resp.status)
            body = resp.read().decode("utf-8")
            dist_url = None
            for line in body.splitlines():
                if "http://localhost:8085/distribution/" in line:
                    for p in line.split():
                        if p.startswith("<http://localhost:8085/distribution/"):
                            dist_url = p.strip("<>;,")
                            break
            print(f"Distribution URL: {dist_url}")
    except urllib.error.HTTPError as e:
        print(f"Distribution creation error: {e.code} - {e.read().decode('utf-8', errors='ignore')}")

def query_graphdb():
    print("\n--- Querying GraphDB Knowledge Graph (coteq-energy) ---")
    query = """
    PREFIX de: <http://example.org/dutch-energy-ontology#>
    SELECT ?city (COUNT(?rec) AS ?records) (ROUND(AVG(?kwh)) AS ?avgAnnualKwh)
    WHERE {
      ?rec de:locatedIn ?loc ;
           de:hasMeasurement ?m .
      ?loc de:city ?city .
      ?m de:annualConsumption ?kwh .
    }
    GROUP BY ?city
    ORDER BY DESC(?records)
    LIMIT 10
    """
    params = urllib.parse.urlencode({"query": query})
    req = urllib.request.Request(
        f"{GRAPHDB_URL}/repositories/coteq-energy?{params}",
        headers={"Accept": "application/sparql-results+json"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"{'City':<20} | {'Record Count':<12} | {'Avg Annual Consumption (kWh)':<28}")
            print("-" * 65)
            for b in data.get("results", {}).get("bindings", []):
                city = b.get("city", {}).get("value", "N/A")
                records = b.get("records", {}).get("value", "N/A")
                avg_kwh = b.get("avgAnnualKwh", {}).get("value", "N/A")
                print(f"{city:<20} | {records:<12} | {avg_kwh:<28}")
    except Exception as e:
        print(f"SPARQL query error: {e}")

if __name__ == "__main__":
    publish_to_fdp()
    query_graphdb()
