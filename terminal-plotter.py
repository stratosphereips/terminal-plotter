import time
import sys
import select
import tty
import termios
import argparse
import plotext as plt
import statistics  # For anomaly detection computations

def get_key():
    """Non-blocking read of a single key from stdin."""
    dr, _, _ = select.select([sys.stdin], [], [], 0)
    if dr:
        return sys.stdin.read(1)
    return None

def read_values(filename):
    """Read a list of y-values (one per line) from the file."""
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
                    print("Could not convert line:", line)
    except FileNotFoundError:
        print(f"File '{filename}' not found.")
    return y_vals

def compute_running_average(data, avg_window):
    """Compute running average over data with a specified window.
       For each index, average over the last `avg_window` samples (or fewer if not available)."""
    if avg_window <= 1:
        return data[:]  # no smoothing if window is 1 or less
    running_avg = []
    for i in range(len(data)):
        start = max(0, i - avg_window + 1)
        window = data[start:i+1]
        avg = sum(window) / len(window)
        running_avg.append(avg)
    return running_avg

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
    window_size = args.window
    interval = args.interval
    avg_window = args.avg_window

    # Additional parameters for anomaly detection:
    anomaly_threshold = 3       # Multiplier for standard deviation
    anomaly_window_size = 10    # AD window size: number of recent points used for detection

    # Variables to persist anomalies and track AD parameter changes.
    stored_anomalies = set()    # Store indices of data points flagged as anomalies
    ad_params_changed = False   # Flag to trigger full re-computation

    # Booleans to control visibility of each plotted line.
    show_raw = True       # Raw data line visible by default.
    show_avg = True       # Running average line visible by default.

    # Plot style control
    plot_style = 'dots'  # Options: 'dots', 'line'

    offset = None
    last_max_offset = None

    # Set terminal to cbreak mode for immediate key reads.
    old_settings = termios.tcgetattr(sys.stdin)
    tty.setcbreak(sys.stdin.fileno())

    # Clear the terminal once at startup.
    sys.stdout.write("\033[2J")
    sys.stdout.flush()

    last_update = time.time()
    update_plot = False

    try:
        while True:
            key = get_key()
            if key:
                # Main window adjustments.
                if key == 'k':
                    window_size += 1
                    update_plot = True
                elif key == 'K':
                    window_size += 100
                    update_plot = True
                elif key == 'j':
                    window_size = max(1, window_size - 1)
                    update_plot = True
                elif key == 'J':
                    window_size = max(1, window_size - 100)
                    update_plot = True
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
                # Running average window adjustments.
                elif key == 'r':
                    avg_window += 1
                    update_plot = True
                elif key == 'R':
                    avg_window += 10
                    update_plot = True
                elif key == 'f':
                    avg_window = max(1, avg_window - 1)
                    update_plot = True
                elif key == 'F':
                    avg_window = max(1, avg_window - 10)
                    update_plot = True
                # Toggle line visibility.
                elif key == '1':
                    show_raw = not show_raw
                    update_plot = True
                elif key == '2':
                    show_avg = not show_avg
                    update_plot = True
                # Toggle plot style.
                elif key == 's':
                    plot_style = 'line' if plot_style == 'dots' else 'dots'
                    update_plot = True
                # New hotkeys for anomaly detection adjustments:
                elif key == 't':  # Increase AD threshold multiplier by 1
                    anomaly_threshold += 1
                    ad_params_changed = True
                    update_plot = True
                elif key == 'g':  # Decrease AD threshold multiplier by 1
                    anomaly_threshold = max(1, anomaly_threshold - 1)
                    ad_params_changed = True
                    update_plot = True
                elif key == 'e':  # Increase AD window size by 1
                    anomaly_window_size += 1
                    ad_params_changed = True
                    update_plot = True
                elif key == 'd':  # Decrease AD window size by 1 (min 2 points)
                    anomaly_window_size = max(2, anomaly_window_size - 1)
                    ad_params_changed = True
                    update_plot = True
                elif key == 'q':
                    break

            # Update the plot if the refresh interval has passed or a key forced an update.
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

                    window_data = data[offset: offset + window_size]
                    x_vals = list(range(offset, offset + len(window_data)))
                    running_avg = compute_running_average(window_data, avg_window)

                    # --- Anomaly Detection ---
                    # If AD parameters changed, recompute anomalies for the entire dataset.
                    if ad_params_changed:
                        stored_anomalies = set()
                        # For each data point from index 'anomaly_window_size' onward,
                        # use the preceding anomaly_window_size points as the baseline.
                        for i in range(anomaly_window_size, len(data)):
                            baseline = data[i - anomaly_window_size:i]
                            if len(baseline) >= 2:
                                mean_baseline = sum(baseline) / len(baseline)
                                stdev_baseline = statistics.stdev(baseline)
                                if stdev_baseline > 0 and abs(data[i] - mean_baseline) > anomaly_threshold * stdev_baseline:
                                    stored_anomalies.add(i)
                        ad_params_changed = False
                    else:
                        # Otherwise, compute anomalies for the newest AD window and add them.
                        if len(data) >= anomaly_window_size:
                            ad_data = data[-anomaly_window_size:]
                            ad_x_all = list(range(len(data) - anomaly_window_size, len(data)))
                            mean_ad = sum(ad_data) / len(ad_data)
                            stdev_ad = statistics.stdev(ad_data) if len(ad_data) > 1 else 0
                            for j, val in enumerate(ad_data):
                                idx = ad_x_all[j]
                                if stdev_ad > 0 and abs(val - mean_ad) > anomaly_threshold * stdev_ad:
                                    stored_anomalies.add(idx)
                    # -------------------------

                    # For plotting, show anomalies that fall within the current window.
                    anomaly_x = []
                    anomaly_y = []
                    for idx in stored_anomalies:
                        if offset <= idx < offset + window_size:
                            anomaly_x.append(idx)
                            anomaly_y.append(data[idx])

                    plt.clear_figure()
                    plt.title("Moving Time Window Graph")
                    plt.xlabel("Index")
                    plt.ylabel("Value")
                    
                    # Plot the raw data and running average.
                    if show_raw:
                        if plot_style == 'dots':
                            plt.plot(x_vals, window_data, marker="dot", color="cyan", label="Data")
                        else:
                            plt.plot(x_vals, window_data, color="cyan", label="Data")
                    if show_avg:
                        if plot_style == 'dots':
                            plt.plot(x_vals, running_avg, marker="dot", color="red",
                                     label=f"Running Avg (window: {avg_window})")
                        else:
                            plt.plot(x_vals, running_avg, color="red",
                                     label=f"Running Avg (window: {avg_window})")
                    # Overlay anomalies.
                    if anomaly_x:
                        plt.plot(anomaly_x, anomaly_y, marker="x", color="yellow", label="Anomaly")
                    
                    plt.grid(True)
                    
                    # Append AD parameters to the legend.
                    legend_text = [
                        f"TW Length: {window_size}",
                        f"Avg window: {avg_window}",
                        f"Plot Style: {plot_style}",
                        f"Data: {'on' if show_raw else 'off'}",
                        f"Running Avg: {'on' if show_avg else 'off'}",
                        f"AD Threshold: {anomaly_threshold}",
                        f"AD Window: {anomaly_window_size}"
                    ]
                    if hasattr(plt, "legend"):
                        plt.legend(legend_text)
                    else:
                        plt.title("Moving Time Window Graph (" + ", ".join(legend_text) + ")")
                else:
                    plt.clear_figure()
                    plt.title("No data available in file")

                plot_str = plt.build()
                sys.stdout.write("\033[H")
                sys.stdout.write(plot_str)
                sys.stdout.flush()

                last_update = time.time()
                update_plot = False

            time.sleep(0.05)
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

if __name__ == "__main__":
    main()

