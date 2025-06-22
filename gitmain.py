
import os
import json
import time
import random
import threading
import queue
import itertools
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Read emails from .env (comma-separated values)
EMAILS = os.getenv("EMAILS", "").split(",")

# JSON file to store subscription URLs with verification status
URL_JSON = "email_subscription.json"

# User-Agent string to spoof
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# BEAST MODE CONFIGURATION - Ultra optimized for 1 sub/sec
MAX_THREADS = 15  # Increased for maximum throughput
RETRY_ATTEMPTS = 1  # Reduced for speed
THREAD_DELAY = 0.1  # Minimal delay between driver creation
PAGE_LOAD_TIMEOUT = 8  # Reduced timeout
ELEMENT_TIMEOUT = 5  # Reduced element wait timeout
TYPE_DELAY = 0.005  # Super fast typing
TASK_TIMEOUT = 10  # Max time per subscription task

# Proxy configuration (add your proxies here)
PROXIES = [
    # Add proxies in format: "ip:port" or "ip:port:username:password"
    # Example: "127.0.0.1:8080", "proxy.example.com:3128"
]

# Thread-safe queue for driver management
driver_queue = queue.Queue(maxsize=MAX_THREADS)
proxy_cycle = itertools.cycle(PROXIES) if PROXIES else None

# Performance tracking
performance_stats = {
    "total_attempts": 0,
    "successful": 0,
    "failed": 0,
    "start_time": None,
    "lock": threading.Lock()
}

def update_stats(success=False):
    """Update performance statistics"""
    with performance_stats["lock"]:
        performance_stats["total_attempts"] += 1
        if success:
            performance_stats["successful"] += 1
        else:
            performance_stats["failed"] += 1

def get_performance_report():
    """Get current performance metrics"""
    with performance_stats["lock"]:
        if performance_stats["start_time"]:
            elapsed = time.time() - performance_stats["start_time"]
            rate = performance_stats["successful"] / elapsed if elapsed > 0 else 0
            return {
                "elapsed": elapsed,
                "rate": rate,
                "successful": performance_stats["successful"],
                "failed": performance_stats["failed"],
                "total": performance_stats["total_attempts"]
            }
    return None

# Function to initialize Selenium WebDriver with maximum performance optimizations
def get_driver(proxy=None):
    from selenium.webdriver import Firefox as StandardFirefox
    from selenium.webdriver.firefox.service import Service
    from webdriver_manager.firefox import GeckoDriverManager
    import os
    import subprocess
    import shutil
    
    options = Options()
    # Maximum performance optimizations
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-tools")
    options.add_argument("--no-first-run")
    options.add_argument("--disable-default-apps")
    options.add_argument("--window-size=800,600")  # Smaller for speed
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-features=TranslateUI")
    options.add_argument("--disable-ipc-flooding-protection")
    options.add_argument("--memory-pressure-off")
    options.add_argument("--max_old_space_size=2048")
    options.add_argument("--disable-images")  # Disable image loading for speed
    options.add_argument("--disable-javascript")  # Disable JS for speed (re-enable if needed)
    options.add_argument("--disable-css")  # Disable CSS for speed
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-java")
    options.add_argument("--disable-flash")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-sync")
    options.add_argument("--disable-translate")
    options.add_argument("--disable-features=VizDisplayCompositor")
    
    # Set performance preferences
    options.set_preference("network.http.pipelining", True)
    options.set_preference("network.http.proxy.pipelining", True)
    options.set_preference("network.http.pipelining.maxrequests", 8)
    options.set_preference("content.notify.interval", 500000)
    options.set_preference("content.notify.ontimer", True)
    options.set_preference("content.switch.threshold", 250000)
    options.set_preference("browser.cache.memory.capacity", 65536)
    options.set_preference("browser.startup.homepage", "about:blank")
    options.set_preference("browser.startup.page", 0)
    options.set_preference("browser.cache.disk.enable", False)
    options.set_preference("browser.cache.memory.enable", False)
    options.set_preference("browser.cache.offline.enable", False)
    options.set_preference("network.http.use-cache", False)
    options.set_preference("permissions.default.image", 2)  # Block images
    options.set_preference("dom.ipc.plugins.enabled.libflashplayer.so", False)
    
    # Set proxy if provided
    if proxy:
        proxy_parts = proxy.split(":")
        if len(proxy_parts) >= 2:
            proxy_host, proxy_port = proxy_parts[0], proxy_parts[1]
            options.add_argument(f"--proxy-server=http://{proxy_host}:{proxy_port}")
    
    # Set display for headless mode (GitHub Codespaces)
    os.environ['DISPLAY'] = ':99'
    
    # GitHub/Linux compatible Firefox binary detection
    firefox_binary = None
    
    # Try standard Linux paths for Firefox
    firefox_paths = [
        "/usr/bin/firefox",
        "/usr/bin/firefox-esr",
        "/opt/firefox/firefox",
        "/snap/bin/firefox",
        "/usr/local/bin/firefox"
    ]
    
    # First try to find Firefox using which command
    try:
        firefox_binary = shutil.which('firefox')
        if firefox_binary and os.path.exists(firefox_binary):
            print(f"Found Firefox using which: {firefox_binary}")
    except:
        pass
    
    # If which didn't work, try the predefined paths
    if not firefox_binary:
        for path in firefox_paths:
            if os.path.exists(path):
                firefox_binary = path
                break
    
    if not firefox_binary:
        raise Exception("Firefox not found. Install with: sudo apt update && sudo apt install -y firefox")
    
    options.binary_location = firefox_binary
    
    # Try to find or install geckodriver
    geckodriver_binary = None
    
    # First try webdriver-manager
    try:
        geckodriver_binary = GeckoDriverManager().install()
    except Exception as e:
        print(f"webdriver-manager failed: {e}")
    
    # If webdriver-manager failed, try manual paths
    if not geckodriver_binary or not os.path.exists(geckodriver_binary):
        geckodriver_paths = [
            "/usr/bin/geckodriver",
            "/usr/local/bin/geckodriver",
            "/opt/geckodriver/geckodriver",
            "./geckodriver"
        ]
        
        # Try which command first
        try:
            geckodriver_binary = shutil.which('geckodriver')
            if geckodriver_binary and os.path.exists(geckodriver_binary):
                pass
        except:
            pass
        
        # Try predefined paths
        if not geckodriver_binary:
            for path in geckodriver_paths:
                if os.path.exists(path):
                    geckodriver_binary = path
                    break
    
    if not geckodriver_binary:
        raise Exception("Geckodriver not found. Install manually or use webdriver-manager.")
    
    try:
        service = Service(geckodriver_binary)
        # Set service timeout for faster startup
        service.start()
        driver = StandardFirefox(service=service, options=options)
        
        # Set aggressive timeouts for maximum speed
        driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
        driver.implicitly_wait(2)
        
        return driver
    except Exception as e:
        print(f"Error initializing Firefox driver: {e}")
        raise

# Optimized driver pool management
def create_driver_pool(pool_size=MAX_THREADS):
    """Create a pool of WebDriver instances with parallel creation"""
    def create_single_driver(i):
        max_attempts = 2
        for attempt in range(max_attempts):
            try:
                proxy = next(proxy_cycle) if proxy_cycle else None
                driver = get_driver(proxy)
                return driver, i
            except Exception as e:
                if attempt < max_attempts - 1:
                    time.sleep(1)
                else:
                    print(f"Failed to create driver {i+1}: {e}")
                    return None, i
    
    print("Creating driver pool in parallel...")
    with ThreadPoolExecutor(max_workers=min(pool_size, 5)) as executor:
        futures = [executor.submit(create_single_driver, i) for i in range(pool_size)]
        
        created_drivers = 0
        for future in as_completed(futures):
            try:
                driver, index = future.result(timeout=30)
                if driver:
                    driver_queue.put(driver)
                    created_drivers += 1
                    print(f"Created driver {created_drivers}/{pool_size}")
            except Exception as e:
                print(f"Driver creation error: {e}")
    
    print(f"Successfully created {created_drivers} drivers out of {pool_size}")

def get_driver_from_pool():
    """Get a driver from the pool with timeout"""
    try:
        return driver_queue.get(timeout=5)
    except queue.Empty:
        # If no driver available, create a new one quickly
        proxy = next(proxy_cycle) if proxy_cycle else None
        return get_driver(proxy)

def return_driver_to_pool(driver):
    """Return a driver to the pool"""
    try:
        driver_queue.put(driver, timeout=0.1)
    except queue.Full:
        # If pool is full, close the driver
        try:
            driver.quit()
        except:
            pass

def cleanup_driver_pool():
    """Clean up all drivers in the pool"""
    while not driver_queue.empty():
        try:
            driver = driver_queue.get_nowait()
            driver.quit()
        except:
            pass

def type_with_delay(element, text, delay=TYPE_DELAY):
    """Ultra-fast typing with minimal delay"""
    if len(text) <= 10:
        # For short text, just send it all at once
        element.send_keys(text)
    else:
        # For longer text, use minimal delay
        for char in text:
            element.send_keys(char)
            if delay > 0:
                time.sleep(delay)

# Ultra-optimized subscription function
def subscribe_email(email, url, input_fields, driver, timeout=TASK_TIMEOUT):
    """Ultra-fast subscription with minimal error handling for maximum speed"""
    try:
        start_time = time.time()
        
        # Set aggressive timeouts
        driver.set_page_load_timeout(timeout)
        driver.implicitly_wait(1)
        
        # Load page with retry
        try:
            driver.get(url)
        except Exception:
            # Quick retry
            time.sleep(0.5)
            driver.get(url)
        
        wait = WebDriverWait(driver, ELEMENT_TIMEOUT)
        
        # Speed optimization: Try most common selectors first
        common_email_selectors = [
            'input[type="email"]',
            'input[name="email"]', 
            'input[id="email"]',
            'input[placeholder*="email" i]',
            'input[class*="email" i]'
        ]
        
        # Fill email field - try common selectors first for speed
        email_filled = False
        
        # First try common selectors
        for selector in common_email_selectors:
            try:
                email_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                email_input.clear()
                type_with_delay(email_input, email)
                email_filled = True
                break
            except:
                continue
        
        # If common selectors fail, try configured ones
        if not email_filled:
            for email_field in input_fields.get("email", []):
                try:
                    email_selector = build_selector(email_field)
                    if email_selector:
                        email_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, email_selector)))
                        email_input.clear()
                        type_with_delay(email_input, email)
                        email_filled = True
                        break
                except:
                    continue
        
        if not email_filled:
            update_stats(False)
            return False

        # Handle checkboxes quickly
        for checkbox in input_fields.get("checkboxes", []):
            try:
                checkbox_selector = build_selector(checkbox)
                if checkbox_selector:
                    checkbox_button = driver.find_element(By.CSS_SELECTOR, checkbox_selector)
                    driver.execute_script("arguments[0].click();", checkbox_button)
            except:
                pass

        # Handle radio buttons quickly
        for radio in input_fields.get("radios", []):
            try:
                radio_selector = build_selector(radio)
                if radio_selector:
                    radio_button = driver.find_element(By.CSS_SELECTOR, radio_selector)
                    driver.execute_script("arguments[0].click();", radio_button)
            except:
                pass

        # Submit - try common submit selectors first
        common_submit_selectors = [
            'button[type="submit"]',
            'input[type="submit"]',
            'button[class*="submit" i]',
            'button[id*="submit" i]',
            'form button',
            '.btn-submit',
            '#submit'
        ]
        
        submit_clicked = False
        
        # Try common submit selectors first
        for selector in common_submit_selectors:
            try:
                submit_button = driver.find_element(By.CSS_SELECTOR, selector)
                driver.execute_script("arguments[0].click();", submit_button)
                submit_clicked = True
                break
            except:
                continue
        
        # If common selectors fail, try configured ones
        if not submit_clicked:
            for submit_field in input_fields.get("submit", []):
                try:
                    submit_selector = build_selector(submit_field)
                    if submit_selector:
                        submit_button = driver.find_element(By.CSS_SELECTOR, submit_selector)
                        driver.execute_script("arguments[0].click();", submit_button)
                        submit_clicked = True
                        break
                except:
                    continue

        if not submit_clicked:
            update_stats(False)
            return False

        # Minimal wait for submission
        time.sleep(0.5)
        
        elapsed = time.time() - start_time
        print(f"✅ {email} -> {url[:30]}... ({elapsed:.2f}s)")
        update_stats(True)
        return True

    except Exception as e:
        update_stats(False)
        return False

def build_selector(field):
    """Build CSS selector from field attributes"""
    selector = ''
    if 'class' in field:
        selector += f'.{field["class"]}'
    if 'id' in field:
        selector += f'#{field["id"]}'
    if 'name' in field:
        selector += f'[name="{field["name"]}"]'
    if 'value' in field:
        selector += f'[value="{field["value"]}"]'
    return selector

# Function to load subscription URLs from JSON file
def load_subscription_urls(verified_only=False, unverified_only=False):
    if not os.path.exists(URL_JSON):
        return []
    with open(URL_JSON, "r") as file:
        data = json.load(file)
        if verified_only:
            return [entry for entry in data if entry["verified"]]
        elif unverified_only:
            return [entry for entry in data if not entry["verified"]]
        return data

# Function to save subscription URLs to JSON file
def save_subscription_urls(data):
    with open(URL_JSON, "w") as file:
        json.dump(data, file, indent=4)

# Add new subscription URLs to JSON file
def add_subscription_url():
    url = input("Enter the subscription URL: ").strip()
    data = load_subscription_urls()
    data.append(
        {
            "url": url, 
            "verified": False,
            "input_fields": {
                "email": [],
                "username": [],
                "phone": [],
                "submit": [],
                "radios": [],
                "checkboxes": [],
                "selections": [],
                "wait": 0
            }
        }
    )
    save_subscription_urls(data)
    print("URL added successfully as unverified!")

# Modify subscription file (manual verification)
def modify_subscription_file():
    data = load_subscription_urls()
    for index, entry in enumerate(data):
        status = "✔ Verified" if entry["verified"] else "❌ Unverified"
        print(f"{index + 1}. {entry['url']} - {status}")

    choice = input("Enter the number to toggle verification status, or 'q' to quit: ").strip()
    if choice.lower() == 'q':
        return
    try:
        idx = int(choice) - 1
        data[idx]["verified"] = not data[idx]["verified"]
        save_subscription_urls(data)
        print("Verification status updated.")
    except (ValueError, IndexError):
        print("Invalid selection.")

# Ultra-fast subscription worker
def subscription_worker(task_queue, results_queue, thread_id):
    """Ultra-optimized worker function for maximum speed"""
    driver = None
    
    try:
        # Get dedicated driver for this worker
        driver = get_driver_from_pool()
        
        while True:
            try:
                task = task_queue.get(timeout=1)
                if task is None:  # Poison pill to stop the worker
                    break
                
                email, url, input_fields = task
                
                # Single attempt for maximum speed
                success = subscribe_email(email, url, input_fields, driver, timeout=TASK_TIMEOUT)
                results_queue.put((email, url, success))
                task_queue.task_done()
                
                # Minimal delay between tasks
                time.sleep(0.1)
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Worker {thread_id} error: {str(e)[:50]}...")
                break
                
    finally:
        if driver:
            try:
                return_driver_to_pool(driver)
            except:
                try:
                    driver.quit()
                except:
                    pass

# BEAST MODE: Ultra-fast threaded attack
def beast_mode_attack(repeat_count=1):
    """BEAST MODE: Maximum speed attack optimized for 1 sub/sec"""
    verified_urls = load_subscription_urls(verified_only=True)
    if not verified_urls:
        print("No verified URLs found.")
        return

    print(f"🔥 BEAST MODE ACTIVATED - {MAX_THREADS} threads targeting 1 sub/sec")
    print(f"📧 Emails: {len(EMAILS)}, URLs: {len(verified_urls)}, Repeats: {repeat_count}")
    
    # Reset performance tracking
    performance_stats["start_time"] = time.time()
    performance_stats["total_attempts"] = 0
    performance_stats["successful"] = 0
    performance_stats["failed"] = 0
    
    # Create driver pool in parallel
    print("Creating beast mode driver pool...")
    create_driver_pool(MAX_THREADS)
    
    for repeat in range(repeat_count):
        print(f"\n🔄 Beast Round {repeat + 1}/{repeat_count}")
        
        # Create task and result queues
        task_queue = queue.Queue()
        results_queue = queue.Queue()
        
        # Filter out known slow URLs for maximum speed
        fast_urls = []
        skip_domains = [
            "thecut.com", "uptain.de", "timeout-prone-site.com"
        ]
        
        for entry in verified_urls:
            url = entry["url"].strip()
            if not any(domain in url for domain in skip_domains):
                fast_urls.append(entry)
        
        # Populate task queue with all combinations
        total_tasks = 0
        for email in EMAILS:
            email = email.strip()
            if email:
                for entry in fast_urls:
                    url = entry["url"].strip()
                    input_fields = entry.get("input_fields", {})
                    task_queue.put((email, url, input_fields))
                    total_tasks += 1
        
        print(f"📋 Beast tasks: {total_tasks}")
        
        # Start beast workers
        threads = []
        for i in range(MAX_THREADS):
            thread = threading.Thread(
                target=subscription_worker,
                args=(task_queue, results_queue, i+1),
                daemon=True
            )
            thread.start()
            threads.append(thread)
        
        # Monitor beast performance
        completed = 0
        start_time = time.time()
        last_report = start_time
        
        while completed < total_tasks:
            try:
                email, url, success = results_queue.get(timeout=2)
                completed += 1
                
                # Real-time performance reporting
                current_time = time.time()
                if current_time - last_report >= 5:  # Report every 5 seconds
                    elapsed = current_time - start_time
                    rate = completed / elapsed if elapsed > 0 else 0
                    stats = get_performance_report()
                    if stats:
                        print(f"🚀 BEAST: {completed}/{total_tasks} | Rate: {rate:.2f}/sec | Success: {stats['successful']}")
                    last_report = current_time
                    
            except queue.Empty:
                continue
        
        # Stop workers
        for _ in range(MAX_THREADS):
            task_queue.put(None)
        
        # Wait for threads to complete
        for thread in threads:
            thread.join(timeout=1)
        
        # Final stats for this round
        elapsed = time.time() - start_time
        rate = completed / elapsed if elapsed > 0 else 0
        stats = get_performance_report()
        if stats:
            print(f"✅ Beast Round {repeat + 1}: {stats['successful']}/{total_tasks} | Rate: {rate:.2f}/sec")
        
        # Minimal delay between rounds
        if repeat < repeat_count - 1:
            print(f"⏳ Beast cooling down for 10 seconds...")
            time.sleep(10)
    
    # Final performance report
    final_stats = get_performance_report()
    if final_stats:
        print(f"\n🎉 BEAST MODE COMPLETE!")
        print(f"📊 Total time: {final_stats['elapsed']:.1f}s")
        print(f"📊 Average rate: {final_stats['rate']:.2f} subs/sec")
        print(f"📊 Success rate: {final_stats['successful']}/{final_stats['total']} ({final_stats['successful']/final_stats['total']*100:.1f}%)")
    
    # Cleanup
    cleanup_driver_pool()

# Verify mode: test unverified URLs and mark them verified if successful
def verify_mode():
    unverified_urls = load_subscription_urls(unverified_only=True)
    if not unverified_urls:
        print("No unverified URLs found.")
        return

    driver = get_driver()
    for entry in unverified_urls:
        url = entry["url"]
        for email in EMAILS:
            success = subscribe_email(email.strip(), url.strip(), entry.get("input_fields", {}), driver)
            if success:
                entry["verified"] = True
                print(f"URL verified: {url}")
                save_subscription_urls(load_subscription_urls())  # Save updated data
            else:
                print(f"URL failed verification: {url}")

    driver.quit()
    print("Verification process completed.")

# Attack mode selection
def attack_mode():
    print("Choose attack mode:")
    print("1. Legacy single-threaded")
    print("2. BEAST MODE (Recommended - 1 sub/sec target)")
    
    choice = input("Choose option (1 or 2): ").strip()
    
    if choice == "2":
        repeat_count = input("Enter number of beast cycles (default 1): ").strip()
        try:
            repeat_count = int(repeat_count) if repeat_count else 1
        except ValueError:
            repeat_count = 1
        
        beast_mode_attack(repeat_count)
    else:
        # Legacy mode
        verified_urls = load_subscription_urls(verified_only=True)
        if not verified_urls:
            print("No verified URLs found.")
            return

        driver = get_driver()
        for email in EMAILS:
            for entry in verified_urls:
                url = entry["url"]
                input_fields = entry.get("input_fields", {"email": ["email"]})
                subscribe_email(email.strip(), url.strip(), input_fields, driver)
        driver.quit()

# Main menu
def main():
    # ASCII Art Banner
    ascii_art = r"""
    _______ ___ ___  ___ _______ _______ ___     _______     _______ _______  _______ _______ ___ ___ _______ _______ 
    |   _   |   Y   )|   |       |       |   |   |   _   |   |   _   |   _   \|   _   |   _   |   Y   |   _   |   _   \
    |   1___|.  1  / |.  |.|   | |.|   | |.  |   |.  1___|   |.  1___|.  1   /|.  |   |.  |   |.      |.  1___|.  l   /
    |____   |.  _  \ |.  `-|.  |-`-|.  |-|.  |___|.  __)_    |.  __)_|.  _   \|.  |   |.  |   |. \_/  |.  __)_|.  _   1
    |:  1   |:  |   \|:  | |:  |   |:  | |:  1   |:  1   |   |:  1   |:  1    |:  1   |:  1   |:  |   |:  1   |:  |   |
    |::.. . |::.| .  |::.| |::.|   |::.| |::.. . |::.. . |   |::.. . |::.. .  |::.. . |::.. . |::.|:. |::.. . |::.|:. |
    `-------`--- ---'`---' `---'   `---' `-------`-------'   `-------`-------'`-------`-------`--- ---`-------`--- ---'
                               >>> by @b3nt3x - EmailBOB (BEAST MODE GitHub Edition)
    """
    print("\033[1;91m" + ascii_art + "\033[0m")

    verified_urls = load_subscription_urls(verified_only=True)
    unverified_urls = load_subscription_urls(unverified_only=True)

    print(f"Current verified URLs: {len(verified_urls)}")
    print(f"Current unverified URLs: {len(unverified_urls)}")
    print(f"🔥 BEAST MODE: {MAX_THREADS} threads, Target: 1 sub/sec")

    while True:
        print("\n=== 🔥 BEAST MODE SUBSCRIPTION BOT (GitHub Edition) ===")
        print("1. Add Subscription URL")
        print("2. Modify Email Subscription List")
        print("3. Verify Mode (Test Unverified URLs)")
        print("4. 🔥 BEAST MODE ATTACK (1 sub/sec)")
        print("5. Configure Beast Settings")
        print("6. GitHub Setup Instructions")
        print("7. Performance Stats")
        print("8. Exit")
        
        choice = input("Choose an option: ").strip()
        if choice == '1':
            add_subscription_url()
        elif choice == '2':
            modify_subscription_file()
        elif choice == '3':
            verify_mode()
        elif choice == '4':
            attack_mode()
        elif choice == '5':
            configure_beast_settings()
        elif choice == '6':
            show_github_setup()
        elif choice == '7':
            show_performance_stats()
        elif choice == '8':
            cleanup_driver_pool()
            break
        else:
            print("Invalid choice. Please try again.")

def configure_beast_settings():
    """Configure threading and proxy settings for maximum performance"""
    global MAX_THREADS, PROXIES, proxy_cycle, PAGE_LOAD_TIMEOUT, ELEMENT_TIMEOUT
    
    print("\n=== 🔥 BEAST MODE Configuration ===")
    print(f"Current threads: {MAX_THREADS}")
    print(f"Current proxies: {len(PROXIES)}")
    print(f"Page timeout: {PAGE_LOAD_TIMEOUT}s")
    print(f"Element timeout: {ELEMENT_TIMEOUT}s")
    
    # Configure threads
    new_threads = input(f"Enter max threads (5-25, current: {MAX_THREADS}): ").strip()
    if new_threads.isdigit() and 5 <= int(new_threads) <= 25:
        MAX_THREADS = int(new_threads)
        print(f"✅ Beast threads set to {MAX_THREADS}")
    
    # Configure timeouts
    new_timeout = input(f"Enter page timeout in seconds (5-15, current: {PAGE_LOAD_TIMEOUT}): ").strip()
    if new_timeout.isdigit() and 5 <= int(new_timeout) <= 15:
        PAGE_LOAD_TIMEOUT = int(new_timeout)
        ELEMENT_TIMEOUT = min(PAGE_LOAD_TIMEOUT - 2, 5)
        print(f"✅ Timeouts set to {PAGE_LOAD_TIMEOUT}s/{ELEMENT_TIMEOUT}s")
    
    # Configure proxies
    print("\nProxy configuration:")
    print("Enter proxies one per line (format: ip:port)")
    print("Enter empty line to finish")
    
    new_proxies = []
    while True:
        proxy = input("Proxy: ").strip()
        if not proxy:
            break
        new_proxies.append(proxy)
    
    if new_proxies:
        PROXIES.clear()
        PROXIES.extend(new_proxies)
        proxy_cycle = itertools.cycle(PROXIES)
        print(f"✅ Added {len(PROXIES)} proxies for beast mode")
    
    print("🔥 Beast configuration updated!")

def show_github_setup():
    """Show GitHub Codespaces setup instructions"""
    print("\n=== 🐙 GitHub Codespaces Beast Setup ===")
    print()
    print("1. Install Firefox and Geckodriver:")
    print("   sudo apt update")
    print("   sudo apt install -y firefox")
    print()
    print("2. Install Geckodriver:")
    print("   wget https://github.com/mozilla/geckodriver/releases/latest/download/geckodriver-v0.33.0-linux64.tar.gz")
    print("   tar -xzf geckodriver-v0.33.0-linux64.tar.gz")
    print("   sudo mv geckodriver /usr/local/bin/")
    print("   sudo chmod +x /usr/local/bin/geckodriver")
    print()
    print("3. Install Python dependencies:")
    print("   pip install selenium webdriver-manager python-dotenv")
    print()
    print("4. Create .env file with your emails:")
    print("   echo 'EMAILS=email1@example.com,email2@example.com' > .env")
    print()
    print("5. Run beast mode:")
    print("   python gitmain.py")
    print()
    print("🔥 BEAST MODE: This version targets 1 subscription per second")
    print("    with aggressive optimizations and minimal error handling.")

def show_performance_stats():
    """Show current performance statistics"""
    stats = get_performance_report()
    if stats:
        print("\n📊 BEAST MODE Performance Stats:")
        print(f"⏱️  Total time: {stats['elapsed']:.1f} seconds")
        print(f"🎯 Target rate: 1.0 subs/sec")
        print(f"🚀 Actual rate: {stats['rate']:.2f} subs/sec")
        print(f"✅ Successful: {stats['successful']}")
        print(f"❌ Failed: {stats['failed']}")
        print(f"📈 Success rate: {stats['successful']/stats['total']*100:.1f}%")
        
        if stats['rate'] >= 1.0:
            print("🔥 BEAST MODE TARGET ACHIEVED!")
        elif stats['rate'] >= 0.8:
            print("⚡ Close to beast mode target")
        else:
            print("⚠️  Consider optimizing: more threads, better URLs, or faster proxies")
    else:
        print("No performance data available. Run beast mode attack first.")

if __name__ == "__main__":
    main()
