from __future__ import annotations

import socket
import struct
import time
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional


NTP_EPOCH_DELTA = 2_208_988_800
DEFAULT_TIME_SERVER = "ntp.tencent.com"
FALLBACK_TIME_SERVERS = (
    DEFAULT_TIME_SERVER,
    "time1.cloud.tencent.com",
    "time2.cloud.tencent.com",
)


class TimeSyncClient:
    def measure(self, server: str = "", timeout: float = 2.0) -> Dict[str, Any]:
        errors = []
        for host in self._candidate_servers(server):
            try:
                result = self._measure_once(host, timeout)
                result["ok"] = True
                result["checked_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
                return result
            except Exception as exc:
                errors.append(f"{host}: {exc}")

        return {
            "ok": False,
            "server": server.strip() or DEFAULT_TIME_SERVER,
            "offset_ms": None,
            "rtt_ms": None,
            "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "error": "; ".join(errors) or "time sync failed",
        }

    def _candidate_servers(self, server: str) -> Iterable[str]:
        preferred = server.strip()
        if preferred:
            yield preferred
        for fallback in FALLBACK_TIME_SERVERS:
            if fallback != preferred:
                yield fallback

    def _measure_once(self, server: str, timeout: float) -> Dict[str, Any]:
        packet = bytearray(48)
        packet[0] = 0x1B
        t1 = time.time()
        self._write_timestamp(packet, 40, t1)

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(timeout)
            sock.sendto(packet, (server, 123))
            data, address = sock.recvfrom(512)
        t4 = time.time()

        if len(data) < 48:
            raise RuntimeError("short NTP response")

        t2 = self._read_timestamp(data, 32)
        t3 = self._read_timestamp(data, 40)
        offset_seconds = ((t2 - t1) + (t3 - t4)) / 2
        rtt_seconds = (t4 - t1) - (t3 - t2)

        return {
            "server": address[0] if address else server,
            "server_name": server,
            "offset_ms": round(offset_seconds * 1000, 3),
            "rtt_ms": round(max(0.0, rtt_seconds) * 1000, 3),
        }

    def _read_timestamp(self, data: bytes, offset: int) -> float:
        seconds, fraction = struct.unpack("!II", data[offset : offset + 8])
        return seconds - NTP_EPOCH_DELTA + fraction / 2**32

    def _write_timestamp(self, packet: bytearray, offset: int, value: float) -> None:
        ntp_value = value + NTP_EPOCH_DELTA
        seconds = int(ntp_value)
        fraction = int((ntp_value - seconds) * 2**32)
        struct.pack_into("!II", packet, offset, seconds, fraction)
