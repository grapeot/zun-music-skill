import pytest

from zun_music.render import RenderError, resolve_soundfont
from zun_music.serve import render_page


def test_missing_soundfont_is_explicit(monkeypatch):
    monkeypatch.delenv("ZUN_MUSIC_SOUNDFONT", raising=False)
    with pytest.raises(RenderError, match="no SoundFont"):
        resolve_soundfont(None)


def test_html_challenge_page_is_rejected(tmp_path):
    fake = tmp_path / "Touhou.sf2"
    fake.write_text("<!DOCTYPE html><title>Just a moment...</title>")
    with pytest.raises(RenderError, match="not a SoundFont"):
        resolve_soundfont(str(fake))


def test_valid_header_accepted(tmp_path):
    sf = tmp_path / "ok.sf2"
    sf.write_bytes(b"RIFF\x00\x00\x00\x00sfbk" + b"\x00" * 16)
    assert resolve_soundfont(str(sf)) == sf


def test_listening_page_lists_versions(tmp_path):
    (tmp_path / "v1.mp3").write_bytes(b"")
    (tmp_path / "v1.txt").write_text("first <try>", encoding="utf-8")
    (tmp_path / "v1.mid").write_bytes(b"")
    (tmp_path / "v2.mp3").write_bytes(b"")
    page = render_page(tmp_path)
    assert page.index("v1") < page.index("v2")
    assert "first &lt;try&gt;" in page
    assert '/files/v1.mid' in page


def test_listening_page_empty_folder(tmp_path):
    assert "No renders yet" in render_page(tmp_path)
