#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Tests for the dependency-free OOMWOO runtime benchmark tool."""

from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import json
import pathlib
import sys
import tempfile
import unittest


HERE = pathlib.Path(__file__).resolve().parent
TOOL = HERE.parent / "ubuntu" / "tools" / "oomwoo_runtime_benchmark.py"
SPEC = importlib.util.spec_from_file_location("oomwoo_runtime_benchmark", TOOL)
assert SPEC is not None and SPEC.loader is not None
benchmark = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = benchmark
SPEC.loader.exec_module(benchmark)


def proc_stat(pid: int, *, session: int, utime: int = 100, stime: int = 20) -> str:
    return (
        f"{pid} (ros node with ) paren) S 1 2 {session} 0 0 0 0 0 0 0 "
        f"{utime} {stime} 0 0 0 0 0 0 0 0 0\n"
    )


def write_process(
    root: pathlib.Path,
    pid: int,
    *,
    session: int,
    command: str,
    rss_kib: int = 12000,
    pss_kib: int = 8000,
) -> None:
    process = root / str(pid)
    process.mkdir()
    (process / "stat").write_text(proc_stat(pid, session=session), encoding="utf-8")
    (process / "cmdline").write_bytes(command.replace(" ", "\0").encode() + b"\0")
    (process / "comm").write_text("ros-node\n", encoding="utf-8")
    (process / "smaps_rollup").write_text(
        "\n".join(
            [
                f"Rss: {rss_kib} kB",
                f"Pss: {pss_kib} kB",
                "Private_Clean: 1000 kB",
                "Private_Dirty: 2000 kB",
                "Shared_Clean: 3000 kB",
                "Shared_Dirty: 4000 kB",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def write_host(root: pathlib.Path, available_kib: int = 1000000) -> None:
    (root / "meminfo").write_text(
        "\n".join(
            [
                "MemTotal: 2000000 kB",
                f"MemAvailable: {available_kib} kB",
                "SwapTotal: 100000 kB",
                "SwapFree: 90000 kB",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (root / "cpuinfo").write_text("model name : Test Cortex-A76\n", encoding="utf-8")
    device_tree = root / "device-tree"
    device_tree.mkdir()
    (device_tree / "model").write_bytes(b"Raspberry Pi 5 Model B Rev 1.0\0")


class ProcParsingTests(unittest.TestCase):
    def test_stat_parser_handles_spaces_and_closing_parenthesis(self) -> None:
        parsed = benchmark.parse_proc_stat(proc_stat(42, session=700, utime=33, stime=9))
        self.assertEqual(parsed.session_id, 700)
        self.assertEqual(parsed.cpu_ticks, 42)

    def test_process_reader_prefers_smaps_rollup(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            write_process(
                root,
                101,
                session=101,
                command="/opt/ros/jazzy/lib/nav2/controller_server __node:=controller",
            )

            process = benchmark.read_process(root, 101)

        self.assertEqual(process.name, "controller")
        self.assertEqual(process.rss_kib, 12000)
        self.assertEqual(process.pss_kib, 8000)
        self.assertEqual(process.private_kib, 3000)
        self.assertEqual(process.shared_kib, 7000)

    def test_selector_combines_session_and_attach_pattern(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            write_process(root, 101, session=101, command="ros2 launch runtime")
            write_process(root, 102, session=999, command="slam_toolbox --ros-args")
            write_process(root, 103, session=999, command="ros2 bag play fixture")

            selected = benchmark.select_processes(
                root,
                session_id=101,
                include=benchmark.re.compile("slam_toolbox|ros2 bag"),
                exclude=benchmark.re.compile("bag play"),
                own_pid=500,
            )

        self.assertEqual([process.pid for process in selected], [101, 102])


class ReportTests(unittest.TestCase):
    def test_budget_is_final_on_target_memory_class(self) -> None:
        samples = [
            {
                "process_count": 2,
                "total_rss_mib": 500.0,
                "total_pss_mib": 350.0,
                "total_cpu_percent": 20.0,
                "mem_available_mib": 900.0,
                "system_used_mib": 1100.0,
                "swap_used_mib": 0.0,
            }
        ]

        summary = benchmark.summarize_samples(
            samples,
            budget_mib=2048.0,
            minimum_headroom_mib=256.0,
            host_total_memory_mib=1953.0,
        )

        self.assertEqual(summary["budget_assessment"]["status"], "pass")
        self.assertTrue(summary["budget_assessment"]["measured_on_target_memory_class"])
        self.assertEqual(summary["budget_assessment"]["estimated_headroom_mib"], 948.0)

    def test_comparison_reports_memory_reduction(self) -> None:
        base = self.report("baseline", 400.0, 50.0)
        candidate = self.report("composition-candidate", 300.0, 45.0)

        comparison = benchmark.comparison_data(base, candidate)
        markdown = benchmark.comparison_markdown(comparison)

        self.assertEqual(comparison["metrics"][0]["change_percent"], -25.0)
        self.assertIn("composition-candidate", markdown)
        self.assertIn("-25.00%", markdown)
        self.assertTrue(all(check["matches"] for check in comparison["comparability"]))

    def test_strict_compare_rejects_a_different_scenario(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = pathlib.Path(temporary)
            baseline_path = temporary_path / "baseline.json"
            candidate_path = temporary_path / "candidate.json"
            markdown_path = temporary_path / "comparison.md"
            baseline_path.write_text(
                json.dumps(self.report("baseline", 400.0, 50.0)), encoding="utf-8"
            )
            candidate = self.report("composition-candidate", 300.0, 45.0)
            candidate["scenario"] = "nav_known_map"
            candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
            args = argparse.Namespace(
                baseline=str(baseline_path),
                candidate=str(candidate_path),
                output=str(markdown_path),
                json_output=None,
                strict=True,
            )

            with (
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                result = benchmark.compare(args)

            markdown = markdown_path.read_text(encoding="utf-8")

        self.assertEqual(result, 3)
        self.assertIn("required mismatch", markdown)

    def test_record_with_fake_proc_writes_self_describing_report(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = pathlib.Path(temporary)
            proc_root = temporary_path / "proc"
            proc_root.mkdir()
            write_host(proc_root)
            write_process(proc_root, 202, session=202, command="ros2 launch oomwoo runtime")
            output = temporary_path / "report.json"
            args = argparse.Namespace(
                proc_root=str(proc_root),
                command=[],
                attach_pattern="ros2 launch oomwoo",
                exclude=benchmark.DEFAULT_EXCLUDE,
                metadata=["board=pi5"],
                output=str(output),
                workspace=None,
                git_sha="abc123",
                settle=0.0,
                duration=0.01,
                interval=0.005,
                scenario="idle",
                variant="baseline",
                lidar_hz=None,
                scan_dropping="unknown",
                budget_mib=2048.0,
                minimum_headroom_mib=256.0,
            )

            with contextlib.redirect_stdout(io.StringIO()):
                result = benchmark.record(args)
            report = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(result, 0)
        self.assertEqual(report["schema"], benchmark.SCHEMA)
        self.assertEqual(report["host"]["model"], "Raspberry Pi 5 Model B Rev 1.0")
        self.assertEqual(report["runtime"]["git_sha"], "abc123")
        self.assertEqual(report["metadata"], {"board": "pi5"})
        self.assertGreaterEqual(report["summary"]["sample_count"], 2)
        self.assertEqual(report["summary"]["peak_total_pss_mib"], 7.81)

    def test_early_command_exit_is_reported_as_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = pathlib.Path(temporary)
            proc_root = temporary_path / "proc"
            proc_root.mkdir()
            write_host(proc_root)
            output = temporary_path / "early-exit.json"
            args = argparse.Namespace(
                proc_root=str(proc_root),
                command=[sys.executable, "-c", "pass"],
                attach_pattern=None,
                exclude=benchmark.DEFAULT_EXCLUDE,
                metadata=[],
                output=str(output),
                workspace=None,
                git_sha=None,
                settle=0.1,
                duration=1.0,
                interval=0.1,
                scenario="idle",
                variant="broken-launch",
                lidar_hz=None,
                scan_dropping="unknown",
                budget_mib=2048.0,
                minimum_headroom_mib=256.0,
            )

            with (
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                result = benchmark.record(args)
            report = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(result, 4)
        self.assertTrue(report["workload"]["command_exited_during_measurement"])

    @staticmethod
    def report(variant: str, pss: float, cpu: float) -> dict:
        return {
            "schema": benchmark.SCHEMA,
            "created_utc": "2026-07-22T00:00:00+00:00",
            "scenario": "slam_5hz",
            "variant": variant,
            "workload": {"lidar_hz": 5.0, "scan_dropping": "no"},
            "host": {"model": "Pi 4", "total_memory_mib": 1950.0},
            "runtime": {"ros_distro": "jazzy", "rmw_implementation": "rmw_fastrtps_cpp"},
            "summary": {
                "peak_total_pss_mib": pss,
                "peak_total_rss_mib": pss + 100.0,
                "mean_total_cpu_percent": cpu,
                "peak_system_used_mib": pss + 700.0,
                "min_mem_available_mib": 1000.0,
                "peak_swap_used_mib": 0.0,
                "budget_assessment": {
                    "target_memory_mib": 2048.0,
                    "minimum_headroom_mib": 256.0,
                    "estimated_headroom_mib": 500.0,
                    "status": "pass",
                    "measured_on_target_memory_class": True,
                    "note": "Measured on the target memory class.",
                },
            },
        }


if __name__ == "__main__":
    unittest.main()
