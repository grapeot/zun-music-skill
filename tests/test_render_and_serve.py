import pytest

from zun_music.render import RenderError, resolve_soundfont
import threading
import urllib.request

from zun_music.serve import make_server, parse_range, render_page


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
    assert 'href="/files/v1.mid" download' in page
    assert 'href="/files/v1.mp3" download' in page
    assert "<audio" in page and "<video" not in page


def test_listening_page_prefers_video(tmp_path):
    (tmp_path / "v1.mp3").write_bytes(b"")
    (tmp_path / "v1.mp4").write_bytes(b"")
    page = render_page(tmp_path)
    assert '<video controls playsinline' in page and 'href="/files/v1.mp4" download' in page


def test_parse_range():
    assert parse_range("", 100) is None
    assert parse_range("bytes=0-9", 100) == (0, 9)
    assert parse_range("bytes=90-", 100) == (90, 99)
    assert parse_range("bytes=-10", 100) == (90, 99)
    assert parse_range("bytes=50-500", 100) == (50, 99)
    assert parse_range("bytes=200-300", 100) == "unsatisfiable"
    assert parse_range("bytes=0-1,5-9", 100) is None


def test_server_range_and_traversal(tmp_path):
    (tmp_path / "clip.mp4").write_bytes(bytes(range(256)) * 4)
    (tmp_path.parent / "secret.txt").write_text("nope")
    server = make_server(tmp_path, port=0, host="127.0.0.1")
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        req = urllib.request.Request(base + "/files/clip.mp4", headers={"Range": "bytes=0-15"})
        with urllib.request.urlopen(req) as r:
            assert r.status == 206
            assert r.headers["Content-Range"] == "bytes 0-15/1024"
            assert r.read() == bytes(range(16))
        with urllib.request.urlopen(base + "/files/clip.mp4") as r:
            assert r.status == 200 and len(r.read()) == 1024
        for bad in ("/files/../secret.txt", "/files/%2e%2e/secret.txt", "/secret.txt"):
            try:
                urllib.request.urlopen(base + bad)
                raise AssertionError(f"{bad} should be 404")
            except urllib.error.HTTPError as e:
                assert e.code == 404
    finally:
        server.shutdown()
        server.server_close()


def test_listening_page_empty_folder(tmp_path):
    assert "No renders yet" in render_page(tmp_path)
