from pathlib import Path
import sys
import traceback

from aurora_core import AuroraApi


SOURCE_ROOT = Path(__file__).resolve().parent
RESOURCE_ROOT = Path(getattr(sys, "_MEIPASS", SOURCE_ROOT))
RUNTIME_ROOT = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else SOURCE_ROOT
LOG_FILE = RUNTIME_ROOT / "aurorachecker.log"


def log_crash(exc: BaseException) -> None:
    message = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    try:
        LOG_FILE.write_text(message, encoding="utf-8")
    except Exception:
        pass
    print(message)


def ensure_admin_auto() -> bool:
    """Restart as admin if not already. Returns True if already admin."""
    try:
        import ctypes
        if ctypes.windll.shell32.IsUserAnAdmin():
            return True
        exe = sys.executable
        script = Path(__file__).resolve()
        if getattr(sys, "frozen", False):
            args = [exe]
            args.extend(a for a in sys.argv[1:] if a != "--auto-scan")
        else:
            args = [exe, str(script.parent / "main.py")]
            args.extend(a for a in sys.argv[1:] if a != "--auto-scan")
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", args[0], " ".join(f'"{a}"' for a in args[1:]), None, 1
        )
        return False
    except Exception:
        return True


def main() -> int:
    try:
        if not ensure_admin_auto():
            return 0  # spawned as admin, exit this non-admin instance
        try:
            import webview
        except ImportError:
            print("pywebview is not installed.")
            print("Run: pip install -r requirements.txt")
            return 1

        auto_scan = "--auto-scan" in sys.argv
        html = RESOURCE_ROOT / "ui" / "index.html"
        icon = RESOURCE_ROOT / "assets" / "app.ico"
        api = AuroraApi()
        window = webview.create_window(
            "AuroraChecker",
            html.as_uri(),
            js_api=api,
            width=1180,
            height=760,
            min_size=(980, 620),
            background_color="#07090e",
            hidden=True,
        )
        api._window = window

        def startup():
            window.show()
            window.evaluate_js("if (window.startSplashTimer) { window.startSplashTimer(); }")
            if auto_scan:
                window.evaluate_js("triggerAutoScan()")

        webview.start(func=startup, debug=False, icon=str(icon) if icon.is_file() else None)
        return 0
    except BaseException as exc:
        log_crash(exc)
        try:
            Path("C:/Users/Admin/Downloads/aurorachecker_python/crash.log").write_text(
                str(exc) + "\n" + "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
                encoding="utf-8"
            )
        except:
            pass
        return 1


if __name__ == "__main__":
    sys.exit(main())
