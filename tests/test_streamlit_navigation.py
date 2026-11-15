"""Lightweight navigation smoke checks without requiring Streamlit in CI.

These run the real app.py module against a tiny fake Streamlit API. They check
branch wiring; they are not a replacement for opening the browser app.
"""
from pathlib import Path
import runpy
import sys

import pytest

from evaluation import document_review

APP = Path(__file__).resolve().parents[1] / "app.py"


class FakeStreamlit:
    def __init__(self, mode):
        self.mode = mode
        self.sidebar = self
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def __getattr__(self, name):
        def method(*args, **kwargs):
            self.calls.append((name, args, kwargs))
            if name == "radio":
                return self.mode
            if name == "columns":
                return [self for _ in range(args[0])]
            if name == "expander":
                return self
            if name == "cache_data":
                return lambda fn: fn
            if name == "selectbox":
                return args[1][0]
            if name == "text_area":
                return kwargs["value"]
            if name == "number_input":
                return args[3]
            return None
        return method


def run_mock_ui(monkeypatch, mode):
    fake = FakeStreamlit(mode)
    monkeypatch.setitem(sys.modules, "streamlit", fake)
    module = runpy.run_path(str(APP), run_name="__main__")
    return fake, module


def has_call(fake, method, text):
    return any(name == method and any(text in str(arg) for arg in args)
               for name, args, _ in fake.calls)


def test_original_regex_demo_page_still_loads(monkeypatch):
    fake, module = run_mock_ui(monkeypatch, "Transform and review")
    assert has_call(fake, "subheader", "Build a basic transformation pipeline")
    assert has_call(fake, "download_button", "Download transformed text")
    assert "&lt;script&gt;" in module["highlighted"]("<script>", [])
    assert "<script>" not in module["highlighted"]("<script>", [])


def test_original_external_audit_page_still_loads(monkeypatch):
    fake, _ = run_mock_ui(monkeypatch, "Audit existing text")
    assert has_call(fake, "subheader", "Audit text transformed elsewhere")


def test_missing_corpus_message_does_not_break_app(monkeypatch, tmp_path):
    monkeypatch.setattr(document_review, "DEFAULT_ARCHIVE", tmp_path / "missing.zip")
    fake, _ = run_mock_ui(monkeypatch, "GraSCCo Document Review")
    assert has_call(fake, "warning", "not installed locally")
    assert not any(name == "selectbox" and args[0] == "Clinical document" for name, args, _ in fake.calls)


@pytest.mark.skipif(not document_review.DEFAULT_ARCHIVE.is_file(), reason="GraSCCo archive absent")
def test_document_review_page_loads_and_exports(monkeypatch):
    fake, _ = run_mock_ui(monkeypatch, "GraSCCo Document Review")
    assert has_call(fake, "subheader", "GraSCCo Document Review")
    assert any(name == "selectbox" and args[0] == "Clinical document" for name, args, _ in fake.calls)
    assert any(name == "selectbox" and args[0] == "Transformation pipeline" for name, args, _ in fake.calls)
    assert has_call(fake, "download_button", "Download transformed text")
    assert has_call(fake, "download_button", "Download audit JSON")
    assert has_call(fake, "metric", "Gold PHI spans")
