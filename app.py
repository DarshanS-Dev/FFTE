#!/usr/bin/env python3
"""
FFTE orchestrator: wires surface discovery, input generation, execution,
failure detection, and reporting into a single fuzzing workflow.
"""

from __future__ import annotations

<<<<<<< HEAD
from core.runner import run
from reporting.report import format_report
=======
import json
import sys
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Any
import re

# Import all your modules
from surface_discovery.openapi_parser import fetch_and_parse, Endpoint
from input_generation.edge_cases import (
    generate_sample_object,
    generate_edge_cases_flat,
)
from execution.http_executor import execute_request
from failure_detection.rules import classify
from reporting.report import ExecutionLogEntry, format_report, generate_report


class FFTEOrchestrator:
    """Main orchestrator that connects all modules."""
    
    def __init__(self, spec_url: str, base_url: str | None = None):
        """
        Initialize the orchestrator.
        
        Args:
            spec_url: URL to OpenAPI spec (e.g., http://localhost:8000/openapi.json)
            base_url: Base URL for API requests (if different from spec URL)
        """
        self.spec_url = spec_url
        self.base_url = base_url or self._extract_base_url(spec_url)
        self.endpoints: List[Endpoint] = []
        self.execution_entries: List[ExecutionLogEntry] = []
        
    def _extract_base_url(self, url: str) -> str:
        """Extract base URL from OpenAPI spec URL."""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"
    
    def discover_surface(self):
        """Step 1: Discover API surface using OpenAPI parser."""
        print(f"🔍 Discovering API surface from {self.spec_url}...")
        self.endpoints = fetch_and_parse(self.spec_url)
        print(f"📊 Found {len(self.endpoints)} endpoints")
        
        # Debug: Print endpoint details
        for i, endpoint in enumerate(self.endpoints):
            print(f"\n  Endpoint {i+1}:")
            print(f"    Path: {endpoint.path}")
            print(f"    Method: {endpoint.method}")
            print(f"    Has request body schema: {endpoint.request_body_schema is not None}")
            if endpoint.request_body_schema:
                print(f"    Schema: {json.dumps(endpoint.request_body_schema, indent=4)}")
        
        return self.endpoints
    
    def _build_full_url(self, endpoint_path: str) -> str:
        """Build complete URL from endpoint path."""
        # Handle path parameters
        if '{' in endpoint_path:
            # Replace path parameters with test values
            for match in re.findall(r'\{(\w+)\}', endpoint_path):
                endpoint_path = endpoint_path.replace(f'{{{match}}}', 'test')
        
        return urljoin(self.base_url.rstrip('/') + '/', endpoint_path.lstrip('/'))
    
    def generate_and_execute_tests(self, max_cases_per_field: int = 3):
        """Steps 2-4: Generate edge cases and execute tests."""
        print(f"\n🔥 Generating edge cases and executing tests...")
        
        for idx, endpoint in enumerate(self.endpoints, 1):
            print(f"\n🎯 Testing endpoint {idx}/{len(self.endpoints)}: {endpoint.method.upper()} {endpoint.path}")
            
            # Build URL
            url = self._build_full_url(endpoint.path)
            print(f"  URL: {url}")
            
            if endpoint.request_body_schema:
                # Debug: Show the schema
                print(f"  Request body schema type: {type(endpoint.request_body_schema)}")
                
                try:
                    # Generate edge cases for request body
                    print(f"  Generating edge cases...")
                    edge_cases = generate_edge_cases_flat(endpoint.request_body_schema)
                    print(f"  Edge cases generated: {edge_cases}")
                    
                    if not edge_cases:
                        print(f"  ⚠️ No edge cases generated! Trying fallback...")
                        # Try a simple fallback
                        simple_schema = {
                            "type": "object",
                            "properties": {
                                "a": {"type": "integer"},
                                "b": {"type": "integer"}
                            },
                            "required": ["a", "b"]
                        }
                        edge_cases = generate_edge_cases_flat(simple_schema)
                        print(f"  Fallback edge cases: {edge_cases}")
                    
                    test_count = 0
                    for field, values in edge_cases.items():
                        print(f"  Testing field: {field} (has {len(values)} values)")
                        
                        for value in values[:max_cases_per_field]:
                            try:
                                test_count += 1
                                # Build test payload with this edge case value
                                print(f"    Test #{test_count}: Building payload for value: {value}")
                                
                                payload = generate_sample_object(
                                    endpoint.request_body_schema,
                                    {field: value}
                                )
                                
                                print(f"      Payload: {payload}")
                                
                                # Execute the request
                                print(f"      Sending request...")
                                result = execute_request(
                                    method=endpoint.method,
                                    url=url,
                                    timeout=10.0,
                                    json=payload
                                )
                                
                                # Create execution log entry
                                entry = ExecutionLogEntry(
                                    method=endpoint.method,
                                    url=url,
                                    json_body=payload,
                                    result=result
                                )
                                self.execution_entries.append(entry)
                                
                                # Classify the result
                                classification = classify(result)
                                
                                if classification.is_failure:
                                    print(f"      ❌ FAILURE: {classification.failure_type} - {classification.message}")
                                else:
                                    print(f"      ✓ OK: HTTP {result.status_code}")
                                    
                            except Exception as e:
                                print(f"      ⚠️ ERROR during test: {e}")
                                import traceback
                                traceback.print_exc()
                                
                except Exception as e:
                    print(f"  ⚠️ ERROR in edge case generation: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                # No request body - just test the endpoint directly
                print(f"  Testing endpoint without request body")
                
                result = execute_request(
                    method=endpoint.method,
                    url=url,
                    timeout=10.0
                )
                
                entry = ExecutionLogEntry(
                    method=endpoint.method,
                    url=url,
                    result=result
                )
                self.execution_entries.append(entry)
                
                classification = classify(result)
                if classification.is_failure:
                    print(f"    ❌ FAILURE: {classification.failure_type}")
                else:
                    print(f"    ✓ OK: HTTP {result.status_code}")
        
        print(f"\n✅ Completed {len(self.execution_entries)} test executions")
        return self.execution_entries
    
    def generate_report(self) -> Dict[str, Any]:
        """Step 5: Generate and return report."""
        print(f"\n📊 Generating report from {len(self.execution_entries)} executions...")
        
        report = generate_report(self.execution_entries)
        return report
    
    def run_full_workflow(self) -> Dict[str, Any]:
        """Run the complete FFTE workflow."""
        print("=" * 60)
        print("🚀 Starting FFTE - Failure-First Testing Engine")
        print("=" * 60)
        
        # Step 1: Discover API surface
        self.discover_surface()
        
        # Steps 2-4: Generate tests and execute
        self.generate_and_execute_tests()
        
        # Step 5: Generate report
        report = self.generate_report()
        
        return report
>>>>>>> e3d87d7576c61f9b0eeb9c2c69d6b5d9b7ece3a3


def main():
    """Command-line interface."""
    # Default to testing the victim.py API
    if len(sys.argv) > 1:
        spec_url = sys.argv[1]
        base_url = sys.argv[2] if len(sys.argv) > 2 else None
    else:
        print("Using default test API (victim.py)")
        spec_url = "http://127.0.0.1:8000/openapi.json"
        base_url = "http://127.0.0.1:8000"
    
    try:
        # Create orchestrator
        orchestrator = FFTEOrchestrator(spec_url, base_url)
        
        # Run full workflow
        report = orchestrator.run_full_workflow()
        
        # Format and display report
        formatted_report = format_report(report)
        
        if formatted_report:
            print("\n" + "=" * 60)
            print("📋 FAILURE REPORT")
            print("=" * 60)
            print(formatted_report)
            
            # Save report to file
            with open("ffte_report.txt", "w") as f:
                f.write(formatted_report)
            print(f"\n💾 Report saved to ffte_report.txt")
            
            # Count failures
            failure_count = sum(len(commands) for commands in report.values())
            print(f"\n📈 Summary: Found {failure_count} failures")
        else:
            print("\n✅ No failures detected!")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())