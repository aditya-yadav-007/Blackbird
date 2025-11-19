import socket
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os

# ---------------------------------------------
# Blackbird Lite Menu
# ---------------------------------------------
def menu():
    print("\n=== Blackbird Lite ===")
    print("1. Port Scanner")
    print("2. Webpage Downloader")
    print("3. Show Available Modules")
    print("4. Quit")
    choice = input("Choose option: ")
    return choice


# ---------------------------------------------
# 1️⃣ Port Scanner (safe + rate-limited)
# ---------------------------------------------
def port_scanner():
    target = input("Enter IP or domain: ")
    print(f"\nScanning {target} (1–1024)...")

    open_ports = []
    for port in range(1, 1025):
        try:
            s = socket.socket()
            s.settimeout(0.4)
            r = s.connect_ex((target, port))
            if r == 0:
                print(f"[+] Port {port} open")
                open_ports.append(port)
            s.close()
        except:
            pass
        time.sleep(0.05)

    print("\nScan Complete.")
    if open_ports:
        print("Open ports:", open_ports)
    else:
        print("No open ports found.")


# ---------------------------------------------
# 2️⃣ Webpage Downloader (HTML, CSS, JS)
# ---------------------------------------------
def download_website():
    url = input("Enter website URL: ")
    folder = "blackbird_download"
    os.makedirs(folder, exist_ok=True)

    print("\n[+] Downloading HTML...")
    html = requests.get(url).text

    with open(f"{folder}/index.html", "w", encoding="utf-8") as f:
        f.write(html)

    soup = BeautifulSoup(html, "html.parser")

    assets = []

    # CSS
    for link in soup.find_all("link", rel="stylesheet"):
        if link.get("href"):
            assets.append(link.get("href"))

    # JS
    for script in soup.find_all("script"):
        if script.get("src"):
            assets.append(script.get("src"))

    print(f"[+] Found {len(assets)} assets")

    for asset in assets:
        asset_url = urljoin(url, asset)
        filename = asset.replace("/", "_")

        try:
            data = requests.get(asset_url).content
            with open(f"{folder}/{filename}", "wb") as f:
                f.write(data)
            print(f"Saved: {asset}")
        except:
            print(f"Failed: {asset}")

    print("\n[✓] Download complete.")


# ---------------------------------------------
# 3️⃣ Available Modules List
# ---------------------------------------------
def module_list():
    print("\n=== Available Blackbird Modules ===")
    print("1. Port Scanner")
    print("2. Webpage Downloader")
    print("3. Coming Soon: OSINT Engine")
    print("4. Coming Soon: Service Fingerprinting")
    print("5. Coming Soon: CVE Mapping")
    print("\nDo you want to run any module? (y/n)")
    ch = input("> ").lower()

    if ch == "y":
        print("Enter module number to run:")
        num = input("> ")

        if num == "1":
            port_scanner()
        elif num == "2":
            download_website()
        else:
            print("Module not available yet.")
    else:
        print("Returning to main menu...")


# ---------------------------------------------
# Main Loop
# ---------------------------------------------
while True:
    user_choice = menu()

    if user_choice == "1":
        port_scanner()
    elif user_choice == "2":
        download_website()
    elif user_choice == "3":
        module_list()
    elif user_choice == "4":
        print("Goodbye.")
        break
    else:
        print("Invalid choice.")
