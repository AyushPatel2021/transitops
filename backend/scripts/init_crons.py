#!/usr/bin/env python3
"""
Initialize cron jobs from static definitions.
This script can be run standalone or as part of the application startup.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def main():
    """Initialize cron jobs from definitions"""
    print("🕒 Cron Job Initialization")
    print("=" * 50)
    
    try:
        from backend.core.cron_definitions import initialize_crons, CRON_DEFINITIONS
        
        print("📋 Defined Cron Jobs:")
        for code, definition in CRON_DEFINITIONS.items():
            print(f"   • {code}: {definition['name']}")
            print(f"     Model: {definition['model_name']}")
            print(f"     Function: {definition['function_name']}")
            print(f"     Schedule: Every {definition['interval_number']} {definition['interval_type']}")
            print(f"     Priority: {definition['priority']}")
            print()
        
        print("🚀 Initializing cron jobs...")
        initialize_crons()
        
        print("✅ Cron job initialization completed!")
        
        # Show current status
        print("\n📊 Current Cron Job Status:")
        from backend.core.database import SessionLocal
        from backend.models.cron import Cron
        
        db = SessionLocal()
        try:
            crons = db.query(Cron).all()
            for cron in crons:
                status = "🟢 Active" if cron.active else "🔴 Inactive"
                print(f"   {status} {cron.code}: Next run at {cron.next_call}")
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()