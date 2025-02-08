# Interactive Console-based Time Window Plotter

Terminal Plotter is script that reads numeric data from a file (by default `data.txt`) and displays it as a live-updating plot in the terminal using [plotext](https://pypi.org/project/plotext/). The plot shows a moving time window (TW) of the data, and you can interactively adjust the window's size and position using keyboard controls.

<img width="1408" alt="image" src="https://github.com/user-attachments/assets/fd7218a5-e979-43ab-bbec-5e0be94a39b5" />


## Features

- **Live Plotting:**  
  Continuously reads new data from a file and updates the plot in real time.
  
- **Moving Time Window:**  
  Displays only the last X data points (a configurable "time window").
  
- **Interactive Controls:**  
  Adjust the plot on the fly using these keys:
  - `k`: Increase window size by **1**
  - `K`: Increase window size by **100**
  - `j`: Decrease window size by **1** (minimum window size is 1)
  - `J`: Decrease window size by **100** (minimum window size is 1)
  - `h`: Move the window to older data (shift left) by the current window size
  - `H`: Move the window to older data by **100** points
  - `l`: Move the window to newer data (shift right) by the current window size
  - `L`: Move the window to newer data by **100** points
  - `q`: Quit the program
  
- **Auto-Scrolling:**  
  When the plot is showing the latest data (the last TW), new data automatically scrolls into view.
  
- **Legend Display:**  
  The plot includes a legend on top displaying the current time window length.

## Installation

1. **Python 3:**  
   Ensure you have Python 3 installed on your Unix-like system (Linux, macOS). This script uses the `termios` and `tty` modules, which are available on Unix.

2. **Install Dependencies:**  
   Install the `plotext` package using pip:
   ```bash
   pip install plotext
    ```

## Usage
Run the script from your terminal. It supports several command-line options:

`python a.py [--window WINDOW] [--file FILE] [--interval INTERVAL]`

## Command-line Options
`-w / --window`
Set the initial number of points in the moving window (default: 10).

`-f / --file`
Specify the path to the data file (default: data.txt).

`-i / --interval`
Set the refresh interval in seconds (default: 2 seconds).


## Example

### Run the script
First, Run the script with a 20-point window, reading from mydata.txt, and updating every 1.5 seconds:

  `python a.py -w 20 -f mydata.txt -i 1.5`


### Feeding Data to the Plot

The script reads numeric values from the data file—one value per line. To see the moving window effect, add data to the file using these example commands:

Test by appending single values by hand:

  ```bash
  echo "3.14" >> data.txt
  echo "4" >> data.txt
  ```

Test of plotting a ping command

    `ping www.toyota.co |awk '{print $7; fflush()}'|awk -F'=' '{print $2; fflush()}' >> data.txt`
