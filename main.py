#!/usr/bin/env python3
"""
Main Entry Point for Koyeb Deployment
Runs all 3 bots in parallel using asyncio
"""

import os
import asyncio
import signal
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import bot modules
from uploader import main as uploader_main
from fileserver import main as fileserver_main
from converter import polling_loop as converter_main


def run_converter_sync():
    """Run converter bot (blocking synchronous)"""
    try:
        print("🔄 Starting Converter Bot...")
        converter_main()
    except Exception as e:
        print(f"❌ Converter Bot failed: {e}")


async def run_all_bots():
    """Run all bots concurrently"""
    print("🚀 Starting all bots on Koyeb...")
    
    # Create tasks for async bots
    uploader_task = asyncio.create_task(uploader_main())
    fileserver_task = asyncio.create_task(fileserver_main())
    
    # Run converter in executor (it's synchronous)
    converter_task = asyncio.get_event_loop().run_in_executor(
        None, 
        run_converter_sync
    )
    
    try:
        # Wait for all bots
        await asyncio.gather(
            uploader_task,
            fileserver_task,
            converter_task,
            return_exceptions=True
        )
    except Exception as e:
        print(f"❌ Error running bots: {e}")


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\n⚠️ Shutdown signal received. Stopping bots...")
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
        "MONGODB_URI"
    ]
    
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        sys.exit(1)
    
    # Run all bots
    try:
        asyncio.run(run_all_bots())
    except KeyboardInterrupt:
        print("\n👋 Bots stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
