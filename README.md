## Overview 

Improved Interview slot generator by Gavin Augsburger

## Approach

Break problem down into multiple parts with an orchestrator function, removing clutter from views file.
All helper functions are tested thoroughly with extensive unit tests for easy detection of bugs and edge case catching.

Orchestrator function:

compute_available_slots()   
    -Trim array to within search window O(n) (do this before sort)  
    -Build Busy window - combine intervals (Requires sort) O(nlogn)  
    -Build available windows (apply interviewer workday and interval start constraints as we build available windows) O(n)  
    -Build Interview Slots from available windows O(n)

Individual workday contraints are computed per day to avoid DST edge cases, and overnight shifts are taken into account by creating datetime values for comparision instead of integer comparison


### Set Up

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd candidate_fyi_takehome_project
   ```

2. Start the development environment:
   ```bash
   make up
   ```
   or
   ```bash
   docker-compose -f docker-compose.local.yml up -d
   ```
3. Run Unit tests:
  ```bash
   make manage ARGS="test"
   ```
   or
   ```bash
   docker compose run --rm django python ./manage.py test
   ```

4. Seed the database with a test interviewtemplate with 3 interviewers of differing US timezone workdays:
   ```bash
   make seed
   ```
   or
   ```bash
   docker compose run --rm django python ./manage.py seed_interviews
   ```

5. Access the API at:
   ```
   http://localhost:8000/api/
   ```

5. Test the API endpoint:
   ```
   http://localhost:8000/api/interviews/<int:templateid>/availability/
   ```

   Optional query parameters:
   - `search_start`: ISO 8601 datetime (default: 24 hours from now) - start of search window
   - `search_end`: ISO 8601 datetime (default: start + 7 days) - end of search window
   - `valid_interval_end`: Integer (60, 30, 15, 10, 5, 1) (default 30) - valid intervals the slots can end/start on 

