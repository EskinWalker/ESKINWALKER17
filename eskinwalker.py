# -*- coding: utf-8 -*-

import os
import sys
import time
import ipaddress
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

import requests


# ============================================================
# ESKINWALKER
# Local / Private HTTP Endpoint Manager
# ============================================================

APP_NAME = "ESKINWALKER"
CREATOR = "ArMin"
VERSION = "5.1"

CAMERA_FILE = "cameras.txt"
RESULT_FILE = "scan_results.txt"

TIMEOUT = 3
MAX_WORKERS = 10

CAMERAS = []


# ============================================================
# ANSI THEME
# ONLY: GREEN / RED / WHITE
# ============================================================

RESET = "\033[0m"
BOLD = "\033[1m"

# GREEN
GREEN = "\033[32m"
BRIGHT_GREEN = "\033[1;32m"

# RED
RED = "\033[31m"
BRIGHT_RED = "\033[1;31m"

# WHITE
WHITE = "\033[37m"
BRIGHT_WHITE = "\033[1;37m"


# Theme mapping
TITLE = BRIGHT_GREEN
TEXT = BRIGHT_WHITE
BORDER = GREEN
SUCCESS = BRIGHT_GREEN
ERROR = BRIGHT_RED
MUTED = WHITE


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


def separator(char="─", color=BORDER):
    print(f"{color}{char * terminal_width()}{RESET}")


def pause():
    print()
    input(
        f"{WHITE}Press Enter to continue...{RESET}"
    )


def header(title):
    clear()

    print(
        f"{BRIGHT_GREEN}{BOLD}"
        f"ESKINWALKER"
        f"{RESET}"
        f"{WHITE}  //  {title}{RESET}"
    )

    separator("═", BRIGHT_GREEN)


def section(title):
    print()

    print(
        f"{BRIGHT_GREEN}{BOLD}"
        f"┌──[ {title} ]"
        f"{RESET}"
    )

    separator("─", GREEN)


# ============================================================
# LOGO
# ============================================================

def logo():
    clear()

    print(
        f"{BRIGHT_GREEN}{BOLD}"
    )

    print(r"""
███████╗███████╗██╗  ██╗██╗███╗   ██╗██╗    ██╗ █████╗ ██╗     ██╗  ██╗███████╗██████╗
██╔════╝██╔════╝██║ ██╔╝██║████╗  ██║██║    ██║██╔══██╗██║     ██║ ██╔╝██╔════╝██╔══██╗
█████╗  ███████╗█████╔╝ ██║██╔██╗ ██║██║ █╗ ██║███████║██║     █████╔╝ █████╗  ██████╔╝
██╔══╝  ╚════██║██╔═██╗ ██║██║╚██╗██║██║███╗██║██╔══██║██║     ██╔═██╗ ██╔══╝  ██╔══██╗
███████╗███████║██║  ██╗██║██║ ╚████║╚███╔███╔╝██║  ██║███████╗██║  ██╗███████╗██║  ██║
╚══════╝╚══════╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝ ╚══╝╚══╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
""")

    print(RESET)

    print(
        f"{BRIGHT_GREEN}{BOLD}"
        f"                 E S K I N W A L K E R"
        f"{RESET}"
    )

    print(
        f"{WHITE}"
        f"                 LOCAL ENDPOINT CONTROL"
        f"{RESET}"
    )

    print()
    separator("═", BRIGHT_GREEN)


# ============================================================
# FILE MANAGEMENT
# ============================================================

def load_cameras():
    CAMERAS.clear()

    if not os.path.exists(CAMERA_FILE):
        open(
            CAMERA_FILE,
            "a",
            encoding="utf-8"
        ).close()
        return

    try:
        with open(
            CAMERA_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            for line in file:
                value = line.strip()

                if not value:
                    continue

                if value.startswith("#"):
                    continue

                if value not in CAMERAS:
                    CAMERAS.append(value)

    except OSError as exc:
        print(
            f"{ERROR}[ ERROR ]{RESET} "
            f"Could not read {CAMERA_FILE}"
        )
        print(
            f"{WHITE}{exc}{RESET}"
        )


def save_cameras():
    try:
        with open(
            CAMERA_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            for camera in CAMERAS:
                file.write(camera + "\n")

        return True

    except OSError as exc:
        print(
            f"{ERROR}[ ERROR ]{RESET} "
            f"Could not save {CAMERA_FILE}"
        )
        print(
            f"{WHITE}{exc}{RESET}"
        )

        return False


# ============================================================
# URL / IP VALIDATION
# ============================================================

def extract_host(url):
    try:
        value = url.strip()

        if "://" not in value:
            return None

        parsed = urlparse(value)

        if parsed.scheme.lower() not in (
            "http",
            "https"
        ):
            return None

        return parsed.hostname

    except Exception:
        return None


def is_local_host(url):
    host = extract_host(url)

    if not host:
        return False

    if host.lower() == "localhost":
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
# STATUS
# ============================================================

def status_header():
    print(
        f"{WHITE}STATUS{RESET} "
        f"{SUCCESS}READY{RESET}"
        f"{WHITE}  |  ENDPOINTS:{RESET} "
        f"{BRIGHT_WHITE}{len(CAMERAS):04d}{RESET}"
        f"{WHITE}  |  TIME:{RESET} "
        f"{BRIGHT_WHITE}"
        f"{datetime.now().strftime('%H:%M:%S')}"
        f"{RESET}"
    )


# ============================================================
# PROGRESS BAR
# ============================================================

def progress_bar(current, total):

    if total <= 0:
        return

    bar_width = 28

    filled = int(
        (current / total) * bar_width
    )

    bar = (
        "█" * filled
        + "─" * (bar_width - filled)
    )

    percent = int(
        (current / total) * 100
    )

    print(
        f"\r{WHITE}[{RESET}"
        f"{BRIGHT_GREEN}{bar}{RESET}"
        f"{WHITE}] {RESET}"
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
            f"{WHITE}[{RESET}"
            f"{BRIGHT_GREEN}+{RESET}"
            f"{WHITE}] "
            f"{BRIGHT_WHITE}{message}{RESET}"
        )

        time.sleep(0.08)

    print()


# ============================================================
# ENDPOINT LIST
# ============================================================

def list_endpoints():

    header("ENDPOINT LIST")

    if not CAMERAS:
        print(
            f"{ERROR}No endpoints found.{RESET}"
        )
        pause()
        return

    for index, url in enumerate(
        CAMERAS,
        start=1
    ):

        print(
            f"{BRIGHT_GREEN}{index:04d}{RESET}  "
            f"{BRIGHT_WHITE}{url}{RESET}"
        )

    print()

    print(
        f"{WHITE}Total:{RESET} "
        f"{BRIGHT_GREEN}{len(CAMERAS)}{RESET}"
    )

    pause()


# ============================================================
# COUNT
# ============================================================

def count_endpoints():

    header("ENDPOINT COUNT")

    print(
        f"{WHITE}Current count:{RESET} "
        f"{BRIGHT_GREEN}{BOLD}"
        f"{len(CAMERAS)}"
        f"{RESET}"
    )

    pause()


# ============================================================
# SEARCH
# ============================================================

def search_endpoints():

    header("ENDPOINT SEARCH")

    query = input(
        f"{BRIGHT_GREEN}{BOLD}"
        f"Search"
        f"{RESET}{WHITE} > {RESET}"
    ).strip().lower()

    if not query:
        print(
            f"{ERROR}[ ERROR ]{RESET} "
            f"Search query cannot be empty."
        )
        pause()
        return

    results = [
        url
        for url in CAMERAS
        if query in url.lower()
    ]

    print()

    if not results:
        print(
            f"{ERROR}[ NOT FOUND ]{RESET} "
            f"No matching endpoints."
        )
        pause()
        return

    for index, url in enumerate(
        results,
        start=1
    ):

        print(
            f"{BRIGHT_GREEN}{index:04d}{RESET}  "
            f"{BRIGHT_WHITE}{url}{RESET}"
        )

    print()

    print(
        f"{WHITE}Matches:{RESET} "
        f"{BRIGHT_GREEN}{len(results)}{RESET}"
    )

    pause()


# ============================================================
# ADD
# ============================================================

def add_endpoint():

    header("ADD ENDPOINT")

    url = input(
        f"{BRIGHT_GREEN}{BOLD}"
        f"Endpoint"
        f"{RESET}{WHITE} > {RESET}"
    ).strip()

    if not url:
        print(
            f"{ERROR}[ ERROR ]{RESET} "
            f"Empty endpoint."
        )
        pause()
        return

    valid, reason = validate_endpoint(url)

    if not valid:
        print(
            f"{ERROR}[ REJECTED ]{RESET} "
            f"{BRIGHT_WHITE}{reason}{RESET}"
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
            f"{BRIGHT_WHITE}{url}{RESET}"
        )

    pause()


# ============================================================
# REMOVE
# ============================================================

def remove_endpoint():

    header("REMOVE ENDPOINT")

    if not CAMERAS:
        print(
            f"{ERROR}No endpoints available.{RESET}"
        )
        pause()
        return

    for index, url in enumerate(
        CAMERAS,
        start=1
    ):

        print(
            f"{BRIGHT_GREEN}{index:04d}{RESET}  "
            f"{BRIGHT_WHITE}{url}{RESET}"
        )

    print()

    choice = input(
        f"{BRIGHT_GREEN}{BOLD}"
        f"Endpoint number"
        f"{RESET}{WHITE} > {RESET}"
    ).strip()

    try:
        index = int(choice)

        if index < 1 or index > len(CAMERAS):
            raise ValueError

    except ValueError:
        print(
            f"{ERROR}[ ERROR ]{RESET} "
            f"Invalid number."
        )
        pause()
        return

    removed = CAMERAS.pop(index - 1)

    if save_cameras():

        print(
            f"{SUCCESS}[ REMOVED ]{RESET} "
            f"{BRIGHT_WHITE}{removed}{RESET}"
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
        print(
            f"{ERROR}No endpoints available.{RESET}"
        )
        pause()
        return

    total = len(CAMERAS)

    print(
        f"{WHITE}Targets:{RESET} "
        f"{BRIGHT_WHITE}{total}{RESET}"
    )

    print(
        f"{WHITE}Workers:{RESET} "
        f"{BRIGHT_WHITE}{MAX_WORKERS}{RESET}"
    )

    print(
        f"{WHITE}Timeout:{RESET} "
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
            executor.submit(
                check_endpoint,
                url
            ): index
            for index, url
            in enumerate(CAMERAS)
        }

        for future in as_completed(
            future_map
        ):

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

            progress_bar(
                completed,
                total
            )

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

            code = result.get(
                "code",
                "?"
            )

            print(
                f"{BRIGHT_GREEN}{BOLD}"
                f"[ ONLINE  ]"
                f"{RESET} "
                f"{BRIGHT_WHITE}{url}{RESET} "
                f"{WHITE}HTTP {code}{RESET}"
            )

        elif status == "OFFLINE":

            detail = result.get(
                "detail",
                ""
            )

            print(
                f"{BRIGHT_RED}{BOLD}"
                f"[ OFFLINE ]"
                f"{RESET} "
                f"{BRIGHT_WHITE}{url}{RESET} "
                f"{WHITE}{detail}{RESET}"
            )

        else:

            print(
                f"{WHITE}{BOLD}"
                f"[ SKIPPED ]"
                f"{RESET} "
                f"{BRIGHT_WHITE}{url}{RESET}"
            )

    elapsed = time.time() - start_time

    print()
    separator("═", BRIGHT_GREEN)

    print(
        f"{WHITE}ONLINE   :{RESET} "
        f"{BRIGHT_GREEN}{BOLD}{online}{RESET}"
    )

    print(
        f"{WHITE}OFFLINE  :{RESET} "
        f"{BRIGHT_RED}{BOLD}{offline}{RESET}"
    )

    print(
        f"{WHITE}SKIPPED  :{RESET} "
        f"{BRIGHT_WHITE}{skipped}{RESET}"
    )

    print(
        f"{WHITE}TOTAL    :{RESET} "
        f"{BRIGHT_WHITE}{total}{RESET}"
    )

    print(
        f"{WHITE}TIME     :{RESET} "
        f"{BRIGHT_WHITE}{elapsed:.2f}s{RESET}"
    )

    separator("═", BRIGHT_GREEN)

    save_scan_results(
        results,
        elapsed
    )

    pause()


# ============================================================
# SAVE REPORT
# ============================================================

def save_scan_results(
    results,
    elapsed
):

    try:

        with open(
            RESULT_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(
                "=" * 70 + "\n"
            )

            file.write(
                "ESKINWALKER SCAN REPORT\n"
            )

            file.write(
                "=" * 70 + "\n"
            )

            file.write(
                "Date: "
                + datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                + "\n"
            )

            file.write(
                f"Total: {len(results)}\n"
            )

            file.write(
                f"Elapsed: {elapsed:.2f}s\n"
            )

            file.write(
                "=" * 70 + "\n\n"
            )

            for result in results:

                status = result["status"]
                url = result["url"]

                if status == "ONLINE":

                    code = result.get(
                        "code",
                        "?"
                    )

                    file.write(
                        f"[ ONLINE ] "
                        f"{url} | HTTP {code}\n"
                    )

                elif status == "OFFLINE":

                    detail = result.get(
                        "detail",
                        ""
                    )

                    file.write(
                        f"[ OFFLINE ] "
                        f"{url} | {detail}\n"
                    )

                else:

                    file.write(
                        f"[ SKIPPED ] "
                        f"{url}\n"
                    )

        print(
            f"{BRIGHT_GREEN}[ SAVED ]{RESET} "
            f"{BRIGHT_WHITE}{RESULT_FILE}{RESET}"
        )

    except OSError as exc:

        print(
            f"{ERROR}[ ERROR ]{RESET} "
            f"Could not save scan report."
        )

        print(
            f"{WHITE}{exc}{RESET}"
        )


# ============================================================
# SYSTEM INFO
# ============================================================

def system_info():

    header("SYSTEM INFORMATION")

    print(
        f"{WHITE}Application :{RESET} "
        f"{BRIGHT_WHITE}{APP_NAME}{RESET}"
    )

    print(
        f"{WHITE}Version     :{RESET} "
        f"{BRIGHT_GREEN}{VERSION}{RESET}"
    )

    print(
        f"{WHITE}Creator     :{RESET} "
        f"{BRIGHT_WHITE}{CREATOR}{RESET}"
    )

    print(
        f"{WHITE}Python      :{RESET} "
        f"{BRIGHT_WHITE}"
        f"{sys.version.split()[0]}"
        f"{RESET}"
    )

    print(
        f"{WHITE}Endpoints   :{RESET} "
        f"{BRIGHT_GREEN}{len(CAMERAS)}{RESET}"
    )

    print(
        f"{WHITE}Workers     :{RESET} "
        f"{BRIGHT_WHITE}{MAX_WORKERS}{RESET}"
    )

    print(
        f"{WHITE}Timeout     :{RESET} "
        f"{BRIGHT_WHITE}{TIMEOUT}s{RESET}"
    )

    print(
        f"{WHITE}Scope       :{RESET} "
        f"{BRIGHT_GREEN}"
        f"LOCAL / PRIVATE / LINK-LOCAL"
        f"{RESET}"
    )

    pause()


# ============================================================
# HELP
# ============================================================

def help_menu():

    header("HELP")

    print(
        f"{BRIGHT_GREEN}{BOLD}"
        f"ESKINWALKER"
        f"{RESET} "
        f"{BRIGHT_WHITE}"
        f"is a local HTTP endpoint management tool."
        f"{RESET}"
    )

    print()

    print(
        f"{WHITE}Supported targets:{RESET}"
    )

    print(
        f"{BRIGHT_WHITE}  - localhost{RESET}"
    )

    print(
        f"{BRIGHT_WHITE}  - loopback addresses{RESET}"
    )

    print(
        f"{BRIGHT_WHITE}  - private IPv4/IPv6 addresses{RESET}"
    )

    print(
        f"{BRIGHT_WHITE}  - link-local addresses{RESET}"
    )

    print()

    print(
        f"{BRIGHT_GREEN}ONLINE:{RESET} "
        f"{BRIGHT_WHITE}"
        f"An HTTP response was received."
        f"{RESET}"
    )

    print(
        f"{BRIGHT_RED}OFFLINE:{RESET} "
        f"{BRIGHT_WHITE}"
        f"The endpoint did not respond successfully."
        f"{RESET}"
    )

    print(
        f"{WHITE}SKIPPED:{RESET} "
        f"{BRIGHT_WHITE}"
        f"The endpoint is outside the supported scope."
        f"{RESET}"
    )

    print()

    print(
        f"{WHITE}Note:{RESET} "
        f"{BRIGHT_WHITE}"
        f"ONLINE does not guarantee a camera video stream."
        f"{RESET}"
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
        f"{BRIGHT_GREEN}"
        f"┌────────────────────────────────────────────┐"
        f"{RESET}"
    )

    print(
        f"{BRIGHT_GREEN}│{RESET} "
        f"{BRIGHT_GREEN}{BOLD}"
        f"ESKINWALKER"
        f"{RESET}"
        f"{WHITE} | {RESET}"
        f"{BRIGHT_WHITE}"
        f"{len(CAMERAS):04d}"
        f"{RESET}"
        f"{WHITE} endpoints"
        f"{RESET}"
        f"                      "
        f"{BRIGHT_GREEN}│{RESET}"
    )

    print(
        f"{GREEN}"
        f"├────────────────────────────────────────────┤"
        f"{RESET}"
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
            f"{BRIGHT_GREEN}│{RESET} "
            f"{BRIGHT_GREEN}{BOLD}{number}{RESET} "
            f"{BRIGHT_WHITE}- {name:<34}{RESET}"
            f"{BRIGHT_GREEN}│{RESET}"
        )

    print(
        f"{BRIGHT_GREEN}│{RESET} "
        f"{BRIGHT_RED}{BOLD}00{RESET} "
        f"{BRIGHT_WHITE}- {'Exit':<34}{RESET}"
        f"{BRIGHT_GREEN}│{RESET}"
    )

    print(
        f"{BRIGHT_GREEN}"
        f"└────────────────────────────────────────────┘"
        f"{RESET}"
    )


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

        "9": lambda: (
            clear(),
            pause()
        ),

        "09": lambda: (
            clear(),
            pause()
        ),
    }

    if command in commands:

        commands[command]()
        return True

    if command in ("0", "00"):
        return False

    print(
        f"{BRIGHT_RED}[ ERROR ]{RESET} "
        f"{BRIGHT_WHITE}Unknown command.{RESET}"
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
                f"{RESET}"
                f"{WHITE} > {RESET}"
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
            f"{WHITE}Session closed.{RESET}"
        )

    except KeyboardInterrupt:

        print()

        print(
            f"{BRIGHT_RED}[ INTERRUPTED ]{RESET} "
            f"{BRIGHT_WHITE}"
            f"Session terminated."
            f"{RESET}"
        )

    except Exception as exc:

        print()

        print(
            f"{BRIGHT_RED}[ FATAL ERROR ]{RESET}"
        )

        print(
            f"{BRIGHT_WHITE}{exc}{RESET}"
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
