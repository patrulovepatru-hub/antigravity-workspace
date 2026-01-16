#!/usr/bin/env python3
"""
Evidence Collector - Automatic evidence capture for findings
"""

import os
import sys
import json
import base64
import hashlib
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional

sys.path.insert(0, '/home/l0ve/Desktop/WD/Tools')


@dataclass
class Evidence:
    id: str
    type: str  # request, response, screenshot, code, log
    title: str
    content: str
    timestamp: str = ""
    metadata: Dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if not self.id:
            self.id = hashlib.md5(f"{self.timestamp}{self.title}".encode()).hexdigest()[:12]


@dataclass
class Finding:
    title: str
    severity: str
    description: str
    category: str = ""
    location: str = ""
    impact: str = ""
    recommendation: str = ""
    evidence: List[Evidence] = field(default_factory=list)
    cvss: float = 0.0
    cwe: str = ""
    references: List[str] = field(default_factory=list)


class EvidenceCollector:
    def __init__(self, project_name: str, output_dir: str = None):
        self.project_name = project_name
        self.output_dir = output_dir or f"/tmp/evidence_{project_name}"
        self.findings: List[Finding] = []
        self.evidence_store: List[Evidence] = []

        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(f"{self.output_dir}/requests", exist_ok=True)
        os.makedirs(f"{self.output_dir}/responses", exist_ok=True)
        os.makedirs(f"{self.output_dir}/screenshots", exist_ok=True)

    def capture_request(self, method: str, url: str, headers: Dict = None,
                       body: str = None, title: str = None) -> Evidence:
        """Capture HTTP request as evidence."""
        content = f"{method} {url}\n"
        if headers:
            for k, v in headers.items():
                content += f"{k}: {v}\n"
        if body:
            content += f"\n{body}"

        evidence = Evidence(
            id="",
            type="request",
            title=title or f"Request to {url}",
            content=content,
            metadata={"method": method, "url": url}
        )

        # Save to file
        filepath = f"{self.output_dir}/requests/{evidence.id}.txt"
        with open(filepath, 'w') as f:
            f.write(content)
        evidence.metadata['file'] = filepath

        self.evidence_store.append(evidence)
        return evidence

    def capture_response(self, status_code: int, headers: Dict = None,
                        body: str = None, url: str = "", title: str = None) -> Evidence:
        """Capture HTTP response as evidence."""
        content = f"HTTP/1.1 {status_code}\n"
        if headers:
            for k, v in headers.items():
                content += f"{k}: {v}\n"
        if body:
            content += f"\n{body[:5000]}"  # Limit body size

        evidence = Evidence(
            id="",
            type="response",
            title=title or f"Response from {url}",
            content=content,
            metadata={"status_code": status_code, "url": url}
        )

        filepath = f"{self.output_dir}/responses/{evidence.id}.txt"
        with open(filepath, 'w') as f:
            f.write(content)
        evidence.metadata['file'] = filepath

        self.evidence_store.append(evidence)
        return evidence

    def capture_code(self, code: str, language: str = "", title: str = None,
                    line_number: int = 0, filename: str = "") -> Evidence:
        """Capture code snippet as evidence."""
        evidence = Evidence(
            id="",
            type="code",
            title=title or "Code Snippet",
            content=code,
            metadata={
                "language": language,
                "line_number": line_number,
                "filename": filename
            }
        )
        self.evidence_store.append(evidence)
        return evidence

    def capture_log(self, log_content: str, title: str = None) -> Evidence:
        """Capture log output as evidence."""
        evidence = Evidence(
            id="",
            type="log",
            title=title or "Log Output",
            content=log_content
        )
        self.evidence_store.append(evidence)
        return evidence

    def add_finding(self, finding: Finding):
        """Add a finding to the collection."""
        self.findings.append(finding)

    def create_finding(self, title: str, severity: str, description: str,
                      evidence_ids: List[str] = None, **kwargs) -> Finding:
        """Create and add a finding with optional evidence."""
        evidence_list = []
        if evidence_ids:
            for eid in evidence_ids:
                for e in self.evidence_store:
                    if e.id == eid:
                        evidence_list.append(e)
                        break

        finding = Finding(
            title=title,
            severity=severity,
            description=description,
            evidence=evidence_list,
            **kwargs
        )
        self.findings.append(finding)
        return finding

    def export_json(self, output_file: str = None) -> str:
        """Export all findings and evidence to JSON."""
        output_file = output_file or f"{self.output_dir}/findings.json"

        data = {
            "project": self.project_name,
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_findings": len(self.findings),
                "critical": sum(1 for f in self.findings if f.severity.upper() == "CRITICAL"),
                "high": sum(1 for f in self.findings if f.severity.upper() == "HIGH"),
                "medium": sum(1 for f in self.findings if f.severity.upper() == "MEDIUM"),
                "low": sum(1 for f in self.findings if f.severity.upper() == "LOW"),
            },
            "findings": [
                {
                    **asdict(f),
                    "evidence": [asdict(e) for e in f.evidence]
                }
                for f in self.findings
            ]
        }

        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

        return output_file

    def generate_poc(self, finding: Finding) -> str:
        """Generate proof of concept from finding evidence."""
        poc_parts = []

        for ev in finding.evidence:
            if ev.type == "request":
                poc_parts.append(f"# Request\n```\n{ev.content}\n```\n")
            elif ev.type == "response":
                poc_parts.append(f"# Response\n```\n{ev.content[:1000]}\n```\n")
            elif ev.type == "code":
                lang = ev.metadata.get('language', '')
                poc_parts.append(f"# Code\n```{lang}\n{ev.content}\n```\n")

        return "\n".join(poc_parts)


# Singleton for global access
_collector: Optional[EvidenceCollector] = None


def init_collector(project_name: str, output_dir: str = None) -> EvidenceCollector:
    """Initialize global evidence collector."""
    global _collector
    _collector = EvidenceCollector(project_name, output_dir)
    return _collector


def get_collector() -> Optional[EvidenceCollector]:
    """Get global evidence collector."""
    return _collector
