#!/usr/bin/env python3
"""
Nexus Test Coverage Report Generator
=====================================

Analyzes all tests and generates a comprehensive coverage report showing:
- Test counts by category
- Component coverage mapping
- API endpoint coverage
- Missing test identification
- Quality metrics

Usage:
    python scripts/generate_test_report.py
    python scripts/generate_test_report.py --output reports/coverage_report.md
    python scripts/generate_test_report.py --html reports/coverage_report.html
"""

import os
import sys
import ast
import json
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Any

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
TESTS_DIR = PROJECT_ROOT / "tests"
SERVICES_DIR = PROJECT_ROOT / "services"
SHARED_DIR = PROJECT_ROOT / "shared"
REPORTS_DIR = PROJECT_ROOT / "reports"

# Component mapping
COMPONENTS = {
    "orchestrator": {
        "path": SERVICES_DIR / "orchestrator",
        "description": "Central ReAct Engine & Query Processing",
        "critical": True
    },
    "jira_agent": {
        "path": SERVICES_DIR / "agents" / "jira_agent",
        "description": "Jira Integration (Tickets, Sprints, Hierarchy)",
        "critical": True
    },
    "git_ci_agent": {
        "path": SERVICES_DIR / "agents" / "git_ci_agent",
        "description": "GitHub & Jenkins Integration",
        "critical": True
    },
    "reporting_agent": {
        "path": SERVICES_DIR / "agents" / "reporting_agent",
        "description": "Report Generation & Confluence Publishing",
        "critical": False
    },
    "slack_agent": {
        "path": SERVICES_DIR / "agents" / "slack_agent",
        "description": "Slack Bot & App Home",
        "critical": True
    },
    "jira_hygiene_agent": {
        "path": SERVICES_DIR / "agents" / "jira_hygiene_agent",
        "description": "Jira Data Quality & Hygiene Checks",
        "critical": False
    },
    "rca_agent": {
        "path": SERVICES_DIR / "agents" / "rca_agent",
        "description": "Root Cause Analysis for Build Failures",
        "critical": False
    },
    "analytics": {
        "path": SERVICES_DIR / "analytics",
        "description": "DORA Metrics, Predictions, Anomaly Detection",
        "critical": False
    },
    "webhooks": {
        "path": SERVICES_DIR / "webhooks",
        "description": "Webhook Integrations & Event Delivery",
        "critical": False
    },
    "admin_dashboard": {
        "path": SERVICES_DIR / "admin_dashboard",
        "description": "Web UI, Configuration, Release Management",
        "critical": True
    },
    "shared_lib": {
        "path": SHARED_DIR / "nexus_lib",
        "description": "Shared Library (Schemas, LLM, Config, Utils)",
        "critical": True
    }
}

# Test category mapping
TEST_CATEGORIES = {
    "unit": {
        "path": TESTS_DIR / "unit",
        "description": "Individual component tests in isolation",
        "weight": 1.0
    },
    "e2e": {
        "path": TESTS_DIR / "e2e",
        "description": "End-to-end API endpoint tests",
        "weight": 1.5
    },
    "integration": {
        "path": TESTS_DIR / "integration",
        "description": "Inter-service communication tests",
        "weight": 2.0
    },
    "smoke": {
        "path": TESTS_DIR / "smoke",
        "description": "Quick health verification tests",
        "weight": 0.5
    }
}


class TestAnalyzer:
    """Analyzes test files and extracts test information."""
    
    def __init__(self):
        self.tests: Dict[str, List[Dict]] = defaultdict(list)
        self.test_counts: Dict[str, int] = defaultdict(int)
        self.component_coverage: Dict[str, Set[str]] = defaultdict(set)
    
    def analyze_file(self, file_path: Path) -> List[Dict]:
        """Analyze a test file and extract test information."""
        tests = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if node.name.startswith('test_'):
                        test_info = {
                            'name': node.name,
                            'file': str(file_path.relative_to(PROJECT_ROOT)),
                            'line': node.lineno,
                            'docstring': ast.get_docstring(node) or "",
                            'is_async': isinstance(node, ast.AsyncFunctionDef),
                            'decorators': [
                                self._get_decorator_name(d) 
                                for d in node.decorator_list
                            ]
                        }
                        tests.append(test_info)
                
                elif isinstance(node, ast.AsyncFunctionDef):
                    if node.name.startswith('test_'):
                        test_info = {
                            'name': node.name,
                            'file': str(file_path.relative_to(PROJECT_ROOT)),
                            'line': node.lineno,
                            'docstring': ast.get_docstring(node) or "",
                            'is_async': True,
                            'decorators': [
                                self._get_decorator_name(d) 
                                for d in node.decorator_list
                            ]
                        }
                        tests.append(test_info)
                
                elif isinstance(node, ast.ClassDef):
                    if node.name.startswith('Test'):
                        class_docstring = ast.get_docstring(node) or ""
                        for item in node.body:
                            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                if item.name.startswith('test_'):
                                    test_info = {
                                        'name': f"{node.name}::{item.name}",
                                        'class': node.name,
                                        'method': item.name,
                                        'file': str(file_path.relative_to(PROJECT_ROOT)),
                                        'line': item.lineno,
                                        'docstring': ast.get_docstring(item) or class_docstring,
                                        'is_async': isinstance(item, ast.AsyncFunctionDef),
                                        'decorators': [
                                            self._get_decorator_name(d) 
                                            for d in item.decorator_list
                                        ]
                                    }
                                    tests.append(test_info)
        
        except SyntaxError as e:
            print(f"  ⚠️ Syntax error in {file_path}: {e}")
        except Exception as e:
            print(f"  ⚠️ Error analyzing {file_path}: {e}")
        
        return tests
    
    def _get_decorator_name(self, decorator) -> str:
        """Extract decorator name from AST node."""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return f"{decorator.value.id}.{decorator.attr}" if hasattr(decorator.value, 'id') else decorator.attr
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                return decorator.func.id
            elif isinstance(decorator.func, ast.Attribute):
                return decorator.func.attr
        return "unknown"
    
    def analyze_all(self) -> None:
        """Analyze all test files."""
        print("📊 Analyzing test files...")
        
        for category, config in TEST_CATEGORIES.items():
            path = config['path']
            if not path.exists():
                print(f"  ⚠️ Category path not found: {path}")
                continue
            
            print(f"  → {category}...")
            
            for test_file in path.glob("test_*.py"):
                tests = self.analyze_file(test_file)
                self.tests[category].extend(tests)
                self.test_counts[category] += len(tests)
                
                # Map tests to components using flexible matching
                file_name = test_file.stem.lower()
                
                # Component name mappings for better detection
                component_patterns = {
                    'orchestrator': ['react', 'orchestrator', 'release_flow', 'query'],
                    'jira_agent': ['jira_agent', 'jira_flow'],
                    'git_ci_agent': ['git_ci', 'git_agent', 'ci_agent'],
                    'reporting_agent': ['reporting', 'report_flow'],
                    'slack_agent': ['slack', 'slack_flow'],
                    'jira_hygiene_agent': ['hygiene'],
                    'rca_agent': ['rca'],
                    'analytics': ['analytics'],
                    'webhooks': ['webhook'],
                    'admin_dashboard': ['admin', 'dashboard'],
                    'shared_lib': ['schema', 'llm', 'config', 'instrumentation', 'util']
                }
                
                for component, patterns in component_patterns.items():
                    for pattern in patterns:
                        if pattern in file_name:
                            self.component_coverage[component].update(
                                t['name'] for t in tests
                            )
                            break
        
        print(f"  ✅ Analyzed {sum(self.test_counts.values())} tests")
    
    def get_component_coverage(self) -> Dict[str, Dict]:
        """Calculate coverage metrics per component."""
        coverage = {}
        
        for component, config in COMPONENTS.items():
            tests = self.component_coverage.get(component, set())
            
            # Calculate coverage score based on test types
            unit_tests = sum(1 for t in self.tests['unit'] if component in t.get('file', '').lower())
            e2e_tests = sum(1 for t in self.tests['e2e'] if component in t.get('file', '').lower())
            integration_tests = sum(1 for t in self.tests['integration'] if component in t.get('file', '').lower())
            smoke_tests = sum(1 for t in self.tests['smoke'] if component in t.get('file', '').lower())
            
            total_tests = unit_tests + e2e_tests + integration_tests + smoke_tests
            
            # Coverage score (weighted)
            weighted_score = (
                unit_tests * 1.0 +
                e2e_tests * 1.5 +
                integration_tests * 2.0 +
                smoke_tests * 0.5
            )
            
            # Determine coverage level
            if total_tests == 0:
                level = "none"
                percentage = 0
            elif weighted_score < 5:
                level = "minimal"
                percentage = 25
            elif weighted_score < 15:
                level = "partial"
                percentage = 50
            elif weighted_score < 30:
                level = "good"
                percentage = 75
            else:
                level = "excellent"
                percentage = min(100, int(weighted_score * 2))
            
            coverage[component] = {
                'description': config['description'],
                'critical': config['critical'],
                'total_tests': total_tests,
                'unit': unit_tests,
                'e2e': e2e_tests,
                'integration': integration_tests,
                'smoke': smoke_tests,
                'weighted_score': weighted_score,
                'level': level,
                'percentage': percentage
            }
        
        return coverage


class APIEndpointAnalyzer:
    """Analyzes API endpoints and their test coverage."""
    
    EXPECTED_ENDPOINTS = {
        "orchestrator": [
            ("GET", "/health"),
            ("GET", "/livez"),
            ("GET", "/readyz"),
            ("GET", "/metrics"),
            ("POST", "/query"),
            ("GET", "/specialists"),
            ("GET", "/specialists/tools/all"),
            ("GET", "/memory/stats"),
        ],
        "jira_agent": [
            ("GET", "/health"),
            ("GET", "/metrics"),
            ("POST", "/execute"),
            ("POST", "/search"),
        ],
        "git_ci_agent": [
            ("GET", "/health"),
            ("GET", "/metrics"),
            ("POST", "/execute"),
        ],
        "reporting_agent": [
            ("GET", "/health"),
            ("GET", "/metrics"),
            ("POST", "/execute"),
        ],
        "slack_agent": [
            ("GET", "/health"),
            ("GET", "/metrics"),
            ("POST", "/execute"),
            ("POST", "/slack/commands"),
            ("POST", "/slack/events"),
            ("POST", "/slack/interactions"),
        ],
        "hygiene_agent": [
            ("GET", "/health"),
            ("GET", "/metrics"),
            ("GET", "/status"),
            ("POST", "/execute"),
        ],
        "rca_agent": [
            ("GET", "/health"),
            ("GET", "/metrics"),
            ("POST", "/analyze"),
            ("POST", "/webhook/jenkins"),
        ],
        "analytics": [
            ("GET", "/health"),
            ("GET", "/metrics"),
            ("GET", "/api/v1/kpis"),
            ("GET", "/api/v1/trends"),
            ("GET", "/api/v1/insights"),
            ("GET", "/api/v1/teams"),
            ("GET", "/api/v1/anomalies"),
        ],
        "webhooks": [
            ("GET", "/health"),
            ("GET", "/metrics"),
            ("GET", "/api/v1/event-types"),
            ("GET", "/api/v1/subscriptions"),
            ("GET", "/api/v1/deliveries"),
            ("GET", "/api/v1/stats"),
        ],
        "admin_dashboard": [
            ("GET", "/health"),
            ("GET", "/metrics"),
            ("GET", "/stats"),
            ("GET", "/mode"),
            ("POST", "/mode"),
            ("GET", "/config"),
            ("POST", "/config"),
            ("GET", "/config/templates"),
            ("GET", "/health-check"),
            ("GET", "/api/metrics"),
            ("GET", "/releases"),
            ("POST", "/releases"),
            ("GET", "/releases/calendar"),
            ("GET", "/releases/templates"),
        ]
    }
    
    def get_endpoint_coverage(self, tests: Dict[str, List[Dict]]) -> Dict[str, Dict]:
        """Calculate endpoint coverage."""
        coverage = {}
        
        for service, endpoints in self.EXPECTED_ENDPOINTS.items():
            tested = 0
            endpoint_details = []
            
            for method, path in endpoints:
                # Check if endpoint is tested
                is_tested = self._is_endpoint_tested(service, method, path, tests)
                endpoint_details.append({
                    'method': method,
                    'path': path,
                    'tested': is_tested
                })
                if is_tested:
                    tested += 1
            
            total = len(endpoints)
            percentage = int((tested / total) * 100) if total > 0 else 0
            
            coverage[service] = {
                'total': total,
                'tested': tested,
                'untested': total - tested,
                'percentage': percentage,
                'endpoints': endpoint_details
            }
        
        return coverage
    
    def _is_endpoint_tested(self, service: str, method: str, path: str, tests: Dict) -> bool:
        """Check if an endpoint is covered by tests."""
        # Simplified check - look for path or endpoint name in test names
        path_parts = path.strip('/').replace('/', '_').replace('-', '_').lower()
        service_normalized = service.replace('_', '').lower()
        
        for category_tests in tests.values():
            for test in category_tests:
                test_name = test['name'].lower()
                # Check if test name suggests it covers this endpoint
                if service_normalized in test_name or any(
                    part in test_name for part in path_parts.split('_') if len(part) > 2
                ):
                    if method.lower() in test_name or (
                        method == "GET" and "get" in test_name
                    ) or (
                        method == "POST" and ("post" in test_name or "create" in test_name or "update" in test_name)
                    ):
                        return True
        
        return False


def generate_markdown_report(
    test_analyzer: TestAnalyzer,
    endpoint_analyzer: APIEndpointAnalyzer
) -> str:
    """Generate comprehensive Markdown report."""
    
    component_coverage = test_analyzer.get_component_coverage()
    endpoint_coverage = endpoint_analyzer.get_endpoint_coverage(test_analyzer.tests)
    
    total_tests = sum(test_analyzer.test_counts.values())
    
    report = []
    report.append("# 📊 Nexus Test Coverage Report")
    report.append("")
    report.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"**Total Tests:** {total_tests}")
    report.append("")
    
    # Executive Summary
    report.append("## 📋 Executive Summary")
    report.append("")
    report.append("| Metric | Value |")
    report.append("|--------|-------|")
    report.append(f"| Total Tests | **{total_tests}** |")
    report.append(f"| Unit Tests | {test_analyzer.test_counts['unit']} |")
    report.append(f"| E2E Tests | {test_analyzer.test_counts['e2e']} |")
    report.append(f"| Integration Tests | {test_analyzer.test_counts['integration']} |")
    report.append(f"| Smoke Tests | {test_analyzer.test_counts['smoke']} |")
    report.append(f"| Components Covered | {len([c for c, d in component_coverage.items() if d['total_tests'] > 0])}/{len(COMPONENTS)} |")
    
    # Calculate overall health
    avg_coverage = sum(c['percentage'] for c in component_coverage.values()) / len(component_coverage)
    health_emoji = "🟢" if avg_coverage >= 70 else "🟡" if avg_coverage >= 40 else "🔴"
    report.append(f"| Overall Health | {health_emoji} {avg_coverage:.0f}% |")
    report.append("")
    
    # Test Distribution by Category
    report.append("## 📈 Test Distribution by Category")
    report.append("")
    report.append("```")
    for category, count in sorted(test_analyzer.test_counts.items(), key=lambda x: -x[1]):
        bar_length = int(count / max(test_analyzer.test_counts.values()) * 40)
        bar = "█" * bar_length + "░" * (40 - bar_length)
        report.append(f"{category:12} |{bar}| {count:3}")
    report.append("```")
    report.append("")
    
    # Component Coverage
    report.append("## 🧩 Component Coverage")
    report.append("")
    report.append("| Component | Description | Tests | Unit | E2E | Int | Smoke | Coverage |")
    report.append("|-----------|-------------|-------|------|-----|-----|-------|----------|")
    
    for component, data in sorted(component_coverage.items(), key=lambda x: -x[1]['percentage']):
        critical = "⭐" if data['critical'] else ""
        level_emoji = {
            "excellent": "🟢",
            "good": "🟡",
            "partial": "🟠",
            "minimal": "🔴",
            "none": "⚫"
        }.get(data['level'], "⚪")
        
        report.append(
            f"| {component} {critical} | {data['description'][:40]}... | "
            f"{data['total_tests']} | {data['unit']} | {data['e2e']} | "
            f"{data['integration']} | {data['smoke']} | {level_emoji} {data['percentage']}% |"
        )
    
    report.append("")
    report.append("*⭐ = Critical component*")
    report.append("")
    
    # API Endpoint Coverage
    report.append("## 🔌 API Endpoint Coverage")
    report.append("")
    report.append("| Service | Endpoints | Tested | Untested | Coverage |")
    report.append("|---------|-----------|--------|----------|----------|")
    
    for service, data in sorted(endpoint_coverage.items(), key=lambda x: -x[1]['percentage']):
        coverage_emoji = "✅" if data['percentage'] >= 80 else "⚠️" if data['percentage'] >= 50 else "❌"
        report.append(
            f"| {service} | {data['total']} | {data['tested']} | "
            f"{data['untested']} | {coverage_emoji} {data['percentage']}% |"
        )
    
    report.append("")
    
    # Untested Endpoints
    report.append("### ⚠️ Untested Endpoints")
    report.append("")
    
    for service, data in endpoint_coverage.items():
        untested = [e for e in data['endpoints'] if not e['tested']]
        if untested:
            report.append(f"**{service}:**")
            for endpoint in untested:
                report.append(f"- `{endpoint['method']} {endpoint['path']}`")
            report.append("")
    
    # Coverage Gaps
    report.append("## 🔍 Identified Coverage Gaps")
    report.append("")
    
    gaps = []
    
    # Check for critical components with low coverage
    for component, data in component_coverage.items():
        if data['critical'] and data['percentage'] < 70:
            gaps.append(f"⚠️ **{component}** (Critical): Only {data['percentage']}% coverage")
    
    # Check for missing test categories
    for component, data in component_coverage.items():
        if data['total_tests'] > 0:
            if data['e2e'] == 0:
                gaps.append(f"📋 **{component}**: Missing E2E tests")
            if data['unit'] == 0 and component != "admin_dashboard":
                gaps.append(f"📋 **{component}**: Missing unit tests")
    
    # Check for services with no tests
    for component, data in component_coverage.items():
        if data['total_tests'] == 0:
            gaps.append(f"❌ **{component}**: No test coverage")
    
    if gaps:
        for gap in gaps:
            report.append(f"- {gap}")
    else:
        report.append("✅ No critical coverage gaps identified!")
    
    report.append("")
    
    # Recommendations
    report.append("## 💡 Recommendations")
    report.append("")
    
    recommendations = []
    
    # Based on coverage analysis
    if sum(data['integration'] for data in component_coverage.values()) < 20:
        recommendations.append("1. **Increase Integration Tests**: Add more tests for inter-service communication")
    
    low_coverage = [c for c, d in component_coverage.items() if d['percentage'] < 50 and d['critical']]
    if low_coverage:
        recommendations.append(f"2. **Prioritize Critical Components**: Focus on {', '.join(low_coverage)}")
    
    if test_analyzer.test_counts['smoke'] < 30:
        recommendations.append("3. **Expand Smoke Tests**: Add more quick health verification tests")
    
    recommendations.append("4. **Add Negative Tests**: Ensure error handling is properly tested")
    recommendations.append("5. **Performance Tests**: Consider adding load/stress tests for critical paths")
    
    for rec in recommendations:
        report.append(f"- {rec}")
    
    report.append("")
    
    # Test File Summary
    report.append("## 📁 Test File Summary")
    report.append("")
    report.append("| Category | Files | Tests |")
    report.append("|----------|-------|-------|")
    
    for category in TEST_CATEGORIES:
        path = TEST_CATEGORIES[category]['path']
        if path.exists():
            files = list(path.glob("test_*.py"))
            report.append(f"| {category} | {len(files)} | {test_analyzer.test_counts[category]} |")
    
    report.append("")
    
    # Footer
    report.append("---")
    report.append("")
    report.append("*Report generated by `scripts/generate_test_report.py`*")
    
    return "\n".join(report)


def generate_html_report(markdown_content: str) -> str:
    """Convert markdown to HTML report."""
    # Simple markdown to HTML conversion
    html = []
    html.append("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nexus Test Coverage Report</title>
    <style>
        :root {
            --bg-primary: #0a0e17;
            --bg-secondary: #141b2d;
            --text-primary: #e0e6ed;
            --text-secondary: #8892a0;
            --accent: #00d4ff;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
        }
        
        body {
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
            line-height: 1.6;
        }
        
        h1, h2, h3 {
            color: var(--accent);
            border-bottom: 1px solid var(--bg-secondary);
            padding-bottom: 0.5rem;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
            background: var(--bg-secondary);
            border-radius: 8px;
            overflow: hidden;
        }
        
        th, td {
            padding: 0.75rem 1rem;
            text-align: left;
            border-bottom: 1px solid var(--bg-primary);
        }
        
        th {
            background: rgba(0, 212, 255, 0.1);
            color: var(--accent);
        }
        
        tr:hover {
            background: rgba(0, 212, 255, 0.05);
        }
        
        code, pre {
            background: var(--bg-secondary);
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-family: 'Fira Code', monospace;
        }
        
        pre {
            padding: 1rem;
            overflow-x: auto;
        }
        
        .success { color: var(--success); }
        .warning { color: var(--warning); }
        .danger { color: var(--danger); }
        
        ul {
            list-style-type: none;
            padding-left: 1rem;
        }
        
        ul li::before {
            content: "→";
            color: var(--accent);
            margin-right: 0.5rem;
        }
    </style>
</head>
<body>
""")
    
    # Simple markdown conversion
    lines = markdown_content.split('\n')
    in_table = False
    in_code = False
    in_list = False
    
    for line in lines:
        if line.startswith('```'):
            if in_code:
                html.append('</pre>')
            else:
                html.append('<pre>')
            in_code = not in_code
            continue
        
        if in_code:
            html.append(line)
            continue
        
        if line.startswith('# '):
            html.append(f'<h1>{line[2:]}</h1>')
        elif line.startswith('## '):
            html.append(f'<h2>{line[3:]}</h2>')
        elif line.startswith('### '):
            html.append(f'<h3>{line[4:]}</h3>')
        elif line.startswith('|'):
            if not in_table:
                html.append('<table>')
                in_table = True
            
            cells = [c.strip() for c in line.split('|')[1:-1]]
            if all(c.startswith('-') for c in cells):
                continue
            
            tag = 'th' if not any(c for c in cells if c and not c.startswith('-'))  else 'td'
            if cells and any(cells):
                tag = 'td'
            
            row = '<tr>'
            for cell in cells:
                # Add color classes for emojis
                cell_class = ''
                if '✅' in cell or '🟢' in cell:
                    cell_class = ' class="success"'
                elif '⚠️' in cell or '🟡' in cell or '🟠' in cell:
                    cell_class = ' class="warning"'
                elif '❌' in cell or '🔴' in cell:
                    cell_class = ' class="danger"'
                
                row += f'<{tag}{cell_class}>{cell}</{tag}>'
            row += '</tr>'
            html.append(row)
        else:
            if in_table:
                html.append('</table>')
                in_table = False
            
            if line.startswith('- '):
                if not in_list:
                    html.append('<ul>')
                    in_list = True
                html.append(f'<li>{line[2:]}</li>')
            else:
                if in_list:
                    html.append('</ul>')
                    in_list = False
                if line.strip():
                    # Handle inline code
                    line = line.replace('`', '<code>', 1).replace('`', '</code>', 1)
                    html.append(f'<p>{line}</p>')
    
    if in_table:
        html.append('</table>')
    if in_list:
        html.append('</ul>')
    
    html.append('</body></html>')
    
    return '\n'.join(html)


def main():
    parser = argparse.ArgumentParser(description='Generate Nexus Test Coverage Report')
    parser.add_argument('--output', '-o', type=str, help='Output file path (markdown)')
    parser.add_argument('--html', type=str, help='Output file path (HTML)')
    parser.add_argument('--json', type=str, help='Output file path (JSON)')
    args = parser.parse_args()
    
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║                                                                   ║")
    print("║   📊 NEXUS TEST COVERAGE REPORT GENERATOR                        ║")
    print("║                                                                   ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    print("")
    
    # Analyze tests
    test_analyzer = TestAnalyzer()
    test_analyzer.analyze_all()
    
    # Analyze endpoints
    endpoint_analyzer = APIEndpointAnalyzer()
    
    # Generate reports
    print("\n📝 Generating reports...")
    
    # Ensure reports directory exists
    REPORTS_DIR.mkdir(exist_ok=True)
    
    # Markdown report
    markdown_report = generate_markdown_report(test_analyzer, endpoint_analyzer)
    
    output_path = args.output or str(REPORTS_DIR / "TEST_COVERAGE_REPORT.md")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown_report)
    print(f"  ✅ Markdown report: {output_path}")
    
    # HTML report
    if args.html:
        html_report = generate_html_report(markdown_report)
        with open(args.html, 'w', encoding='utf-8') as f:
            f.write(html_report)
        print(f"  ✅ HTML report: {args.html}")
    else:
        html_path = str(REPORTS_DIR / "TEST_COVERAGE_REPORT.html")
        html_report = generate_html_report(markdown_report)
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_report)
        print(f"  ✅ HTML report: {html_path}")
    
    # JSON report
    if args.json:
        json_data = {
            'generated_at': datetime.now().isoformat(),
            'total_tests': sum(test_analyzer.test_counts.values()),
            'test_counts': dict(test_analyzer.test_counts),
            'component_coverage': test_analyzer.get_component_coverage(),
            'endpoint_coverage': endpoint_analyzer.get_endpoint_coverage(test_analyzer.tests)
        }
        with open(args.json, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, default=str)
        print(f"  ✅ JSON report: {args.json}")
    
    print("\n✅ Report generation complete!")
    
    # Print summary
    print("\n═══════════════════════════════════════════════════════════════════")
    print("                         QUICK SUMMARY")
    print("═══════════════════════════════════════════════════════════════════")
    print(f"  Total Tests:       {sum(test_analyzer.test_counts.values())}")
    print(f"  Unit Tests:        {test_analyzer.test_counts['unit']}")
    print(f"  E2E Tests:         {test_analyzer.test_counts['e2e']}")
    print(f"  Integration Tests: {test_analyzer.test_counts['integration']}")
    print(f"  Smoke Tests:       {test_analyzer.test_counts['smoke']}")
    print("═══════════════════════════════════════════════════════════════════")


if __name__ == "__main__":
    main()

