import time
import sys
import select
import tty
import termios
import argparse
import plotext as plt

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
       For each index, average over the last 'avg_window' samples (or fewer if not available)."""
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
        description="Plot a moving window of data with running average and background toggle, with interactive control."
    )
    parser.add_argument(
        "-w", "--window", type=int, default=10,
        help="Initial number of points in the moving window (default: 10)"
    )
    parser.add_argument(
        "-f", "--file", type=str, default="data.txt",
        help="Path to the data file (default: data.txt)"
    )
    parser.add_argument(
        "-i", "--interval", type=float, default=2,
        help="Refresh interval in seconds (default: 2)"
    )
    parser.add_argument(
        "-a", "--avg-window", type=int, default=5,
        help="Window size for running average (default: 5)"
    )
    return parser.parse_args()

def main():
    args = parse_args()
    filename = args.file
    window_size = args.window
    interval = args.interval
    avg_window = args.avg_window

    # Use a boolean to track background mode; True means dark background.
    dark_mode = True

    # offset is the starting index of the displayed window in the full data.
    # When auto-scrolling, offset is updated to show the newest data.
    offset = None
    # last_max_offset holds the maximum valid offset from the previous update.
    last_max_offset = None

    # Save current terminal settings and set cbreak mode for immediate key reads.
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
                # Main window adjustments
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
                # Toggle background mode.
                elif key == 'b':
                    dark_mode = not dark_mode
                    update_plot = True
                elif key == 'q':
                    break

            # Update the plot if the refresh interval has passed or a key forced an update.
            if time.time() - last_update >= interval or update_plot:
                data = read_values(filename)
                if data:
                    # Compute the maximum valid offset so that a full window is shown.
                    new_max_offset = max(0, len(data) - window_size)
                    # Auto-scroll if offset is unset or currently at the end.
                    if offset is None or (last_max_offset is not None and offset == last_max_offset):
                        offset = new_max_offset
                    else:
                        if offset > new_max_offset:
                            offset = new_max_offset
                    last_max_offset = new_max_offset

                    # Slice the window from the full data.
                    window_data = data[offset: offset + window_size]
                    x_vals = list(range(offset, offset + len(window_data)))

                    # Compute the running average for the displayed window.
                    running_avg = compute_running_average(window_data, avg_window)

                    # Set theme and colors based on background mode.
                    if dark_mode:
                        plt.theme("dark")
                        raw_color = "cyan"
                        avg_color = "yellow"
                    else:
                        plt.theme("light")
                        raw_color = "blue"
                        avg_color = "red"

                    plt.clear_figure()
                    plt.title("Moving Time Window Graph")
                    plt.xlabel("Index")
                    plt.ylabel("Value")
                    
                    # Plot the raw data and the running average.
                    plt.plot(x_vals, window_data, marker="dot", color=raw_color, label="Data")
                    plt.plot(x_vals, running_avg, marker="dot", color=avg_color,
                             label=f"Running Avg (window: {avg_window})")
                    plt.grid(True)
                    
                    # Prepare legend information.
                    legend_text = [f"TW Length: {window_size}", f"Avg window: {avg_window}"]
                    if dark_mode:
                        legend_text.append("Background: Dark")
                    else:
                        legend_text.append("Background: Light")
                    if hasattr(plt, "legend"):
                        plt.legend(legend_text)
                    else:
                        plt.title("Moving Time Window Graph (" + ", ".join(legend_text) + ")")
                else:
                    plt.clear_figure()
                    plt.title("No data available in file")

                # Build the plot as a string and update display without flickering.
                plot_str = plt.build()
                sys.stdout.write("\033[H")  # Move cursor to top-left.
                sys.stdout.write(plot_str)
                sys.stdout.flush()

                last_update = time.time()
                update_plot = False

            time.sleep(0.05)
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

if __name__ == "__main__":
    main()

