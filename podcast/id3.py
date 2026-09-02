"""Writing an episode's CMS metadata into its own MP3 file.

Podcast clients and the Radio Moss stream both read ID3 tags off the file
itself, not from the CMS. Episodes 196-237 were published with no tags at
all, and because Icecast keeps displaying whatever title it was last sent, an
untagged track on the stream showed the *previous* episode's name — wrong
information rather than missing information. Tagging at publish time is what
stops that recurring; see `podcast/signals.py`.

The frame set here matches what episodes 1-195 already carry (tagged by a
deployment script before the move to Wagtail), so the catalogue stays
uniform. Reference file: 102_qUTXw55.mp3.
"""

import html
import logging
import os
import re

from mutagen.id3 import (
    APIC, COMM, ID3, PCST, TALB, TCON, TCOP, TDES, TDRC, TGID, TIT2, TPE1,
    TPE2, TPOS, TRCK, WXXX, ID3NoHeaderError,
)

logger = logging.getLogger(__name__)

ARTIST = "Into the Moss"
GENRE = "Ambient"
BROADCAST = "First broadcast {date} on Resonance 104.4 FM (www.resonancefm.com)"
EPISODE_URL = "https://intothemoss.com/episodes/{number}/"


class TaggingError(Exception):
    """The episode's audio could not be tagged."""


def _plain(rich_text):
    """Wagtail rich text -> the plain string iTunes' TDES frame expects."""
    return html.unescape(re.sub(r"<[^>]+>", "", rich_text or "")).strip()


def _artwork(image):
    """Cover art bytes and mime type, or (None, None, reason).

    Prefers the stored original. A Wagtail image's original file can go
    missing while its pre-generated renditions survive (episode 212 is the
    known case), so fall back to the largest rendition still on disk rather
    than shipping an episode with no cover.
    """
    if image is None:
        return None, None, "no cover_image set"

    candidates = []
    try:
        if os.path.exists(image.file.path):
            candidates.append(image.file.path)
    except (ValueError, NotImplementedError):
        pass

    if not candidates:
        for rendition in image.renditions.all():
            try:
                if os.path.exists(rendition.file.path):
                    candidates.append(rendition.file.path)
            except (ValueError, NotImplementedError):
                continue
        candidates.sort(key=os.path.getsize, reverse=True)

    if not candidates:
        return None, None, "no cover file on disk"

    path = candidates[0]
    mime = "image/png" if path.lower().endswith(".png") else "image/jpeg"
    with open(path, "rb") as handle:
        return handle.read(), mime, os.path.basename(path)


def write_tags(episode):
    """Write `episode`'s metadata into its MP3, in place. Returns a note.

    Raises TaggingError if there is no audio file to write to, or the write
    fails. Missing cover art is not fatal: the rest of the tags are still
    worth writing, and the reason is included in the returned note.
    """
    if not episode.audio_file:
        raise TaggingError(f"episode {episode.episode_number} has no audio file")

    try:
        path = episode.audio_file.path
    except (ValueError, NotImplementedError) as exc:
        # Non-filesystem storage (Spaces) would need download/upload instead.
        raise TaggingError(f"audio file is not on local disk: {exc}") from exc

    if not os.path.exists(path):
        raise TaggingError(f"audio file missing on disk: {path}")

    published = episode.publication_date
    year = published.year
    image, mime, art_note = _artwork(episode.cover_image)

    try:
        tags = ID3(path)
    except ID3NoHeaderError:
        # ffmpeg writes some files with no ID3 container at all.
        tags = ID3()

    tags.add(TIT2(encoding=3, text=episode.title))
    tags.add(TPE1(encoding=3, text=ARTIST))
    tags.add(TPE2(encoding=3, text=ARTIST))
    tags.add(TALB(encoding=3, text=f"Season {episode.season_number}"))
    tags.add(TPOS(encoding=3, text=str(episode.season_number)))
    tags.add(TRCK(encoding=3, text=str(episode.season_episode_number)))
    tags.add(TDRC(encoding=3, text=str(year)))
    tags.add(TCOP(encoding=3, text=f"© {ARTIST} {year}"))
    tags.add(TCON(encoding=3, text=GENRE))
    tags.add(TDES(encoding=3, text=_plain(episode.description)))
    tags.add(TGID(encoding=3, text=episode.guid or f"itm-ep{episode.episode_number}"))
    tags.add(COMM(encoding=3, lang="eng", desc="",
                  text=BROADCAST.format(date=f"{published:%d %b %Y}")))
    tags.add(WXXX(encoding=3, desc="",
                  url=EPISODE_URL.format(number=episode.episode_number)))
    tags.add(PCST(value=0))
    if image:
        tags.add(APIC(encoding=3, mime=mime, type=3, desc="", data=image))

    try:
        # v2.4 keeps TDRC as-is; v2.3 would downgrade it to TYER.
        tags.save(path, v2_version=4)
    except OSError as exc:
        raise TaggingError(f"could not write tags to {path}: {exc}") from exc

    return f"{episode.title!r} S{episode.season_number}E{episode.season_episode_number}, art: {art_note}"
