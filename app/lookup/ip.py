import httpx

async def lookup_ip(address: str) -> dict:
    url = f"http://ip-api.com/json/{address}?fields=status,message,country,countryCode,regionName,city,zip,lat,lon,timezone,isp,org,as,mobile,proxy,hosting,query"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url)
            data = r.json()

        if data.get("status") == "fail":
            return {"found": False, "error": data.get("message", "Noma'lum xato")}

        result = {
            "found": True,
            "ip": data.get("query"),
            "country": data.get("country"),
            "country_code": data.get("countryCode"),
            "region": data.get("regionName"),
            "city": data.get("city"),
            "zip": data.get("zip"),
            "lat": data.get("lat"),
            "lon": data.get("lon"),
            "timezone": data.get("timezone"),
            "isp": data.get("isp"),
            "org": data.get("org"),
            "as": data.get("as"),
            "is_mobile": data.get("mobile"),
            "is_proxy": data.get("proxy"),
            "is_hosting": data.get("hosting"),
        }

        if data.get("lat") and data.get("lon"):
            lat, lon = data["lat"], data["lon"]
            result["maps_link"] = f"https://www.google.com/maps?q={lat},{lon}"

        return result

    except Exception as e:
        return {"found": False, "error": str(e)}
