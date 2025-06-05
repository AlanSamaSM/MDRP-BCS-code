from datetime import datetime, timedelta

# (courier_id, on_time, off_time, location)
start_day = datetime(2025, 1, 1, 8, 0)

courierList = [
    (1, start_day, start_day + timedelta(hours=4), (19.4310, -99.1320)),
    (2, start_day + timedelta(hours=1), start_day + timedelta(hours=5), (19.4290, -99.1300)),
    (3, start_day + timedelta(hours=2), start_day + timedelta(hours=6), (19.4350, -99.1340)),
]

