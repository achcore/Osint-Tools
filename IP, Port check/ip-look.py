import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
from rich.layout import Layout


def fetch_ip_info(ip_address):
    url = f"http://ip-api.com/json/{ip_address}?fields=status,message,continent,country,regionName,city,zip,lat,lon,isp,org,as,proxy,hosting,query"
    try:
        response = requests.get(url)
        data = response.json()
        if data.get("status") == "fail":
            return None, data.get("message", "Unknown error")
        return data, None
    except Exception as e:
        return None, str(e)


def create_info_panel(data):
    location = f"{data.get('city', 'N/A')}, {data.get('regionName', 'N/A')}, {data.get('country', 'N/A')}"
    isp_info = f"{data.get('isp', 'N/A')} ({data.get('org', 'N/A')})"

    panel = Panel.fit(
        Text.from_markup(
            f"[bold]🔍 IP:[/bold] [cyan]{data.get('query', 'N/A')}[/cyan]\n"
            f"[bold]📍 Location:[/bold] {location}\n"
            f"[bold]📡 ISP:[/bold] {isp_info}\n"
            f"[bold]🌐 Continent:[/bold] {data.get('continent', 'N/A')}\n"
            f"[bold]📌 Coordinates:[/bold] {data.get('lat', 'N/A')}, {data.get('lon', 'N/A')}"
        ),
        title="[bold green]IP Information[/bold green]",
        border_style="blue",
        padding=(1, 2)
    )
    return panel


def create_details_table(data):
    table = Table(box=box.ROUNDED, show_header=False)
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")

    details = {
        "ZIP Code": data.get('zip', 'N/A'),
        "AS Number": data.get('as', 'N/A'),
        "Proxy/VPN": "✅ Yes" if data.get('proxy') else "❌ No",
        "Hosting": "✅ Yes" if data.get('hosting') else "❌ No",
        "Network": data.get('org', 'N/A')
    }

    for field, value in details.items():
        table.add_row(field, str(value))

    return table


def display_ip_info(data):
    console = Console()

    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=7)
    )

    layout["header"].update(
        Panel.fit("[bold]🌐 IP Address Lookup Tool[/bold]",
                  style="bold blue",
                  subtitle="Powered by achcore")
    )

    layout["main"].update(create_info_panel(data))
    layout["footer"].update(Panel(create_details_table(data), title="[bold]Details[/bold]"))

    console.print(layout)


def main():
    console = Console()

    console.print("\n")
    ip_address = console.input("[bold yellow]?[/bold yellow] [bold]Enter IP address to lookup: [/bold]")

    if not ip_address.strip():
        console.print("[red]Error: Please enter a valid IP address[/red]")
        return

    with console.status("[bold green]Fetching IP information...[/bold green]"):
        data, error = fetch_ip_info(ip_address)

    if error:
        console.print(f"[red]Error: {error}[/red]")
    else:
        display_ip_info(data)


if __name__ == "__main__":
    main()