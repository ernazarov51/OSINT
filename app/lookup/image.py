import io
import urllib.parse

import httpx

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"}

INTERESTING_EXIF_TAGS = {
    "Make", "Model", "Software", "DateTime", "DateTimeOriginal",
    "GPSLatitude", "GPSLongitude", "GPSAltitude", "GPSLatitudeRef",
    "GPSLongitudeRef", "Artist", "Copyright", "ImageDescription",
    "XPComment", "XPAuthor",
}

def _parse_exif(content: bytes) -> dict:
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS, GPSTAGS
        import io

        img = Image.open(io.BytesIO(content))
        raw = img._getexif()
        if not raw:
            return {}

        exif = {}
        gps_raw = {}

        for tag_id, value in raw.items():
            tag = TAGS.get(tag_id, str(tag_id))
            if tag == "GPSInfo" and isinstance(value, dict):
                for k, v in value.items():
                    gps_raw[GPSTAGS.get(k, k)] = v
            elif tag in INTERESTING_EXIF_TAGS and isinstance(value, (str, int, float, bytes)):
                exif[tag] = str(value)[:200] if not isinstance(value, bytes) else value.decode("utf-8", errors="ignore")[:200]

        if gps_raw:
            lat = _dms_to_decimal(gps_raw.get("GPSLatitude"), gps_raw.get("GPSLatitudeRef", "N"))
            lon = _dms_to_decimal(gps_raw.get("GPSLongitude"), gps_raw.get("GPSLongitudeRef", "E"))
            if lat and lon:
                exif["gps_lat"] = round(lat, 6)
                exif["gps_lon"] = round(lon, 6)
                exif["gps_maps"] = f"https://www.google.com/maps?q={round(lat,6)},{round(lon,6)}"

        return exif
    except Exception:
        return {}

def _dms_to_decimal(dms, ref):
    if not dms or len(dms) < 3:
        return None
    try:
        def ratio(v):
            return float(v.numerator) / float(v.denominator) if hasattr(v, "numerator") else float(v)
        d = ratio(dms[0]) + ratio(dms[1]) / 60 + ratio(dms[2]) / 3600
        if ref in ("S", "W"):
            d = -d
        return d
    except Exception:
        return None

async def lookup_image(url: str) -> dict:
    url = url.strip()
    enc = urllib.parse.quote(url, safe="")

    result = {
        "found": True,
        "image_url": url,
        "reverse_search": {
            "Google":  f"https://www.google.com/searchbyimage?image_url={enc}",
            "Yandex":  f"https://yandex.com/images/search?url={enc}&rpt=imageview",
            "TinEye":  f"https://www.tineye.com/search?url={enc}",
            "Bing":    f"https://www.bing.com/images/search?q=imgurl:{enc}&view=detailv2&iss=sbi",
        },
    }

    try:
        async with httpx.AsyncClient(timeout=10, headers=HEADERS, follow_redirects=True) as client:
            r = await client.get(url)

        if r.status_code == 200:
            content = r.content
            ctype = r.headers.get("content-type", "")
            result["content_type"] = ctype
            result["size_kb"] = round(len(content) / 1024, 1)

            if "image" in ctype:
                try:
                    from PIL import Image
                    img = Image.open(io.BytesIO(content))
                    result["dimensions"] = f"{img.width} x {img.height} px"
                    result["format"] = img.format
                except Exception:
                    pass

                exif = _parse_exif(content)
                if exif:
                    result["exif"] = exif
                    if "gps_maps" in exif:
                        result["gps_maps"] = exif.pop("gps_maps")
    except Exception as e:
        result["fetch_error"] = str(e)

    return result
