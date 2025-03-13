import time
import sys
import select
import tty
import termios
import argparse
import plotext as plt
import statistics  # For anomaly detection computations
import yaml
import os

CONFIG_FILE = "config.yaml"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            try:
                data = yaml.safe_load(f)
                return data if data else {}
            except yaml.YAMLError as e:
                print("Error loading config:", e)
    return {}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        yaml.safe_dump(config, f)

def get_key():
    """Non-blocking read of a single key from stdin."""
    dr, _, _ = select.select([sys.stdin], [], [], 0)
    if dr:
        return sys.stdin.read(1)
    return None

def read_values(filename):
    """Read float values from file, skipping blank/comment lines."""
    y_vals = []
    try:
        with open(filename, "r") as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                try:
                    y_vals.append(float(line))
                except ValueError:
                    print(f"Could not convert line: {line}")
    except FileNotFoundError:
        print(f"File '{filename}' not found.")
    return y_vals

def compute_running_average(data, avg_window):
    """Compute running average. If avg_window <= 1, pass data through."""
    if avg_window <= 1:
        return data[:]
    result = []
    for i in range(len(data)):
        start = max(0, i - avg_window + 1)
        subset = data[start : i + 1]
        result.append(sum(subset) / len(subset))
    return result

def parse_args():
    parser = argparse.ArgumentParser(
        description="Plot a moving window of data with running average and interactive line toggles."
    )
    parser.add_argument("-w", "--window", type=int, default=10,
                        help="Initial number of points in the moving window (default: 10)")
    parser.add_argument("-f", "--file", type=str, default="data.txt",
                        help="Path to the data file (default: data.txt)")
    parser.add_argument("-i", "--interval", type=float, default=2,
                        help="Refresh interval in seconds (default: 2)")
    parser.add_argument("-a", "--avg-window", type=int, default=5,
                        help="Window size for running average (default: 5)")
    return parser.parse_args()

def main():
    args = parse_args()
    filename = args.file

    config = load_config()
    window_size         = config.get("window_size", args.window)
    avg_window          = config.get("avg_window", args.avg_window)
    anomaly_threshold   = config.get("anomaly_threshold", 3)
    anomaly_window_size = config.get("anomaly_window_size", 10)
    ra_ad_threshold     = config.get("ra_ad_threshold", 3)
    ra_ad_window_size   = config.get("ra_ad_window_size", 10)
    show_raw            = config.get("show_raw", True)
    show_avg            = config.get("show_avg", True)
    show_anomalies      = config.get("show_anomalies", True)
    show_ra_anomalies   = config.get("show_ra_anomalies", True)
    plot_style          = config.get("plot_style", "line")
    compute_ad          = config.get("compute_ad", True)
    
    interval = args.interval

    # We'll track offset for the visible portion, updated each refresh.
    offset = None
    last_max_offset = None

    # Configure terminal for raw key reads.
    old_settings = termios.tcgetattr(sys.stdin)
    tty.setcbreak(sys.stdin.fileno())

    # Clear screen at startup
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()

    # For top legend second line
    color_legend = "Legend: Data(CYN) | Avg(RED) | Raw AD(ORN) | RA AD(DGN)"

    def build_title():
        """Two-line title: param line + color legend line."""
        param_line = (
            f"Moving Time Window Graph (TW:{window_size} | "
            f"AVG:{avg_window} | RTH:{anomaly_threshold} | RWND:{anomaly_window_size} | "
            f"RAT:{ra_ad_threshold} | RAWD:{ra_ad_window_size} | "
            f"AD:{'ADON' if compute_ad else 'ADOF'} | Style:{plot_style})"
        )
        return param_line + "\n" + color_legend

    def hotkeys_legend():
        """Single-line hotkeys footer."""
        ad_state = "ADON" if compute_ad else "ADOF"
        return (
            "(SHFT:++ for big jumps) "
            "Hotkeys: k:WIN+ | j:WIN- | H:WIN++ | J:WIN-- | "
            "h:LEFT | l:RGHT | r:AVG+ | f:AVG- | .:PLOT | a:"
            + ad_state
            + " | t:RTH+ | g:RTH- | e:RAW+ | d:RAW- | z:RAWD- | x:RAWD+ | c:RAT- | v:RAT+ | "
            "s:SAVE | 1:RAWL | 2:AVGL | 3:RADA | 4:RAAD | q:QUIT"
        )

    last_update = time.time()
    update_plot = False

    try:
        while True:
            key = get_key()
            if key:
                # Adjust parameters based on hotkey
                if key == 'k':
                    window_size += 1; update_plot = True
                elif key == 'K':
                    window_size += 100; update_plot = True
                elif key == 'j':
                    window_size = max(1, window_size - 1); update_plot = True
                elif key == 'J':
                    window_size = max(1, window_size - 100); update_plot = True
                elif key == 'h':
                    if offset is not None:
                        offset = max(0, offset - window_size)
                    update_plot = True
                elif key == 'H':
                    if offset is not None:
                        offset = max(0, offset - 100)
                    update_plot = True
                elif key == 'l':
                    if offset is not None:
                        offset += window_size
                    update_plot = True
                elif key == 'L':
                    if offset is not None:
                        offset += 100
                    update_plot = True
                elif key == 'r':
                    avg_window += 1; update_plot = True
                elif key == 'R':
                    avg_window += 10; update_plot = True
                elif key == 'f':
                    avg_window = max(1, avg_window - 1); update_plot = True
                elif key == 'F':
                    avg_window = max(1, avg_window - 10); update_plot = True
                elif key == '1':
                    show_raw = not show_raw; update_plot = True
                elif key == '2':
                    show_avg = not show_avg; update_plot = True
                elif key == '3':
                    show_anomalies = not show_anomalies; update_plot = True
                elif key == '4':
                    show_ra_anomalies = not show_ra_anomalies; update_plot = True
                elif key == '.':
                    plot_style = 'line' if plot_style == 'dots' else 'dots'
                    update_plot = True
                elif key == 'a':
                    compute_ad = not compute_ad
                    update_plot = True
                elif key == 't':
                    anomaly_threshold += 1; update_plot = True
                elif key == 'g':
                    anomaly_threshold = max(1, anomaly_threshold - 1); update_plot = True
                elif key == 'e':
                    anomaly_window_size += 1; update_plot = True
                elif key == 'd':
                    anomaly_window_size = max(2, anomaly_window_size - 1); update_plot = True
                elif key == 'z':
                    ra_ad_window_size = max(2, ra_ad_window_size - 1); update_plot = True
                elif key == 'x':
                    ra_ad_window_size += 1; update_plot = True
                elif key == 'c':
                    ra_ad_threshold = max(1, ra_ad_threshold - 1); update_plot = True
                elif key == 'v':
                    ra_ad_threshold += 1; update_plot = True
                elif key == 's':
                    # Save to YAML
                    cfg = {
                        "window_size": window_size,
                        "avg_window": avg_window,
                        "anomaly_threshold": anomaly_threshold,
                        "anomaly_window_size": anomaly_window_size,
                        "ra_ad_threshold": ra_ad_threshold,
                        "ra_ad_window_size": ra_ad_window_size,
                        "show_raw": show_raw,
                        "show_avg": show_avg,
                        "show_anomalies": show_anomalies,
                        "show_ra_anomalies": show_ra_anomalies,
                        "plot_style": plot_style,
                        "compute_ad": compute_ad
                    }
                    save_config(cfg)
                    update_plot = True
                elif key == 'q':
                    break

            # Refresh if time interval or forced update
            if time.time() - last_update >= interval or update_plot:
                data = read_values(filename)
                if data:
                    new_max_offset = max(0, len(data) - window_size)
                    if offset is None or (last_max_offset is not None and offset == last_max_offset):
                        offset = new_max_offset
                    else:
                        if offset > new_max_offset:
                            offset = new_max_offset
                    last_max_offset = new_max_offset

                    window_data = data[offset : offset + window_size]
                    x_vals = list(range(offset, offset + len(window_data)))
                    running_avg = compute_running_average(window_data, avg_window)

                    # Clear figure (full screen usage)
                    plt.clear_figure()
                    # no forced smaller plot => let it fill terminal

                    # AD on raw
                    raw_anomaly_x = []
                    raw_anomaly_y = []
                    if compute_ad and len(window_data) >= anomaly_window_size:
                        for i in range(anomaly_window_size - 1, len(window_data)):
                            base = window_data[i - anomaly_window_size + 1 : i + 1]
                            if len(base) >= 2:
                                mean_b = sum(base) / len(base)
                                stdev_b = statistics.stdev(base)
                                if stdev_b > 0 and abs(window_data[i] - mean_b) > anomaly_threshold * stdev_b:
                                    raw_anomaly_x.append(offset + i)
                                    raw_anomaly_y.append(window_data[i])

                    # AD on running average
                    ra_anomaly_x = []
                    ra_anomaly_y = []
                    if compute_ad and len(running_avg) >= ra_ad_window_size:
                        for i in range(ra_ad_window_size - 1, len(running_avg)):
                            base = running_avg[i - ra_ad_window_size + 1 : i + 1]
                            if len(base) >= 2:
                                mean_b = sum(base) / len(base)
                                stdev_b = statistics.stdev(base)
                                if stdev_b > 0 and abs(running_avg[i] - mean_b) > ra_ad_threshold * stdev_b:
                                    ra_anomaly_x.append(offset + i)
                                    ra_anomaly_y.append(running_avg[i])

                    # Two-line title
                    plt.title(build_title())
                    plt.xlabel("Index")
                    plt.ylabel("Value")

                    # Plot raw data
                    if show_raw:
                        if plot_style == 'dots':
                            plt.plot(x_vals, window_data, marker="dot", color="cyan")
                        else:
                            plt.plot(x_vals, window_data, color="cyan")

                    # Plot running average
                    if show_avg:
                        if plot_style == 'dots':
                            plt.plot(x_vals, running_avg, marker="dot", color="red")
                        else:
                            plt.plot(x_vals, running_avg, color="red")

                    # Plot anomalies
                    if show_anomalies and raw_anomaly_x:
                        plt.scatter(raw_anomaly_x, raw_anomaly_y, color="orange", marker="■")
                    if show_ra_anomalies and ra_anomaly_x:
                        plt.scatter(ra_anomaly_x, ra_anomaly_y, color="dark_green", marker="●")

                    plt.grid(True)

                    ascii_chart = plt.build().rstrip("\n")
                    # **Push** the chart down ~N lines so top lines are in plain view
                    push_down_lines = 5  # increase if you need more top space
                    final_output = (
                        "\033[2J\033[H"        # Clear screen + cursor to top
                        + ("\n" * push_down_lines)
                        + ascii_chart
                        + "\n"
                        + hotkeys_legend()
                        + "\n"
                    )

                    sys.stdout.write(final_output)
                    sys.stdout.flush()
                else:
                    plt.clear_figure()
                    plt.title("No data available in file")
                    out = plt.build()
                    sys.stdout.write("\033[2J\033[H" + out)
                    sys.stdout.flush()

                last_update = time.time()
                update_plot = False

            time.sleep(0.05)

    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

if __name__ == "__main__":
    main()

