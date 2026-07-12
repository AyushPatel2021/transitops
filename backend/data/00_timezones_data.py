"""
Timezone data initialization
This file is loaded on first app startup to populate timezone data
"""
import pytz
from datetime import datetime

def get_timezone_records():
    """Generate timezone records from pytz"""
    records = {}
    
    # Common timezones to prioritize
    common_tz = [
        'UTC',
        'America/New_York',
        'America/Chicago',
        'America/Denver',
        'America/Los_Angeles',
        'America/Toronto',
        'America/Mexico_City',
        'America/Sao_Paulo',
        'Europe/London',
        'Europe/Paris',
        'Europe/Berlin',
        'Europe/Madrid',
        'Europe/Rome',
        'Europe/Moscow',
        'Asia/Dubai',
        'Asia/Kolkata',
        'Asia/Shanghai',
        'Asia/Tokyo',
        'Asia/Singapore',
        'Asia/Hong_Kong',
        'Australia/Sydney',
        'Australia/Melbourne',
        'Pacific/Auckland',
    ]
    
    # Add common timezones first
    for tz_name in common_tz:
        if tz_name in pytz.all_timezones:
            try:
                tz = pytz.timezone(tz_name)
                now = datetime.now(tz)
                offset = now.strftime('%z')
                # Format offset as +HH:MM or -HH:MM
                if offset:
                    offset_formatted = f"{offset[:3]}:{offset[3:]}"
                else:
                    offset_formatted = "+00:00"
                
                display_name = tz_name.replace('_', ' ')
                xml_id = f'tz_{tz_name.lower().replace("/", "_").replace("_", "")}'
                
                records[xml_id] = {
                    'model': 'timezone',
                    'values': {
                        'name': tz_name,
                        'display_name': display_name,
                        'offset': offset_formatted
                    },
                    'noupdate': True
                }
            except Exception:
                pass
    
    # Add all other timezones
    for tz_name in sorted(pytz.all_timezones):
        if tz_name not in common_tz:
            try:
                tz = pytz.timezone(tz_name)
                now = datetime.now(tz)
                offset = now.strftime('%z')
                if offset:
                    offset_formatted = f"{offset[:3]}:{offset[3:]}"
                else:
                    offset_formatted = "+00:00"
                
                display_name = tz_name.replace('_', ' ')
                xml_id = f'tz_{tz_name.lower().replace("/", "_").replace("_", "")}'
                
                records[xml_id] = {
                    'model': 'timezone',
                    'values': {
                        'name': tz_name,
                        'display_name': display_name,
                        'offset': offset_formatted
                    },
                    'noupdate': True
                }
            except Exception:
                pass
    
    return records

# Data to be loaded
RECORDS = get_timezone_records()
