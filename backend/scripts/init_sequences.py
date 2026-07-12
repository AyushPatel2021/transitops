#!/usr/bin/env python3
"""
Initialize sequences using the static definitions.
This is now automatically called on server startup.
"""

import sys
import os
# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def main():
    """Initialize sequences from static definitions"""
    print("🔧 Initializing Sequences from Static Definitions")
    print("=" * 50)
    
    try:
        from backend.core.sequence_definitions import initialize_sequences, SEQUENCE_DEFINITIONS
        
        print("📋 Defined Sequences:")
        for code, definition in SEQUENCE_DEFINITIONS.items():
            print(f"  • {definition['name']} ({code})")
            print(f"    Format: {definition['prefix']}{'0' * definition['padding']}")
            print()
        
        print("🚀 Initializing sequences...")
        initialize_sequences()
        
        print("✅ Sequence initialization completed!")
        print()
        print("💡 To manage sequences:")
        print("  1. Use the web UI: Settings > Sequences")
        print("  2. Or use: python3 backend/scripts/sequence_helper.py list")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)