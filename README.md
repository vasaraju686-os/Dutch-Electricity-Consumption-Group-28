# Dutch Electricity FAIR Data Project

A semantic web and FAIR data engineering project providing ontology modeling, RDF conversion, SHACL quality validation, DCAT/DCTERMS metadata, and a FAIR data assessment for regional electricity consumption data in the Netherlands.

---

## 1. Project Purpose & Dataset Description

This project converts tabular public utility data into a linked RDF knowledge graph according to the **FAIR Data Principles** (Findable, Accessible, Interoperable, Reusable).

- **Original Dataset**: `data/raw/coteq_electricity_2013.csv`
- **Coverage**: Year 2013 electricity distribution across municipalities in the service area of regional grid operator **Coteq Netbeheer B.V.** (e.g. Almelo, Goor, Enter, Oldenzaal in Overijssel, Netherlands).
- **Scope**: 2,503 records detailing electricity connections, annual consumption, smart meter uptake, active connections percentage, delivery percentage, and low-tariff consumption percentages.
- **Semantic Graph**: 46,236 RDF triples serialized in Turtle (`text/turtle`).

---

## 2. Workspace Folder Structure

```
Dutch_Electricity_fair_project/
├── data/
│   ├── raw/
│   │   └── coteq_electricity_2013.csv       # Original tabular CSV dataset (2,503 records)
│   └── sample/                              # Reserved for sample datasets
├── ontology/
│   └── dutch_electricity_ontology.owx       # OWL 2 XML domain ontology (engineered in Protégé)
├── rdf/
│   └── coteq_electricity_2013_csv (1).ttl   # Primary RDF Turtle dataset (46,236 triples)
├── shacl/
│   ├── coteq_electricity_shapes.ttl         # SHACL validation shapes with SPARQL business rules
│   └── energy_shapes.ttl                    # Compact baseline node shapes
├── reports/
│   ├── dataset_metadata.ttl                 # DCAT 2.0 & DCTERMS dataset metadata
│   ├── shacl_validation_report.txt          # SHACL validation execution report (Conforms: True)
│   └── FAIR_assessment.md                   # Systematic evaluation of F, A, I, R principles
├── scripts/                                 # Helper utilities
├── validate.py                              # Python SHACL validation script using pySHACL & RDFLib
├── test_invalid.ttl                         # 5 records with deliberate errors testing constraint rules
└── README.md                                # Project documentation
```

---

## 3. Confirmed Tools & Stack

| Tool                               | Role in Project                                                | Evidence & Artifacts                                                                                                                                                                                                       |
| :--------------------------------- | :------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **OpenRefine** (with RDFTransform) | Tabular data cleaning and RDF mapping to Turtle                | Column GREL mappings, URI minting, and RDF export                                                                                                                                                                          |
| **Protégé**                        | Conceptual ontology modeling in OWL 2 XML                      | [`ontology/dutch_electricity_ontology.owx`](file:///C:/Users/mahesh/Desktop/Dutch_Electricity_fair_project/ontology/dutch_electricity_ontology.owx)                                                                        |
| **RDFLib** (Python 7.6.0)          | Graph parsing, programmatic serialization, metadata validation | [`validate.py`](file:///C:/Users/mahesh/Desktop/Dutch_Electricity_fair_project/validate.py), [`reports/dataset_metadata.ttl`](file:///C:/Users/mahesh/Desktop/Dutch_Electricity_fair_project/reports/dataset_metadata.ttl) |
| **pySHACL** (Python 0.40.1)        | W3C SHACL shape validation with SHACL-SPARQL advanced features | [`shacl/coteq_electricity_shapes.ttl`](file:///C:/Users/mahesh/Desktop/Dutch_Electricity_fair_project/shacl/coteq_electricity_shapes.ttl)                                                                                  |

---

## 4. RDF Transformation Workflow

The transformation was carried out in OpenRefine using the RDFTransform extension:

1. **Record URI Minting**: Each CSV row is mapped to an `EnergyRecord` instance using a standardized identifier pattern:
   `http://example.org/coteq/record/coteq-electricity-2013-{ROW_ID}`
2. **Entity Decomposition**:
   - **Measurement**: Linked via `de:hasMeasurement` to `http://example.org/coteq/measurement/coteq-electricity-2013-{ROW_ID}`.
   - **Location**: Linked via `de:locatedIn` to `http://example.org/coteq/location/{zipcode_from}-{zipcode_to}`.
   - **Street**: Linked via `de:hasStreet` to `http://example.org/coteq/street/{street_name}`.
   - **Network Manager**: Linked via `de:managedBy` to `http://example.org/coteq/network-manager/CoteqNetbeheerBV`.
3. **Datatypes & Literals**: Numeric metrics were cast to typed literals:
   - `de:numberOfConnections` (`xsd:int`)
   - `de:annualConsumption`, `de:deliveryPercentage`, `de:smartMeterPercentage`, `de:activeConnectionsPercentage`, `de:annualConsumptionLowTariffPercentage` (`xsd:double`)
   - Dutch postcodes and cities (`xsd:string`).

---

## 5. Ontology Architecture

- **Ontology IRI / Namespace**: `http://example.org/dutch-energy-ontology#` (prefix: `de:`)
- **Serialization**: OWL 2 XML Syntax in [`ontology/dutch_electricity_ontology.owx`](file:///C:/Users/mahesh/Desktop/Dutch_Electricity_fair_project/ontology/dutch_electricity_ontology.owx)

### Classes

- `de:EnergyRecord`: Represents a single annual electricity distribution record for a street/postcode segment.
- `de:EnergyMeasurement`: Captures consumption metrics, connection figures, and smart meter percentages.
- `de:Location`: Represents the geographic postcode interval (`zipCodeFrom` to `zipCodeTo`).
- `de:Street`: Represents the street entity.
- `de:NetworkManager`: Represents the regional distribution system operator (Coteq Netbeheer B.V.).

### Object Properties

- `de:hasMeasurement` (Domain: `de:EnergyRecord`, Range: `de:EnergyMeasurement`)
- `de:hasStreet` (Domain: `de:EnergyRecord`, Range: `de:Street`)
- `de:locatedIn` (Domain: `de:EnergyRecord`, Range: `de:Location`)
- `de:managedBy` (Domain: `de:EnergyRecord`, Range: `de:NetworkManager`)

---

## 6. SHACL Quality Validation

Validation is implemented in [`validate.py`](file:///C:/Users/mahesh/Desktop/Dutch_Electricity_fair_project/validate.py) and executed against [`shacl/coteq_electricity_shapes.ttl`](file:///C:/Users/mahesh/Desktop/Dutch_Electricity_fair_project/shacl/coteq_electricity_shapes.ttl).

### Constraints Verified

1. **Cardinality & Types**: Mandatory single occurrences for record identifiers, postcodes, cities, and measurements.
2. **Dutch Postcode Regex**: Enforces Dutch postcode formatting (`^[0-9]{4}[A-Z]{2}$`).
3. **Value Ranges**: Ensures percentages stay within `[0.0, 100.0]` and connection counts are $\ge 1$.
4. **Closed Shapes**: Disallows unexpected properties on records and measurements.
5. **SPARQL Business Rules**:
   - Record identifier matches the local name of the record IRI.
   - `zipCodeFrom` must lexicographically sort before or equal to `zipCodeTo`.
   - Location IRI suffix strictly corresponds to `<zipCodeFrom>-<zipCodeTo>`.

### Canonical Validation Command

```powershell
python validate.py -d "rdf/coteq_electricity_2013_csv (1).ttl" -s "shacl/coteq_electricity_shapes.ttl" -r "reports/shacl_validation_report.txt"
```

### Result

```
CONFORMANCE RESULT: True
VIOLATIONS COUNT:   0
```

> [!NOTE]
> Conformance indicates that the dataset satisfies all constraint components defined in the SHACL shapes. It does not guarantee the complete absence of data quality issues beyond the properties and constraints modeled in these shapes.

---

## 7. Dataset Metadata

Machine-readable dataset metadata is authored in [`reports/dataset_metadata.ttl`](file:///C:/Users/mahesh/Desktop/Dutch_Electricity_fair_project/reports/dataset_metadata.ttl) conforming to **DCAT 2.0**, **Dublin Core Terms (`dcterms`)**, and **PROV-O**.

### Key Metadata Fields

- **Identifier**: `http://example.org/dataset/coteq-electricity-2013` (local placeholder pending persistent DOI).
- **Creator / Grid Operator**: Coteq Netbeheer B.V.
- **Semantic Author**: Mahesh (ontology & transformation).
- **Formats**: Turtle (`text/turtle`), CSV (`text/csv`).
- **Licence**: **Unverified / Unknown**. _Note: No licence is assumed or assigned without verifiable evidence from the source provider._
- **Original Publisher / Release Date**: Marked as unverified from the local source archive.

---

## 8. FAIR Assessment Summary

A comprehensive assessment is available in [`reports/FAIR_assessment.md`](file:///C:/Users/mahesh/Desktop/Dutch_Electricity_fair_project/reports/FAIR_assessment.md):

- **Findable (F)**: Strong local metadata and structured URIs. Primary gaps are the absence of a registered persistent identifier (DOI/w3id) and indexing in public data catalogs.
- **Accessible (A)**: Standards-based serialization (Turtle, XML). Currently stored in a local workspace; requires deployment to an HTTPS server with content negotiation or a public repository.
- **Interoperable (I)**: Formal RDF knowledge graph, OWL 2 ontology, and W3C SHACL shapes. Recommended next action is linking entities to Dutch national registers (BAG) and Wikidata.
- **Reusable (R)**: High data attribute granularity with confirmed structural compliance. **Critical gap: Absence of a verified data licence.** Clarification with Coteq Netbeheer is required before public reuse.

---

## 9. Reproduction Instructions

### Prerequisites

- Python 3.10+
- Virtual environment with `pyshacl` and `rdflib` installed.

### Step 1: Activate Environment & Verify Packages

```powershell
# Activate existing virtual environment
.\.venv\Scripts\Activate.ps1

# Verify installed packages
python -c "import pyshacl, rdflib; print('RDFLib:', rdflib.__version__, '| pySHACL:', pyshacl.__version__)"
```

### Step 2: Validate Metadata Syntax

```powershell
python -c "import rdflib; g = rdflib.Graph().parse('reports/dataset_metadata.ttl', format='turtle'); print('Metadata parsed successfully, total triples:', len(g))"
```

### Step 3: Run Validation on Real Dataset

```powershell
python validate.py -d "rdf/coteq_electricity_2013_csv (1).ttl" -s "shacl/coteq_electricity_shapes.ttl" -r "reports/shacl_validation_report.txt"
```

_Expected Result_: `CONFORMS: True`, 0 violations.

### Step 4: Run Validation on Intentional Error Test Suite

```powershell
python validate.py -d "test_invalid.ttl" -s "shacl/coteq_electricity_shapes.ttl"
```

_Expected Result_: `CONFORMS: False`, 7 violations reporting all 5 deliberate test errors.

Group 28 aims to make the Dutch Electricity Consumption Dataset from Coteq Netbeheer (2013) easier to find, access, understand, and reuse. We transform CSV data into RDF using OpenRefine, organise it with an ontology in Protégé, store it in GraphDB, and publish it through a FAIR Data Point.
