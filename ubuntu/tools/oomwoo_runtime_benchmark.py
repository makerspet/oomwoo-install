#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Record and compare OOMWOO runtime resource measurements on Linux.

The collector uses only the Python standard library and Linux /proc. It can
launch a command in an isolated process session or attach to already-running
processes by command-line regular expression. Reports contain enough host and
ROS metadata to make baseline and optimization runs reviewable.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import platform
import re
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


SCHEMA = "oomwoo.runtime-benchmark/v1"
DEFAULT_EXCLUDE = r"oomwoo_runtime_benchmark\.py"
PAGE_KIB = os.sysconf("SC_PAGE_SIZE") // 1024
CLK_TCK = os.sysconf("SC_CLK_TCK")


@dataclass(frozen=True)
class ProcStat:
    ppid: int
    session_id: int
    cpu_ticks: int


@dataclass(frozen=True)
class ProcessSnapshot:
    pid: int
    name: str
    command: str
    rss_kib: int
    pss_kib: int | None
    private_kib: int | None
    shared_kib: int | None
    cpu_ticks: int


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def mib(kib: int | float | None) -> float | None:
    if kib is None:
        return None
    return round(kib / 1024.0, 2)


def read_text(path: Path, *, binary_nuls: bool = False) -> str:
    try:
        data = path.read_bytes()
    except OSError:
        return ""
    if binary_nuls:
        data = data.replace(b"\0", b" ")
    return data.decode("utf-8", errors="replace").strip("\0\n ")


def parse_kib_fields(text: str) -> dict[str, int]:
    fields: dict[str, int] = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0].endswith(":"):
            try:
                fields[parts[0][:-1]] = int(parts[1])
            except ValueError:
                continue
    return fields


def parse_proc_stat(text: str) -> ProcStat | None:
    """Parse /proc/<pid>/stat while allowing spaces and ')' in comm."""
    try:
        fields = text.rsplit(")", 1)[1].split()
        return ProcStat(
            ppid=int(fields[1]),
            session_id=int(fields[3]),
            cpu_ticks=int(fields[11]) + int(fields[12]),
        )
    except (IndexError, ValueError):
        return None


def process_name(command: str, fallback: str) -> str:
    tokens = command.split()
    for token in tokens:
        if token.startswith("__node:="):
            return token.split(":=", 1)[1]
    for token in tokens:
        if "/lib/" in token or token.endswith(".py"):
            return Path(token).name
    return Path(tokens[0]).name if tokens else fallback


def read_process(proc_root: Path, pid: int) -> ProcessSnapshot | None:
    proc_dir = proc_root / str(pid)
    stat = parse_proc_stat(read_text(proc_dir / "stat"))
    if stat is None:
        return None

    command = read_text(proc_dir / "cmdline", binary_nuls=True)
    fallback = read_text(proc_dir / "comm") or str(pid)
    rollup = parse_kib_fields(read_text(proc_dir / "smaps_rollup"))

    if rollup:
        rss_kib = rollup.get("Rss", 0)
        pss_kib: int | None = rollup.get("Pss")
        private_kib: int | None = (
            rollup.get("Private_Clean", 0) + rollup.get("Private_Dirty", 0)
        )
        shared_kib: int | None = (
            rollup.get("Shared_Clean", 0) + rollup.get("Shared_Dirty", 0)
        )
    else:
        status = parse_kib_fields(read_text(proc_dir / "status"))
        rss_kib = status.get("VmRSS", 0)
        if not rss_kib:
            try:
                statm = read_text(proc_dir / "statm").split()
                rss_kib = int(statm[1]) * PAGE_KIB
            except (IndexError, ValueError):
                rss_kib = 0
        pss_kib = None
        private_kib = None
        shared_kib = None

    return ProcessSnapshot(
        pid=pid,
        name=process_name(command, fallback),
        command=command,
        rss_kib=rss_kib,
        pss_kib=pss_kib,
        private_kib=private_kib,
        shared_kib=shared_kib,
        cpu_ticks=stat.cpu_ticks,
    )


def iter_pid_dirs(proc_root: Path) -> Iterable[tuple[int, Path]]:
    try:
        entries = proc_root.iterdir()
    except OSError:
        return
    for entry in entries:
        try:
            is_pid_dir = entry.name.isdigit() and entry.is_dir()
        except OSError:
            continue
        if is_pid_dir:
            yield int(entry.name), entry


def select_processes(
    proc_root: Path,
    *,
    session_id: int | None,
    include: re.Pattern[str] | None,
    exclude: re.Pattern[str] | None,
    own_pid: int,
) -> list[ProcessSnapshot]:
    selected: list[ProcessSnapshot] = []
    for pid, proc_dir in iter_pid_dirs(proc_root):
        if pid == own_pid:
            continue
        stat = parse_proc_stat(read_text(proc_dir / "stat"))
        if stat is None:
            continue
        command = read_text(proc_dir / "cmdline", binary_nuls=True)
        matches_session = session_id is not None and stat.session_id == session_id
        matches_pattern = include is not None and bool(include.search(command))
        if not (matches_session or matches_pattern):
            continue
        if exclude is not None and exclude.search(command):
            continue
        snapshot = read_process(proc_root, pid)
        if snapshot is not None:
            selected.append(snapshot)
    return sorted(selected, key=lambda process: process.pid)


def read_meminfo(proc_root: Path) -> dict[str, int]:
    return parse_kib_fields(read_text(proc_root / "meminfo"))


def cpu_model(proc_root: Path) -> str:
    for line in read_text(proc_root / "cpuinfo").splitlines():
        key, separator, value = line.partition(":")
        if separator and key.strip() in {"Model", "model name", "Hardware"}:
            return value.strip()
    return platform.processor() or "unknown"


def hardware_model(proc_root: Path) -> str:
    model = read_text(proc_root / "device-tree" / "model")
    return model or platform.node() or "unknown"


def parse_os_release(path: Path = Path("/etc/os-release")) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in read_text(path).splitlines():
        key, separator, value = line.partition("=")
        if separator:
            values[key] = value.strip().strip('"')
    return values


def detect_git_sha(workspace: Path | None) -> str | None:
    if workspace is None:
        return None
    try:
        result = subprocess.run(
            ["git", "-C", str(workspace), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None


def parse_metadata(entries: list[str]) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for entry in entries:
        key, separator, value = entry.partition("=")
        if not separator or not key.strip():
            raise ValueError(f"metadata must use KEY=VALUE, got {entry!r}")
        metadata[key.strip()] = value
    return metadata


def host_context(proc_root: Path) -> dict[str, Any]:
    meminfo = read_meminfo(proc_root)
    os_release = parse_os_release()
    return {
        "model": hardware_model(proc_root),
        "architecture": platform.machine(),
        "cpu_model": cpu_model(proc_root),
        "cpu_count": os.cpu_count(),
        "kernel": platform.release(),
        "os": os_release.get("PRETTY_NAME", platform.platform()),
        "total_memory_mib": mib(meminfo.get("MemTotal", 0)),
    }


def process_to_dict(
    process: ProcessSnapshot,
    *,
    previous_ticks: dict[int, int],
    elapsed: float,
) -> dict[str, Any]:
    old_ticks = previous_ticks.get(process.pid)
    cpu_percent = 0.0
    if old_ticks is not None and elapsed > 0:
        delta = max(0, process.cpu_ticks - old_ticks)
        cpu_percent = 100.0 * delta / CLK_TCK / elapsed
    return {
        "pid": process.pid,
        "name": process.name,
        "command": process.command,
        "rss_mib": mib(process.rss_kib),
        "pss_mib": mib(process.pss_kib),
        "private_mib": mib(process.private_kib),
        "shared_mib": mib(process.shared_kib),
        "cpu_percent": round(cpu_percent, 2),
    }


def make_sample(
    proc_root: Path,
    processes: list[ProcessSnapshot],
    *,
    sample_index: int,
    elapsed_since_start: float,
    previous_ticks: dict[int, int],
    cpu_elapsed: float,
) -> dict[str, Any]:
    process_rows = [
        process_to_dict(
            process,
            previous_ticks=previous_ticks,
            elapsed=cpu_elapsed,
        )
        for process in processes
    ]
    meminfo = read_meminfo(proc_root)
    total_kib = meminfo.get("MemTotal", 0)
    available_kib = meminfo.get("MemAvailable", 0)
    swap_total_kib = meminfo.get("SwapTotal", 0)
    swap_free_kib = meminfo.get("SwapFree", 0)
    pss_values = [process.pss_kib for process in processes]
    pss_available = all(value is not None for value in pss_values)

    return {
        "index": sample_index,
        "elapsed_s": round(elapsed_since_start, 3),
        "timestamp_utc": utc_now(),
        "process_count": len(process_rows),
        "total_rss_mib": mib(sum(process.rss_kib for process in processes)),
        "total_pss_mib": (
            mib(sum(value for value in pss_values if value is not None))
            if pss_available
            else None
        ),
        "total_cpu_percent": round(
            sum(process["cpu_percent"] for process in process_rows), 2
        ),
        "mem_available_mib": mib(available_kib),
        "system_used_mib": mib(max(0, total_kib - available_kib)),
        "swap_used_mib": mib(max(0, swap_total_kib - swap_free_kib)),
        "processes": sorted(
            process_rows,
            key=lambda process: process["pss_mib"] or process["rss_mib"] or 0,
            reverse=True,
        ),
    }


def summarize_samples(
    samples: list[dict[str, Any]],
    *,
    budget_mib: float,
    minimum_headroom_mib: float,
    host_total_memory_mib: float | None,
) -> dict[str, Any]:
    if not samples:
        raise ValueError("cannot summarize an empty sample set")

    pss_values = [
        sample["total_pss_mib"]
        for sample in samples
        if sample["total_pss_mib"] is not None
    ]
    peak_used = max(sample["system_used_mib"] or 0 for sample in samples)
    headroom = round(budget_mib - peak_used, 2)
    on_target_memory = (
        host_total_memory_mib is not None
        and host_total_memory_mib >= budget_mib * 0.75
        and host_total_memory_mib <= budget_mib * 1.25
    )
    passes = headroom >= minimum_headroom_mib
    budget_status = ("pass" if passes else "fail") if on_target_memory else (
        "indicative-pass" if passes else "indicative-fail"
    )

    cpu_samples = samples[1:] if len(samples) > 1 else samples
    return {
        "sample_count": len(samples),
        "max_processes": max(sample["process_count"] for sample in samples),
        "peak_total_rss_mib": max(sample["total_rss_mib"] or 0 for sample in samples),
        "peak_total_pss_mib": max(pss_values) if pss_values else None,
        "mean_total_cpu_percent": round(
            sum(sample["total_cpu_percent"] for sample in cpu_samples)
            / len(cpu_samples),
            2,
        ),
        "peak_total_cpu_percent": max(
            sample["total_cpu_percent"] for sample in samples
        ),
        "min_mem_available_mib": min(
            sample["mem_available_mib"] or 0 for sample in samples
        ),
        "peak_system_used_mib": peak_used,
        "peak_swap_used_mib": max(sample["swap_used_mib"] or 0 for sample in samples),
        "budget_assessment": {
            "target_memory_mib": budget_mib,
            "minimum_headroom_mib": minimum_headroom_mib,
            "estimated_headroom_mib": headroom,
            "status": budget_status,
            "measured_on_target_memory_class": on_target_memory,
            "note": (
                "Measured on the target memory class."
                if on_target_memory
                else "Indicative only; repeat on a target-memory board before freezing the BOM."
            ),
        },
    }


def stop_process_session(process: subprocess.Popen[Any], grace_s: float = 8.0) -> int | None:
    if process.poll() is not None:
        return process.returncode
    try:
        os.killpg(process.pid, signal.SIGINT)
    except ProcessLookupError:
        return process.poll()
    try:
        return process.wait(timeout=grace_s)
    except subprocess.TimeoutExpired:
        pass

    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return process.poll()
    try:
        return process.wait(timeout=2.0)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        return process.wait(timeout=2.0)


def normalized_command(remainder: list[str]) -> list[str]:
    if remainder and remainder[0] == "--":
        return remainder[1:]
    return remainder


def record(args: argparse.Namespace) -> int:
    proc_root = Path(args.proc_root)
    if not proc_root.is_dir():
        print(f"error: Linux procfs is required at {proc_root}", file=sys.stderr)
        return 2

    command = normalized_command(args.command)
    if not command and not args.attach_pattern:
        print("error: provide a command after '--' or use --attach-pattern", file=sys.stderr)
        return 2

    try:
        metadata = parse_metadata(args.metadata)
        include = re.compile(args.attach_pattern) if args.attach_pattern else None
        exclude = re.compile(args.exclude) if args.exclude else None
    except (ValueError, re.error) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    output = Path(args.output)
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        print(f"error: cannot create {output.parent}: {error}", file=sys.stderr)
        return 2
    workspace = Path(args.workspace).expanduser() if args.workspace else None
    host = host_context(proc_root)
    launched: subprocess.Popen[Any] | None = None
    session_id: int | None = None
    command_exit_code: int | None = None
    command_exited_during_measurement = False
    started_utc = utc_now()
    samples: list[dict[str, Any]] = []
    first_selected_process_s: float | None = None
    measurement_interrupted = False
    launch_reference = time.monotonic()

    if command:
        try:
            launched = subprocess.Popen(command, start_new_session=True)
        except OSError as error:
            print(f"error: cannot start {command[0]!r}: {error}", file=sys.stderr)
            return 2
        session_id = launched.pid

    try:
        settle_end = time.monotonic() + args.settle
        while time.monotonic() < settle_end:
            if first_selected_process_s is None:
                settling_processes = select_processes(
                    proc_root,
                    session_id=session_id,
                    include=include,
                    exclude=exclude,
                    own_pid=os.getpid(),
                )
                if settling_processes:
                    first_selected_process_s = round(
                        time.monotonic() - launch_reference, 3
                    )
            if launched is not None and launched.poll() is not None:
                command_exited_during_measurement = True
                break
            time.sleep(max(0.0, min(0.25, settle_end - time.monotonic())))

        previous_ticks: dict[int, int] = {}
        previous_sample_at = time.monotonic()
        measure_started = previous_sample_at
        sample_index = 0

        while True:
            now = time.monotonic()
            processes = select_processes(
                proc_root,
                session_id=session_id,
                include=include,
                exclude=exclude,
                own_pid=os.getpid(),
            )
            if processes and first_selected_process_s is None:
                first_selected_process_s = round(now - launch_reference, 3)
            sample = make_sample(
                proc_root,
                processes,
                sample_index=sample_index,
                elapsed_since_start=now - measure_started,
                previous_ticks=previous_ticks,
                cpu_elapsed=now - previous_sample_at,
            )
            samples.append(sample)
            previous_ticks = {process.pid: process.cpu_ticks for process in processes}
            previous_sample_at = now
            sample_index += 1

            if launched is not None and launched.poll() is not None:
                command_exited_during_measurement = True
                break
            remaining = args.duration - (time.monotonic() - measure_started)
            if remaining <= 0:
                break
            time.sleep(min(args.interval, remaining))
    except KeyboardInterrupt:
        measurement_interrupted = True
        print("measurement interrupted; writing the samples collected so far", file=sys.stderr)
    finally:
        if launched is not None:
            command_exit_code = stop_process_session(launched)

    if not samples:
        print("error: no samples were collected", file=sys.stderr)
        return 1

    actual_duration = round(samples[-1]["elapsed_s"], 3)
    report = {
        "schema": SCHEMA,
        "created_utc": utc_now(),
        "started_utc": started_utc,
        "scenario": args.scenario,
        "variant": args.variant,
        "workload": {
            "lidar_hz": args.lidar_hz,
            "scan_dropping": args.scan_dropping,
            "command": command or None,
            "attach_pattern": args.attach_pattern,
            "exclude_pattern": args.exclude,
            "settle_s": args.settle,
            "requested_duration_s": args.duration,
            "actual_duration_s": actual_duration,
            "interval_s": args.interval,
            "time_to_first_selected_process_s": first_selected_process_s,
            "command_exit_code": command_exit_code,
            "command_exited_during_measurement": command_exited_during_measurement,
            "measurement_interrupted": measurement_interrupted,
        },
        "host": host,
        "runtime": {
            "ros_distro": os.environ.get("ROS_DISTRO"),
            "rmw_implementation": os.environ.get("RMW_IMPLEMENTATION"),
            "ros_domain_id": os.environ.get("ROS_DOMAIN_ID"),
            "git_sha": args.git_sha or detect_git_sha(workspace),
            "python": platform.python_version(),
        },
        "metadata": metadata,
        "summary": summarize_samples(
            samples,
            budget_mib=args.budget_mib,
            minimum_headroom_mib=args.minimum_headroom_mib,
            host_total_memory_mib=host["total_memory_mib"],
        ),
        "samples": samples,
    }
    try:
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except OSError as error:
        print(f"error: cannot write {output}: {error}", file=sys.stderr)
        return 2

    summary = report["summary"]
    budget = summary["budget_assessment"]
    pss = summary["peak_total_pss_mib"]
    pss_text = f"{pss:.1f} MiB" if pss is not None else "unavailable"
    print(
        f"[{args.scenario}/{args.variant}] peak PSS={pss_text}, "
        f"peak RSS={summary['peak_total_rss_mib']:.1f} MiB, "
        f"mean CPU={summary['mean_total_cpu_percent']:.1f}%, "
        f"2 GiB budget={budget['status']} -> {output}"
    )
    if command_exited_during_measurement:
        print("error: launched command exited before the measurement completed", file=sys.stderr)
        return 4
    if measurement_interrupted:
        return 130
    return 0


def load_report(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as source:
        report = json.load(source)
    if report.get("schema") != SCHEMA:
        raise ValueError(f"{path} is not an {SCHEMA} report")
    return report


def nested(report: dict[str, Any], path: str) -> Any:
    value: Any = report
    for key in path.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def comparability(base: dict[str, Any], candidate: dict[str, Any]) -> list[dict[str, Any]]:
    checks = [
        ("scenario", "scenario", True),
        ("LiDAR rate", "workload.lidar_hz", True),
        ("scan dropping", "workload.scan_dropping", True),
        ("hardware model", "host.model", False),
        ("memory size", "host.total_memory_mib", False),
        ("ROS distro", "runtime.ros_distro", False),
        ("RMW", "runtime.rmw_implementation", False),
    ]
    return [
        {
            "name": name,
            "baseline": nested(base, path),
            "candidate": nested(candidate, path),
            "matches": nested(base, path) == nested(candidate, path),
            "required": required,
        }
        for name, path, required in checks
    ]


def change_percent(baseline: float | None, candidate: float | None) -> float | None:
    if baseline in (None, 0) or candidate is None:
        return None
    return round(100.0 * (candidate - baseline) / baseline, 2)


def comparison_data(base: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    metrics = [
        ("Peak PSS", "peak_total_pss_mib", "MiB", "lower"),
        ("Peak RSS", "peak_total_rss_mib", "MiB", "lower"),
        ("Mean CPU", "mean_total_cpu_percent", "%", "lower"),
        ("Peak system memory used", "peak_system_used_mib", "MiB", "lower"),
        ("Minimum memory available", "min_mem_available_mib", "MiB", "higher"),
        ("Peak swap used", "peak_swap_used_mib", "MiB", "lower"),
    ]
    rows = []
    for label, key, unit, better in metrics:
        baseline_value = base["summary"].get(key)
        candidate_value = candidate["summary"].get(key)
        rows.append(
            {
                "metric": label,
                "unit": unit,
                "better": better,
                "baseline": baseline_value,
                "candidate": candidate_value,
                "change_percent": change_percent(baseline_value, candidate_value),
            }
        )
    return {
        "schema": "oomwoo.runtime-benchmark-comparison/v1",
        "created_utc": utc_now(),
        "baseline": {
            "scenario": base["scenario"],
            "variant": base["variant"],
            "created_utc": base["created_utc"],
        },
        "candidate": {
            "scenario": candidate["scenario"],
            "variant": candidate["variant"],
            "created_utc": candidate["created_utc"],
        },
        "comparability": comparability(base, candidate),
        "metrics": rows,
        "budget_assessment": {
            "baseline": base["summary"]["budget_assessment"],
            "candidate": candidate["summary"]["budget_assessment"],
        },
    }


def display_value(value: Any, unit: str = "") -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.2f}{unit}"
    return f"{value}{unit}"


def comparison_markdown(comparison: dict[str, Any]) -> str:
    baseline = comparison["baseline"]
    candidate = comparison["candidate"]
    lines = [
        "# OOMWOO runtime benchmark comparison",
        "",
        f"Baseline: `{baseline['variant']}`. Candidate: `{candidate['variant']}`. ",
        "Negative changes are improvements for PSS, RSS, CPU, system memory, and swap.",
        "",
        "| Metric | Baseline | Candidate | Change |",
        "|---|---:|---:|---:|",
    ]
    for metric in comparison["metrics"]:
        unit = f" {metric['unit']}" if metric["unit"] else ""
        change = metric["change_percent"]
        change_text = "n/a" if change is None else f"{change:+.2f}%"
        lines.append(
            f"| {metric['metric']} | "
            f"{display_value(metric['baseline'], unit)} | "
            f"{display_value(metric['candidate'], unit)} | {change_text} |"
        )

    lines.extend(
        [
            "",
            "## Comparability",
            "",
            "| Check | Baseline | Candidate | Result |",
            "|---|---|---|---|",
        ]
    )
    for check in comparison["comparability"]:
        result = "match" if check["matches"] else (
            "required mismatch" if check["required"] else "warning"
        )
        lines.append(
            f"| {check['name']} | {display_value(check['baseline'])} | "
            f"{display_value(check['candidate'])} | {result} |"
        )

    baseline_budget = comparison["budget_assessment"]["baseline"]
    candidate_budget = comparison["budget_assessment"]["candidate"]
    lines.extend(
        [
            "",
            "## 2 GiB budget",
            "",
            f"Baseline: **{baseline_budget['status']}** "
            f"({baseline_budget['estimated_headroom_mib']:.1f} MiB estimated headroom).",
            f"Candidate: **{candidate_budget['status']}** "
            f"({candidate_budget['estimated_headroom_mib']:.1f} MiB estimated headroom).",
            "",
            "An indicative result from a larger-memory host must be repeated on a 2 GB board "
            "before changing the minimum hardware BOM.",
        ]
    )
    return "\n".join(lines) + "\n"


def compare(args: argparse.Namespace) -> int:
    try:
        baseline = load_report(Path(args.baseline))
        candidate = load_report(Path(args.candidate))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    comparison = comparison_data(baseline, candidate)
    markdown = comparison_markdown(comparison)
    try:
        if args.output:
            output = Path(args.output)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(markdown, encoding="utf-8")
            print(f"wrote {output}")
        else:
            print(markdown, end="")

        if args.json_output:
            json_output = Path(args.json_output)
            json_output.parent.mkdir(parents=True, exist_ok=True)
            json_output.write_text(
                json.dumps(comparison, indent=2) + "\n", encoding="utf-8"
            )
            print(f"wrote {json_output}")
    except OSError as error:
        print(f"error: cannot write comparison: {error}", file=sys.stderr)
        return 2

    mismatches = [
        check
        for check in comparison["comparability"]
        if check["required"] and not check["matches"]
    ]
    if args.strict and mismatches:
        print("error: required comparability checks failed", file=sys.stderr)
        return 3
    return 0


def positive_float(value: str) -> float:
    number = float(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return number


def non_negative_float(value: str) -> float:
    number = float(value)
    if number < 0:
        raise argparse.ArgumentTypeError("must be zero or greater")
    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="action", required=True)

    record_parser = subparsers.add_parser(
        "record", help="launch or attach to a workload and write a JSON report"
    )
    record_parser.add_argument("--scenario", required=True, help="idle, slam_5hz, nav, etc.")
    record_parser.add_argument("--variant", default="baseline", help="baseline or candidate name")
    record_parser.add_argument("--duration", type=positive_float, default=60.0)
    record_parser.add_argument("--interval", type=positive_float, default=2.0)
    record_parser.add_argument("--settle", type=non_negative_float, default=10.0)
    record_parser.add_argument("--output", required=True, help="JSON report path")
    record_parser.add_argument(
        "--attach-pattern", help="include already-running process command lines matching REGEX"
    )
    record_parser.add_argument(
        "--exclude", default=DEFAULT_EXCLUDE, help="exclude matching process command lines"
    )
    record_parser.add_argument("--lidar-hz", type=positive_float)
    record_parser.add_argument(
        "--scan-dropping", choices=("yes", "no", "unknown"), default="unknown"
    )
    record_parser.add_argument("--budget-mib", type=positive_float, default=2048.0)
    record_parser.add_argument(
        "--minimum-headroom-mib", type=non_negative_float, default=256.0
    )
    record_parser.add_argument(
        "--metadata", action="append", default=[], metavar="KEY=VALUE"
    )
    record_parser.add_argument("--workspace", help="workspace used to auto-detect git SHA")
    record_parser.add_argument("--git-sha", help="explicit workload git SHA")
    record_parser.add_argument(
        "--proc-root", default="/proc", help=argparse.SUPPRESS
    )
    record_parser.add_argument(
        "command", nargs=argparse.REMAINDER, help="command to launch, preceded by --"
    )
    record_parser.set_defaults(handler=record)

    compare_parser = subparsers.add_parser(
        "compare", help="compare baseline and candidate JSON reports"
    )
    compare_parser.add_argument("baseline")
    compare_parser.add_argument("candidate")
    compare_parser.add_argument("--output", help="write the Markdown comparison")
    compare_parser.add_argument("--json-output", help="write machine-readable comparison JSON")
    compare_parser.add_argument(
        "--strict", action="store_true", help="fail when scenario/workload checks differ"
    )
    compare_parser.set_defaults(handler=compare)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
