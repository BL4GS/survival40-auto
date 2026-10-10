#!/usr/bin/env python3
"""Opt-in, bounded AI engineering review. Never writes to production or the main branch."""
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

def run(*args):
    return subprocess.run(args, text=True, capture_output=True, check=True).stdout

def main():
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")
    if not key:
        raise SystemExit("MISSING_KEY: GEMINI_API_KEY or GOOGLE_API_KEY repository secret is required. No AI call made.")
    vision = Path("PROJECT_VISION.md").read_text(encoding="utf-8")[:12000]
    safety = Path("docs/release-01921-production-safety.md").read_text(encoding="utf-8")[:10000]
    inventory = run("git", "ls-files", ".github", "docs", "planning")[:14000]
    recent = run("git", "log", "-8", "--pretty=%h %s")[:2500]
    task = Path(".github/agent/BACKLOG.md").read_text(encoding="utf-8")[:7000]
    source_snippets = {
        path: Path(path).read_text(encoding="utf-8")[:6500]
        for path in (".github/scripts/patch_affiliate_frontend_staged.py",
                     ".github/workflows/release.yml",
                     ".github/scripts/patch_author_update_stability_01920.py")
    }
    prompt = """You are a cautious software engineering regression-test author working on Survival40.
Follow PROJECT_VISION.md and production safety plan. Respond with ONE JSON object, with keys:
title, rationale, proposed_files (list), test_plan (list), risks (list), next_action,
change (object with path and content strings).
Generate exactly ONE *new* read-only Python unittest regression test.
The path MUST match .github/agent/generated_tests/test_s40_<lowercase_slug>.py.
The file content MUST use unittest.TestCase and at least one def test_ method.
Allowed imports only: unittest, pathlib, re, ast. No file writes, network, shell,
subprocess, credential reading, dynamic evaluation or side effects.
Tests may inspect tracked repository files for invariant assertions; avoid brittle
assertions that merely search generic phrases. Prefer tests for default-off
affiliate display, release approval gating, narrator assets and update safety.
Do not claim the test passed. Do not write implementation changes or run commands.
Test code must be <= 4500 characters. The test plan is informational; no
AI-proposed command will be executed. Keep JSON under 6000 tokens.
"""
    model = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
    payload = {"systemInstruction":{"parts":[{"text":prompt}]},"contents":[
        {"role":"user","parts":[{"text":json.dumps({
            "vision":vision,"release_safety":safety,"backlog":task,
            "tracked_files":inventory,"recent_commits":recent,"source_snippets":source_snippets
        },ensure_ascii=False)}]}
    ],"generationConfig":{"responseMimeType":"application/json","maxOutputTokens":6000}}
    request = urllib.request.Request(
        "https://generativelanguage.googleapis.com/v1beta/models/"+model+":generateContent",
        data=json.dumps(payload).encode(),
        headers={"x-goog-api-key":key,"Content-Type":"application/json"},method="POST")
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            result=json.load(response)
    except urllib.error.HTTPError as error:
        raise SystemExit("Gemini API request failed (HTTP "+str(error.code)+"); response withheld")
    except (urllib.error.URLError,TimeoutError) as error:
        raise SystemExit("Gemini connection failed: "+type(error).__name__)
    raw="\n".join(part.get("text","") for candidate in result.get("candidates",[])
        for part in candidate.get("content",{}).get("parts",[])
        if isinstance(part,dict)).strip()
    try:
        proposal=json.loads(raw)
        assert all(k in proposal for k in ("title","rationale","proposed_files","test_plan","risks","next_action","change"))
        assert isinstance(proposal["proposed_files"],list) and isinstance(proposal["test_plan"],list)
        assert isinstance(proposal["change"],dict)
        assert isinstance(proposal["change"].get("path"),str) and isinstance(proposal["change"].get("content"),str)
    except (ValueError, AssertionError) as error:
        raise SystemExit("No valid structured proposal: "+str(error))
    Path("agent-output").mkdir(exist_ok=True)
    Path("agent-output/proposal.json").write_text(json.dumps(proposal,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    summary=os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary,"a",encoding="utf-8") as f:
            f.write("## Survival40 unattended AI review\n\n")
            f.write("**Automated review and candidate only; execution and PR are separately gated. No release.**\n\n")
            f.write("**"+str(proposal["title"]).replace("\n"," ")+"**\n\n")
            f.write(str(proposal["rationale"]).replace("\n"," ")[:1300]+"\n")
    print("Gemini proposed a constrained regression test; validation and PR pending.")

if __name__=="__main__":
    main()
