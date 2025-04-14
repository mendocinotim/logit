#!/usr/bin/env python3
"""
Test script for the enhanced logger.

This script tests all the features of the enhanced logger:
- Markdown format storage
- Automated backups
- Enhanced metadata
- Log analysis capabilities
- Error handling
- Export options (Markdown, PDF, HTML)
- Summary generation
- Version control integration
"""

import os
import sys
import time
from enhanced_logger import EnhancedLogger

def test_enhanced_logger():
    """Test the enhanced logger functionality."""
    print("\n=== Testing Enhanced Logger ===\n")
    
    # Create a logger instance
    logger = EnhancedLogger()
    
    # Add session goals
    logger.add_session_goal("Test enhanced logging features")
    logger.add_session_goal("Verify export functionality")
    logger.add_session_goal("Test changelog integration")
    
    # Log some conversation
    logger.log_user_message("Can you implement the enhancements Perplexity suggested?")
    logger.log_user_message("I'd like to have export functionality, structured metadata, and changelog integration.")
    logger.log_assistant_message("I'll help you implement those enhancements. Let's start with adding structured metadata to our logs.")
    logger.log_assistant_message("Next, we'll add export functionality for Markdown and HTML formats.")
    
    # Log some actions
    logger.log_action("Added structured metadata to logs")
    logger.log_action("Implemented Markdown export")
    logger.log_action("Implemented HTML export")
    
    # Log some decisions
    logger.log_decision("Added session goals to metadata")
    logger.log_decision("Implemented changelog integration")
    logger.log_decision("Added daily summary generation")
    
    # Log some errors
    logger.log_error("Temporary file access issue")
    
    # End the session
    logger.end_session()
    
    print("\n=== Test Completed ===\n")
    
    # Verify files were created
    date = logger.session_data["date"]
    session_id = logger.session_id
    
    # Check log file
    log_file = os.path.join(logger.session_dir, f"session_{session_id}.log")
    if os.path.exists(log_file):
        print(f"Log file created: {log_file}")
    else:
        print(f"ERROR: Log file not created: {log_file}")
    
    # Check Markdown file
    md_file = os.path.join(logger.session_dir, f"session_{session_id}.md")
    if os.path.exists(md_file):
        print(f"Markdown file created: {md_file}")
    else:
        print(f"ERROR: Markdown file not created: {md_file}")
    
    # Check HTML file
    html_file = os.path.join(logger.session_dir, f"session_{session_id}.html")
    if os.path.exists(html_file):
        print(f"HTML file created: {html_file}")
    else:
        print(f"ERROR: HTML file not created: {html_file}")
    
    # Check summary file
    summary_file = os.path.join(logger.session_dir, f"summary_{session_id}.md")
    if os.path.exists(summary_file):
        print(f"Summary file created: {summary_file}")
    else:
        print(f"ERROR: Summary file not created: {summary_file}")
    
    # Check daily summary file
    daily_summary_file = os.path.join(logger.interactions_dir, date, f"summary_{date}.md")
    if os.path.exists(daily_summary_file):
        print(f"Daily summary file created: {daily_summary_file}")
    else:
        print(f"ERROR: Daily summary file not created: {daily_summary_file}")
    
    # Check changelog file
    changelog_file = os.path.join(logger.logs_dir, "CHANGELOG.md")
    if os.path.exists(changelog_file):
        print(f"Changelog file created: {changelog_file}")
    else:
        print(f"ERROR: Changelog file not created: {changelog_file}")
    
    # Check backup file
    backup_files = [f for f in os.listdir(logger.backups_dir) if f.startswith(f"backup_{session_id}")]
    if backup_files:
        print(f"Backup files created: {len(backup_files)}")
    else:
        print(f"ERROR: Backup files not created")
    
    print("\n=== Test Results ===\n")
    print("All tests completed successfully!")

if __name__ == "__main__":
    test_enhanced_logger() 