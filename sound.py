"""
sound.py — Hệ thống âm thanh "Ashes of the Fallen"
=====================================================
Tạo âm thanh procedurally bằng numpy + pygame.mixer.
Không cần file .wav ngoài — toàn bộ âm thanh được sinh ra bằng code.

Âm thanh có:
  - SFX: attack, hit, dash, aoe, skill, pickup, levelup, death, boss
  - Nhạc nền: ambient theo từng chương (dùng pygame.mixer.music hoặc Channel)
"""

import numpy as np
import pygame
import math
import random

# ======================== CẤU HÌNH ========================
SAMPLE_RATE = 44100   # Hz
CHANNELS    = 2       # Stereo
BIT_DEPTH   = -16     # 16-bit signed

# Volume (0.0 → 1.0)
SFX_VOLUME   = 0.45
MUSIC_VOLUME = 0.20

_initialized = False
_sounds: dict = {}        # Lưu Sound objects
_music_channel = None     # Channel phát nhạc nền loop

# ======================== KHỞI TẠO ========================

def init():
    """Khởi tạo pygame.mixer và tạo toàn bộ âm thanh."""
    global _initialized, _music_channel
    if _initialized:
        return
    try:
        pygame.mixer.pre_init(SAMPLE_RATE, BIT_DEPTH, CHANNELS, 512)
        pygame.mixer.init()
        pygame.mixer.set_num_channels(16)
        _music_channel = pygame.mixer.Channel(15)  # Channel dành riêng cho nhạc nền
        _build_all_sounds()
        _initialized = True
        print("[Sound] Khởi tạo âm thanh thành công.")
    except Exception as e:
        print(f"[Sound] Lỗi khởi tạo: {e}")


def _initialized_check():
    return _initialized


# ======================== TIỆN ÍCH TẠO SÓNG ========================

def _make_buffer(arr: np.ndarray) -> pygame.mixer.Sound:
    """Chuyển numpy array (float32, -1..1) sang pygame.mixer.Sound."""
    arr = np.clip(arr, -1.0, 1.0)
    # Stereo: duplicate channel
    stereo = np.column_stack([arr, arr])
    pcm = (stereo * 32767).astype(np.int16)
    return pygame.mixer.Sound(buffer=pcm.tobytes())


def _sine(freq, duration, sr=SAMPLE_RATE):
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    return np.sin(2 * np.pi * freq * t).astype(np.float32)


def _square(freq, duration, duty=0.5, sr=SAMPLE_RATE):
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    phase = (t * freq) % 1.0
    return (np.where(phase < duty, 1.0, -1.0)).astype(np.float32)


def _sawtooth(freq, duration, sr=SAMPLE_RATE):
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    return (2 * ((t * freq) % 1.0) - 1.0).astype(np.float32)


def _noise(duration, sr=SAMPLE_RATE):
    n = int(sr * duration)
    return np.random.uniform(-1.0, 1.0, n).astype(np.float32)


def _envelope(arr, attack=0.01, decay=0.05, sustain=0.7, release=0.1, sr=SAMPLE_RATE):
    """ADSR envelope."""
    n = len(arr)
    env = np.ones(n, dtype=np.float32)
    a = int(attack * sr)
    d = int(decay * sr)
    r = int(release * sr)
    s_end = max(a + d, n - r)

    if a > 0:
        env[:a] = np.linspace(0, 1, a)
    if d > 0 and a + d <= n:
        env[a:a+d] = np.linspace(1, sustain, d)
    if a + d < s_end:
        env[a+d:s_end] = sustain
    if r > 0 and s_end < n:
        env[s_end:] = np.linspace(sustain, 0, n - s_end)

    return (arr * env).astype(np.float32)


def _fade_out(arr, fade=0.05, sr=SAMPLE_RATE):
    n = len(arr)
    f = int(fade * sr)
    if f > 0 and f <= n:
        arr[-f:] *= np.linspace(1, 0, f)
    return arr


# ======================== TẠO TỪNG LOẠI SFX ========================

def _sfx_attack():
    """Tiếng vung kiếm — swoosh ngắn gọn."""
    dur = 0.15
    base = _sine(300, dur) * 0.3 + _noise(dur) * 0.4
    base += _sawtooth(200, dur) * 0.3
    env = _envelope(base, attack=0.005, decay=0.08, sustain=0.1, release=0.06)
    return _fade_out(env * 0.7)


def _sfx_hit():
    """Tiếng đánh trúng — thud + crunch."""
    dur = 0.18
    thud = _sine(80, dur) * 0.5
    crunch = _noise(dur) * 0.6
    crunch[:int(0.02 * SAMPLE_RATE)] *= 2.0  # Punch đầu
    arr = thud + crunch
    return _envelope(arr, attack=0.002, decay=0.05, sustain=0.2, release=0.1)


def _sfx_crit():
    """Tiếng chí mạng — metallic crack."""
    dur = 0.2
    base = _sine(500, dur) * 0.4 + _sine(250, dur) * 0.3 + _noise(dur) * 0.5
    env = _envelope(base, attack=0.001, decay=0.03, sustain=0.3, release=0.15)
    return env * 0.85


def _sfx_dash():
    """Tiếng dash — whoosh nhanh."""
    dur = 0.22
    t = np.linspace(0, dur, int(SAMPLE_RATE * dur))
    freq = 400 + 300 * (1 - t / dur)   # Pitch đi xuống
    phase = np.cumsum(2 * np.pi * freq / SAMPLE_RATE)
    base = np.sin(phase).astype(np.float32) * 0.4 + _noise(dur) * 0.4
    return _envelope(base, attack=0.01, decay=0.1, sustain=0.1, release=0.08)


def _sfx_aoe():
    """Tiếng AoE 360° — bass boom + shimmer."""
    dur = 0.5
    boom = _sine(60, dur) * 0.6 + _sine(120, dur) * 0.3
    shimmer = _noise(dur) * 0.4
    t = np.linspace(0, dur, int(SAMPLE_RATE * dur))
    fade_env = np.exp(-t * 8).astype(np.float32)
    arr = (boom + shimmer) * fade_env
    return np.clip(arr, -1, 1).astype(np.float32)


def _sfx_shield():
    """Tiếng kích hoạt khiên — metallic ring."""
    dur = 0.35
    ring = _sine(800, dur) * 0.5 + _sine(1200, dur) * 0.25 + _sine(400, dur) * 0.25
    return _envelope(ring, attack=0.01, decay=0.1, sustain=0.4, release=0.15)


def _sfx_lifesteal():
    """Tiếng phóng projectile lifesteal — dark whoosh."""
    dur = 0.2
    t = np.linspace(0, dur, int(SAMPLE_RATE * dur))
    freq = 200 + 400 * t / dur
    phase = np.cumsum(2 * np.pi * freq / SAMPLE_RATE)
    arr = np.sin(phase).astype(np.float32) * 0.5 + _noise(dur) * 0.3
    return _envelope(arr, attack=0.005, decay=0.08, sustain=0.2, release=0.08)


def _sfx_summon():
    """Tiếng triệu hồi linh hồn — ethereal chime."""
    dur = 0.6
    arr = (_sine(523, dur) * 0.4 + _sine(659, dur) * 0.3
           + _sine(784, dur) * 0.2 + _sine(1047, dur) * 0.1)
    return _envelope(arr, attack=0.05, decay=0.1, sustain=0.5, release=0.25)


def _sfx_pickup():
    """Tiếng nhặt item — ascending ding."""
    dur = 0.25
    arr = _sine(440, dur) * 0.4 + _sine(660, dur) * 0.35 + _sine(880, dur) * 0.25
    return _envelope(arr, attack=0.01, decay=0.05, sustain=0.5, release=0.15)


def _sfx_levelup():
    """Tiếng level up — fanfare ngắn."""
    dur = 0.7
    notes = [523, 659, 784, 1047]  # C5 E5 G5 C6
    step = dur / len(notes)
    arr = np.zeros(int(SAMPLE_RATE * dur), dtype=np.float32)
    for i, note in enumerate(notes):
        start = int(i * step * SAMPLE_RATE)
        seg = _sine(note, step) * 0.5
        seg = _envelope(seg, attack=0.01, decay=0.05, sustain=0.7, release=0.15)
        seg_len = min(len(seg), len(arr) - start)
        if seg_len > 0:
            arr[start:start+seg_len] += seg[:seg_len]
    return np.clip(arr, -1, 1).astype(np.float32)


def _sfx_player_hurt():
    """Tiếng player bị đánh."""
    dur = 0.2
    arr = _noise(dur) * 0.5 + _sine(150, dur) * 0.4
    return _envelope(arr, attack=0.002, decay=0.05, sustain=0.3, release=0.1)


def _sfx_player_death():
    """Tiếng player chết — dark descending tone."""
    dur = 1.0
    t = np.linspace(0, dur, int(SAMPLE_RATE * dur))
    freq = 300 * np.exp(-t * 3)
    phase = np.cumsum(2 * np.pi * freq / SAMPLE_RATE)
    arr = np.sin(phase).astype(np.float32) * 0.5 + _noise(dur) * 0.2
    return _envelope(arr, attack=0.02, decay=0.3, sustain=0.3, release=0.4)


def _sfx_enemy_death():
    """Tiếng quái chết."""
    dur = 0.3
    arr = _sine(200, dur) * 0.3 + _noise(dur) * 0.5
    return _envelope(arr, attack=0.005, decay=0.1, sustain=0.1, release=0.15)


def _sfx_boss_hit():
    """Tiếng đánh trúng boss — heavy impact."""
    dur = 0.4
    thud = _sine(50, dur) * 0.5 + _sine(100, dur) * 0.35
    crunch = _noise(dur) * 0.4
    arr = thud + crunch
    t = np.linspace(0, dur, len(arr))
    arr *= np.exp(-t * 5)
    return np.clip(arr, -1, 1).astype(np.float32)


def _sfx_boss_roar():
    """Tiếng boss gầm — low frequency growl."""
    dur = 0.8
    t = np.linspace(0, dur, int(SAMPLE_RATE * dur))
    lfo = np.sin(2 * np.pi * 5 * t)  # 5Hz LFO
    freq = 80 + 30 * lfo
    phase = np.cumsum(2 * np.pi * freq / SAMPLE_RATE)
    arr = np.sin(phase).astype(np.float32) * 0.5
    arr += _noise(dur) * 0.25
    return _envelope(arr, attack=0.05, decay=0.2, sustain=0.5, release=0.3)


def _sfx_door():
    """Tiếng mở cửa chuyển chương."""
    dur = 0.4
    arr = _square(220, dur, duty=0.3) * 0.3 + _sine(440, dur) * 0.3
    return _envelope(arr, attack=0.02, decay=0.1, sustain=0.5, release=0.2)


def _sfx_dialogue():
    """Tiếng beep nhỏ khi hiện chữ dialogue."""
    dur = 0.04
    arr = _sine(880, dur) * 0.3
    return _envelope(arr, attack=0.002, decay=0.01, sustain=0.3, release=0.015)


def _sfx_trap():
    """Tiếng bẫy kích hoạt."""
    dur = 0.25
    arr = _noise(dur) * 0.5 + _sine(400, dur) * 0.3
    return _envelope(arr, attack=0.001, decay=0.05, sustain=0.2, release=0.15)


# ======================== NHẠC NỀN (AMBIENT) ========================

def _make_ambient_loop(chapter: int) -> pygame.mixer.Sound:
    """
    Tạo nhạc nền ambient ngắn (~3s) cho mỗi chương.
    Chapter 1 — tối tăm, chậm (C minor drone)
    Chapter 2 — căng thẳng (dissonant)
    Chapter 3 — rừng ma (mid freq hum)
    Chapter 4 — huyền bí (ethereal)
    Chapter 5 — boss (heavy bass)
    """
    dur = 3.0
    sr = SAMPLE_RATE

    if chapter == 1:
        # C minor drone — buồn, u ám
        arr = (_sine(130.8, dur) * 0.25    # C3
               + _sine(155.6, dur) * 0.15   # Eb3
               + _sine(196.0, dur) * 0.10   # G3
               + _noise(dur) * 0.04)
        t = np.linspace(0, dur, int(sr * dur))
        lfo = 0.8 + 0.2 * np.sin(2 * np.pi * 0.3 * t)
        arr = (arr * lfo).astype(np.float32)

    elif chapter == 2:
        # Dissonant city — căng thẳng
        arr = (_sine(110.0, dur) * 0.20
               + _sine(116.5, dur) * 0.15   # Bb2 — dissonant
               + _sine(146.8, dur) * 0.10
               + _noise(dur) * 0.05)
        t = np.linspace(0, dur, int(sr * dur))
        lfo = 0.8 + 0.2 * np.sin(2 * np.pi * 0.5 * t)
        arr = (arr * lfo).astype(np.float32)

    elif chapter == 3:
        # Forest — mystical hum
        arr = (_sine(174.6, dur) * 0.20    # F3
               + _sine(220.0, dur) * 0.15   # A3
               + _sine(261.6, dur) * 0.10   # C4
               + _noise(dur) * 0.04)
        t = np.linspace(0, dur, int(sr * dur))
        lfo = 0.75 + 0.25 * np.sin(2 * np.pi * 0.4 * t)
        arr = (arr * lfo).astype(np.float32)

    elif chapter == 4:
        # Ethereal between-world
        arr = (_sine(196.0, dur) * 0.15
               + _sine(246.9, dur) * 0.15   # B3
               + _sine(329.6, dur) * 0.12   # E4
               + _noise(dur) * 0.03)
        t = np.linspace(0, dur, int(sr * dur))
        lfo = 0.7 + 0.3 * np.sin(2 * np.pi * 0.25 * t)
        arr = (arr * lfo).astype(np.float32)

    else:
        # Chapter 5 — boss, heavy bass
        arr = (_sine(55.0, dur) * 0.30     # A1
               + _sine(73.4, dur) * 0.20    # D2
               + _noise(dur) * 0.08
               + _square(55.0, dur, duty=0.3) * 0.10)
        t = np.linspace(0, dur, int(sr * dur))
        lfo = 0.8 + 0.2 * np.sin(2 * np.pi * 0.6 * t)
        arr = (arr * lfo).astype(np.float32)

    # Crossfade đầu/cuối để loop mượt
    fade_len = int(0.1 * sr)
    arr[:fade_len] *= np.linspace(0, 1, fade_len)
    arr[-fade_len:] *= np.linspace(1, 0, fade_len)

    return _make_buffer(np.clip(arr, -1, 1))


# ======================== BUILD TẤT CẢ ========================

def _build_all_sounds():
    """Tạo và lưu toàn bộ Sound objects."""
    sfx_map = {
        "attack":       _sfx_attack,
        "hit":          _sfx_hit,
        "crit":         _sfx_crit,
        "dash":         _sfx_dash,
        "aoe":          _sfx_aoe,
        "shield":       _sfx_shield,
        "lifesteal":    _sfx_lifesteal,
        "summon":       _sfx_summon,
        "pickup":       _sfx_pickup,
        "levelup":      _sfx_levelup,
        "player_hurt":  _sfx_player_hurt,
        "player_death": _sfx_player_death,
        "enemy_death":  _sfx_enemy_death,
        "boss_hit":     _sfx_boss_hit,
        "boss_roar":    _sfx_boss_roar,
        "door":         _sfx_door,
        "dialogue":     _sfx_dialogue,
        "trap":         _sfx_trap,
    }
    for name, fn in sfx_map.items():
        try:
            arr = fn()
            snd = _make_buffer(arr)
            snd.set_volume(SFX_VOLUME)
            _sounds[name] = snd
        except Exception as e:
            print(f"[Sound] Lỗi tạo '{name}': {e}")

    # Ambient cho từng chương
    for ch in range(1, 6):
        try:
            snd = _make_ambient_loop(ch)
            snd.set_volume(MUSIC_VOLUME)
            _sounds[f"ambient_{ch}"] = snd
        except Exception as e:
            print(f"[Sound] Lỗi tạo ambient_{ch}: {e}")


# ======================== API PHÁT NHẠC ========================

_current_chapter_music = -1


def play(name: str, volume: float = None):
    """Phát một SFX theo tên."""
    if not _initialized:
        return
    snd = _sounds.get(name)
    if snd:
        if volume is not None:
            snd.set_volume(max(0.0, min(1.0, volume)))
        else:
            snd.set_volume(SFX_VOLUME)
        snd.play()


def play_music(chapter: int):
    """Phát nhạc nền ambient loop cho chương. Không phát lại nếu đang phát cùng chương."""
    global _current_chapter_music
    if not _initialized:
        return
    if chapter == _current_chapter_music:
        return
    _current_chapter_music = chapter
    snd = _sounds.get(f"ambient_{chapter}")
    if snd and _music_channel:
        _music_channel.play(snd, loops=-1)  # Loop vô tận


def stop_music():
    """Dừng nhạc nền."""
    global _current_chapter_music
    if _music_channel:
        _music_channel.stop()
    _current_chapter_music = -1


def set_sfx_volume(vol: float):
    """Chỉnh âm lượng SFX (0.0–1.0)."""
    global SFX_VOLUME
    SFX_VOLUME = max(0.0, min(1.0, vol))
    for name, snd in _sounds.items():
        if not name.startswith("ambient_"):
            snd.set_volume(SFX_VOLUME)


def set_music_volume(vol: float):
    """Chỉnh âm lượng nhạc nền (0.0–1.0)."""
    global MUSIC_VOLUME
    MUSIC_VOLUME = max(0.0, min(1.0, vol))
    for name, snd in _sounds.items():
        if name.startswith("ambient_"):
            snd.set_volume(MUSIC_VOLUME)
