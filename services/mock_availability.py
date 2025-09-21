import random
from datetime import datetime, timedelta, time
from faker import Faker

fake = Faker()
Faker.seed(0)


def generate_busy_blocks(start_date, days=7):
    busy_blocks = []
    work_hours = (9, 17)  # Work hours from 9 AM to 5 PM
    
    # Generate 3-6 busy blocks
    for _ in range(random.randint(3, 6)):
        day_offset = random.randint(0, days - 1)
        date = start_date + timedelta(days=day_offset)

        # Choose random hour between 9 and 15 (to ensure end time <= 17)
        start_hour = random.randint(work_hours[0], work_hours[1] - 2)
        duration_hours = random.randint(1, 2)
        end_hour = min(start_hour + duration_hours, work_hours[1])

        start_dt = datetime.combine(date, time(start_hour, 0)).replace(tzinfo=None)
        end_dt = datetime.combine(date, time(end_hour, 0)).replace(tzinfo=None)

        busy_blocks.append({
            "start": start_dt.isoformat() + "Z",
            "end": end_dt.isoformat() + "Z",
        })

    return busy_blocks


def get_free_busy_data(interviewer_ids: list[int]) -> list[dict]:
    start_date = datetime.utcnow().date()
    data = []

    for id_ in interviewer_ids:
        interviewer = {
            "interviewerId": id_,
            "name": fake.name(),
            "busy": generate_busy_blocks(start_date)  # Changed from 'availability' to 'busy'
        }
        data.append(interviewer)

    return data 