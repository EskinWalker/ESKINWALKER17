# -*- coding: utf-8 -*-

import os
import sys
import time
import ipaddress
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests


# ============================================================
# ESKINWALKER
# Local / Private HTTP Endpoint Manager
# ============================================================

APP_NAME = "ESKINWALKER"
CREATOR = "ArMin"
VERSION = "7.1"

CAMERA_FILE = "cameras.txt"
RESULT_FILE = "scan_results.txt"

TIMEOUT = 3
MAX_WORKERS = 10


# ============================================================
# ANSI THEME
# ============================================================

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

GREEN = "\033[32m"
BRIGHT_GREEN = "\033[1;32m"
DARK_GREEN = "\033[2;32m"

WHITE = "\033[37m"
BRIGHT_WHITE = "\033[1;37m"

RED = "\033[31m"
BRIGHT_RED = "\033[1;31m"


TITLE = BRIGHT_GREEN
TEXT = BRIGHT_WHITE
MUTED = DARK_GREEN
SUCCESS = BRIGHT_GREEN
ERROR = BRIGHT_RED


# ============================================================
# DATA
# ============================================================

CAMERAS = []


# ============================================================
# TERMINAL
# ============================================================

def clear():
    os.system("cls" if os.name == "nt" else "clear")


def terminal_width():
    try:
        return min(os.get_terminal_size().columns, 76)
    except OSError:
        return 76


def separator(char="─"):
    print(f"{MUTED}{char * terminal_width()}{RESET}")


def section(title):
    print()
    separator()
    print(f"{TITLE}{BOLD}{title}{RESET}")
    separator()


def pause():
    print()
    input(f"{MUTED}Press Enter to continue...{RESET}")


# ============================================================
# LOGO
# ============================================================

def logo():
    clear()

    print(f"{BRIGHT_GREEN}{BOLD}")
    print(r"""
██╗    ██╗ █████╗ ██╗     ██╗  ██╗███████╗██████╗
██║    ██║██╔══██╗██║     ██║ ██╔╝██╔════╝██╔══██╗
██║ █╗ ██║███████║██║     █████╔╝ █████╗  ██████╔╝
██║███╗██║██╔══██║██║     ██╔═██╗ ██╔══╝  ██╔══██╗
╚███╔███╔╝██║  ██║███████╗██║  ██╗███████╗██║  ██║
 ╚══╝╚══╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
""")
    print(RESET)

    print(
        f"{MUTED}                 E S K I N W A L K E R{RESET}"
    )
    print(
        f"{MUTED}              LOCAL ENDPOINT CONTROL{RESET}"
    )

    print()
    separator()


# ============================================================
# FILE MANAGEMENT
# ============================================================

def load_cameras():
    global CAMERAS

    CAMERAS.clear()

    if not os.path.exists(CAMERA_FILE):
        open(CAMERA_FILE, "a", encoding="utf-8").close()
        return

    try:
        with open(CAMERA_FILE, "r", encoding="utf-8") as file:
            for line in file:
                value = line.strip()

                if not value:
                    continue

                if value.startswith("#"):
                    continue

                if value not in CAMERAS:
                    CAMERAS.append(value)

    except OSError as exc:
        print(f"{ERROR}[ ERROR ]{RESET} Could not read {CAMERA_FILE}")
        print(f"{MUTED}{exc}{RESET}")


def save_cameras():
    try:
        with open(CAMERA_FILE, "w", encoding="utf-8") as file:
            for camera in CAMERAS:
                file.write(camera + "\n")

        return True

    except OSError as exc:
        print(f"{ERROR}[ ERROR ]{RESET} Could not save {CAMERA_FILE}")
        print(f"{MUTED}{exc}{RESET}")
        return False


# ============================================================
# URL / IP VALIDATION
# ============================================================

def extract_host(url):
    try:
        value = url.strip()

        if "://" not in value:
            return None

        from urllib.parse import urlparse

        parsed = urlparse(value)

        if parsed.scheme.lower() not in ("http", "https"):
            return None

        return parsed.hostname

    except Exception:
        return None


def is_local_host(url):
    host = extract_host(url)

    if not host:
        return False

    host_lower = host.lower()

    if host_lower == "localhost":
        return True

    try:
        ip = ipaddress.ip_address(host)

        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
        )

    except ValueError:
        return False


def validate_endpoint(url):
    host = extract_host(url)

    if not host:
        return False, "Invalid HTTP/HTTPS URL"

    if not is_local_host(url):
        return False, "Endpoint is outside local/private scope"

    return True, "OK"


# ============================================================
# STATUS HEADER
# ============================================================

def status_header():
    print(
        f"{MUTED}STATUS{RESET} "
        f"{SUCCESS}READY{RESET}"
        f"{MUTED}  |  ENDPOINTS:{RESET} "
        f"{BRIGHT_WHITE}{len(CAMERAS):04d}{RESET}"
        f"{MUTED}  |  TIME:{RESET} "
        f"{BRIGHT_WHITE}{datetime.now().strftime('%H:%M:%S')}{RESET}"
    )


# ============================================================
# PROGRESS BAR
# ============================================================

def progress_bar(current, total):
    if total <= 0:
        return

    width = 28
    filled = int((current / total) * width)

    bar = "█" * filled + "─" * (width - filled)
    percent = int((current / total) * 100)

    print(
        f"\r{MUTED}[{RESET}"
        f"{BRIGHT_GREEN}{bar}{RESET}"
        f"{MUTED}] {RESET}"
        f"{BRIGHT_WHITE}{percent:3d}%{RESET}",
        end="",
        flush=True
    )


# ============================================================
# BOOT
# ============================================================

def boot_sequence():
    logo()

    messages = [
        "Initializing endpoint database",
        "Loading local scope rules",
        "Loading HTTP engine",
        "Preparing worker pool",
        "System ready"
    ]

    for message in messages:
        print(
            f"{MUTED}[{RESET}"
            f"{BRIGHT_GREEN}+{RESET}"
            f"{MUTED}]{RESET} "
            f"{WHITE}{message}{RESET}"
        )
        time.sleep(0.08)

    print()


# ============================================================
# ENDPOINT MANAGEMENT
# ============================================================

def list_endpoints():
    header("ENDPOINT LIST")

    if not CAMERAS:
        print(f"{ERROR}No endpoints found.{RESET}")
        pause()
        return

    for index, url in enumerate(CAMERAS, start=1):
        print(
            f"{MUTED}{index:04d}{RESET}  "
            f"{WHITE}{url}{RESET}"
        )

    print()
    print(
        f"{MUTED}Total:{RESET} "
        f"{BRIGHT_WHITE}{len(CAMERAS)}{RESET}"
    )

    pause()


def count_endpoints():
    header("ENDPOINT COUNT")

    print(
        f"{MUTED}Current count:{RESET} "
        f"{BRIGHT_GREEN}{len(CAMERAS)}{RESET}"
    )

    pause()


def search_endpoints():
    header("ENDPOINT SEARCH")

    query = input(
        f"{BRIGHT_GREEN}Search > {RESET}"
    ).strip().lower()

    if not query:
        print(f"{ERROR}Search query cannot be empty.{RESET}")
        pause()
        return

    results = [
        url for url in CAMERAS
        if query in url.lower()
    ]

    print()

    if not results:
        print(f"{ERROR}[ NOT FOUND ]{RESET} No matching endpoints.")
        pause()
        return

    for index, url in enumerate(results, start=1):
        print(
            f"{BRIGHT_GREEN}{index:04d}{RESET}  "
            f"{WHITE}{url}{RESET}"
        )

    print()
    print(
        f"{MUTED}Matches:{RESET} "
        f"{BRIGHT_GREEN}{len(results)}{RESET}"
    )

    pause()


def add_endpoint():
    header("ADD ENDPOINT")

    url = input(
        f"{BRIGHT_GREEN}Endpoint > {RESET}"
    ).strip()

    if not url:
        print(f"{ERROR}[ ERROR ]{RESET} Empty endpoint.")
        pause()
        return

    valid, reason = validate_endpoint(url)

    if not valid:
        print(
            f"{ERROR}[ REJECTED ]{RESET} "
            f"{WHITE}{reason}{RESET}"
        )
        pause()
        return

    if url in CAMERAS:
        print(
            f"{ERROR}[ EXISTS ]{RESET} "
            f"Endpoint already exists."
        )
        pause()
        return

    CAMERAS.append(url)

    if save_cameras():
        print(
            f"{SUCCESS}[ ADDED ]{RESET} "
            f"{WHITE}{url}{RESET}"
        )

    pause()


def remove_endpoint():
    header("REMOVE ENDPOINT")

    if not CAMERAS:
        print(f"{ERROR}No endpoints available.{RESET}")
        pause()
        return

    for index, url in enumerate(CAMERAS, start=1):
        print(
            f"{MUTED}{index:04d}{RESET}  "
            f"{WHITE}{url}{RESET}"
        )

    print()

    choice = input(
        f"{BRIGHT_GREEN}Endpoint number > {RESET}"
    ).strip()

    try:
        index = int(choice)

        if index < 1 or index > len(CAMERAS):
            raise ValueError

    except ValueError:
        print(f"{ERROR}[ ERROR ]{RESET} Invalid number.")
        pause()
        return

    removed = CAMERAS.pop(index - 1)

    if save_cameras():
        print(
            f"{SUCCESS}[ REMOVED ]{RESET} "
            f"{WHITE}{removed}{RESET}"
        )

    pause()


# ============================================================
# HTTP CHECK
# ============================================================

def check_endpoint(url):
    valid, reason = validate_endpoint(url)

    if not valid:
        return {
            "url": url,
            "status": "SKIPPED",
            "detail": reason
        }

    try:
        response = requests.get(
            url,
            timeout=TIMEOUT,
            allow_redirects=False
        )

        return {
            "url": url,
            "status": "ONLINE",
            "code": response.status_code
        }

    except requests.exceptions.Timeout:
        return {
            "url": url,
            "status": "OFFLINE",
            "detail": "Timeout"
        }

    except requests.exceptions.ConnectionError:
        return {
            "url": url,
            "status": "OFFLINE",
            "detail": "Connection failed"
        }

    except requests.exceptions.RequestException as exc:
        return {
            "url": url,
            "status": "OFFLINE",
            "detail": str(exc)
        }

    except Exception as exc:
        return {
            "url": url,
            "status": "OFFLINE",
            "detail": str(exc)
        }


# ============================================================
# SCAN
# ============================================================

def scan_endpoints():
    header("LOCAL ENDPOINT SCAN")

    if not CAMERAS:
        print(f"{ERROR}No endpoints available.{RESET}")
        pause()
        return

    total = len(CAMERAS)

    print(
        f"{MUTED}Targets:{RESET} "
        f"{BRIGHT_WHITE}{total}{RESET}"
    )

    print(
        f"{MUTED}Workers:{RESET} "
        f"{BRIGHT_WHITE}{MAX_WORKERS}{RESET}"
    )

    print(
        f"{MUTED}Timeout:{RESET} "
        f"{BRIGHT_WHITE}{TIMEOUT}s{RESET}"
    )

    print()

    results = [None] * total
    completed = 0

    start_time = time.time()

    with ThreadPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:

        future_map = {
            executor.submit(check_endpoint, url): index
            for index, url in enumerate(CAMERAS)
        }

        for future in as_completed(future_map):
            index = future_map[future]

            try:
                result = future.result()

            except Exception as exc:
                result = {
                    "url": CAMERAS[index],
                    "status": "OFFLINE",
                    "detail": str(exc)
                }

            results[index] = result
            completed += 1

            progress_bar(completed, total)

    print("\n")

    online = 0
    offline = 0
    skipped = 0

    for result in results:
        if result["status"] == "ONLINE":
            online += 1

        elif result["status"] == "OFFLINE":
            offline += 1

        elif result["status"] == "SKIPPED":
            skipped += 1

    for result in results:
        status = result["status"]
        url = result["url"]

        if status == "ONLINE":
            code = result.get("code", "?")

            print(
                f"{SUCCESS}[ ONLINE  ]{RESET} "
                f"{WHITE}{url}{RESET} "
                f"{MUTED}HTTP {code}{RESET}"
            )

        elif status == "OFFLINE":
            detail = result.get("detail", "")

            print(
                f"{ERROR}[ OFFLINE ]{RESET} "
                f"{WHITE}{url}{RESET} "
                f"{MUTED}{detail}{RESET}"
            )

        else:
            print(
                f"{MUTED}[ SKIPPED ]{RESET} "
                f"{WHITE}{url}{RESET}"
            )

    elapsed = time.time() - start_time

    print()
    separator()

    print(
        f"{MUTED}ONLINE   :{RESET} "
        f"{SUCCESS}{online}{RESET}"
    )

    print(
        f"{MUTED}OFFLINE  :{RESET} "
        f"{ERROR}{offline}{RESET}"
    )

    print(
        f"{MUTED}SKIPPED  :{RESET} "
        f"{WHITE}{skipped}{RESET}"
    )

    print(
        f"{MUTED}TOTAL    :{RESET} "
        f"{BRIGHT_WHITE}{total}{RESET}"
    )

    print(
        f"{MUTED}TIME     :{RESET} "
        f"{BRIGHT_WHITE}{elapsed:.2f}s{RESET}"
    )

    separator()

    save_scan_results(results, elapsed)

    pause()


# ============================================================
# SAVE SCAN REPORT
# ============================================================

def save_scan_results(results, elapsed):
    try:
        with open(
            RESULT_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            file.write("=" * 70 + "\n")
            file.write("ESKINWALKER SCAN REPORT\n")
            file.write("=" * 70 + "\n")
            file.write(
                f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            )
            file.write(
                f"Total: {len(results)}\n"
            )
            file.write(
                f"Elapsed: {elapsed:.2f}s\n"
            )
            file.write("=" * 70 + "\n\n")

            for result in results:
                status = result["status"]
                url = result["url"]

                if status == "ONLINE":
                    code = result.get("code", "?")

                    file.write(
                        f"[ ONLINE ] {url} | HTTP {code}\n"
                    )

                elif status == "OFFLINE":
                    detail = result.get("detail", "")

                    file.write(
                        f"[ OFFLINE ] {url} | {detail}\n"
                    )

                else:
                    file.write(
                        f"[ SKIPPED ] {url}\n"
                    )

        print(
            f"{SUCCESS}[ SAVED ]{RESET} "
            f"{RESULT_FILE}"
        )

    except OSError as exc:
        print(
            f"{ERROR}[ ERROR ]{RESET} "
            f"Could not save scan report."
        )
        print(f"{MUTED}{exc}{RESET}")


# ============================================================
# SYSTEM INFO
# ============================================================

def system_info():
    header("SYSTEM INFORMATION")

    print(
        f"{MUTED}Application :{RESET} "
        f"{BRIGHT_WHITE}{APP_NAME}{RESET}"
    )

    print(
        f"{MUTED}Version     :{RESET} "
        f"{BRIGHT_GREEN}{VERSION}{RESET}"
    )

    print(
        f"{MUTED}Creator     :{RESET} "
        f"{BRIGHT_WHITE}{CREATOR}{RESET}"
    )

    print(
        f"{MUTED}Python      :{RESET} "
        f"{BRIGHT_WHITE}{sys.version.split()[0]}{RESET}"
    )

    print(
        f"{MUTED}Endpoints   :{RESET} "
        f"{BRIGHT_GREEN}{len(CAMERAS)}{RESET}"
    )

    print(
        f"{MUTED}Workers     :{RESET} "
        f"{BRIGHT_WHITE}{MAX_WORKERS}{RESET}"
    )

    print(
        f"{MUTED}Timeout     :{RESET} "
        f"{BRIGHT_WHITE}{TIMEOUT}s{RESET}"
    )

    print(
        f"{MUTED}Scope       :{RESET} "
        f"{BRIGHT_GREEN}LOCAL / PRIVATE / LINK-LOCAL{RESET}"
    )

    pause()


# ============================================================
# HELP
# ============================================================

def help_menu():
    header("HELP")

    print(
        f"{BRIGHT_GREEN}ESKINWALKER{RESET} "
        f"{WHITE}is a local HTTP endpoint management tool.{RESET}"
    )

    print()
    print(
        f"{MUTED}Supported targets:{RESET}"
    )

    print(
        f"{WHITE}- localhost{RESET}"
    )

    print(
        f"{WHITE}- loopback addresses{RESET}"
    )

    print(
        f"{WHITE}- private IPv4/IPv6 addresses{RESET}"
    )

    print(
        f"{WHITE}- link-local addresses{RESET}"
    )

    print()
    print(
        f"{MUTED}ONLINE:{RESET} "
        f"{WHITE}An HTTP response was received.{RESET}"
    )

    print(
        f"{MUTED}OFFLINE:{RESET} "
        f"{WHITE}The endpoint did not respond successfully.{RESET}"
    )

    print(
        f"{MUTED}SKIPPED:{RESET} "
        f"{WHITE}The endpoint is outside the supported scope.{RESET}"
    )

    print()
    print(
        f"{MUTED}Note:{RESET} "
        f"{WHITE}ONLINE does not guarantee a camera video stream.{RESET}"
    )

    pause()


# ============================================================
# MENU
# ============================================================

def show_menu():
    print()

    status_header()

    print()

    print(
        f"{MUTED}┌────────────────────────────────────────────┐{RESET}"
    )

    print(
        f"{MUTED}│{RESET} "
        f"{BRIGHT_GREEN}{BOLD}ESKINWALKER{RESET}"
        f"{MUTED} | {RESET}"
        f"{BRIGHT_WHITE}{len(CAMERAS):04d}{RESET}"
        f"{MUTED} endpoints"
        f"{' ' * max(0, 20 - len(str(len(CAMERAS))))}"
        f"│{RESET}"
    )

    print(
        f"{MUTED}├────────────────────────────────────────────┤{RESET}"
    )

    menu_items = [
        ("01", "List"),
        ("02", "Count"),
        ("03", "Search"),
        ("04", "Scan"),
        ("05", "Add"),
        ("06", "Remove"),
        ("07", "System Info"),
        ("08", "Help"),
        ("09", "Clear"),
    ]

    for number, name in menu_items:
        print(
            f"{MUTED}│{RESET} "
            f"{BRIGHT_GREEN}{number}{RESET} "
            f"{WHITE}- {name:<34}{RESET}"
            f"{MUTED}│{RESET}"
        )

    print(
        f"{MUTED}│{RESET} "
        f"{BRIGHT_RED}00{RESET} "
        f"{WHITE}- {'Exit':<34}{RESET}"
        f"{MUTED}│{RESET}"
    )

    print(
        f"{MUTED}└────────────────────────────────────────────┘{RESET}"
    )


# ============================================================
# HEADER
# ============================================================

def header(title):
    clear()

    print(
        f"{BRIGHT_GREEN}{BOLD}"
        f"ESKINWALKER"
        f"{RESET}"
        f"{WHITE}  |  {title}{RESET}"
    )

    separator()


# ============================================================
# COMMAND HANDLER
# ============================================================

def handle_command(command):
    commands = {
        "1": list_endpoints,
        "01": list_endpoints,

        "2": count_endpoints,
        "02": count_endpoints,

        "3": search_endpoints,
        "03": search_endpoints,

        "4": scan_endpoints,
        "04": scan_endpoints,

        "5": add_endpoint,
        "05": add_endpoint,

        "6": remove_endpoint,
        "06": remove_endpoint,

        "7": system_info,
        "07": system_info,

        "8": help_menu,
        "08": help_menu,

        "9": lambda: (clear(), pause()),
        "09": lambda: (clear(), pause()),
    }

    if command in commands:
        commands[command]()
        return True

    if command in ("0", "00"):
        return False

    print(
        f"{ERROR}[ ERROR ]{RESET} "
        f"Unknown command."
    )

    time.sleep(0.8)
    return True


# ============================================================
# MAIN
# ============================================================

def main():
    try:
        load_cameras()
        boot_sequence()

        while True:
            show_menu()

            command = input(
                f"\n{BRIGHT_GREEN}{BOLD}"
                f"ESKINWALKER"
                f"{RESET}{WHITE} > {RESET}"
            ).strip()

            if not handle_command(command):
                break

        clear()

        print(
            f"{BRIGHT_GREEN}{BOLD}"
            f"ESKINWALKER"
            f"{RESET}"
        )

        print(
            f"{MUTED}Session closed.{RESET}"
        )

    except KeyboardInterrupt:
        print()
        print(
            f"\n{ERROR}[ INTERRUPTED ]{RESET} "
            f"Session terminated."
        )

    except Exception as exc:
        print()
        print(
            f"{ERROR}[ FATAL ERROR ]{RESET}"
        )
        print(
            f"{MUTED}{exc}{RESET}"
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
