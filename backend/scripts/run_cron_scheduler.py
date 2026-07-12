#!/usr/bin/env python3
"""
Run the cron scheduler to execute due jobs.
This script can be run manually or by an external scheduler (like system cron).
"""

import sys
import os
from datetime import datetime

# Add the project root directory to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def main():
    """Run the cron scheduler"""
    print(f"🕒 Cron Scheduler - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    try:
        from backend.core.cron_definitions import run_cron_scheduler
        
        # Run the scheduler
        result = run_cron_scheduler()
        
        print(f"📊 Execution Summary:")
        print(f"   Total jobs checked: {result['total']}")
        print(f"   Successfully executed: {result['executed']}")
        print(f"   Failed executions: {result['failed']}")
        
        if result['results']:
            print(f"\n📋 Job Details:")
            for job_result in result['results']:
                status = "✅" if job_result['success'] else "❌"
                print(f"   {status} {job_result['code']}: {job_result['message']}")
        
        if result['total'] == 0:
            print("   No jobs were due for execution")
            
        print(f"\n✅ Scheduler run completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"❌ Scheduler Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()