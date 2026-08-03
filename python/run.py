from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


BROWSER_CLI_REPOSITORY = "git+https://github.com/lexmount/browser-cli.git"
LANGUAGE_ROOT = Path(__file__).resolve().parent
ARTIFACTS_DIR = LANGUAGE_ROOT / "artifacts"
SCREENSHOT_PATH = ARTIFACTS_DIR / "page.png"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def command_exists(command: str) -> bool:
    return shutil.which(command) is not None


def run_command(args: list[str], *, inherit: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        check=False,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={
            **os.environ,
            "PYTHONUTF8": "1",
            "PYTHONIOENCODING": "utf-8",
        },
        stdout=None if inherit else subprocess.PIPE,
        stderr=None if inherit else subprocess.PIPE,
    )


def ensure_browser_cli() -> None:
    if command_exists("browser-cli"):
        return

    if not command_exists("uv"):
        raise RuntimeError("未找到 browser-cli 或 uv。请先安装 uv：https://docs.astral.sh/uv/")

    print("首次运行：正在安装 browser-cli…")
    result = run_command(
        ["uv", "tool", "install", "--force", BROWSER_CLI_REPOSITORY],
        inherit=True,
    )
    if result.returncode != 0 or not command_exists("browser-cli"):
        raise RuntimeError("browser-cli 安装失败。")


def run_cli_json(*args: str) -> dict[str, Any]:
    result = run_command(["browser-cli", *args])
    if result.returncode != 0:
        raise RuntimeError(f"browser-cli 命令执行失败：{' '.join(args[:2])}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"browser-cli 命令未返回有效 JSON：{' '.join(args[:2])}") from error


def action_result(response: dict[str, Any]) -> dict[str, Any]:
    result = response.get("result")
    return result if isinstance(result, dict) else response


def runtime_auth_usable(status: dict[str, Any]) -> bool:
    if status.get("runtime_auth_usable") is True:
        return True
    credentials = status.get("api_key_credentials") or {}
    return credentials.get("usable_for_runtime") is True


def ensure_authorized() -> None:
    status = run_cli_json("auth", "status")
    if not runtime_auth_usable(status):
        print("首次运行：即将打开 Lexmount 网页，请在网页中确认授权。无需输入 API Key 或 Project ID。")
        login = run_command(["browser-cli", "auth", "login", "--open"], inherit=True)
        if login.returncode != 0:
            raise RuntimeError("网页授权未完成。")
        status = run_cli_json("auth", "status")

    if not runtime_auth_usable(status):
        raise RuntimeError("当前授权不能用于云端浏览器任务。")

    doctor = run_cli_json("doctor", "--json")
    if doctor.get("ready_for_browser_actions") is not True:
        raise RuntimeError("browser-cli 尚未准备好执行浏览器任务，请根据 doctor 输出修复后重试。")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="打开网页、验证 URL 与标题并保存截图。")
    parser.add_argument("--url", default="https://www.baidu.com/")
    parser.add_argument("--expected-url", default="baidu.com")
    parser.add_argument("--expected-title", default="百度一下")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ensure_browser_cli()
    ensure_authorized()
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"正在验证：{args.url}")
    session_id: str | None = None
    page: dict[str, Any] = {}
    screenshot: dict[str, Any] = {}
    cleanup = "session_not_created"
    task_error: Exception | None = None

    try:
        created = run_cli_json("session", "create")
        session = created.get("session") or {}
        session_id = session.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            raise RuntimeError("云端浏览器创建成功，但没有返回可用的 Session。")

        run_cli_json("action", "open-url", "--session-id", session_id, "--url", args.url)
        run_cli_json(
            "action", "wait-load-state", "--session-id", session_id, "--state", "complete"
        )
        run_cli_json(
            "action", "wait-url", "--session-id", session_id,
            "--url", args.expected_url, "--match", "contains",
        )
        run_cli_json(
            "action", "wait-title", "--session-id", session_id,
            "--title", args.expected_title, "--match", "contains",
        )
        page = action_result(run_cli_json("action", "page-info", "--session-id", session_id))
        screenshot = action_result(
            run_cli_json(
                "action", "screenshot", "--session-id", session_id,
                "--output", str(SCREENSHOT_PATH),
            )
        )
    except Exception as error:
        task_error = error
    finally:
        if session_id:
            try:
                closed = run_cli_json("session", "close", "--session-id", session_id)
                cleanup = (
                    "session_closed"
                    if closed.get("closed") is True
                    else "session_close_unconfirmed"
                )
            except Exception:
                cleanup = "session_close_failed"

    if task_error:
        raise RuntimeError(f"模板任务执行失败；清理状态：{cleanup}。") from task_error

    print(
        json.dumps(
            {
                "ok": True,
                "url": page.get("url", args.url),
                "title": page.get("title"),
                "screenshot": screenshot.get("path", str(SCREENSHOT_PATH)),
                "cleanup": cleanup,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from error
