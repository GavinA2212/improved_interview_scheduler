from django.test import SimpleTestCase
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace

from candidate_fyi_takehome_project.interviews.utils import *

# ------------------- InterviewAvailability util function tests ---------------------------
class computeAvailableSlotsTests(SimpleTestCase):
    def setUp(self):
        self.interviewers = [
             SimpleNamespace(workday_start_hour=9,workday_end_hour=17,timezone="UTC"),
        ]
        self.valid_interval = 60
        self.duration = 60
    
    # Test single interviewer
    def test_one_slot(self):
        search_start = utc_dt(2025, 10, day=6, hour=9)
        search_end = utc_dt(2025, 10, day=6, hour=17)
        busy_data = [
            {"start": utc_dt(2025, 10, day=6, hour=9), "end": utc_dt(2025, 10, day=6, hour=10)},
            {"start": utc_dt(2025, 10, day=6, hour=12), "end": utc_dt(2025, 10, day=6, hour=13)},
            {"start": utc_dt(2025, 10, day=6, hour=15), "end": utc_dt(2025, 10, day=6, hour=16)},
        ]
        
        expected = [
            [utc_dt(2025, 10, day=6, hour=10), utc_dt(2025, 10, day=6, hour=11)],
            [utc_dt(2025, 10, day=6, hour=11), utc_dt(2025, 10, day=6, hour=12)],
            [utc_dt(2025, 10, day=6, hour=13), utc_dt(2025, 10, day=6, hour=14)],
            [utc_dt(2025, 10, day=6, hour=14), utc_dt(2025, 10, day=6, hour=15)],
            [utc_dt(2025, 10, day=6, hour=16), utc_dt(2025, 10, day=6, hour=17)],
        ]
        actual = compute_available_slots(search_start, search_end, self.valid_interval, busy_data, self.interviewers, self.duration)
        self.assertEqual(actual,expected)
    
    # Test with multpiple timezone workdays
    def test_multiple_us_timezones(self):
        search_start = utc_dt(2025, 10, day=6, hour=12)
        search_end = utc_dt(2025, 10, day=7, hour=2)
        busy_data = [
            {"start": utc_dt(2025, 10, day=6, hour=14), "end": utc_dt(2025, 10, day=6, hour=15)},
            {"start": utc_dt(2025, 10, day=6, hour=22), "end": utc_dt(2025, 10, day=6, hour=23)},
        ]
        
        # EST interviewer: 9-17 EST = 13-21 UTC
        # PST interviewer: 9-17 PST = 16-0 UTC (next day)
        # Overlap: 16-21 UTC
        us_interviewers = [
            SimpleNamespace(workday_start_hour=9, workday_end_hour=17, timezone="America/New_York"),
            SimpleNamespace(workday_start_hour=9, workday_end_hour=17, timezone="America/Los_Angeles"),
        ]
        
        expected = [
            [utc_dt(2025, 10, day=6, hour=16), utc_dt(2025, 10, day=6, hour=17)],
            [utc_dt(2025, 10, day=6, hour=17), utc_dt(2025, 10, day=6, hour=18)],
            [utc_dt(2025, 10, day=6, hour=18), utc_dt(2025, 10, day=6, hour=19)],
            [utc_dt(2025, 10, day=6, hour=19), utc_dt(2025, 10, day=6, hour=20)],
            [utc_dt(2025, 10, day=6, hour=20), utc_dt(2025, 10, day=6, hour=21)],
        ]
        actual = compute_available_slots(search_start, search_end, self.valid_interval, busy_data, us_interviewers, self.duration)
        self.assertEqual(actual,expected)
    
    # Test in thirty minute intervals
    def test_thirty_minute_intervals(self):
        search_start = utc_dt(2025, 10, day=6, hour=9)
        search_end = utc_dt(2025, 10, day=6, hour=12)
        busy_data = [
            {"start": utc_dt(2025, 10, day=6, hour=10), "end": utc_dt(2025, 10, day=6, hour=10, minute=30)},
        ]
        
        valid_interval = 30
        duration = 30
        
        expected = [
            [utc_dt(2025, 10, day=6, hour=9), utc_dt(2025, 10, day=6, hour=9, minute=30)],
            [utc_dt(2025, 10, day=6, hour=9, minute=30), utc_dt(2025, 10, day=6, hour=10)],
            [utc_dt(2025, 10, day=6, hour=11), utc_dt(2025, 10, day=6, hour=11, minute=30)],
            [utc_dt(2025, 10, day=6, hour=11, minute=30), utc_dt(2025, 10, day=6, hour=12)],
        ]
        actual = compute_available_slots(search_start, search_end, valid_interval, busy_data, self.interviewers, duration)
        self.assertEqual(actual,expected)


class trimBusySlotsToWindowTests(SimpleTestCase):
    def setUp(self):
        self.search_start = utc_dt(2025, 10, 7, 3)
        self.search_end = utc_dt(2025, 10, 7, 9)
        self.start_boundary = [self.search_start - timedelta(hours=1), self.search_start]
        self.end_boundary = [self.search_end, self.search_end + timedelta(hours=1)]
        
    # Test slot start out, slot end in
    def test_slot_start_out_slot_end_in(self):
        slots = [{"start": utc_dt(2025, 10, 7, 1), "end": utc_dt(2025, 10, 7, 6)}]
        
        expected = [
            self.start_boundary,
            [utc_dt(2025, 10, 7, 3), utc_dt(2025, 10, 7, 6)],
            self.end_boundary
        ]
        actual = trim_busy_slots_to_search_window(self.search_start, self.search_end, slots)
        self.assertEqual(actual, expected)
        
    # Test slot start in, end slot out
    def test_slot_start_in_slot_end_out(self):
        slots = [{"start": utc_dt(2025, 10, 7, 4), "end": utc_dt(2025, 10, 7, 11)}]
         
        expected = [
            self.start_boundary,
            [utc_dt(2025, 10, 7, 4), utc_dt(2025, 10, 7, 9)],
            self.end_boundary
        ]
        actual = trim_busy_slots_to_search_window(self.search_start, self.search_end, slots)    
        self.assertEqual(actual, expected)
        
    # Test slot fully inside window
    def test_slot_fully_in_window(self):
        slots = [{"start": utc_dt(2025, 10, 7, 4), "end": utc_dt(2025, 10, 7, 6)}]
        
        expected = [
            self.start_boundary,
            [utc_dt(2025, 10, 7, 4), utc_dt(2025, 10, 7, 6)],
            self.end_boundary
        ]
        actual = trim_busy_slots_to_search_window(self.search_start, self.search_end, slots)
        self.assertEqual(actual, expected)
        
    # Test slot fully outside window
    def test_slot_fully_outside_window(self):
        slots = [{"start": utc_dt(2025, 10, 6, 1), "end": utc_dt(2025, 10, 6, 6)}]
        
        expected = [
            self.start_boundary,
            self.end_boundary
        ]
        actual = trim_busy_slots_to_search_window(self.search_start, self.search_end, slots)
        self.assertEqual(actual, expected)
        
        
class buildBusyWindowsTests(SimpleTestCase):
    def setUp(self):
        self.slot_one = [utc_dt(2025, 10, 6, 12), utc_dt(2025, 10, 6, 19)]
    
    # Test no overlap
    def test_no_overlap(self):
        test_slot = [utc_dt(2025, 10, 6, 8), utc_dt(2025, 10, 6, 10)]
        expected = [[
            utc_dt(2025, 10, 6, 8), utc_dt(2025, 10, 6, 10)],
            [utc_dt(2025, 10, 6, 12), utc_dt(2025, 10, 6, 19)]
        ]
        actual = build_busy_windows([test_slot, self.slot_one ])
        self.assertEqual(actual, expected)
        
    # Test overlap over start
    def test_overlap_over_start(self):
        test_slot = [utc_dt(2025, 10, 6, 8), utc_dt(2025, 10, 6, 14)]
        expected = [[utc_dt(2025, 10, 6, 8), utc_dt(2025, 10, 6, 19)]]
        actual = build_busy_windows([test_slot, self.slot_one ])
        self.assertEqual(actual, expected)
    
    # Test overlap end on exact start
    def test_overlap_end_on_exact_start(self):
        test_slot = [utc_dt(2025, 10, 6, 8), utc_dt(2025, 10, 6, 12)]
        expected = [[utc_dt(2025, 10, 6, 8), utc_dt(2025, 10, 6, 19)]]
        actual = build_busy_windows([test_slot, self.slot_one])
        self.assertEqual(actual, expected)
        
    # Test overlap start on exact end
    def test_start_on_exact_end(self):
        test_slot = [utc_dt(2025, 10, 6, 19), utc_dt(2025, 10, 6, 23)]
        expected = [[utc_dt(2025, 10, 6, 12), utc_dt(2025, 10, 6, 23)]]
        actual = build_busy_windows([self.slot_one, test_slot])
        self.assertEqual(actual, expected)
    
    # Test overlap over entire interval
    def test_overlap_over_entire_interval(self):
        test_slot = [utc_dt(2025, 10, 6, 8), utc_dt(2025, 10, 6, 22)]
        expected = [[utc_dt(2025, 10, 6, 8), utc_dt(2025, 10, 6, 22)]]
        actual = build_busy_windows([test_slot, self.slot_one ])
        self.assertEqual(actual, expected)


class trimSlotToAvailableWorkdaysTests(SimpleTestCase):
    def setUp(self):
        self.interviewers = [
            SimpleNamespace(workday_start_hour=9,workday_end_hour=17,timezone="UTC"),
            SimpleNamespace(workday_start_hour=11,workday_end_hour=19,timezone="UTC")
            # Valid slots should be in = 11-17
        ]
        
    # Test slot fully in
    def test_slot_fully_in(self):
        slot_start = utc_dt(2025, 10, day=9, hour=13)
        slot_end = utc_dt(2025, 10, day=9, hour=15)
        
        expected = [[slot_start, slot_end]]
        actual = trim_slot_to_available_workdays(slot_start, slot_end, self.interviewers)
        self.assertEqual(actual, expected)
    
    # Test slot fully out
    def test_slot_fully_out(self):
        slot_start = utc_dt(2025, 10, day=9, hour=9)
        slot_end = utc_dt(2025, 10, day=9, hour=10)
        
        expected = None
        actual = trim_slot_to_available_workdays(slot_start, slot_end, self.interviewers)
        self.assertEqual(actual, expected)
    
    # Test start outside, end inside
    def test_start_out_end_in(self):
        slot_start = utc_dt(2025, 10, day=9, hour=10)
        slot_end = utc_dt(2025, 10, day=9, hour=12)
        
        expected = [[utc_dt(2025, 10, day=9, hour=11), utc_dt(2025, 10, day=9, hour=12)]]
        actual = trim_slot_to_available_workdays(slot_start, slot_end, self.interviewers)
        self.assertEqual(actual, expected)
    
    # Test start inside, end outside
    def test_start_in_end_out(self):
        slot_start = utc_dt(2025, 10, day=9, hour=16)
        slot_end = utc_dt(2025, 10, day=9, hour=20)
        
        expected = [[utc_dt(2025, 10, day=9, hour=16), utc_dt(2025, 10, day=9, hour=17)]]
        actual = trim_slot_to_available_workdays(slot_start, slot_end, self.interviewers)
        self.assertEqual(actual, expected)
        
    # Test multi-day window spanning multiple workdays
    def test_multi_day_window(self):
        slot_start = utc_dt(2025, 10, day=9, hour=7)
        slot_end = utc_dt(2025, 10, day=12, hour=14)
        
        expected = [
            [utc_dt(2025, 10, day=9, hour=11), utc_dt(2025, 10, day=9, hour=17)],
            [utc_dt(2025, 10, day=10, hour=11), utc_dt(2025, 10, day=10, hour=17)],
            [utc_dt(2025, 10, day=11, hour=11), utc_dt(2025, 10, day=11, hour=17)],
            [utc_dt(2025, 10, day=12, hour=11), utc_dt(2025, 10, day=12, hour=14)],
        ]
        actual = actual = trim_slot_to_available_workdays(slot_start, slot_end, self.interviewers)
        self.assertEqual(actual, expected)
        
        
class buildAvailableWorkdaySlotTests(SimpleTestCase):
    def setUp(self):
        self.standard_start = utc_dt(2025, 10, day=9, hour=13)
        
    # Test standard utc workday
    def test_standard_utc_workday(self):
        test_interviewers = [
            SimpleNamespace(workday_start_hour=9,workday_end_hour=17,timezone="UTC"),
            SimpleNamespace(workday_start_hour=7,workday_end_hour=15,timezone="UTC")
            ]
        # 9 - 17 utc
        # 7 - 15 utc
        # expected 9 - 15 
         
        expected = [utc_dt(2025, 10, day=9, hour=9), utc_dt(2025, 10, 9, hour=15)]
        actual = build_available_workday_slot(self.standard_start,  test_interviewers)
        self.assertEqual(actual, expected)
        
    # Test EST standard workday with PST workday
    def test_est_with_pst(self):
        test_interviewers = [
            SimpleNamespace(workday_start_hour=9,workday_end_hour=17,timezone="America/New_York"),
            SimpleNamespace(workday_start_hour=9,workday_end_hour=17,timezone="America/Los_Angeles")
        ]
        # 9 - 17 est = 13 - 21 utc
        # 9 - 17 pst = 16 - 0 utc
        # expected 16 - 21
        
        expected = [utc_dt(2025, 10, day=9, hour=16), utc_dt(2025, 10, day=9, hour=21)]
        actual = build_available_workday_slot(self.standard_start, test_interviewers)
        self.assertEqual(actual, expected)
        
    # Test est overnight shift to utc
    def test_overnight_est(self):
        test_interviewers = [
            SimpleNamespace(workday_start_hour=18,workday_end_hour=4,timezone="America/New_York"),
        ]
        
        expected = [utc_dt(2025,10, day=9, hour=22), utc_dt(2025, 10, day=10, hour=8) ]
        actual = build_available_workday_slot(self.standard_start, test_interviewers)
        self.assertEqual(actual, expected)
        
    def test_overnight_on_dst_day(self):
        slot_start = utc_dt(2026, 3, day=7, hour=22)

        test_interviewers = [
            SimpleNamespace(workday_start_hour=18,workday_end_hour=4,timezone="America/New_York"),
        ]
        # Expected:
        # start - March 7th 18:00 EST = 23:00 UTC (-5)
        # end - March 8th 4:00 EST = 8:00 UTC (-4)
        
        expected = [utc_dt(2026,3, day=7, hour=23), utc_dt(2026, 3, day=8, hour=8) ]
        actual = build_available_workday_slot(slot_start,  test_interviewers)
        
        self.assertEqual(actual, expected)
    
      
class buildAvailableWindowsTests(SimpleTestCase):
    def setUp(self):
        self.interviewers = [
             SimpleNamespace(workday_start_hour=9,workday_end_hour=17,timezone="UTC"),
        ]
        self.valid_interval = 30
    
    # Test standard window    
    def test_standard_window(self):
        busy_windows = [
            [utc_dt(2025, 10, day=6, hour=9), utc_dt(2025, 10, day=6, hour=12)],
            [utc_dt(2025, 10, day=6, hour=17), utc_dt(2025, 10, day=6, hour=20)],
        ]
        expected = [
            [utc_dt(2025, 10, day=6, hour=12), utc_dt(2025, 10, day=6, hour=17)]
        ]
        actual = build_available_windows(busy_windows, self.interviewers, self.valid_interval)
        self.assertEqual(actual,expected)
        
    def test_multiple_windows(self):
        busy_windows = [
            [utc_dt(2025, 10, day=6, hour=9), utc_dt(2025, 10, day=6, hour=10)],
            [utc_dt(2025, 10, day=6, hour=12, minute=30), utc_dt(2025, 10, day=6, hour=13)],
            [utc_dt(2025, 10, day=6, hour=14), utc_dt(2025, 10, day=6, hour=15)],
            [utc_dt(2025, 10, day=6, hour=17), utc_dt(2025, 10, day=6, hour=20)],
        ]
        
        expected = [
            [utc_dt(2025, 10, day=6, hour=10), utc_dt(2025, 10, day=6, hour=12, minute=30)],
            [utc_dt(2025, 10, day=6, hour=13), utc_dt(2025, 10, day=6, hour=14)],
            [utc_dt(2025, 10, day=6, hour=15), utc_dt(2025, 10, day=6, hour=17)],
        ]
        actual = build_available_windows(busy_windows, self.interviewers, self.valid_interval)
        self.assertEqual(actual,expected)

class buildAvailableInterviewSlotsTests(SimpleTestCase):
    
    def test_one_hour_slot(self):
        interval = 60
        duration = 60
        available_windows = [
            [utc_dt(2025, 10, day=6, hour=6), utc_dt(2025, 10, day=6, hour=10)]
        ]
        expected = [
            [utc_dt(2025, 10, day=6, hour=6), utc_dt(2025, 10, day=6, hour=7)],
            [utc_dt(2025, 10, day=6, hour=7), utc_dt(2025, 10, day=6, hour=8)],
            [utc_dt(2025, 10, day=6, hour=8), utc_dt(2025, 10, day=6, hour=9)],
            [utc_dt(2025, 10, day=6, hour=9), utc_dt(2025, 10, day=6, hour=10)]
        ]
        actual = build_available_interview_slots(available_windows, interval, duration)
        self.assertEqual(actual, expected)
        
    def test_thirty_minute_slot(self):
        interval = 30
        duration = 30
        available_windows = [
            [utc_dt(2025, 10, day=6, hour=6), utc_dt(2025, 10, day=6, hour=8)]
        ]
        expected = [
            [utc_dt(2025, 10, day=6, hour=6), utc_dt(2025, 10, day=6, hour=6, minute=30)],
            [utc_dt(2025, 10, day=6, hour=6, minute=30), utc_dt(2025, 10, day=6, hour=7)],
            [utc_dt(2025, 10, day=6, hour=7), utc_dt(2025, 10, day=6, hour=7, minute=30)],
            [utc_dt(2025, 10, day=6, hour=7, minute=30), utc_dt(2025, 10, day=6, hour=8)],
        ]
        actual = build_available_interview_slots(available_windows, interval, duration)
        self.assertEqual(actual, expected)
    

    def test_forty_five_interval_fit(self):
        interval = 45
        duration = 45
        available_windows = [
            [utc_dt(2025, 10, day=6, hour=6, minute=45), utc_dt(2025, 10, day=6, hour=7, minute=40)]
        ]
        expected = [[utc_dt(2025, 10, day=6, hour=6, minute=45), utc_dt(2025, 10, day=6, hour=7, minute=30)]]
        actual = build_available_interview_slots(available_windows, interval, duration)
        self.assertEqual(actual, expected)

    def test_one_minute_slot(self):
        interval = 1
        duration = 1
        available_windows = [
            [utc_dt(2025, 10, day=6, hour=6), utc_dt(2025, 10, day=6, hour=6, minute=3)]
        ]
        expected = [
            [utc_dt(2025, 10, day=6, hour=6), utc_dt(2025, 10, day=6, hour=6, minute=1)],
            [utc_dt(2025, 10, day=6, hour=6, minute=1), utc_dt(2025, 10, day=6, hour=6, minute=2)],
            [utc_dt(2025, 10, day=6, hour=6, minute=2), utc_dt(2025, 10, day=6, hour=6, minute=3)],
        ]
        actual = build_available_interview_slots(available_windows, interval, duration)
        self.assertEqual(actual, expected)
        
    def test_5_min_interval_30_min_duration(self):
        interval = 5
        duration = 30
        available_windows = [
            [utc_dt(2025, 10, day=6, hour=6), utc_dt(2025, 10, day=6, hour=7)]
        ]
        expected = [
            [utc_dt(2025, 10, day=6, hour=6), utc_dt(2025, 10, day=6, hour=6, minute=30)],
            [utc_dt(2025, 10, day=6, hour=6, minute=5), utc_dt(2025, 10, day=6, hour=6, minute=35)],
            [utc_dt(2025, 10, day=6, hour=6, minute=10), utc_dt(2025, 10, day=6, hour=6, minute=40)],
            [utc_dt(2025, 10, day=6, hour=6, minute=15), utc_dt(2025, 10, day=6, hour=6, minute=45)],
            [utc_dt(2025, 10, day=6, hour=6, minute=20), utc_dt(2025, 10, day=6, hour=6, minute=50)],
            [utc_dt(2025, 10, day=6, hour=6, minute=25), utc_dt(2025, 10, day=6, hour=6, minute=55)],
            [utc_dt(2025, 10, day=6, hour=6, minute=30), utc_dt(2025, 10, day=6, hour=7)],
        ]
        actual = build_available_interview_slots(available_windows, interval, duration)
        self.assertEqual(actual, expected)
        
    def test_no_fit(self):
        interval = 30
        duration = 30
        available_windows = [
            [utc_dt(2025, 10, day=6, hour=6), utc_dt(2025, 10, day=6, hour=6, minute=20)]
        ]
        expected = []
        actual = build_available_interview_slots(available_windows, interval, duration)
        self.assertEqual(actual, expected)
           
# ------------------------ Test util helpers -----------------------------

class ceilSlotToInterval(SimpleTestCase):

    # Test round up with 60-minute interval
    def test_round_up_60_min(self):
        date = utc_dt(2025, 10, day=9, hour=13, minute=10, second=22)
        # 13:10:22 -> 14:00:00
        expected = utc_dt(2025, 10, day=9, hour=14)
        actual = ceil_slot_to_interval(date, 60)
        self.assertEqual(actual, expected)

    # Test round up with 30-minute interval just before boundary
    def test_round_up_30_min_before(self):
        # 13:29:59 -> 13:30:00
        date = utc_dt(2025, 10, day=9, hour=13, minute=29, second=59)
        expected = utc_dt(2025, 10, day=9, hour=13, minute=30)
        actual = ceil_slot_to_interval(date, 30)
        self.assertEqual(actual, expected)

    # Test round up with 30-minute interval after boundary
    def test_round_up_30_min_after(self):
        # 13:30:22 -> 14:00:00
        date = utc_dt(2025, 10, day=9, hour=13, minute=30, second=22)
        
        expected = utc_dt(2025, 10, day=9, hour=14)
        actual = ceil_slot_to_interval(date, 30)
        self.assertEqual(actual, expected)

    # Test round up with 15-minute interval
    def test_round_up_15_min(self):
        # 13:37:42 -> 13:45:00
        date = utc_dt(2025, 10, day=9, hour=13, minute=37, second=42)  
        expected = utc_dt(2025, 10, day=9, hour=13, minute=45)
        actual = ceil_slot_to_interval(date, 15)
        self.assertEqual(actual, expected)

    # Test round up with 10-minute interval
    def test_round_up_10_min(self):
        # 13:01:00 -> 13:10:00
        date = utc_dt(2025, 10, day=9, hour=13, minute=1, second=0)
        expected = utc_dt(2025, 10, day=9, hour=13, minute=10)
        actual = ceil_slot_to_interval(date, 10)
        self.assertEqual(actual, expected)

    # Test round up with 5-minute interval
    def test_round_up_5_min(self):
        # 13:04:00 -> 13:05:00
        date = utc_dt(2025, 10, day=9, hour=13, minute=4, second=0)
        expected = utc_dt(2025, 10, day=9, hour=13, minute=5)
        actual = ceil_slot_to_interval(date, 5)
        self.assertEqual(actual, expected)

    # Test round up with 1-minute interval
    def test_round_up_1_min(self):
        # 13:10:01 -> 13:11:00
        date = utc_dt(2025, 10, day=9, hour=13, minute=10, second=1)
        expected = utc_dt(2025, 10, day=9, hour=13, minute=11)
        actual = ceil_slot_to_interval(date, 1)
        self.assertEqual(actual, expected)
        
        
        
        
    
        
    
            
    

        
        
    
        
    
    
        
        
    
    

        

