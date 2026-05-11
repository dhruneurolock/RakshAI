# RakshAI Backend Executive Summary

## Purpose
RakshAI is a backend-driven, multi-agent security testing platform that automates target discovery, attack planning, controlled execution, validation, and reporting.

## What the Backend Does
The backend manages the full lifecycle of a scan:
- Accepts a target and scan request
- Checks scope, policy, and rate limits
- Discovers application surface area and technologies
- Maps findings to OWASP categories
- Selects test cases and payloads from the knowledge base
- Executes tests through controlled tooling
- Validates findings to reduce false positives
- Generates downloadable reports in PDF, Word, Excel, and JSON

## Why It Matters
The system combines deterministic security rules with LLM assistance to improve coverage, reduce manual effort, and keep testing controlled and repeatable.

## Core Safety Model
- Scope checks block unsafe or out-of-scope targets
- Policy checks prevent disallowed scans
- Rate limiting prevents repeated or aggressive probing
- Safety enforcement removes destructive payloads
- Validation replays findings before they are treated as real

## Agent Roles
- Coordinator Agent: Orchestrates the full workflow
- Recon Agent: Discovers endpoints, forms, and technologies
- Strategy Agent: Prioritizes likely attack paths
- Executor Agent: Runs security tests and captures evidence
- Validator Agent: Replays findings and reduces false positives
- PoC Agent: Produces reproducible proof-of-concept material
- Remediation Agent: Produces fix guidance and impact wording

## How Test Cases and Payloads Work
The rule engine selects test cases from the knowledge base based on the discovered target context. Payloads are then bound to those tests, filtered by safety rules, and executed in a controlled sandbox.

## How LLM Is Used
The LLM helps with:
- Strategy generation
- Threat analysis
- Executive summaries
- Vulnerability explanations
- Remediation language

It is not allowed to directly execute commands or replace deterministic validation.

## Client Value
- Faster assessments
- Better consistency
- Stronger traceability
- Safer controlled testing
- Clear downloadable outputs for stakeholders

## Output Artifacts
The backend produces:
- Scan records
- Vulnerability findings
- Evidence and PoC material
- Remediation guidance
- Reports for download and review
