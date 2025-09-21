from typing import List
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import logging

logger = logging.getLogger(__name__)

from candidate_fyi_takehome_project.interviews.models import Interviewer


# ------------------------- InterviewAvailability util functions ------------------------
def compute_available_slots(search_start: datetime, search_end:datetime, valid_interval:int, busy_data:object, interviewers: List[Interviewer], duration:int):
    '''
    Orchestrator - Builds available interview slots
    1). Trim busy array to within search window O(n) (do this before sort)
    2). Build non overlapping Busy windows - combine intervals (Requires sort) O(nlogn)
    3). Build available windows, applying interviewers workday contraints per day and interval rounding up O(n)
    4). Build Interview Slots from available windows O(n)
    '''
    search_window_constrained_busy_slots = trim_busy_slots_to_search_window(search_start, search_end, busy_data)
    busy_windows = build_busy_windows(search_window_constrained_busy_slots)
    available_windows = build_available_windows(busy_windows, interviewers, valid_interval)
    available_interview_slots = build_available_interview_slots(available_windows, valid_interval, duration)
    
    return available_interview_slots
    

def trim_busy_slots_to_search_window(search_start:datetime, search_end:datetime, busy_slots):
    """ 
    Trim busy blocks to be in search window, throw out blocks outside of window
    Adds boundary search start and search end busy slots
    Avoids expensive sorting of unneeded busy blocks later
    """
    
    trimmed_slots = []
    # Add start boundary slot, start of search window
    trimmed_slots.append([search_start - timedelta(hours=1), search_start])
    
    for slot in busy_slots:
        # Convert to iso format
        if isinstance(slot["start"], str):
            slot_start = datetime.fromisoformat(slot["start"].replace('Z', '+00:00'))
        else:
            slot_start = slot["start"].astimezone(timezone.utc)   
        if isinstance(slot["end"], str):
            slot_end = datetime.fromisoformat(slot["end"].replace('Z', '+00:00'))
        else:
            slot_end = slot["end"].astimezone(timezone.utc)
        
        # Trim up start - Search window: 5:00-9:00 - Busy 3:00-7:00 -> 5:00-7:00
        if slot_start < search_start and slot_end > search_start:
            slot_start = search_start
        # Trim back end - Search window: 5:00-9:00 - Busy 8:00-12:00 -> 8:00 ->9:00
        if slot_end > search_end and slot_start < slot_end:
            slot_end = search_end
        # Fully within search window, add slot as is
        if slot_start>= search_start and slot_end <= search_end:
            trimmed_slots.append([slot_start, slot_end])
        # Slots completely outside of search window get ignored
            
    # Add end boundary slot, end of search window
    trimmed_slots.append([search_end, search_end + timedelta(hours=1)])
            
    return trimmed_slots
 
 
def build_busy_windows(busy_slots):
    """
    Merge together overlapping busy slots, Requires sort to merge intervals
    Returns array of nonoverlapping busy windows
    """
    if not busy_slots:
        return []
    
    # Sort by start time
    busy_slots.sort(key = lambda x: x[0])
    
    # Initialize previous slot to start of array
    busy_windows = [busy_slots[0]]  
    
    # Loop starting at 2nd slot, merging overlapping intervals
    for slot in busy_slots[1:]:
        slot_start = slot[0]
        slot_end = slot[1]
        prev_end = busy_windows[-1][1]
        
        if slot_start <= prev_end:
            # Merge intervals together if overlapping by extending previous slot
            busy_windows[-1][1] = max(prev_end, slot_end)
        else:
            busy_windows.append([slot_start, slot_end])
    
    return busy_windows

def build_available_windows(busy_windows, interviewers, valid_interval):
    '''
    Build array of available windows off of the busy windows
    Available windows get trimmed to be within each days workday contraints
    Start times get rounded up to the provided valid interval for later processing
    '''
    available_windows=[]
    
    if not busy_windows:
        return available_windows
    # Keep track of first busy window
    prev = busy_windows[0]
    # Loop over busy_windows starting at 2nd window, creating available windows
    for current_slot in busy_windows[1:]:
        current_slot_start = current_slot[0]
        prev_end = prev[1]
        # Move to next iteration if invalid slot_start > prev_end = an available window
        if(current_slot_start <= prev_end):
            prev = current_slot
            continue
        
        # prev_end -> slot_start = available window
        # Trim the available window down to slots in workday (can be multiple if window spans multiple days)
        valid_slots = trim_slot_to_available_workdays(prev_end, current_slot_start, interviewers)
        
        # Loop over valid slots, adding available windows
        if valid_slots:
            for valid_slot in valid_slots:
                # Round start values up to a valid interval multiple for later 
                valid_slot_start = ceil_slot_to_interval(valid_slot[0], valid_interval)
                valid_slot_end = valid_slot[1]
                available_windows.append([valid_slot_start, valid_slot_end])
        prev = current_slot
                
    return available_windows

def trim_slot_to_available_workdays(slot_start:datetime, slot_end:datetime, interviewers:List[Interviewer]):
    '''
    Trims an available window to slot(s) within interviewers workdays
    
    '''
    # Initialize window_end to floor value for comparison later
    valid_workday_window = [0, datetime(1,1,1,tzinfo=timezone.utc)]
    
    # Current start and end is used for day to day values for multi day spans
    current_start = slot_start
    current_end = slot_end
    valid_slots = []
    
    # Loop incase of window spanning multiple workdays, always runs atleast once
    while slot_end > valid_workday_window[1]:
        # Get first day available times
        valid_workday_window = build_available_workday_slot(current_start, interviewers)
        workday_start = valid_workday_window[0]
        workday_end = valid_workday_window[1]
        
        # End loop when slot completely outside of computed workday
        if slot_end < workday_start or slot_start > workday_end:
            break
        
        # Trim up current start to workday start
        if current_start < workday_start:
            current_start = workday_start
            
        # Trim current End down to workday end, else use original end (final day of trim)
        if slot_end > workday_end:
            current_end = workday_end
        else:
            current_end = slot_end
            
        valid_slots.append([current_start, current_end])
        # Begin next day
        current_start = workday_start + timedelta(hours=24)
        
    return valid_slots if len(valid_slots) > 0 else None

def build_available_workday_slot(slot_start:datetime, interviewers: List[Interviewer] ):
    """"
    Build a workday availability slot for a specific slot, this needs to be computed per slot due to DST edge cases 
    """
    wd_starts_utc = []
    wd_ends_utc = []
    
    for interviewer in interviewers:
        interviewer_tz = ZoneInfo(interviewer.timezone)
        # Convert slot_start to interviewers timezone 
        local_start = slot_start.astimezone(interviewer_tz)
        y, m, d = local_start.year, local_start.month, local_start.day
        
        # Create datetime objects of the same day as the local start with the interviewers workday hours
        # This works around DST since we compute per day
        workday_start = datetime(year=y, month=m, day=d, hour=interviewer.workday_start_hour, tzinfo=interviewer_tz) 
        workday_end = datetime(year=y, month=m, day=d, hour=interviewer.workday_end_hour, tzinfo=interviewer_tz) 
        
        # Overnight shift case
        if workday_start >= workday_end:
            workday_end += timedelta(days=1)
            
        # Convert to utc
        wd_start_utc = workday_start.astimezone(timezone.utc)
        wd_end_utc = workday_end.astimezone(timezone.utc)
        
        # Add to lists
        wd_starts_utc.append(wd_start_utc)
        wd_ends_utc.append(wd_end_utc)
    
    # Find earliest_start and latest_end to find available interval across all interviewers     
    earliest_start = max(wd_starts_utc)
    latest_end = min(wd_ends_utc)
    
    return [earliest_start, latest_end]

def build_available_interview_slots(available_windows, valid_interval, duration):
    """
    Build available interview slots of the provided duration and increasing interval from all available windows
    Ex with one window:
        duration=30 - valid_interval=5 - start=8:00 - end=8:45
        result = [[8:00->8:30], [8:05->8:35], [8:10->8:40], [8:15>-8:45]]
     
    """
    available_interview_slots = []
    
    for slot in available_windows:
        window_end=slot[1]
        current_slot_start = slot[0]
        current_slot_end = current_slot_start + timedelta(minutes=duration)
        
        # Create all possible interview slots within window
        while current_slot_end <= window_end:
            available_interview_slots.append([current_slot_start, current_slot_end])
            current_slot_end+=timedelta(minutes=valid_interval)
            current_slot_start+=timedelta(minutes=valid_interval)
        
    return available_interview_slots
        

# ------------------ Helpers -------------------------
def ceil_slot_to_interval(date:datetime, valid_interval:int):
    '''
        rounds datetime to the next interval multiple given the interval.
        x:30:22 -> x:00:00 (30)
        x:37:42 -> x:45:00 (15)
    '''
    if (date.minute == date.second == date.microsecond == 0):
        return date
    
    # find next valid interval, subtract date.min,s,ms from it then add that value to date to reach interval
    trimmed_date = timedelta(minutes=date.minute, seconds=date.second, microseconds=date.microsecond)
    i = valid_interval
    while trimmed_date >= timedelta(minutes=i):
        i+=valid_interval
    next_valid_interval = timedelta(minutes=i)
    dif = next_valid_interval - trimmed_date
    date += dif
    
    return date

def utc_dt(year:int, month:int, day:int, hour:int, minute:int=0, second:int=0, millisecond:int=0):
    '''
    Create utc datetime
    '''
    return datetime(year, month, day, hour, minute, second, millisecond, tzinfo=timezone.utc)
    
    
    

            
            

    
    
