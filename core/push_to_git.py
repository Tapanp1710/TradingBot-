"""
Simple Git Push Function - One Command Does Everything
November 5, 2025
"""

import os
import subprocess
import sys


def push_to_git(commit_message=None):
    """
    Simple one-function push to GitHub
    
    Usage:
        python push_to_git.py "Your commit message"
        
    Or in Python:
        push_to_git("v6.4 - Adaptive threshold system")
    """
    
    # Default message if none provided
    if commit_message is None:
        commit_message = "Update: v6.4 adaptive threshold system"
    
    try:
        print("\n" + "="*70)
        print("🚀 PUSHING TO GITHUB")
        print("="*70)
        
        # Step 1: Add all files
        print("\n1️⃣  Adding all files...")
        result = subprocess.run(['git', 'add', '.'], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Add failed: {result.stderr}")
            return False
        print("✅ Files added")
        
        # Step 2: Commit
        print(f"\n2️⃣  Committing with message: '{commit_message}'")
        result = subprocess.run(
            ['git', 'commit', '-m', commit_message], 
            capture_output=True, 
            text=True
        )
        if result.returncode != 0:
            print(f"❌ Commit failed: {result.stderr}")
            return False
        print("✅ Committed")
        
        # Step 3: Push
        print("\n3️⃣  Pushing to GitHub...")
        result = subprocess.run(['git', 'push', 'origin', 'main'], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Push failed: {result.stderr}")
            return False
        print("✅ Pushed successfully!")
        
        print("\n" + "="*70)
        print("✨ ALL DONE! Files updated on GitHub")
        print("="*70 + "\n")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    # Get message from command line argument
    message = sys.argv[1] if len(sys.argv) > 1 else None
    
    success = push_to_git(message)
    sys.exit(0 if success else 1)
