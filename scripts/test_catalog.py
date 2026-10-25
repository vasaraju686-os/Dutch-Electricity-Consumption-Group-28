import urllib.request
import json

auth_data = json.dumps({'email': 'albert.einstein@example.com', 'password': 'password'}).encode('utf-8')
req = urllib.request.Request('http://localhost:8085/tokens', data=auth_data, headers={'Content-Type': 'application/json'}, method='POST')
with urllib.request.urlopen(req) as resp:
    token = json.loads(resp.read().decode('utf-8'))['token']

catalog_ttl = """@prefix dct: <http://purl.org/dc/terms/> .
@prefix dcat: <http://www.w3.org/ns/dcat#> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .

<> a dcat:Catalog ;
  dct:title "Dutch Utilities and Energy Catalog"@en ;
  dct:description "Catalog of regional Dutch electricity consumption and distribution datasets."@en ;
  dcat:version "1.0" ;
  dct:isPartOf <http://localhost:8085> ;
  dct:publisher [
    a foaf:Agent ;
    foaf:name "Coteq Netbeheer B.V."
  ] .
""".encode('utf-8')

req = urllib.request.Request(
    'http://localhost:8085/catalog',
    data=catalog_ttl,
    headers={'Authorization': f'Bearer {token}', 'Content-Type': 'text/turtle', 'Accept': 'text/turtle'},
    method='POST'
)
try:
    with urllib.request.urlopen(req) as resp:
        print('Status:', resp.status)
        print(resp.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print('HTTPError:', e.code, e.read().decode('utf-8'))
