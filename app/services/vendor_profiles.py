"""Справочные профили производителей.

Hikvision: типичный основной поток /Streaming/Channels/101
Hikvision: типичный дополнительный поток /Streaming/Channels/102
EZVIZ DP2: RTSP/ONVIF не подтверждены; облачная интеграция не входит в эту сборку.
"""
def hikvision_url(host, username, password, channel="101"):
    return f"rtsp://{username}:{password}@{host}:554/Streaming/Channels/{channel}"
