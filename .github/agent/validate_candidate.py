#!/usr/bin/env python3
"""Validate one new AI-authored regression test. Never edit production files."""
import ast
import json
import re
import sys
from pathlib import Path

MAX_BYTES = 7000
ALLOWED = {'unittest', 'pathlib', 're', 'ast'}
BANNED_FUNCTIONS = {'eval','exec','compile','__import__','open','input','breakpoint'}
BANNED_METHODS = {'write_text','write_bytes','unlink','rename','replace','rmdir',
                  'mkdir','touch','chmod','symlink_to','link_to','open','system',
                  'popen','run','Popen','check_output','check_call','call','urlopen',
                  'request','connect'}

def validate(proposal, root):
    change = proposal.get('change') if isinstance(proposal, dict) else None
    if not isinstance(change, dict):
        raise ValueError('Missing change')
    path, content = change.get('path'), change.get('content')
    if not isinstance(path,str) or not re.fullmatch(r'\.github/agent/generated_tests/test_s40_[a-z0-9_]{3,50}\.py',path):
        raise ValueError('Invalid or unsafe proposed path')
    if not isinstance(content,str) or not 60 <= len(content.encode('utf-8')) <= MAX_BYTES:
        raise ValueError('Invalid generated test length')
    dest = root/path
    if dest.exists() or dest.is_symlink():
        raise ValueError('Existing test cannot be overwritten')
    tree = ast.parse(content, filename=path)
    imports = set()
    has_unittest_class = False
    for node in ast.walk(tree):
        if isinstance(node,(ast.Import,ast.ImportFrom)):
            modules = ([i.name for i in node.names] if isinstance(node,ast.Import)
                       else [node.module or ''])
            if isinstance(node,ast.ImportFrom) and node.level:
                raise ValueError('Relative imports forbidden')
            for module in modules:
                top=module.split('.')[0]
                if top not in ALLOWED:
                    raise ValueError('Forbidden import: '+top)
                imports.add(top)
        if isinstance(node,ast.Call):
            f=node.func
            if isinstance(f,ast.Name) and f.id in BANNED_FUNCTIONS:
                raise ValueError('Unsafe call: '+f.id)
            if isinstance(f,ast.Attribute) and f.attr in BANNED_METHODS:
                raise ValueError('Unsafe method: '+f.attr)
        if isinstance(node,ast.ClassDef):
            if any(isinstance(b,ast.Attribute) and b.attr=='TestCase' for b in node.bases):
                has_unittest_class=True
    if 'unittest' not in imports or not has_unittest_class or 'def test_' not in content:
        raise ValueError('Expected unittest.TestCase with a test_ method')
    return path,content

def main():
    proposal=json.loads(Path('agent-output/proposal.json').read_text(encoding='utf-8'))
    path,content=validate(proposal,Path.cwd())
    dest=Path(path)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(content,encoding='utf-8')
    print('PASS: staged a single bounded regression test:',path)

if __name__ == '__main__':
    try:
        main()
    except (OSError,ValueError,SyntaxError) as error:
        sys.exit('Candidate rejected: '+str(error))
