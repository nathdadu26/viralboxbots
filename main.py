#!/usr/bin/env python3
"""
Main Entry Point for Koyeb Deployment
Runs all 3 bots using multiprocessing (no event loop conflicts)
"""

import os
import sys
import signal
import time
from multiprocessing import Process
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_converter():
    """Run converter bot"""
    try:
        from converter import polling_loop
        print("🔄 Starting Converter Bot...")
        polling_loop()
    except Exception as e:
        print(f"❌ Converter Bot failed: {e}")
        sys.exit(1)


def run_uploader():
    """Run uploader bot"""
    try:
        import asyncio
        from uploader import main as uploader_main
        print("📤 Starting Uploader Bot...")
        asyncio.run(uploader_main())
    except Exception as e:
        print(f"❌ Uploader Bot failed: {e}")
        sys.exit(1)


def run_fileserver():
    """Run fileserver bot"""
    try:
        from fileserver import main as fileserver_main
        print("📁 Starting File Server Bot...")
        fileserver_main()
    except Exception as e:
        print(f"❌ File Server Bot failed: {e}")
        sys.exit(1)


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\n⚠️ Shutdown signal received. Stopping all bots...")
    sys.exit(0)


if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("=" * 60)
    print("🤖 Viralbox Bots - Koyeb Deployment")
    print("=" * 60)
    
    # Verify required environment variables
    required_vars = [
        "UPLOADER_BOT_TOKEN",
        "CONVERTER_BOT_TOKEN", 
        "FILE_SERVER_BOT_TOKEN",
        "MONGODB_URI",
        "STORAGE_CHANNEL_ID",
        "BOT_USERNAME",
        "F_SUB_CHANNEL_ID",
        "F_SUB_CHANNEL_LINK",
        "WORKER_DOMAIN"
    ]
    
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        print(f"❌ Missing environment variables:")
        for var in missing:
            print(f"   - {var}")
        print("\n💡 Add these in Koyeb Environment Variables settings")
        sys.exit(1)
    
    print("✅ All environment variables found")
    print("🚀 Starting all bots in parallel...\n")
    
    # Create processes for each bot
    processes = []
    
    try:
        # Start converter bot
        p1 = Process(target=run_converter, name="Converter")
        p1.start()
        processes.append(p1)
        time.sleep(2)
        
        # Start uploader bot
        p2 = Process(target=run_uploader, name="Uploader")
        p2.start()
        processes.append(p2)
        time.sleep(2)
        
        # Start fileserver bot
        p3 = Process(target=run_fileserver, name="FileServer")
        p3.start()
        processes.append(p3)
        
        print("\n✅ All bots started successfully!")
        print("📊 Monitoring bot processes...\n")
        
        # Keep main process alive and monitor children
        while True:
            for p in processes:
                if not p.is_alive():
                    print(f"⚠️ {p.name} bot stopped! Restarting...")
                    processes.remove(p)
                    
                    # Restart based on name
                    if p.name == "Converter":
                        new_p = Process(target=run_converter, name="Converter")
                    elif p.name == "Uploader":
                        new_p = Process(target=run_uploader, name="Uploader")
                    else:
                        new_p = Process(target=run_fileserver, name="FileServer")
                    
                    new_p.start()
                    processes.append(new_p)
            
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\n👋 Stopping all bots...")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
    finally:
        # Terminate all processes
        for p in processes:
            if p.is_alive():
                p.terminate()
                p.join(timeout=5)
        print("🛑 All bots stopped")
        sys.exit(0)
