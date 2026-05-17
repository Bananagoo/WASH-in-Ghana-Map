"""
Sound manager with complete graceful fallback.
If pygame.mixer fails (browser, no audio device, missing files), game runs silently.
"""
import os
import pygame


SOUND_PATHS = {
    "click":      "assets/audio/click.wav",       # 0.12s — soft tick for UI buttons
    "open_stop":  "assets/audio/open_stop.wav",   # 0.45s — gentle discovery chime on location click
    "collect":    "assets/audio/collect.wav",     # 1.10s — reward fanfare on token collect
    "transition": "assets/audio/transition.wav",  # 0.35s — smooth ascending sweep
    "levelup":    "assets/audio/levelup.wav",     # 1.33s — warm celebration on final screen
}
MUSIC_PATH = "assets/audio/music_village.ogg"


class AudioManager:
    def __init__(self):
        self.enabled = False
        self.muted   = False
        self._sounds: dict = {}
        self._music_loaded = False
        self._try_init()

    # ------------------------------------------------------------------
    # Init
    # ------------------------------------------------------------------

    def _try_init(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=4096)
            self.enabled = True
            self._load_sounds()
        except Exception:
            self.enabled = False

    def _load_sounds(self):
        for name, path in SOUND_PATHS.items():
            if os.path.exists(path):
                try:
                    s = pygame.mixer.Sound(path)
                    s.set_volume(0.35)
                    self._sounds[name] = s
                except Exception:
                    pass

    # ------------------------------------------------------------------
    # Playback
    # ------------------------------------------------------------------

    def play(self, name: str):
        if not self.enabled or self.muted:
            return
        sound = self._sounds.get(name)
        if sound:
            sound.play()

    def play_music(self):
        if not self.enabled or self.muted or self._music_loaded:
            return
        if os.path.exists(MUSIC_PATH):
            try:
                pygame.mixer.music.load(MUSIC_PATH)
                pygame.mixer.music.set_volume(0.15)
                pygame.mixer.music.play(-1)
                self._music_loaded = True
            except Exception:
                pass

    def stop_music(self):
        if self.enabled:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass

    def toggle_mute(self):
        self.muted = not self.muted
        if not self.enabled:
            return
        try:
            if self.muted:
                pygame.mixer.music.pause()
            else:
                pygame.mixer.music.unpause()
        except Exception:
            pass

    @property
    def status_label(self) -> str:
        if not self.enabled:
            return "♪ N/A"
        return "♪ OFF (M)" if self.muted else "♪ ON  (M)"
