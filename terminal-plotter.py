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

def parse_args():
    parser = argparse.ArgumentParser(
        description="Plot a moving window of data from a file with interactive control."
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
    return parser.parse_args()

def main():
    args = parse_args()
    filename = args.file
    window_size = args.window
    interval = args.interval

    # offset is the starting index of the window in the data.
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
                elif key == 'q':
                    break

            # Update the plot if enough time has passed or a key forced an update.
            if time.time() - last_update >= interval or update_plot:
                data = read_values(filename)
                if data:
                    # Compute the maximum valid offset so that a full window is shown.
                    new_max_offset = max(0, len(data) - window_size)
                    # If offset is not set or we are auto-scrolling, update offset.
                    if offset is None or (last_max_offset is not None and offset == last_max_offset):
                        offset = new_max_offset
                    else:
                        # Clamp offset to valid range.
                        if offset > new_max_offset:
                            offset = new_max_offset
                    last_max_offset = new_max_offset

                    window_data = data[offset: offset + window_size]
                    x_vals = list(range(offset, offset + len(window_data)))

                    plt.clear_figure()
                    plt.title("Moving Time Window Graph")
                    plt.xlabel("Index")
                    plt.ylabel("Value")
                    plt.plot(x_vals, window_data, marker="dot", color="cyan")
                    plt.grid(True)

                    # Prepare legend text showing TW length.
                    legend_text = f"TW Length: {window_size}"
                    # If the plot library supports legend(), use it.
                    if hasattr(plt, "legend"):
                        plt.legend([legend_text])
                    else:
                        # Otherwise, append the legend info to the title.
                        plt.title("Moving Time Window Graph (" + legend_text + ")")
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

