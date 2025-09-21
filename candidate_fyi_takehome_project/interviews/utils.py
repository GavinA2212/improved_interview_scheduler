from typing import List
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import logging

logger = logging.getLogger(__name__)


from candidate_fyi_takehome_project.interviews.models import Interviewer

def utc_dt(year:int, month:int, day:int, hour:int, minute:int=0, second:int=0, millisecond:int=0):
    return datetime(year, month, day, hour, minute, second, millisecond, tzinfo=timezone.utc)
    

def trim_busy_slots_to_search_window(search_start:datetime, search_end:datetime, busy_slots):
    """ 
    Trim busy blocks to search window to avoid expensive sorting of busy blocks outside of search window
    """
    
    trimmed_slots = []
    # Add start boundary slot
    trimmed_slots.append([search_start - timedelta(hours=1), search_start])
    
    for slot in busy_slots:
        if isinstance(slot["start"], str):
            slot_start = datetime.fromisoformat(slot["start"].replace('Z', '+00:00'))
        else:
            slot_start = slot["start"].astimezone(timezone.utc)   
        if isinstance(slot["end"], str):
            slot_end = datetime.fromisoformat(slot["end"].replace('Z', '+00:00'))
        else:
            slot_end = slot["end"].astimezone(timezone.utc)
        
        if slot_start < search_start and slot_end > search_start:
            slot_start = search_start
        if slot_end > search_end and slot_start < slot_end:
            slot_end = search_end
        if slot_start>= search_start and slot_end <= search_end:
            trimmed_slots.append([slot_start, slot_end])
        # Slots completely outside of search window get ignored
            
    # Add end boundary slot
    trimmed_slots.append([search_end, search_end + timedelta(hours=1)])
            
    return trimmed_slots
 
 
def build_busy_windows(busy_slots):
    """
    Builds non overlapping busy window intervals
    """
    if not busy_slots:
        return []
    
    # Sort by start time
    busy_slots.sort(key = lambda x: x[0])
    
    busy_windows = [busy_slots[0]]  # Fixed initialization
    
    for slot in busy_slots[1:]:
        slot_start = slot[0]
        slot_end = slot[1]
        prev_end = busy_windows[-1][1]
        
        if slot_start <= prev_end:
            # Merge intervals together if overlapping
            busy_windows[-1][1] = max(prev_end, slot_end)
        else:
            busy_windows.append([slot_start, slot_end])
    
    return busy_windows

def build_available_workday_slot(slot_start:datetime, slot_end:datetime, interviewers: List[Interviewer] ):
    """"
    Build a workday availability slot for a specific slot, this needs to be computed per slot due to DST edge cases 
    """
    wd_starts_utc = []
    wd_ends_utc = []
    
    for interviewer in interviewers:
        tz = ZoneInfo(interviewer.timezone)
        # Convert slot_start to interviewers timezone 
        local_start = slot_start.astimezone(tz)
        y, m, d = local_start.year, local_start.month, local_start.day
        
        # Create datetime objects of the same day as the local start with the interviewers workday hours
        workday_start = datetime(year=y, month=m, day=d, hour=interviewer.workday_start_hour, tzinfo=tz) 
        workday_end = datetime(year=y, month=m, day=d, hour=interviewer.workday_end_hour, tzinfo=tz) 
        
        # Overnight shift
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
        

def trim_slot_to_available_workdays(slot_start:datetime, slot_end:datetime, interviewers:List[Interviewer]):
    valid_workday_window = [0, datetime(1,1,1,tzinfo=timezone.utc)]
    current_start = slot_start
    current_end = slot_end
    valid_slots = []
    
    # Find more slots
    while slot_end > valid_workday_window[1]:
        valid_workday_window = build_available_workday_slot(current_start, slot_end, interviewers)
        workday_start = valid_workday_window[0]
        workday_end = valid_workday_window[1]
        
        if slot_end < workday_start or slot_start > workday_end:
            break
        
        # Trim up start to workday start
        if current_start < workday_start:
            current_start = workday_start
        # Trim End down to workday end, else use original end (final day of trim)
        if slot_end > workday_end:
            current_end = workday_end
        else:
            current_end = slot_end
            
        valid_slots.append([current_start, current_end])
        current_start = workday_start + timedelta(hours=24)
        
    return valid_slots if len(valid_slots) > 0 else None
        
    
    '''
    
    
    # Trim slot to available workday window
    
    if slot_start < workday_start:
        slot_start = workday_start
    if slot_end > workday_end:
        slot_end = workday_end
     '''
        
        
    return [slot_start, slot_end]

def ceil_slot_to_interval(date:datetime, valid_interval:int):
    '''
        rounds slot to the next interval multiple given the interval.
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
    
    
    
def build_available_windows(busy_windows, interviewers, valid_interval):
    available_windows=[]
    
    if not busy_windows:
        return available_windows
        
    prev = busy_windows[0]
    
    for slot in busy_windows[1:]:
        slot_start = slot[0]
        prev_end = prev[1]
        
        if(slot_start <= prev_end):
            prev = slot
            continue
        # prev_end -> slot_start = an available window
        
        # Trim the available window down to slots in workday (can be multiple if window spans multiple days)
        valid_slots = trim_slot_to_available_workdays(prev_end, slot_start, interviewers)
        
        if valid_slots:
            for valid_slot in valid_slots:
                # Round start values up to a valid interval multiple for later 
                start = ceil_slot_to_interval(valid_slot[0], valid_interval)
                end = valid_slot[1]
                available_windows.append([start, end])
        prev = slot
                
    return available_windows
            
            
def build_available_interview_slots(available_windows, valid_interval, duration):
    available_interview_slots = []
    for slot in available_windows:
        window_end=slot[1]
        current_slot_start = slot[0]
        current_slot_end = current_slot_start + timedelta(minutes=duration)
        
        while current_slot_end <= window_end:
            available_interview_slots.append([current_slot_start, current_slot_end])
            current_slot_end+=timedelta(minutes=valid_interval)
            current_slot_start+=timedelta(minutes=valid_interval)
        
    return available_interview_slots
    
    
def compute_available_slots(search_start: datetime, search_end:datetime, valid_interval:int, busy_data:object, interviewers: List[Interviewer], duration:int):
    '''
    Trim array to within search window O(n) (do this before sort)
    Build Busy window - combine intervals (Requires sort) O(nlogn)
    Build available windows (apply interviewer workday and interval start constraints) O(n)
    Build Interview Slots from available windows O(n)
    '''
    search_window_constrained_busy_slots = trim_busy_slots_to_search_window(search_start, search_end, busy_data)
    busy_windows = build_busy_windows(search_window_constrained_busy_slots)
    available_windows = build_available_windows(busy_windows, interviewers, valid_interval)
    available_interview_slots = build_available_interview_slots(available_windows, valid_interval, duration)
    
    return available_interview_slots