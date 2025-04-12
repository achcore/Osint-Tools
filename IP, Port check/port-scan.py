import socket
import requests
import paramiko
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, BarColumn
from rich import box
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Optional

console = Console()

# Конфигурация
TIMEOUT = 2
THREADS = 50
COMMON_PORTS = [21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 993, 995, 3389, 5900, 8080]

def scan_port(ip: str, port: int) -> Optional[Dict]:
    """Сканирует один порт и возвращает информацию о сервисе"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(TIMEOUT)
            result = s.connect_ex((ip, port))
            if result == 0:
                service = get_service_name(port)
                banner = grab_banner(ip, port)
                return {
                    'port': port,
                    'service': service,
                    'banner': banner,
                    'status': 'OPEN'
                }
    except:
        pass
    return None

def get_service_name(port: int) -> str:
    """Возвращает имя сервиса для порта"""
    try:
        return socket.getservbyport(port)
    except:
        return "unknown"

def grab_banner(ip: str, port: int) -> str:
    """Пытается получить баннер сервиса"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(TIMEOUT)
            s.connect((ip, port))
            if port in [80, 443, 8080]:
                s.send(b"GET / HTTP/1.1\r\nHost: %s\r\n\r\n" % ip.encode())
            return s.recv(1024).decode(errors='ignore').strip()
    except:
        return ""

def check_http(ip: str, port: int) -> Dict:
    """Проверяет HTTP/HTTPS сервисы"""
    try:
        protocol = 'https' if port == 443 else 'http'
        url = f"{protocol}://{ip}:{port}"
        response = requests.get(url, timeout=TIMEOUT, verify=False)
        
        return {
            'status_code': response.status_code,
            'server': response.headers.get('Server', ''),
            'title': response.text[:100].split('<title>')[-1].split('</title>')[0][:50] if '<title>' in response.text else ''
        }
    except:
        return {}

def check_ssh(ip: str, port: int) -> Dict:
    """Проверяет SSH сервисы"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, port=port, username='root', password='password', timeout=TIMEOUT, banner_timeout=TIMEOUT)
        ssh.close()
        return {'auth': 'weak_credentials_possible'}
    except paramiko.AuthenticationException:
        return {'auth': 'requires_credentials'}
    except:
        return {}

def check_ftp(ip: str, port: int) -> Dict:
    """Проверяет FTP сервисы"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(TIMEOUT)
            s.connect((ip, port))
            banner = s.recv(1024).decode(errors='ignore').strip()
            return {'banner': banner, 'auth': 'required'}
    except:
        return {}

def full_scan(ip: str, ports: List[int]) -> List[Dict]:
    """Выполняет полное сканирование с проверками"""
    results = []
    
    with Progress(
        "[progress.description]{task.description}",
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        transient=True
    ) as progress:
        task = progress.add_task(f"Scanning {ip}", total=len(ports))
        
        with ThreadPoolExecutor(max_workers=THREADS) as executor:
            futures = {executor.submit(scan_port, ip, port): port for port in ports}
            
            for future in futures:
                result = future.result()
                if result:
                    port = result['port']
                    
                    # HTTP/HTTPS проверки
                    if port in [80, 443, 8080]:
                        result['http_info'] = check_http(ip, port)
                    
                    # SSH проверки
                    elif port == 22:
                        result['ssh_info'] = check_ssh(ip, port)
                    
                    # FTP проверки
                    elif port == 21:
                        result['ftp_info'] = check_ftp(ip, port)
                    
                    results.append(result)
                progress.update(task, advance=1)
    
    return sorted(results, key=lambda x: x['port'])

def display_results(ip: str, results: List[Dict]):
    """Выводит результаты в красивом формате"""
    console.print(Panel.fit(f"[bold]Scan Results for [cyan]{ip}[/cyan][/bold]", style="blue"))
    
    if not results:
        console.print("[yellow]No open ports found[/yellow]")
        return
    
    # Основная таблица с портами
    table = Table(title="Open Ports", box=box.ROUNDED)
    table.add_column("Port", style="cyan")
    table.add_column("Service", style="magenta")
    table.add_column("Banner", style="green")
    table.add_column("Details", style="yellow")
    
    for result in results:
        details = []
        
        if 'http_info' in result:
            http = result['http_info']
            details.append(f"HTTP {http.get('status_code', '')} | Server: {http.get('server', '')}")
        
        if 'ssh_info' in result:
            details.append(f"SSH: {result['ssh_info'].get('auth', '')}")
        
        if 'ftp_info' in result:
            details.append(f"FTP: {result['ftp_info'].get('banner', '')[:50]}...")
        
        table.add_row(
            str(result['port']),
            result['service'],
            result['banner'][:50] + "..." if len(result['banner']) > 50 else result['banner'],
            "\n".join(details) if details else "-"
        )
    
    console.print(table)
    
    # Вывод рекомендаций
    recommendations = []
    for result in results:
        port = result['port']
        
        if port == 22 and 'ssh_info' in result:
            recommendations.append("[yellow]SSH (22):[/yellow] Проверьте на использование слабых паролей")
        
        if port in [80, 443, 8080] and 'http_info' in result:
            recommendations.append(f"[yellow]HTTP{'S' if port == 443 else ''} ({port}):[/yellow] Проверьте {result['http_info'].get('server', '')} на уязвимости")
        
        if port == 21 and 'ftp_info' in result:
            recommendations.append("[yellow]FTP (21):[/yellow] Проверьте на анонимный доступ")
    
    if recommendations:
        console.print(Panel("\n".join(recommendations), title="[bold]Recommendations[/bold]", style="red"))

def main():
    console.print(Panel.fit("[bold green]Advanced Port Scanner[/bold green]", subtitle="HTTP/SSH/FTP checks"))
    
    ip = console.input("[bold]? Enter target IP: [/bold]")
    if not ip:
        console.print("[red]IP address is required[/red]")
        return
    
    console.print("\n[bold]Select scan type:[/bold]")
    console.print("1. Quick scan (common ports)")
    console.print("2. Full scan (1-1024)")
    choice = console.input("[bold]? Choose (1-2): [/bold]")
    
    ports = COMMON_PORTS if choice == "1" else range(1, 1025)
    
    results = full_scan(ip, ports)
    display_results(ip, results)

if __name__ == "__main__":
    main()