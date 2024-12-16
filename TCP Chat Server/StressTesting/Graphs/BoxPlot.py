import matplotlib.pyplot as plt

# Data for 75, 125, 175, and 225 clients
data = {
    'Clients': [75, 125, 175, 225],
    'Total Messages Processed per Interval': [
        [20328, 21263, 21260, 21263, 21266, 21261, 21258, 21264, 21263, 21033, 21295, 21191, 21291, 21236, 21273],  # 75 clients
        [32750, 35459, 35488, 32681, 26326, 32629, 35483, 34259, 32248, 31581, 35387, 35459, 33185, 32662, 35443],  # 125 clients
        [44155, 49539, 49489, 49391, 44530, 29596, 27801, 40492, 48771, 49518, 49532, 49219, 49524, 49327, 49184],  # 175 clients
        [32098, 56828, 56541, 37420, 22237, 50241, 56836, 56657, 56106, 56887, 56717, 57036, 42015, 39754, 51668]   # 225 clients
    ],
    'CPU Usage per Interval': [
        [0.00, 11.20, 10.80, 11.10, 10.90, 9.90, 10.20, 11.30, 11.30, 11.40, 10.10, 10.30, 10.40, 9.80, 10.50],  # 75 clients
        [0.00, 26.10, 32.20, 27.90, 20.40, 22.50, 32.20, 29.10, 26.60, 27.30, 31.70, 32.60, 27.80, 22.10, 32.50],  # 125 clients
        [0.00, 62.50, 54.80, 60.80, 52.50, 30.20, 28.20, 48.40, 60.70, 62.90, 58.80, 54.40, 60.90, 60.60, 60.70],  # 175 clients
        [0.00, 77.80, 79.10, 53.10, 25.60, 76.90, 70.80, 80.00, 79.70, 83.70, 81.50, 75.40, 52.90, 50.50, 74.30]   # 225 clients
    ],
    'Packets Received per Interval': [
        [71456, 74140, 74359, 74902, 76496, 75820, 75602, 75037, 74246, 73306, 74802, 74311, 75220, 74298, 74705],  # 75 clients
        [107533, 111907, 112377, 106301, 91977, 112483, 118410, 113470, 113344, 108020, 118383, 120123, 114741, 111307, 119319],  # 125 clients
        [156840, 175377, 177223, 176768, 160860, 117330, 115401, 147695, 171355, 174317, 173797, 168589, 173018, 176291, 171818],  # 175 clients
        [132590, 212861, 210753, 169622, 130403, 197027, 210288, 210844, 209844, 212597, 211984, 211699, 172799, 162464, 196781]   # 225 clients
    ],
    'Bytes Sent per Interval': [
        [48.59, 51.91, 51.89, 52.59, 53.55, 53.44, 53.40, 53.48, 53.39, 52.87, 53.59, 53.35, 53.64, 53.46, 53.52],  # 75 clients
        [144.41, 158.55, 158.70, 147.32, 119.99, 149.19, 162.80, 157.25, 148.31, 144.72, 162.11, 162.87, 152.53, 160.78, 162.92],  # 125 clients
        [272.42, 310.83, 310.40, 312.79, 286.50, 189.24, 178.09, 260.27, 313.82, 318.91, 318.83, 316.45, 318.80, 317.60, 316.45],  # 175 clients
        [251.54, 457.17, 454.85, 301.46, 179.72, 411.62, 468.98, 467.72, 463.21, 469.77, 468.36, 470.65, 347.22, 328.09, 426.71]   # 225 clients
    ]
}

# First figure: Total Messages Processed and CPU Usage
fig1, axes1 = plt.subplots(1, 2, figsize=(12, 6))

# Box plot for Total Messages Processed per Interval
axes1[0].boxplot([data['Total Messages Processed per Interval'][0], data['Total Messages Processed per Interval'][1], data['Total Messages Processed per Interval'][2], data['Total Messages Processed per Interval'][3]])
axes1[0].set_title('Total Messages Processed per Interval')
axes1[0].set_xticklabels(['75 Clients', '125 Clients', '175 Clients', '225 Clients'])
axes1[0].set_ylabel('Messages Processed')

# Box plot for CPU Usage per Interval
axes1[1].boxplot([data['CPU Usage per Interval'][0], data['CPU Usage per Interval'][1], data['CPU Usage per Interval'][2], data['CPU Usage per Interval'][3]])
axes1[1].set_title('CPU Usage per Interval')
axes1[1].set_xticklabels(['75 Clients', '125 Clients', '175 Clients', '225 Clients'])
axes1[1].set_ylabel('CPU Usage (%)')

plt.tight_layout()
plt.savefig('box_plots_messages_cpu.png')

# Second figure: Packets Received and Bytes Sent
fig2, axes2 = plt.subplots(1, 2, figsize=(12, 6))

# Box plot for Packets Received per Interval
axes2[0].boxplot([data['Packets Received per Interval'][0], data['Packets Received per Interval'][1], data['Packets Received per Interval'][2], data['Packets Received per Interval'][3]])
axes2[0].set_title('Packets Received per Interval')
axes2[0].set_xticklabels(['75 Clients', '125 Clients', '175 Clients', '225 Clients'])
axes2[0].set_ylabel('Packets Received')

# Box plot for Bytes Sent per Interval
axes2[1].boxplot([data['Bytes Sent per Interval'][0], data['Bytes Sent per Interval'][1], data['Bytes Sent per Interval'][2], data['Bytes Sent per Interval'][3]])
axes2[1].set_title('Bytes Sent per Interval')
axes2[1].set_xticklabels(['75 Clients', '125 Clients', '175 Clients', '225 Clients'])
axes2[1].set_ylabel('Bytes Sent (MB)')

plt.tight_layout()
plt.savefig('box_plots_packets_bytes.png')

plt.show()
