import platform
import subprocess
import re


def ping_site(website):
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '4', website]

    try:
        print(f"\n\033[1mPING {website}\033[0m")
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, universal_newlines=True)

        # Parse ping results
        pattern = r'Reply from \S+: bytes=\d+ time=(\d+)ms TTL=\d+'
        times = [int(match) for match in re.findall(pattern, output)]

        if not times:
            print("No valid ping responses received")
            return False

        # Display individual ping responses
        for i, time in enumerate(times, 1):
            print(f"\033[94mReply from {website}\033[0m: bytes=32 time={time}ms TTL=56")

        # Calculate statistics
        packet_loss = (4 - len(times)) / 4 * 100
        stats = {
            'min': min(times),
            'max': max(times),
            'avg': sum(times) / len(times),
            'loss': packet_loss
        }

        # Display statistics
        print(f"\n\033[1mPING STATISTICS\033[0m")
        print(f"Packets: Sent = 4, Received = {len(times)}, Lost = {4 - len(times)} ({stats['loss']:.0f}% loss)")
        print(f"Round-trip times (ms):")
        print(f"    Minimum = {stats['min']}ms, Maximum = {stats['max']}ms, Average = {stats['avg']:.1f}ms")

        return True

    except subprocess.CalledProcessError:
        print(f"\n\033[91mError: Could not reach {website}\033[0m")
        return False


if __name__ == "__main__":
    website = input("Enter website to ping: ").strip()
    website = re.sub(r'^https?://', '', website).split('/')[0]
    ping_site(website)