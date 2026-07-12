#!/usr/bin/env python3
"""
Simple sequence helper for quick operations.
Most sequence management should be done through the web UI.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def list_sequences():
    """List all sequences"""
    from backend.core.database import SessionLocal
    from backend.models.sequence import Sequence
    
    db = SessionLocal()
    try:
        sequences = db.query(Sequence).all()
        
        print("📋 Current Sequences:")
        print("-" * 50)
        
        if not sequences:
            print("No sequences found.")
        else:
            for seq in sequences:
                print(f"• {seq.name} ({seq.code})")
                print(f"  Preview: {seq.preview_format()}")
                print(f"  Next: {seq.number_next}, Active: {seq.active}")
                print()
                
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

def reset_sequence(code: str, number: int = 1):
    """Reset a sequence to a specific number"""
    from backend.core.database import SessionLocal
    from backend.models.sequence import Sequence
    
    db = SessionLocal()
    try:
        sequence = db.query(Sequence).filter(Sequence.code == code).first()
        
        if not sequence:
            print(f"❌ Sequence '{code}' not found")
            return False
            
        old_next = sequence.number_next
        sequence.reset_sequence(db, number)
        
        print(f"✅ Reset sequence '{code}' from {old_next} to {number}")
        print(f"   Next preview: {sequence.preview_format()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("🔧 Sequence Helper")
        print("Usage:")
        print("  python3 sequence_helper.py list")
        print("  python3 sequence_helper.py reset <code> [number]")
        print()
        print("Examples:")
        print("  python3 sequence_helper.py list")
        print("  python3 sequence_helper.py reset student.student 1")
        print()
        print("💡 For full sequence management, use the web UI:")
        print("   Settings > Sequences")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "list":
        list_sequences()
    elif command == "reset":
        if len(sys.argv) < 3:
            print("❌ Missing sequence code")
            print("Usage: python3 sequence_helper.py reset <code> [number]")
            sys.exit(1)
            
        code = sys.argv[2]
        number = int(sys.argv[3]) if len(sys.argv) > 3 else 1
        
        if reset_sequence(code, number):
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        print(f"❌ Unknown command: {command}")
        print("Available commands: list, reset")
        sys.exit(1)