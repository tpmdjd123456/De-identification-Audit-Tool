"""Dependency-free quick demo: python demo.py"""
from audit_tool import run_pipeline
from audit_tool.sample_data import SAMPLES

for language, example in SAMPLES.items():
    outcome = run_pipeline(example, language=language)
    print(f"\n[{language.upper()}] {len(outcome.spans)} rule matches")
    print("ORIGINAL:", outcome.original_text)
    print("REDACTED:", outcome.transformed_text)
    print("EXACT-STRING PERSISTENCE:", outcome.unchanged_identifier_count)
