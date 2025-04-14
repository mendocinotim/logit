#!/usr/bin/env python3
from interaction_logger import interaction_logger

def test_interaction_logger():
    """Test the interaction logger functionality"""
    # Log some user messages
    interaction_logger.log_user_message("Hello, can you help me with my project?")
    interaction_logger.log_user_message("I need to set up a logging system.")
    
    # Log some assistant messages
    interaction_logger.log_assistant_message("Of course! I'd be happy to help you set up a logging system.")
    interaction_logger.log_assistant_message("What kind of logging system do you need?")
    
    # Log some actions
    interaction_logger.log_action("Created logging configuration file")
    interaction_logger.log_action("Set up file handlers")
    
    # Get recent logs
    recent_logs = interaction_logger.get_recent_logs()
    print("\n=== Recent Logs ===")
    print(recent_logs)
    
    # Generate Perplexity link
    perplexity_link = interaction_logger.generate_perplexity_link()
    print("\n=== Perplexity Link ===")
    print(perplexity_link)
    
    # Get current log path
    log_path = interaction_logger.get_current_log_path()
    print(f"\nCurrent log file: {log_path}")

if __name__ == "__main__":
    test_interaction_logger() 