#!/usr/bin/env python3
"""
Karai Prometheus Metrics Exporter (Port 9835)
Exposes:
1. NVIDIA GeForce RTX 5070 GPU Telemetry (VRAM, Utilization, Temp, Power, Fan, P-State)
2. Karai Host CPU & RAM Telemetry (via Win32 APIs)
3. Llama.cpp (Gemma 4 E4B Q8_0) Model Health, Slot Occupancy, Context Capacity, and Native Prometheus Metrics
"""

import ctypes
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import subprocess
import time
import urllib.request

API_KEY_PATH = r"C:\Users\Bryan\AppData\Local\Packages\4e440e29-8151-4465-b20f-fb3acb283925_et8rgxdxvrbdj\LocalCache\Local\Llama\.llama.apikey"
LLAMA_URL = "http://127.0.0.1:9931"


def get_api_key() -> str:
    try:
        with open(API_KEY_PATH, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return ""


class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


class FILETIME(ctypes.Structure):
    _fields_ = [
        ("dwLowDateTime", ctypes.c_ulong),
        ("dwHighDateTime", ctypes.c_ulong),
    ]


_last_cpu_times = None


def _ft_to_int(ft: FILETIME) -> int:
    return (ft.dwHighDateTime << 32) | ft.dwLowDateTime


def get_host_cpu_percent() -> float:
    global _last_cpu_times
    idle = FILETIME()
    kernel = FILETIME()
    user = FILETIME()
    if not ctypes.windll.kernel32.GetSystemTimes(
        ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user)
    ):
        return 0.0
    cur = (_ft_to_int(idle), _ft_to_int(kernel), _ft_to_int(user))
    if _last_cpu_times is None:
        _last_cpu_times = cur
        time.sleep(0.1)
        ctypes.windll.kernel32.GetSystemTimes(
            ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user)
        )
        cur = (_ft_to_int(idle), _ft_to_int(kernel), _ft_to_int(user))
    prev = _last_cpu_times
    _last_cpu_times = cur
    idle_diff = cur[0] - prev[0]
    total_diff = (cur[1] - prev[1]) + (cur[2] - prev[2])
    if total_diff <= 0:
        return 0.0
    busy_pct = max(0.0, min(100.0, (1.0 - (idle_diff / total_diff)) * 100.0))
    return busy_pct


def get_host_memory():
    stat = MEMORYSTATUSEX()
    stat.dwLength = ctypes.sizeof(stat)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
    total_mib = stat.ullTotalPhys / (1024 * 1024)
    avail_mib = stat.ullAvailPhys / (1024 * 1024)
    used_mib = total_mib - avail_mib
    return used_mib, total_mib, float(stat.dwMemoryLoad)


def get_gpu_metrics():
    cmd = [
        "nvidia-smi",
        "--query-gpu=name,temperature.gpu,utilization.gpu,utilization.memory,memory.used,memory.free,memory.total,power.draw,power.limit,fan.speed,pstate",
        "--format=csv,noheader,nounits",
    ]
    out = subprocess.check_output(
        cmd, encoding="utf-8", timeout=4, creationflags=0x08000000
    ).strip()
    parts = [p.strip() for p in out.split(",")]
    pstate_str = parts[10] if len(parts) > 10 else "P8"
    pstate_num = (
        int(pstate_str.replace("P", ""))
        if pstate_str.startswith("P") and pstate_str[1:].isdigit()
        else 8
    )
    return {
        "name": parts[0],
        "temp": float(parts[1] or 0),
        "util_gpu": float(parts[2] or 0),
        "util_mem": float(parts[3] or 0),
        "mem_used": float(parts[4] or 0),
        "mem_free": float(parts[5] or 0),
        "mem_total": float(parts[6] or 0),
        "power_draw": float(parts[7] or 0),
        "power_limit": float(parts[8] or 0),
        "fan_speed": float(
            parts[9] if parts[9] not in ("[N/A]", "N/A", "") else 0
        ),
        "pstate": pstate_num,
        "pstate_label": pstate_str,
    }


def fetch_json(path: str, api_key: str):
    req = urllib.request.Request(f"{LLAMA_URL}{path}")
    if api_key:
        req.add_header("Authorization", f"Bearer {api_key}")
    with urllib.request.urlopen(req, timeout=3) as resp:
        return json.loads(resp.read().decode("utf-8"))


def collect_metrics() -> str:
    lines = []

    # 1. Host CPU & Memory
    try:
        cpu_pct = get_host_cpu_percent()
        lines.append("# HELP karai_host_cpu_usage_percent Host CPU utilization percentage")
        lines.append("# TYPE karai_host_cpu_usage_percent gauge")
        lines.append(f"karai_host_cpu_usage_percent {cpu_pct:.2f}")

        used_mib, total_mib, pct = get_host_memory()
        lines.append("# HELP karai_host_memory_used_mib Host RAM used in MiB")
        lines.append("# TYPE karai_host_memory_used_mib gauge")
        lines.append(f"karai_host_memory_used_mib {used_mib:.2f}")
        lines.append("# HELP karai_host_memory_total_mib Host RAM total in MiB")
        lines.append("# TYPE karai_host_memory_total_mib gauge")
        lines.append(f"karai_host_memory_total_mib {total_mib:.2f}")
        lines.append("# HELP karai_host_memory_usage_percent Host RAM usage percentage")
        lines.append("# TYPE karai_host_memory_usage_percent gauge")
        lines.append(f"karai_host_memory_usage_percent {pct:.1f}")
    except Exception:
        pass

    # 2. GPU Metrics
    try:
        g = get_gpu_metrics()
        gpu_label = f'gpu="{g["name"]}"'
        lines.append("# HELP karai_gpu_temperature_celsius GPU temperature in Celsius")
        lines.append("# TYPE karai_gpu_temperature_celsius gauge")
        lines.append(f"karai_gpu_temperature_celsius{{{gpu_label}}} {g['temp']}")
        lines.append("# HELP karai_gpu_utilization_percent GPU core compute utilization percentage")
        lines.append("# TYPE karai_gpu_utilization_percent gauge")
        lines.append(f"karai_gpu_utilization_percent{{{gpu_label}}} {g['util_gpu']}")
        lines.append("# HELP karai_gpu_memory_controller_utilization_percent GPU memory controller utilization percentage")
        lines.append("# TYPE karai_gpu_memory_controller_utilization_percent gauge")
        lines.append(f"karai_gpu_memory_controller_utilization_percent{{{gpu_label}}} {g['util_mem']}")
        lines.append("# HELP karai_gpu_memory_used_mib GPU VRAM used in MiB")
        lines.append("# TYPE karai_gpu_memory_used_mib gauge")
        lines.append(f"karai_gpu_memory_used_mib{{{gpu_label}}} {g['mem_used']}")
        lines.append("# HELP karai_gpu_memory_free_mib GPU VRAM free in MiB")
        lines.append("# TYPE karai_gpu_memory_free_mib gauge")
        lines.append(f"karai_gpu_memory_free_mib{{{gpu_label}}} {g['mem_free']}")
        lines.append("# HELP karai_gpu_memory_total_mib GPU VRAM total in MiB")
        lines.append("# TYPE karai_gpu_memory_total_mib gauge")
        lines.append(f"karai_gpu_memory_total_mib{{{gpu_label}}} {g['mem_total']}")
        vram_pct = (g["mem_used"] / g["mem_total"] * 100.0) if g["mem_total"] > 0 else 0.0
        lines.append("# HELP karai_gpu_vram_usage_percent GPU VRAM usage percentage")
        lines.append("# TYPE karai_gpu_vram_usage_percent gauge")
        lines.append(f"karai_gpu_vram_usage_percent{{{gpu_label}}} {vram_pct:.2f}")
        lines.append("# HELP karai_gpu_power_draw_watts GPU power draw in Watts")
        lines.append("# TYPE karai_gpu_power_draw_watts gauge")
        lines.append(f"karai_gpu_power_draw_watts{{{gpu_label}}} {g['power_draw']}")
        lines.append("# HELP karai_gpu_power_limit_watts GPU power limit in Watts")
        lines.append("# TYPE karai_gpu_power_limit_watts gauge")
        lines.append(f"karai_gpu_power_limit_watts{{{gpu_label}}} {g['power_limit']}")
        lines.append("# HELP karai_gpu_fan_speed_percent GPU fan speed percentage")
        lines.append("# TYPE karai_gpu_fan_speed_percent gauge")
        lines.append(f"karai_gpu_fan_speed_percent{{{gpu_label}}} {g['fan_speed']}")
        lines.append("# HELP karai_gpu_pstate GPU performance state (0=P0 max, 8=P8 idle)")
        lines.append("# TYPE karai_gpu_pstate gauge")
        lines.append(f"karai_gpu_pstate{{{gpu_label}}} {g['pstate']}")
    except Exception:
        pass

    # 3. Llama.cpp Model & Slot State + Native Metrics
    api_key = get_api_key()
    model_up = 0
    try:
        health = fetch_json("/health", api_key)
        if health.get("status") == "ok":
            model_up = 1
    except Exception:
        model_up = 0

    model_name = "gemma-4-E4B-it-Q8_0.gguf"
    build_info = "unknown"
    total_slots = 4
    total_ctx = 16384
    try:
        props = fetch_json("/props", api_key)
        raw_path = props.get("model_path", model_name)
        model_name = raw_path.split("\\")[-1].split("/")[-1]
        build_info = props.get("build_info", "unknown")
        total_slots = int(props.get("total_slots", 4))
        total_ctx = int(props.get("default_generation_settings", {}).get("n_ctx", 16384))
    except Exception:
        pass

    lines.append("# HELP karai_model_up Whether the llama.cpp model server on Karai is healthy (1=up, 0=down)")
    lines.append("# TYPE karai_model_up gauge")
    lines.append(
        f'karai_model_up{{model="{model_name}",quantization="Q8_0",architecture="Gemma 4 E4B Multimodal",persona="Captain Jean-Luc Picard",build="{build_info}"}} {model_up}'
    )
    lines.append("# HELP karai_model_context_length_tokens Total configured context window tokens")
    lines.append("# TYPE karai_model_context_length_tokens gauge")
    lines.append(f"karai_model_context_length_tokens {total_ctx}")
    lines.append("# HELP karai_model_slots_total Total parallel inference slots")
    lines.append("# TYPE karai_model_slots_total gauge")
    lines.append(f"karai_model_slots_total {total_slots}")

    try:
        slots = fetch_json("/slots", api_key)
        if isinstance(slots, dict) and "value" in slots:
            slots = slots["value"]
        busy_count = 0
        lines.append("# HELP karai_model_slot_busy Whether a specific inference slot is currently processing (1=busy, 0=idle)")
        lines.append("# TYPE karai_model_slot_busy gauge")
        lines.append("# HELP karai_model_slot_context_tokens Context capacity of each inference slot")
        lines.append("# TYPE karai_model_slot_context_tokens gauge")
        for s in slots:
            sid = s.get("id", 0)
            busy = 1 if s.get("is_processing") else 0
            busy_count += busy
            s_ctx = int(s.get("n_ctx", 0))
            lines.append(f'karai_model_slot_busy{{slot="{sid}"}} {busy}')
            lines.append(f'karai_model_slot_context_tokens{{slot="{sid}"}} {s_ctx}')
        idle_count = max(0, len(slots) - busy_count)
        lines.append("# HELP karai_model_slots_busy Number of inference slots currently active")
        lines.append("# TYPE karai_model_slots_busy gauge")
        lines.append(f"karai_model_slots_busy {busy_count}")
        lines.append("# HELP karai_model_slots_idle Number of inference slots currently idle")
        lines.append("# TYPE karai_model_slots_idle gauge")
        lines.append(f"karai_model_slots_idle {idle_count}")
    except Exception:
        pass

    lines.append("# HELP karai_model_size_bytes Model GGUF file size in bytes")
    lines.append("# TYPE karai_model_size_bytes gauge")
    lines.append("karai_model_size_bytes 8015415464")
    lines.append("# HELP karai_model_parameters_total Total model parameters")
    lines.append("# TYPE karai_model_parameters_total gauge")
    lines.append("karai_model_parameters_total 7518069290")

    # Append native llama.cpp /metrics
    try:
        req = urllib.request.Request(f"{LLAMA_URL}/metrics")
        if api_key:
            req.add_header("Authorization", f"Bearer {api_key}")
        with urllib.request.urlopen(req, timeout=3) as resp:
            raw_metrics = resp.read().decode("utf-8").strip()
            if raw_metrics:
                lines.append(raw_metrics)
    except Exception:
        pass

    return "\n".join(lines) + "\n"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/metrics"):
            body = collect_metrics().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Karai Metrics Exporter OK\n")

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    # Prime CPU counter
    get_host_cpu_percent()
    server = HTTPServer(("0.0.0.0", 9835), Handler)
    server.serve_forever()
