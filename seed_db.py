from src.db import init_db, add_items

init_db()

test_items = [
    {'source': 'ebay', 'title': 'BMW M3 E92 Meistershaft Exhaust System', 'price': '$1,299.99', 'url': 'https://example.com/1', 'keyword': 'Meistershaft exhaust', 'category': 'Exhaust/Drivetrain', 'image': None},
    {'source': 'forum:e90post', 'title': 'OEM M3 Brake Pads Set - New Condition', 'price': '$89.50', 'url': 'https://example.com/2', 'keyword': 'M3 brakes', 'category': 'Brakes', 'image': None},
    {'source': 'ebay', 'title': 'KW Suspension V3 Coilovers E9x M3', 'price': '$1,599.00', 'url': 'https://example.com/3', 'keyword': 'E9x suspension', 'category': 'Suspension', 'image': None},
    {'source': 'forum:m3cutters', 'title': 'Carbon Fiber Spoiler - E92 M3', 'price': '$450.00', 'url': 'https://example.com/4', 'keyword': 'E9x parts', 'category': 'Exterior', 'image': None},
    {'source': 'forum:bimmerpost', 'title': 'Lightweight Wheels 19" OEM Style', 'price': '$750.00', 'url': 'https://example.com/5', 'keyword': 'E9x suspension', 'category': 'Wheels', 'image': None},
    {'source': 'ebay', 'title': 'E92 M3 Recaro Seats - Black Leather', 'price': '$1,200.00', 'url': 'https://example.com/6', 'keyword': 'interior', 'category': 'Interior', 'image': None},
    {'source': 'forum:e90post', 'title': 'M3 E9x Front Bumper with Splitter', 'price': '$350.00', 'url': 'https://example.com/7', 'keyword': 'bumper', 'category': 'Exterior', 'image': None},
    {'source': 'ebay', 'title': 'Brembo M4 Brake Rotors Set', 'price': '$299.99', 'url': 'https://example.com/8', 'keyword': 'brake rotor', 'category': 'Brakes', 'image': None},
]

count = add_items(test_items)
print(f'Added {count} test items to database')
