import shutil
import subprocess

import numpy as np
import pytest

from zun_music import video
from zun_music.render import RenderError


def _sine(freq, seconds=1.0, sr=video.SR):
    t = np.arange(int(sr * seconds)) / sr
    return (0.5 * np.sin(2 * np.pi * freq * t)).astype(np.float32)


def test_band_levels_shape_and_range():
    lv = video.band_levels(_sine(440, 1.0))
    assert lv.shape == (video.FPS, video.BANDS)  # 1 s at 30 fps
    assert lv.min() >= 0 and lv.max() <= 1


def test_band_levels_puts_energy_in_the_right_band():
    lo = video.band_levels(_sine(100)).mean(axis=0).argmax()
    hi = video.band_levels(_sine(5000)).mean(axis=0).argmax()
    assert lo < hi


def test_frames_have_expected_size_and_count():
    lv = np.random.default_rng(0).random((5, video.BANDS))
    out = list(video.frames(lv, title="songbie · test 送别"))
    assert len(out) == 5
    assert all(len(f) == video.W * video.H * 3 for f in out)


def test_title_from_trims_description():
    assert video.title_from("v1", "drums only: constant velocity") == "v1  ·  drums only"
    assert video.title_from("v1") == "v1"
    assert len(video.title_from("v1", "x" * 200)) <= 40


def _has_x265():
    if shutil.which("ffmpeg") is None:
        return False
    enc = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True).stdout
    return "libx265" in enc


@pytest.mark.skipif(not _has_x265(), reason="needs ffmpeg with libx265")
def test_render_video_end_to_end(tmp_path):
    mp3 = tmp_path / "a.mp3"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
                    str(mp3)], check=True)
    mp4 = video.render_video(mp3, title="a")
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_name,codec_tag_string",
                            "-of", "csv=p=0", str(mp4)], capture_output=True, text=True).stdout
    assert "hevc,hvc1" in probe and "aac" in probe


def test_render_video_reports_missing_input(tmp_path):
    if shutil.which("ffmpeg") is None:
        pytest.skip("needs ffmpeg")
    with pytest.raises(RenderError, match="could not decode"):
        video.render_video(tmp_path / "missing.mp3")
