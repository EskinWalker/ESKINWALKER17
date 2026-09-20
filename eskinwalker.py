# -*- coding: utf-8 -*-

import os
import sys
import time
import ipaddress
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import requests
except ImportError:
    print("The 'requests' library is not installed.")
    print("Run: pip install requests")
    sys.exit(1)


# =========================================================
#                         CONFIG
# =========================================================

APP_NAME = "ESKINWALKER"
CREATOR = "ArMin"
VERSION = "7.0"

CAMERA_FILE = "cameras.txt"
RESULT_FILE = "scan_results.txt"

TIMEOUT = 3
MAX_WORKERS = 10


# =========================================================
#                         COLORS
# =========================================================

RESET = "\033[0m"

GREEN = "\033[32;1m"
RED = "\033[31;1m"
YELLOW = "\033[33;1m"
CYAN = "\033[36;1m"
BLUE = "\033[34;1m"
MAGENTA = "\033[35;1m"
WHITE = "\033[37;1m"
GRAY = "\033[90;1m"


# =========================================================
#                          DATA
# =========================================================

CAMERAS = []


# =========================================================
#                           UI
# =========================================================

def clear():
    os.system("cls" if os.name == "nt" else "clear")


def pause():
    input(f"\n{GRAY}Press Enter to continue...{RESET}")


def get_terminal_width():
    try:
        return os.get_terminal_size().columns
    except OSError:
        return 70


def separator(char="─"):
    print(
        GRAY
        + char * min(get_terminal_width(), 80)
        + RESET
    )


def section(title):
    print()
    separator()
    print(f"{CYAN}  {title}{RESET}")
    separator()


def logo():
    print(f"""
{CYAN}
███████╗███████╗██╗  ██╗██╗███╗   ██╗██╗    ██╗ █████╗ ██╗     ██╗  ██╗███████╗██████╗
██╔════╝██╔════╝██║ ██╔╝██║████╗  ██║██║    ██║██╔══██╗██║     ██║ ██╔╝██╔════╝██╔══██╗
█████╗  ███████╗█████╔╝ ██║██╔██╗ ██║██║ █╗ ██║███████║██║     █████╔╝ █████╗  ██████╔╝
██╔══╝  ╚════██║██╔═██╗ ██║██║╚██╗██║██║███╗██║██╔══██║██║     ██╔═██╗ ██╔══╝  ██╔══██╗
███████╗███████║██║  ██╗██║██║ ╚████║╚███╔███╔╝██║  ██║███████╗██║  ██╗███████╗██║  ██║
╚══════╝╚══════╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝ ╚══╝╚══╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
{RESET}
{GRAY}              Local HTTP Endpoint Manager & Scanner{RESET}
{GRAY}                      Version {VERSION} | {CREATOR}{RESET}
""")


# =========================================================
#                     FILE MANAGEMENT
# =========================================================

def load_cameras():
    global CAMERAS

    CAMERAS.clear()

    if not os.path.exists(CAMERA_FILE):
        return

    try:
        with open(
            CAMERA_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            for line in file:

                url = line.strip()

                if not url:
                    continue

                if url.startswith("#"):
                    continue

                if url not in CAMERAS:
                    CAMERAS.append(url)

    except OSError as error:
        print(
            f"{RED}Error reading file: "
            f"{error}{RESET}"
        )


def save_cameras():
    try:
        with open(
            CAMERA_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            for url in CAMERAS:
                file.write(url + "\n")

        return True

    except OSError as error:
        print(
            f"{RED}Error saving file: "
            f"{error}{RESET}"
        )

        return False


# =========================================================
#                   URL / HOST VALIDATION
# =========================================================

def extract_host(url):
    try:
        value = url.strip()

        if "://" not in value:
            value = "http://" + value

        parsed = requests.utils.urlparse(value)

        return parsed.hostname

    except Exception:
        return None


def is_local_host(host):

    if not host:
        return False

    host = host.strip().lower()

    if host == "localhost":
        return True

    try:
        ip = ipaddress.ip_address(host)

        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
        )

    except ValueError:
        # Unknown/public hostnames are rejected.
        return False


# =========================================================
#                         STATUS
# =========================================================

def status_header():

    print()

    print(
        f"{GREEN}ONLINE{RESET}   = HTTP response received"
    )

    print(
        f"{RED}OFFLINE{RESET}  = No HTTP response received"
    )

    print(
        f"{YELLOW}SKIPPED{RESET}  = Target is outside the allowed local scope"
    )

    print()


# =========================================================
#                      PROGRESS BAR
# =========================================================

def progress_bar(current, total, width=30):

    if total <= 0:
        return

    percent = current / total

    filled = int(width * percent)

    bar = (
        "█" * filled
        + "░" * (width - filled)
    )

    print(
        f"\r{CYAN}[{bar}] "
        f"{current}/{total} "
        f"({percent * 100:5.1f}%)"
        f"{RESET}",
        end="",
        flush=True
    )


# =========================================================
#                           BOOT
# =========================================================

def boot():

    clear()

    print(
        f"{CYAN}Starting {APP_NAME}...{RESET}"
    )

    print()

    steps = [
        "Loading configuration",
        "Loading local endpoints",
        "Checking scanner",
        "Preparing interface"
    ]

    for step in steps:

        print(
            f"{GRAY}[+] {step}...{RESET}"
        )

        time.sleep(0.25)

    print()

    print(
        f"{GREEN}System ready.{RESET}"
    )

    time.sleep(0.5)

    clear()

    logo()


# =========================================================
#                    ENDPOINT MANAGEMENT
# =========================================================

def show_cameras():

    section("Endpoint List")

    if not CAMERAS:

        print(
            f"{YELLOW}No endpoints have been added.{RESET}"
        )

        return

    for index, url in enumerate(
        CAMERAS,
        start=1
    ):

        print(
            f"{CYAN}{index:>3}.{RESET} "
            f"{url}"
        )

    print()

    print(
        f"{GRAY}Total: {len(CAMERAS)}{RESET}"
    )


def camera_count():

    section("Endpoint Count")

    print(
        f"{CYAN}Current count: "
        f"{WHITE}{len(CAMERAS)}"
        f"{CYAN}{RESET}"
    )


def search_camera():

    section("Search")

    if not CAMERAS:

        print(
            f"{YELLOW}The endpoint list is empty.{RESET}"
        )

        return

    query = input(
        "Search query: "
    ).strip().lower()

    if not query:

        print(
            f"{YELLOW}Search query cannot be empty.{RESET}"
        )

        return

    found = []

    for index, url in enumerate(
        CAMERAS,
        start=1
    ):

        if query in url.lower():
            found.append(
                (index, url)
            )

    print()

    if not found:

        print(
            f"{RED}No matching endpoints found.{RESET}"
        )

        return

    for index, url in found:

        print(
            f"{GREEN}{index:>3}.{RESET} "
            f"{url}"
        )

    print()

    print(
        f"{GRAY}Results: {len(found)}{RESET}"
    )


def add_camera():

    section("Add Endpoint")

    url = input(
        "Local HTTP endpoint: "
    ).strip()

    if not url:

        print(
            f"{RED}Endpoint cannot be empty.{RESET}"
        )

        return

    host = extract_host(url)

    if not is_local_host(host):

        print(
            f"{RED}"
            f"This endpoint is not within the allowed "
            f"local/private scope."
            f"{RESET}"
        )

        return

    if "://" not in url:
        url = "http://" + url

    if url in CAMERAS:

        print(
            f"{YELLOW}This endpoint already exists.{RESET}"
        )

        return

    CAMERAS.append(url)

    if save_cameras():

        print(
            f"{GREEN}Endpoint added successfully.{RESET}"
        )


def remove_camera():

    section("Remove Endpoint")

    if not CAMERAS:

        print(
            f"{YELLOW}The endpoint list is empty.{RESET}"
        )

        return

    show_cameras()

    try:

        number = int(
            input("\nEndpoint number to remove: ")
        )

        if number < 1 or number > len(CAMERAS):

            print(
                f"{RED}Invalid endpoint number.{RESET}"
            )

            return

        removed = CAMERAS.pop(
            number - 1
        )

        if save_cameras():

            print(
                f"{GREEN}Removed:{RESET} "
                f"{removed}"
            )

    except ValueError:

        print(
            f"{RED}Input must be a number.{RESET}"
        )


# =========================================================
#                        HTTP CHECK
# =========================================================

def check_camera(url):

    host = extract_host(url)

    if not is_local_host(host):

        return {
            "url": url,
            "status": "SKIPPED",
            "code": None
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

    except (
        requests.exceptions.Timeout,
        requests.exceptions.ConnectionError,
        requests.exceptions.RequestException
    ):

        return {
            "url": url,
            "status": "OFFLINE",
            "code": None
        }


# =========================================================
#                         SCANNER
# =========================================================

def scan_cameras():

    section("Starting Scan")

    if not CAMERAS:

        print(
            f"{YELLOW}"
            f"No endpoints are available for scanning."
            f"{RESET}"
        )

        return

    status_header()

    total = len(CAMERAS)

    results = [None] * total

    start_time = time.time()

    print(
        f"{CYAN}Total targets: "
        f"{total}{RESET}"
    )

    print(
        f"{CYAN}Workers: "
        f"{MAX_WORKERS}{RESET}"
    )

    print()

    with ThreadPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:

        future_map = {
            executor.submit(
                check_camera,
                url
            ): index

            for index, url in enumerate(CAMERAS)
        }

        completed = 0

        for future in as_completed(
            future_map
        ):

            index = future_map[future]

            try:

                result = future.result()

            except Exception:

                result = {
                    "url": CAMERAS[index],
                    "status": "OFFLINE",
                    "code": None
                }

            results[index] = result

            completed += 1

            progress_bar(
                completed,
                total
            )

    print("\n")

    online = []
    offline = []
    skipped = []

    for result in results:

        if result["status"] == "ONLINE":

            online.append(result)

        elif result["status"] == "OFFLINE":

            offline.append(result)

        else:

            skipped.append(result)

    # =====================================================
    #                     DISPLAY RESULTS
    # =====================================================

    print(
        f"{GREEN}ONLINE:{RESET}"
    )

    if online:

        for result in online:

            code = result["code"]

            print(
                f"  {GREEN}[ONLINE]{RESET} "
                f"{result['url']} "
                f"{GRAY}(HTTP {code}){RESET}"
            )

    else:

        print(
            f"  {GRAY}No online endpoints.{RESET}"
        )

    print()

    print(
        f"{RED}OFFLINE:{RESET}"
    )

    if offline:

        for result in offline:

            print(
                f"  {RED}[OFFLINE]{RESET} "
                f"{result['url']}"
            )

    else:

        print(
            f"  {GRAY}No offline endpoints.{RESET}"
        )

    print()

    print(
        f"{YELLOW}SKIPPED:{RESET}"
    )

    if skipped:

        for result in skipped:

            print(
                f"  {YELLOW}[SKIPPED]{RESET} "
                f"{result['url']}"
            )

    else:

        print(
            f"  {GRAY}No skipped endpoints.{RESET}"
        )

    # =====================================================
    #                     SAVE REPORT
    # =====================================================

    try:

        with open(
            RESULT_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(
                f"{APP_NAME} Scan Report\n"
            )

            file.write(
                f"Version: {VERSION}\n"
            )

            file.write(
                "Date: "
                + datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                + "\n"
            )

            file.write(
                "=" * 60
                + "\n\n"
            )

            file.write(
                "[ONLINE]\n"
            )

            for result in online:

                file.write(
                    f"{result['url']} "
                    f"(HTTP {result['code']})\n"
                )

            file.write(
                "\n[OFFLINE]\n"
            )

            for result in offline:

                file.write(
                    f"{result['url']}\n"
                )

            file.write(
                "\n[SKIPPED]\n"
            )

            for result in skipped:

                file.write(
                    f"{result['url']}\n"
                )

            file.write(
                "\n"
                + "=" * 60
                + "\n"
            )

            file.write(
                f"Total: {total}\n"
            )

            file.write(
                f"Online: {len(online)}\n"
            )

            file.write(
                f"Offline: {len(offline)}\n"
            )

            file.write(
                f"Skipped: {len(skipped)}\n"
            )

    except OSError as error:

        print(
            f"{RED}"
            f"Error saving scan report: {error}"
            f"{RESET}"
        )

    elapsed = time.time() - start_time

    # =====================================================
    #                       SUMMARY
    # =====================================================

    section("Scan Summary")

    print(
        f"{WHITE}Total    : {total}{RESET}"
    )

    print(
        f"{GREEN}ONLINE   : {len(online)}{RESET}"
    )

    print(
        f"{RED}OFFLINE  : {len(offline)}{RESET}"
    )

    print(
        f"{YELLOW}SKIPPED  : {len(skipped)}{RESET}"
    )

    print(
        f"{CYAN}Time     : {elapsed:.2f}s{RESET}"
    )

    print()

    print(
        f"{GREEN}"
        f"Report saved to {RESULT_FILE}"
        f"{RESET}"
    )


# =========================================================
#                       SYSTEM INFO
# =========================================================

def system_info():

    section("System Information")

    print(
        f"{CYAN}Application : "
        f"{WHITE}{APP_NAME}{RESET}"
    )

    print(
        f"{CYAN}Version     : "
        f"{WHITE}{VERSION}{RESET}"
    )

    print(
        f"{CYAN}Creator     : "
        f"{WHITE}{CREATOR}{RESET}"
    )

    print(
        f"{CYAN}Python      : "
        f"{WHITE}{sys.version.split()[0]}"
        f"{RESET}"
    )

    print(
        f"{CYAN}Platform    : "
        f"{WHITE}{sys.platform}"
        f"{RESET}"
    )

    print(
        f"{CYAN}Endpoints   : "
        f"{WHITE}{len(CAMERAS)}"
        f"{RESET}"
    )

    print(
        f"{CYAN}Workers     : "
        f"{WHITE}{MAX_WORKERS}"
        f"{RESET}"
    )

    print(
        f"{CYAN}Timeout     : "
        f"{WHITE}{TIMEOUT}s"
        f"{RESET}"
    )


# =========================================================
#                           HELP
# =========================================================

def help_menu():

    section("Help")

    commands = [
        ("1", "List", "Show all endpoints"),
        ("2", "Count", "Show endpoint count"),
        ("3", "Search", "Search endpoints"),
        ("4", "Scan", "Check endpoint status"),
        ("5", "Add", "Add an endpoint"),
        ("6", "Remove", "Remove an endpoint"),
        ("7", "System Info", "Show system information"),
        ("8", "Help", "Show help"),
        ("9", "Clear", "Clear the terminal"),
        ("0", "Exit", "Exit the program"),
    ]

    for number, name, description in commands:

        print(
            f"{CYAN}{number}{RESET} - "
            f"{WHITE}{name:<12}{RESET} "
            f"{GRAY}{description}{RESET}"
        )


# =========================================================
#                      CLEAR TERMINAL
# =========================================================

def clear_terminal():

    clear()
    logo()


# =========================================================
#                         SHUTDOWN
# =========================================================

def shutdown():

    print()

    print(
        f"{CYAN}Closing {APP_NAME}...{RESET}"
    )

    time.sleep(0.5)

    print(
        f"{GREEN}Goodbye.{RESET}"
    )


# =========================================================
#                     COMMAND HANDLER
# =========================================================

def handle_command(command):

    command = command.strip().lower()

    commands = {

        "1": show_cameras,
        "list": show_cameras,

        "2": camera_count,
        "count": camera_count,

        "3": search_camera,
        "search": search_camera,

        "4": scan_cameras,
        "scan": scan_cameras,

        "5": add_camera,
        "add": add_camera,

        "6": remove_camera,
        "remove": remove_camera,

        "7": system_info,
        "info": system_info,

        "8": help_menu,
        "help": help_menu,

        "9": clear_terminal,
        "clear": clear_terminal,
    }

    if command in (
        "0",
        "exit",
        "quit"
    ):

        return False

    function = commands.get(command)

    if function:

        function()

        return True

    print(
        f"{RED}Invalid command.{RESET}"
    )

    return True


# =========================================================
#                           MAIN
# =========================================================

def main():

    load_cameras()

    boot()

    while True:

        print()

        separator()

        print(
            f"{CYAN}ESKINWALKER{RESET}"
            f" | "
            f"{GRAY}{len(CAMERAS)} endpoints{RESET}"
        )

        separator()

        print(
            f"""
{CYAN}1{RESET} - List
{CYAN}2{RESET} - Count
{CYAN}3{RESET} - Search
{CYAN}4{RESET} - Scan
{CYAN}5{RESET} - Add
{CYAN}6{RESET} - Remove
{CYAN}7{RESET} - System Info
{CYAN}8{RESET} - Help
{CYAN}9{RESET} - Clear
{CYAN}0{RESET} - Exit
"""
        )

        command = input(
            f"{MAGENTA}ESKINWALKER > {RESET}"
        )

        if not handle_command(command):

            break

        pause()


# =========================================================
#                       ENTRY POINT
# =========================================================

if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        print()

        print(
            f"{YELLOW}"
            f"Program interrupted by user."
            f"{RESET}"
        )

    except Exception as error:

        print()

        print(
            f"{RED}"
            f"Unexpected error: {error}"
            f"{RESET}"
        )

    finally:

        shutdown()
