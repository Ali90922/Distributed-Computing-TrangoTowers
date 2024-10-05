import matplotlib.pyplot as plt
import pandas as pd

# Updated data with correct values
data = {
    'Clients': [200, 175, 150, 125, 100, 75, 50, 25, 10, 5, 2, 1],
    'Total Messages Processed': [771403, 685847, 570540, 502758, 419027, 318591, 212880, 106375, 42600, 21320, 8536, 3721],
    'Elapsed Time (s)': [301.79, 302.40, 301.26, 301.06, 300.49, 301.19, 301.26, 300.59, 300.72, 300.80, 300.90, 300.65],
    'Messages Per Second': [2556.11, 2267.98, 1895.90, 1669.95, 1394.48, 1057.78, 706.64, 353.89, 141.66, 70.88, 28.37, 12.38],
    'Average CPU Usage (%)': [67.97, 50.43, 34.66, 26.07, 16.25, 9.95, 3.86, 1.03, 0.21, 0.14, 0.10, 0.08],
    'Average Memory Usage (MB)': [12.62, 12.62, 12.87, 12.73, 12.62, 12.75, 12.75, 12.75, 12.62, 12.87, 12.99, 12.75],
    'Bytes Sent (MB)': [393.30, 289.43, 187.61, 152.83, 99.68, 52.85, 23.35, 6.03, 1.06, 0.34, 0.06, 0.02],
    'Bytes Received (MB)': [13.08, 11.58, 8.94, 8.06, 6.74, 5.32, 3.58, 1.61, 0.69, 0.39, 0.17, 0.09],
    'Packets Sent': [738123.93, 588347.87, 385319.07, 325119.07, 218646.47, 142494.93, 66773.80, 21445.60, 5726.00, 2870.00, 594.80, 264.57],
    'Packets Received': [183558.87, 162445.27, 125192.93, 111979.67, 94029.47, 74580.00, 50173.20, 22329.13, 9506.79, 5312.53, 2062.67, 1232.43],
    'CPU Frequency (MHz)': [1546.51, 1486.96, 1577.62, 1635.37, 1513.21, 1401.47, 1361.85, 1395.03, 1315.99, 1348.48, 1446.53, 1259.85]
}

df = pd.DataFrame(data)

# Define a list of (column_name, plot_title, y_label) tuples for plotting
plot_specs = [
    ('Total Messages Processed', 'Total Messages Processed vs Clients', 'Total Messages Processed'),
    ('Elapsed Time (s)', 'Elapsed Time vs Clients', 'Elapsed Time (s)'),
    ('Messages Per Second', 'Messages Per Second vs Clients', 'Messages Per Second'),
    ('Average CPU Usage (%)', 'Average CPU Usage vs Clients', 'CPU Usage (%)'),
    ('Average Memory Usage (MB)', 'Average Memory Usage vs Clients', 'Memory Usage (MB)'),
    ('Bytes Sent (MB)', 'Bytes Sent vs Clients', 'Bytes Sent (MB)'),
    ('Bytes Received (MB)', 'Bytes Received vs Clients', 'Bytes Received (MB)'),
    ('Packets Sent', 'Packets Sent vs Clients', 'Packets Sent'),
    ('Packets Received', 'Packets Received vs Clients', 'Packets Received'),
    ('CPU Frequency (MHz)', 'CPU Frequency vs Clients', 'CPU Frequency (MHz)')
]

# Plot and save each graph as a PNG file
for column_name, title, ylabel in plot_specs:
    plt.figure(figsize=(10, 6))
    plt.plot(df['Clients'], df[column_name], marker='o')
    plt.title(title)
    plt.xlabel('Number of Clients')
    plt.ylabel(ylabel)
    plt.grid(True)
    plt.savefig(f'{title.replace(" ", "_").replace("/", "_")}.png')  # Save as PNG, replacing spaces and slashes
    plt.close()

print("All graphs have been saved as PNG files in the current directory.")

