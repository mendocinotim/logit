#!/usr/bin/env python3
"""
Enhanced Logger for EverythingSwing Project

This module provides an enhanced logging system with the following features:
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
import json
import time
import logging
import datetime
import platform
import subprocess
import base64
import shutil
import markdown
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('enhanced_logger')

class EnhancedLogger:
    """Enhanced logging system for EverythingSwing project."""
    
    def __init__(self, project_name: str = "EverythingSwing", base_dir: str = None):
        """Initialize the enhanced logger.
        
        Args:
            project_name: Name of the project
            base_dir: Base directory for logs (defaults to project root)
        """
        self.project_name = project_name
        self.base_dir = base_dir or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.logs_dir = os.path.join(self.base_dir, "logs")
        self.cursor_logs_dir = os.path.join(self.logs_dir, "cursor")
        self.interactions_dir = os.path.join(self.cursor_logs_dir, "interactions")
        self.backups_dir = os.path.join(self.logs_dir, "backups")
        
        # Create necessary directories
        for directory in [self.logs_dir, self.cursor_logs_dir, self.interactions_dir, self.backups_dir]:
            os.makedirs(directory, exist_ok=True)
        
        # Initialize session data
        self.session_id = self._generate_session_id()
        self.session_data = {
            "session_id": self.session_id,
            "project": self.project_name,
            "date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "started_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "system_info": self._get_system_info(),
            "git_info": self._get_git_info(),
            "session_goals": [],
            "conversation": [],
            "actions": [],
            "decisions": [],
            "errors": []
        }
        
        # Create session directory
        self.session_dir = os.path.join(self.interactions_dir, self.session_data["date"])
        os.makedirs(self.session_dir, exist_ok=True)
        
        # Initialize log file
        self.log_file = os.path.join(self.session_dir, f"session_{self.session_id}.log")
        self._initialize_log_file()
        
        # Initialize backup
        self._create_backup()
        
        logger.info(f"Enhanced logging initialized. Log file: {self.log_file}")
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID based on timestamp."""
        return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def _get_system_info(self) -> Dict[str, str]:
        """Get system information for metadata."""
        return {
            "os": platform.system(),
            "os_version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": sys.version,
            "hostname": platform.node()
        }
    
    def _get_git_info(self) -> Dict[str, str]:
        """Get git information for metadata."""
        git_info = {
            "branch": "unknown",
            "commit": "unknown",
            "status": "unknown"
        }
        
        try:
            # Get current branch
            branch = subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.base_dir,
                stderr=subprocess.STDOUT
            ).decode().strip()
            git_info["branch"] = branch
            
            # Get current commit
            commit = subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=self.base_dir,
                stderr=subprocess.STDOUT
            ).decode().strip()
            git_info["commit"] = commit
            
            # Get git status
            status = subprocess.check_output(
                ["git", "status", "--porcelain"],
                cwd=self.base_dir,
                stderr=subprocess.STDOUT
            ).decode().strip()
            git_info["status"] = "clean" if not status else "modified"
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.warning("Git information could not be retrieved")
        
        return git_info
    
    def _initialize_log_file(self) -> None:
        """Initialize the log file with metadata."""
        with open(self.log_file, 'w') as f:
            f.write(f"=== Cursor Interaction Log: {self.session_id} ===\n")
            f.write(f"Project: {self.project_name}\n")
            f.write(f"Date: {self.session_data['date']}\n")
            f.write(f"Started at: {self.session_data['started_at']}\n")
            f.write("=" * 50 + "\n\n")
    
    def _create_backup(self) -> None:
        """Create a backup of the current log file."""
        backup_file = os.path.join(
            self.backups_dir,
            f"backup_{self.session_id}_{int(time.time())}.log"
        )
        shutil.copy2(self.log_file, backup_file)
        logger.info(f"Backup created: {backup_file}")
    
    def add_session_goal(self, goal: str) -> None:
        """Add a session goal.
        
        Args:
            goal: Description of the goal
        """
        self.session_data["session_goals"].append(goal)
        with open(self.log_file, 'a') as f:
            f.write(f"GOAL: {goal}\n")
    
    def log_user_message(self, message: str) -> None:
        """Log a user message.
        
        Args:
            message: The user's message
        """
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.session_data["conversation"].append({
            "role": "user",
            "content": message,
            "timestamp": timestamp
        })
        
        with open(self.log_file, 'a') as f:
            f.write(f"[{timestamp}] USER: {message}\n")
    
    def log_assistant_message(self, message: str) -> None:
        """Log an assistant message.
        
        Args:
            message: The assistant's message
        """
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.session_data["conversation"].append({
            "role": "assistant",
            "content": message,
            "timestamp": timestamp
        })
        
        with open(self.log_file, 'a') as f:
            f.write(f"[{timestamp}] ASSISTANT: {message}\n")
    
    def log_action(self, action: str) -> None:
        """Log an action taken.
        
        Args:
            action: Description of the action
        """
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.session_data["actions"].append({
            "description": action,
            "timestamp": timestamp
        })
        
        with open(self.log_file, 'a') as f:
            f.write(f"[{timestamp}] ACTION: {action}\n")
    
    def log_decision(self, decision: str) -> None:
        """Log a decision made.
        
        Args:
            decision: Description of the decision
        """
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.session_data["decisions"].append({
            "description": decision,
            "timestamp": timestamp
        })
        
        with open(self.log_file, 'a') as f:
            f.write(f"[{timestamp}] DECISION: {decision}\n")
    
    def log_error(self, error: str) -> None:
        """Log an error that occurred.
        
        Args:
            error: Description of the error
        """
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.session_data["errors"].append({
            "description": error,
            "timestamp": timestamp
        })
        
        with open(self.log_file, 'a') as f:
            f.write(f"[{timestamp}] ERROR: {error}\n")
    
    def export_markdown(self) -> str:
        """Export the session to Markdown format.
        
        Returns:
            Path to the exported Markdown file
        """
        md_file = os.path.join(self.session_dir, f"session_{self.session_id}.md")
        
        with open(md_file, 'w') as f:
            # Write header
            f.write(f"# Cursor Interaction Log: {self.session_id}\n\n")
            f.write(f"**Project:** {self.project_name}\n")
            f.write(f"**Date:** {self.session_data['date']}\n")
            f.write(f"**Started at:** {self.session_data['started_at']}\n\n")
            
            # Write system info
            f.write("## System Information\n\n")
            f.write("```json\n")
            f.write(json.dumps(self.session_data["system_info"], indent=2))
            f.write("\n```\n\n")
            
            # Write git info
            f.write("## Git Information\n\n")
            f.write("```json\n")
            f.write(json.dumps(self.session_data["git_info"], indent=2))
            f.write("\n```\n\n")
            
            # Write session goals
            if self.session_data["session_goals"]:
                f.write("## Session Goals\n\n")
                for goal in self.session_data["session_goals"]:
                    f.write(f"- {goal}\n")
                f.write("\n")
            
            # Write conversation
            f.write("## Conversation\n\n")
            for entry in self.session_data["conversation"]:
                role = entry["role"].capitalize()
                content = entry["content"]
                timestamp = entry["timestamp"]
                f.write(f"**{role}** ({timestamp}):\n\n{content}\n\n")
            
            # Write actions
            if self.session_data["actions"]:
                f.write("## Actions\n\n")
                for action in self.session_data["actions"]:
                    f.write(f"- [{action['timestamp']}] {action['description']}\n")
                f.write("\n")
            
            # Write decisions
            if self.session_data["decisions"]:
                f.write("## Decisions\n\n")
                for decision in self.session_data["decisions"]:
                    f.write(f"- [{decision['timestamp']}] {decision['description']}\n")
                f.write("\n")
            
            # Write errors
            if self.session_data["errors"]:
                f.write("## Errors\n\n")
                for error in self.session_data["errors"]:
                    f.write(f"- [{error['timestamp']}] {error['description']}\n")
                f.write("\n")
        
        logger.info(f"Exported to Markdown: {md_file}")
        return md_file
    
    def export_html(self) -> str:
        """Export the session to HTML format.
        
        Returns:
            Path to the exported HTML file
        """
        md_file = self.export_markdown()
        html_file = os.path.join(self.session_dir, f"session_{self.session_id}.html")
        
        with open(md_file, 'r') as f:
            md_content = f.read()
        
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cursor Interaction Log: {self.session_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; max-width: 1200px; margin: 0 auto; }}
        h1, h2 {{ color: #333; }}
        pre {{ background-color: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }}
        code {{ background-color: #f4f4f4; padding: 2px 5px; border-radius: 3px; }}
        .user {{ color: #0066cc; }}
        .assistant {{ color: #009933; }}
        .action {{ color: #cc6600; }}
        .decision {{ color: #9900cc; }}
        .error {{ color: #cc0000; }}
    </style>
</head>
<body>
{markdown.markdown(md_content, extensions=['fenced_code', 'tables'])}
</body>
</html>
"""
        
        with open(html_file, 'w') as f:
            f.write(html_content)
        
        logger.info(f"Exported to HTML: {html_file}")
        return html_file
    
    def generate_summary(self) -> str:
        """Generate a summary of the session.
        
        Returns:
            Path to the summary file
        """
        summary_file = os.path.join(self.session_dir, f"summary_{self.session_id}.md")
        
        with open(summary_file, 'w') as f:
            f.write(f"# Session Summary: {self.session_id}\n\n")
            f.write(f"**Date:** {self.session_data['date']}\n\n")
            
            # Summary of goals
            if self.session_data["session_goals"]:
                f.write("## Goals\n\n")
                for goal in self.session_data["session_goals"]:
                    f.write(f"- {goal}\n")
                f.write("\n")
            
            # Summary of decisions
            if self.session_data["decisions"]:
                f.write("## Key Decisions\n\n")
                for decision in self.session_data["decisions"]:
                    f.write(f"- {decision['description']}\n")
                f.write("\n")
            
            # Summary of actions
            if self.session_data["actions"]:
                f.write("## Actions Taken\n\n")
                for action in self.session_data["actions"]:
                    f.write(f"- {action['description']}\n")
                f.write("\n")
            
            # Summary of errors
            if self.session_data["errors"]:
                f.write("## Issues Encountered\n\n")
                for error in self.session_data["errors"]:
                    f.write(f"- {error['description']}\n")
                f.write("\n")
        
        logger.info(f"Generated summary: {summary_file}")
        return summary_file
    
    def generate_perplexity_link(self) -> str:
        """Generate a link for Perplexity.
        
        Returns:
            Perplexity link
        """
        # Create a simplified version of the session data for the link
        simplified_data = {
            "session_id": self.session_id,
            "project": self.project_name,
            "date": self.session_data["date"],
            "conversation": self.session_data["conversation"]
        }
        
        # Convert to JSON and encode
        json_data = json.dumps(simplified_data)
        encoded_data = base64.b64encode(json_data.encode()).decode()
        
        # Create the link
        link = f"https://perplexity.ai/?log_file={self.log_file}&conversation={encoded_data}"
        
        return link
    
    def update_changelog(self) -> None:
        """Update the project changelog with session information."""
        changelog_file = os.path.join(self.logs_dir, "CHANGELOG.md")
        
        # Create changelog if it doesn't exist
        if not os.path.exists(changelog_file):
            with open(changelog_file, 'w') as f:
                f.write("# Changelog\n\n")
                f.write("All notable changes to the EverythingSwing project will be documented in this file.\n\n")
                f.write("## [Unreleased]\n\n")
        
        # Read existing changelog
        with open(changelog_file, 'r') as f:
            changelog = f.read()
        
        # Check if today's date is already in the changelog
        today = self.session_data["date"]
        if f"## [{today}]" not in changelog:
            # Add today's date section
            with open(changelog_file, 'w') as f:
                f.write(changelog)
                f.write(f"\n## [{today}]\n\n")
        
        # Add session decisions to changelog
        if self.session_data["decisions"]:
            with open(changelog_file, 'a') as f:
                for decision in self.session_data["decisions"]:
                    f.write(f"- {decision['description']}\n")
        
        logger.info(f"Updated changelog: {changelog_file}")
    
    def generate_daily_summary(self) -> str:
        """Generate a summary of all sessions for the day.
        
        Returns:
            Path to the daily summary file
        """
        date = self.session_data["date"]
        summary_file = os.path.join(self.interactions_dir, date, f"summary_{date}.md")
        
        # Get all session files for today
        session_files = [f for f in os.listdir(self.session_dir) if f.startswith("session_") and f.endswith(".log")]
        
        with open(summary_file, 'w') as f:
            f.write(f"# Daily Summary: {date}\n\n")
            f.write("## Sessions\n\n")
            
            for session_file in sorted(session_files):
                session_id = session_file.replace("session_", "").replace(".log", "")
                f.write(f"### Session: {session_id}\n\n")
                
                # Read session file
                with open(os.path.join(self.session_dir, session_file), 'r') as sf:
                    session_content = sf.read()
                
                # Extract decisions
                decisions = []
                for line in session_content.split("\n"):
                    if "DECISION:" in line:
                        decisions.append(line.split("DECISION:")[1].strip())
                
                if decisions:
                    f.write("**Decisions:**\n")
                    for decision in decisions:
                        f.write(f"- {decision}\n")
                
                f.write("\n---\n\n")
        
        logger.info(f"Generated daily summary: {summary_file}")
        return summary_file
    
    def end_session(self) -> None:
        """End the current session and perform cleanup."""
        # Export to Markdown and HTML
        self.export_markdown()
        self.export_html()
        
        # Generate summary
        self.generate_summary()
        
        # Update changelog
        self.update_changelog()
        
        # Generate daily summary
        self.generate_daily_summary()
        
        # Create final backup
        self._create_backup()
        
        # Generate Perplexity link
        perplexity_link = self.generate_perplexity_link()
        
        logger.info(f"Session ended. Perplexity link: {perplexity_link}")
        print(f"\nPerplexity Link: {perplexity_link}")
        print(f"\nChangelog path: {os.path.join(self.logs_dir, 'CHANGELOG.md')}")


# Example usage
if __name__ == "__main__":
    # Create a logger instance
    logger = EnhancedLogger()
    
    # Add session goals
    logger.add_session_goal("Implement enhanced logging features")
    logger.add_session_goal("Test export functionality")
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
    
    # End the session
    logger.end_session() 