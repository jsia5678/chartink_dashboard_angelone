#!/usr/bin/env python3
import subprocess
import os

# Change to the project directory
os.chdir(r'C:\Users\shyam\chartink_dash_angelone\chartink_dashboard_angelone')

# Run git commands
try:
    print("Adding files...")
    subprocess.run(['git', 'add', '.'], check=True)
    
    print("Committing changes...")
    subprocess.run(['git', 'commit', '-m', 'Fix TOTP to try using short secret instead of empty'], check=True)
    
    print("Pushing to GitHub...")
    subprocess.run(['git', 'push', 'origin', 'main'], check=True)
    
    print("✅ Changes successfully pushed to GitHub!")
    
except subprocess.CalledProcessError as e:
    print(f"❌ Error: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
