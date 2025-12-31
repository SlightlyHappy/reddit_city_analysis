"""
Unified application runner for Replit deployment.
Starts background data collection scheduler and Streamlit dashboard simultaneously.
"""
import subprocess
import sys
import os
import time
import logging
from threading import Thread

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def start_scheduler():
    """Start the background data collection scheduler."""
    try:
        from scheduler import DataCollectionScheduler
        
        # Collect every 6 hours (adjust as needed)
        interval_hours = int(os.getenv('COLLECTION_INTERVAL_HOURS', '6'))
        
        logger.info(f"Starting data collection scheduler (every {interval_hours} hours)...")
        scheduler = DataCollectionScheduler(interval_hours=interval_hours)
        scheduler.start()
        
        # Keep thread alive
        while True:
            time.sleep(60)
            
    except Exception as e:
        logger.error(f"Scheduler error: {str(e)}")


def start_streamlit():
    """Start the Streamlit dashboard."""
    try:
        logger.info("Starting Streamlit dashboard...")
        
        # Get port from environment (Replit sets this)
        port = os.getenv('PORT', '8501')
        
        # Start Streamlit
        cmd = [
            sys.executable,
            '-m',
            'streamlit',
            'run',
            'dashboard/app.py',
            '--server.port', port,
            '--server.address', '0.0.0.0',
            '--server.headless', 'true',
            '--server.enableCORS', 'false',
            '--server.enableXsrfProtection', 'false'
        ]
        
        subprocess.run(cmd)
        
    except Exception as e:
        logger.error(f"Streamlit error: {str(e)}")


def main():
    """Main entry point - starts both scheduler and Streamlit."""
    logger.info("=" * 60)
    logger.info("Reddit Sentiment Analysis - Unified Application")
    logger.info("Starting background scheduler + Streamlit dashboard")
    logger.info("=" * 60)
    
    # Start scheduler in background thread
    scheduler_thread = Thread(target=start_scheduler, daemon=True)
    scheduler_thread.start()
    logger.info("✓ Background scheduler started")
    
    # Give scheduler time to initialize
    time.sleep(2)
    
    # Start Streamlit in main thread (keeps app running)
    logger.info("✓ Starting Streamlit dashboard...")
    start_streamlit()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n\nApplication stopped by user")
    except Exception as e:
        logger.error(f"\n\nApplication error: {str(e)}")
        import traceback
        traceback.print_exc()
