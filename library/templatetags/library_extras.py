import re

from django import template

register = template.Library()

# https://rutube.ru/video/7ad9de2f84e2a7e25b4784f85e5a060c/?r=wd -> id
_RUTUBE_WATCH_RE = re.compile(r"rutube\.ru/video/([0-9a-fA-F]+)")
# https://vk.com/video-123456789_456239017  или  https://vkvideo.ru/video-123_456
_VK_WATCH_RE = re.compile(r"vk(?:video)?\.(?:com|ru)/video(-?\d+)_(\d+)")
# https://www.youtube.com/watch?v=abc123 или https://youtu.be/abc123
_YT_WATCH_RE = re.compile(r"(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]+)")


@register.filter
def video_embed_url(url):
    """Приводит ссылку на видео к embed-формату, пригодному для <iframe>."""
    if not url:
        return url

    if "/play/embed/" in url:
        return url  # уже embed-ссылка Rutube

    match = _RUTUBE_WATCH_RE.search(url)
    if match:
        return f"https://rutube.ru/play/embed/{match.group(1)}/"

    if "video_ext.php" in url:
        return url  # уже embed-ссылка VK

    match = _VK_WATCH_RE.search(url)
    if match:
        oid, video_id = match.group(1), match.group(2)
        return f"https://vk.com/video_ext.php?oid={oid}&id={video_id}&hd=2"

    if "/embed/" in url:
        return url

    match = _YT_WATCH_RE.search(url)
    if match:
        return f"https://www.youtube.com/embed/{match.group(1)}"

    return url


@register.filter
def video_platform_label(url):
    """Человекочитаемое название площадки — для запасной ссылки под видео."""
    if not url:
        return ""
    if "rutube" in url:
        return "Rutube"
    if "vk.com" in url or "vkvideo.ru" in url:
        return "ВКонтакте"
    return "источнике"
