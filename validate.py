"""
SHACL Validation Script for Dutch Electricity Dataset
Validates RDF data against SHACL shapes using pySHACL.
"""

import sys
import time
import argparse
from datetime import datetime, timezone
from pathlib import Path
import rdflib
from rdflib.namespace import RDF, SH
import pyshacl


def run_validation(data_path: str, shapes_path: str, advanced: bool = True, report_path: str = None):
    timestamp_str = datetime.now(timezone.utc).isoformat()
    header_lines = [
        "=" * 70,
        "SHACL VALIDATION REPORT",
        "=" * 70,
        f"Timestamp (UTC): {timestamp_str}",
        f"Data file:       {data_path}",
        f"Shapes file:     {shapes_path}",
        f"Advanced SHACL:  {advanced} (supports SHACL-SPARQL constraints)",
        "-" * 70,
    ]
    for line in header_lines:
        print(line)

    # 1. Load Shapes Graph
    start_time = time.time()
    shapes_graph = rdflib.Graph()
    try:
        shapes_graph.parse(shapes_path, format="turtle")
    except Exception as e:
        print(f"ERROR: Failed to load shapes file '{shapes_path}': {e}", file=sys.stderr)
        return False, None
    shapes_triples = len(shapes_graph)
    shapes_load_time = time.time() - start_time
    shapes_msg = f"Loaded shapes graph: {shapes_triples} triples ({shapes_load_time:.2f}s)"
    print(shapes_msg)

    # 2. Load Data Graph
    start_time = time.time()
    data_graph = rdflib.Graph()
    try:
        data_graph.parse(data_path, format="turtle")
    except Exception as e:
        print(f"ERROR: Failed to load data file '{data_path}': {e}", file=sys.stderr)
        return False, None
    data_triples = len(data_graph)
    data_load_time = time.time() - start_time
    data_msg = f"Loaded data graph:   {data_triples} triples ({data_load_time:.2f}s)"
    print(data_msg)

    # 3. Validate
    print("Running pySHACL validation...")
    val_start = time.time()
    conforms, results_graph, results_text = pyshacl.validate(
        data_graph,
        shacl_graph=shapes_graph,
        advanced=advanced,
        inference="none",
        debug=False
    )
    val_duration = time.time() - val_start
    val_msg = f"Validation completed in {val_duration:.2f}s"
    print(val_msg)
    print("-" * 70)

    # 4. Conformance status
    status_line = f"CONFORMS: {conforms}"
    print(status_line)
    print("-" * 70)

    # 5. Extract structured violations from results_graph
    def shorten_uri(uri_str):
        if not uri_str or uri_str == "N/A":
            return "N/A"
        try:
            return shapes_graph.namespace_manager.normalizeUri(rdflib.URIRef(uri_str))
        except Exception:
            return uri_str

    violations = []
    for report in results_graph.subjects(RDF.type, SH.ValidationReport):
        for result in results_graph.objects(report, SH.result):
            focus_node = results_graph.value(result, SH.focusNode)
            path = results_graph.value(result, SH.resultPath)
            message = results_graph.value(result, SH.resultMessage)
            severity = results_graph.value(result, SH.resultSeverity)
            value = results_graph.value(result, SH.value)
            source_component = results_graph.value(result, SH.sourceConstraintComponent)

            violations.append({
                "focusNode": str(focus_node) if focus_node else "N/A",
                "resultPath": shorten_uri(str(path)) if path else "N/A",
                "resultMessage": str(message) if message else "No message provided",
                "value": str(value) if value else None,
                "severity": str(severity).split("#")[-1] if severity else "Violation",
                "sourceComponent": str(source_component).split("#")[-1] if source_component else "N/A",
            })

    body_lines = []
    if conforms:
        res_msg = "Success: No SHACL violations found in the dataset (Violations count: 0)."
        print(res_msg)
        body_lines.append(res_msg)
    else:
        res_msg = f"Total Violations: {len(violations)}\n"
        print(res_msg)
        body_lines.append(res_msg)
        for idx, v in enumerate(violations, 1):
            v_lines = [
                f"[{idx}] Severity: {v['severity']} | Component: {v['sourceComponent']}",
                f"    Focus Node:    {v['focusNode']}",
                f"    Property Path: {v['resultPath']}"
            ]
            if v["value"] is not None:
                v_lines.append(f"    Value:         {v['value']}")
            v_lines.append(f"    Message:       {v['resultMessage']}\n")
            formatted_v = "\n".join(v_lines)
            print(formatted_v)
            body_lines.append(formatted_v)

    scope_note = (
        "Note on validation scope:\n"
        "Conformance indicates that the dataset satisfies all constraint components defined\n"
        "in the supplied SHACL shapes file. It does not guarantee the complete absence of data\n"
        "quality issues beyond the properties and constraints modeled in these shapes."
    )
    print("-" * 70)
    print(scope_note)
    print("=" * 70)

    # 6. Save report if requested
    if report_path:
        out_p = Path(report_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        report_content = [
            "=" * 70,
            "SHACL VALIDATION REPORT",
            "=" * 70,
            f"Timestamp (UTC):    {timestamp_str}",
            f"Data file:          {data_path}",
            f"Shapes file:        {shapes_path}",
            f"Data triple count:  {data_triples}",
            f"Shapes triple count:{shapes_triples}",
            f"Validation runtime: {val_duration:.2f} seconds",
            f"Advanced features:  {advanced}",
            "-" * 70,
            f"CONFORMANCE RESULT: {conforms}",
            f"VIOLATIONS COUNT:   {len(violations)}",
            "-" * 70,
            *body_lines,
            "-" * 70,
            scope_note,
            "=" * 70,
            ""
        ]
        out_p.write_text("\n".join(report_content), encoding="utf-8")
        print(f"Validation report saved to: {out_p.resolve()}")

        ttl_path = out_p.with_suffix(".ttl")
        results_graph.serialize(destination=str(ttl_path), format="turtle")
        print(f"Machine-readable Turtle report saved to: {ttl_path.resolve()}")

    return conforms, len(violations)


def main():
    parser = argparse.ArgumentParser(description="Validate RDF data against SHACL shapes using pySHACL.")
    parser.add_argument(
        "--data", "-d",
        default="rdf/coteq_electricity_2013_csv (1).ttl",
        help="Path to RDF data file (Turtle format)"
    )
    parser.add_argument(
        "--shapes", "-s",
        default="shacl/coteq_electricity_shapes.ttl",
        help="Path to SHACL shapes file (Turtle format)"
    )
    parser.add_argument(
        "--report", "-r",
        default=None,
        help="Optional path to save text report (e.g. reports/shacl_validation_report.txt)"
    )
    parser.add_argument(
        "--no-advanced",
        action="store_true",
        help="Disable SHACL Advanced Features (SPARQL constraints)"
    )

    args = parser.parse_args()

    # Fallback to alternative naming if default not directly found
    data_path = Path(args.data)
    if not data_path.exists():
        alt_data = Path("coteq_electricity_2013_csv__1_.ttl")
        if alt_data.exists():
            data_path = alt_data

    shapes_path = Path(args.shapes)
    if not shapes_path.exists():
        alt_shapes = Path("coteq_electricity_shapes.ttl")
        if alt_shapes.exists():
            shapes_path = alt_shapes

    conforms, v_count = run_validation(
        str(data_path),
        str(shapes_path),
        advanced=not args.no_advanced,
        report_path=args.report
    )

    sys.exit(0 if conforms else 1)


if __name__ == "__main__":
    main()
