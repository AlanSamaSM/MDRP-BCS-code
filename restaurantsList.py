class Restaurant:
    def __init__(self, rest_id, location):
        self.id = rest_id
        self.location = location  # (lat, lon)
        self.orders = []


# Simple example restaurants used for testing
restaurantList = [
    Restaurant(1, (19.4326, -99.1332)),
    Restaurant(2, (19.4300, -99.1300)),
    Restaurant(3, (19.4340, -99.1290)),
]

