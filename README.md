# Interactive Console-based Time Window Plotter

Terminal Plotter is a scripts that reads numeric data from a file (by default `data.txt`) and displays a live-updating plot in your terminal using [plotext](https://pypi.org/project/plotext/). The plot shows a moving time window (TW) of your data along with its running average. The script provides interactive controls to adjust the time window, modify the running average window, and toggle the visibility of each plotted line.

<img width="1408" alt="image" src="https://github.com/user-attachments/assets/fd7218a5-e979-43ab-bbec-5e0be94a39b5" />

## Features

- **Live Plotting:** Continuously updates the plot as new data is added to the file.
- **Moving Time Window:** Displays only a subset of the full dataset.  
  *Default TW length is 10 points.*
- **Running Average:**  
  Computes and plots a running average for the data in the current time window.  
  *Default running average window is 5 points.*
- **Interactive Controls:**
  - **Time Window Adjustments:**
    - `k`: Increase window size by 1.
    - `K`: Increase window size by 100.
    - `j`: Decrease window size by 1 (minimum 1).
    - `J`: Decrease window size by 100 (minimum 1).
  - **Scrolling:**
    - `h`: Scroll backward (older data) by the current window size.
    - `H`: Scroll backward by 100.
    - `l`: Scroll forward (newer data) by the current window size.
    - `L`: Scroll forward by 100.
  - **Running Average Adjustments:**
    - `r`: Increase running average window by 1.
    - `R`: Increase running average window by 10.
    - `f`: Decrease running average window by 1 (minimum 1).
    - `F`: Decrease running average window by 10 (minimum 1).
  - **Toggle Line Visibility:**
    - `1`: Toggle the raw data line on/off.
    - `2`: Toggle the running average line on/off.
  - **Quit:**
    - `q`: Quit the program.

The legend in the plot updates with the current settings (e.g., TW length, running average window, and which lines are visible).

## Installation

1. **Prerequisites:**  
   Ensure you have Python 3 installed on your system.

2. **Install Dependencies:**  
   The script uses the [plotext](https://pypi.org/project/plotext/) library. Install it using pip:
   ```bash
   pip install plotext
   ```

## Usage
Run the script from your terminal. It supports several command-line options:

`python a.py [--window WINDOW] [--file FILE] [--interval INTERVAL] [--avg-window AVG_WINDOW]`


## Command-line Options
`-w / --window`
Set the initial number of points in the moving window (default: 10).

`-f / --file`
Specify the path to the data file (default: data.txt).

`-i / --interval`
Set the refresh interval in seconds (default: 2 seconds).

`-a, --avg-window`
Window size for running average (default: 5).


## Interactive Controls

While the script is running, you can interact with the plot using the following keys:


Time Window Adjustments:


-   k / K: Increase window size by 1 or 100.
-   j / J: Decrease window size by 1 or 100.
-   Scrolling:
-   h / H: Scroll backward by the current window size or 100.
-   l / L: Scroll forward by the current window size or 100.
-   Running Average Adjustments:
-   r / R: Increase running average window by 1 or 10.
-   f / F: Decrease running average window by 1 or 10.
-   Toggle Line Visibility:
-   1: Toggle the raw data line on/off.
-   2: Toggle the running average line on/off.
-   Quit:
-   q: Quit the program.

## Example

### Run the script
First, Run the script with a 20-point window, reading from mydata.txt, and updating every 1.5 seconds:

  `python a.py --window 20 --file mydata.txt --interval 1.5 --avg-window 5`









### Feeding Data to the Plot

The script reads numeric values from the data file—one value per line. To see the moving window effect, add data to the file using these example commands:

Test by appending single values by hand:

  ```bash
  echo "3.14" >> data.txt
  echo "4" >> data.txt
  ```

Test of plotting a ping command

    `ping www.toyota.co |awk '{print $7; fflush()}'|awk -F'=' '{print $2; fflush()}' >> data.txt`

Test of plotting CPU usage (macos):

    `while true; do ps -A -o %cpu | awk '{sum+=$1} END {print sum}' >> data.txt; sleep 1; done`

