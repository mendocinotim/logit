#!/usr/bin/env python3
from cursor_logger import cursor_logger, generate_cursor_tag

def test_logging():
    """Test the cursor logging configuration"""
    cursor_logger.info("This is a test log message")
    cursor_logger.warning("This is a test warning message")
    cursor_logger.error("This is a test error message")
    
    try:
        raise ValueError("Test exception")
    except Exception as e:
        cursor_logger.exception("This is a test exception message")

def test_cursor_tagging():
    """Test the Cursor tagging system"""
    # Example of generating a tag for a code contribution
    tag = generate_cursor_tag("Implemented speaker diarization for multi-channel audio")
    print("\nExample Cursor tag:")
    print(tag)
    
    # Example of how it would look in code
    print("\nExample of tag in code context:")
    print(f"{tag}")
    print("def process_audio(audio_file):")
    print("    # Process the audio file")
    print("    return processed_audio")

if __name__ == "__main__":
    test_logging()
    test_cursor_tagging() 