#!/usr/bin/env python3
import os
import sys
import logging
import shutil
import json
import base64
import zlib
import markdown
import html
import csv
from pathlib import Path
from datetime import datetime, timedelta
import re
import platform
import socket
import hashlib
import gzip
from typing import Dict, List, Optional, Union, Any
import pandas as pd
from collections import defaultdict
import glob
import urllib.parse
import time
import webbrowser

# Import the cursor logger for consistency
from .cursor_logger import cursor_logger

class InteractionLogger:
    """Logger for Cursor-user interactions with enhanced features"""
    
    def __init__(self):
        """Initialize the interaction logger."""
        # Set up base directory in user's home
        self.base_dir = Path(os.path.expanduser('~')) / '.logit'
        self.log_dir = self.base_dir / 'logs' / 'cursor'
        self.archive_dir = self.base_dir / 'archive'
        self.backup_dir = self.base_dir / 'backups'
        
        # Create necessary directories
        for directory in [self.log_dir, self.archive_dir, self.backup_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            
        self.daily_dir = self.log_dir / datetime.now().strftime('%Y%m%d')
        self.daily_dir.mkdir(exist_ok=True)
        
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.project_name = os.path.basename(os.getcwd())
        self.date = datetime.now().strftime('%Y-%m-%d')
        self.conversation = []
        self.session_goals = []
        
        # Set up logging
        self.logger = logging.getLogger('interaction_logger')
        self.logger.setLevel(logging.INFO)
        
        # Set up file handler
        self.log_file = self.daily_dir / f"cursor_{self.session_id}.log"
        handler = logging.FileHandler(self.log_file)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        self.logger.addHandler(handler)
        
        # Log initialization
        self.log_interaction('initialization', {
            'session_id': self.session_id,
            'project_name': self.project_name,
            'date': self.date
        })
        
        # Statistics tracking
        self.current_topic = None
        self.topic_start_time = None
        self.topic_stats = defaultdict(lambda: {
            'time_spent': 0,
            'token_usage': 0,
            'files_modified': set(),
            'commands_executed': []
        })
        
        # Enhanced conversation tracking
        self.message_threads = defaultdict(list)  # For tracking reply chains
        self.message_reactions = defaultdict(list)  # For tracking reactions/tags
        self.code_blocks = []  # For tracking code blocks with metadata
        self.file_attachments = []  # For tracking file references
        
        # Detect shell environment
        self.shell = os.environ.get('SHELL', '/bin/sh')
        self.shell_name = os.path.basename(self.shell)
        
        # Set up topics directory
        self.topics_dir = self.log_dir / 'topics'
        self.topics_dir.mkdir(exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('cursor_interaction')
        
        # Log initial session info only once
        if not hasattr(self.__class__, '_logged_init'):
            self._log_initialization()
            self.__class__._logged_init = True
        
        # Initialize session data
        self.session_data = {
            'messages': [],
            'actions': [],
            'decisions': [],
            'goals': None,
            'code_blocks': [],
            'file_attachments': [],
            'threads': {},
            'reactions': {}
        }
    
    def _log_initialization(self):
        """Log initialization information with enhanced metadata"""
        try:
            self.logger.info(f"=== Cursor Interaction Log: {self.session_id} ===")
            self.logger.info(f"Project: {self.project_name}")
            self.logger.info(f"Date: {self.date}")
            self.logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.logger.info("System Information:")
            self.logger.info(f"  os: {platform.system()}")
            self.logger.info(f"  os_version: {platform.version()}")
            self.logger.info(f"  machine: {platform.machine()}")
            self.logger.info(f"  processor: {platform.processor()}")
            self.logger.info(f"  hostname: {platform.node()}")
            self.logger.info(f"  python_version: {sys.version}")
            self.logger.info(f"  shell: {self.shell_name}")
            self.logger.info("=" * 50)
        except Exception as e:
            print(f"Error during initialization logging: {e}")
    
    def _create_backup(self):
        """Create a compressed backup of the previous session"""
        try:
            # Find the most recent log file before the current one
            previous_logs = sorted(
                self.daily_dir.glob("session_*.log"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            previous_logs = [f for f in previous_logs if f != self.log_file]
            
            if previous_logs:
                latest_log = previous_logs[0]
                backup_path = self.backup_dir / f"{latest_log.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.gz"
                
                # Create compressed backup
                with open(latest_log, 'rb') as f_in:
                    with gzip.open(backup_path, 'wb') as f_out:
                        f_out.writelines(f_in)
                
                # Keep only the last 5 backups
                backups = sorted(self.backup_dir.glob("*.gz"), key=lambda x: x.stat().st_mtime)
                if len(backups) > 5:
                    for old_backup in backups[:-5]:
                        old_backup.unlink()
        except Exception as e:
            print(f"Error creating backup: {e}")
    
    def _check_log_rotation(self):
        """Check if log rotation is needed and perform it if necessary"""
        try:
            # Get all daily directories
            daily_dirs = [d for d in self.interaction_dir.iterdir() if d.is_dir()]
            
            # Sort by date (newest first)
            daily_dirs.sort(key=lambda x: x.name, reverse=True)
            
            # Keep only the last 30 days of logs
            if len(daily_dirs) > 30:
                for old_dir in daily_dirs[30:]:
                    # Create archive directory for this month if it doesn't exist
                    month = old_dir.name[:7]  # YYYY-MM
                    month_archive_dir = self.archive_dir / month
                    month_archive_dir.mkdir(exist_ok=True)
                    
                    # Move the directory to the archive
                    archive_path = month_archive_dir / old_dir.name
                    if not archive_path.exists():
                        shutil.move(str(old_dir), str(archive_path))
                    
                    # Compress the archived directory
                    archive_zip = archive_path.with_suffix('.zip')
                    if not archive_zip.exists():
                        shutil.make_archive(str(archive_path), 'zip', str(archive_path))
                        # Remove the original directory after compression
                        shutil.rmtree(str(archive_path))
            
            # Clean up old archive files (keep last 6 months)
            archive_dirs = [d for d in self.archive_dir.iterdir() if d.is_dir()]
            archive_dirs.sort(key=lambda x: x.name, reverse=True)
            
            if len(archive_dirs) > 6:
                for old_archive in archive_dirs[6:]:
                    shutil.rmtree(str(old_archive))
        except Exception as e:
            print(f"Error during log rotation: {e}")
    
    def _update_checksum(self):
        """Update the checksum of the current log file"""
        try:
            if self.log_file.exists():
                with open(self.log_file, 'rb') as f:
                    content = f.read()
                    self.metadata['checksum'] = hashlib.sha256(content).hexdigest()
        except Exception as e:
            print(f"Error updating checksum: {e}")
    
    def log_user_message(self, message: str, reply_to: Optional[str] = None, attachments: Optional[List[str]] = None) -> str:
        """Log a message from the user with enhanced features"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            message_id = f"msg_{len(self.conversation)}"
            
            # Extract code blocks and their languages
            code_blocks = []
            if "```" in message:
                pattern = r"```(\w+)?\n(.*?)\n```"
                for match in re.finditer(pattern, message, re.DOTALL):
                    lang = match.group(1) or "text"
                    code = match.group(2)
                    block_id = f"code_{len(self.code_blocks)}"
                    code_blocks.append({
                        "id": block_id,
                        "language": lang,
                        "content": code
                    })
                    self.code_blocks.append(code_blocks[-1])
                    # Replace code block with reference
                    message = message.replace(match.group(0), f"[code:{block_id}]")
            
            # Process file attachments
            if attachments:
                for file_path in attachments:
                    attachment_id = f"file_{len(self.file_attachments)}"
                    self.file_attachments.append({
                        "id": attachment_id,
                        "path": file_path,
                        "name": os.path.basename(file_path)
                    })
                    message += f"\n[attachment:{attachment_id}]"
            
            # Create message entry
            message_entry = {
                "id": message_id,
                "role": "user",
                "content": message,
                "timestamp": timestamp,
                "type": "message",
                "code_blocks": code_blocks,
                "attachments": attachments or [],
                "reply_to": reply_to
            }
            
            # Add to conversation
            self.conversation.append(message_entry)
            
            # Update thread tracking if this is a reply
            if reply_to:
                self.message_threads[reply_to].append(message_id)
            
            # Log the message
            log_entry = f"[{timestamp}] USER: {message}"
            self.logger.info(log_entry)
            self.logger.info(f"### Human: {message}")
            
            self._update_checksum()
            return message_id
            
        except Exception as e:
            print(f"Error logging user message: {e}")
            return ""
    
    def log_assistant_message(self, message: str) -> str:
        """Log a message from the assistant with error handling"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] ASSISTANT: {message}"
            self.logger.info(log_entry)
            self.logger.info(f"### Assistant: {message}")  # Add markdown-style formatting
            
            # Store the conversation content
            self.conversation.append({
                "role": "assistant",
                "content": message,
                "timestamp": timestamp,
                "type": "message"  # Add type for better rendering
            })
            
            self._update_checksum()
            return log_entry
        except Exception as e:
            print(f"Error logging assistant message: {e}")
            return ""
    
    def log_action(self, action_description: str) -> str:
        """Log an action performed by the assistant with error handling"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] ACTION: {action_description}"
            self.logger.info(log_entry)
            
            # Store the conversation content
            self.conversation.append({
                "role": "action",
                "content": action_description,
                "timestamp": timestamp,
                "type": "event"  # Add type for better rendering
            })
            
            self._update_checksum()
            return log_entry
        except Exception as e:
            print(f"Error logging action: {e}")
            return ""
    
    def log_decision(self, decision_description: str) -> str:
        """Log a decision made during the conversation with error handling"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] DECISION: {decision_description}"
            self.logger.info(log_entry)
            
            # Store the conversation content
            self.conversation.append({
                "role": "decision",
                "content": decision_description,
                "timestamp": timestamp,
                "type": "event"  # Add type for better rendering
            })
            
            # Add to changelog
            self._add_to_changelog(decision_description)
            
            self._update_checksum()
            return log_entry
        except Exception as e:
            print(f"Error logging decision: {e}")
            return ""
    
    def get_recent_logs(self, hours=24):
        """
        Get logs from the last N hours.
        
        Args:
            hours (int): Number of hours to look back
            
        Returns:
            str: Formatted recent logs
        """
        try:
            if not self.log_dir.exists():
                return "No logs directory found."
            
            # Calculate cutoff time
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            # Find all log files from the last N hours
            log_files = []
            for log_file in self.log_dir.glob("**/cursor_*.log"):
                if log_file.stat().st_mtime >= cutoff_time.timestamp():
                    log_files.append(log_file)
            
            if not log_files:
                return f"No log files found from the last {hours} hours."
            
            # Sort by modification time
            log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Process logs
            recent_logs = []
            for log_file in log_files:
                with open(log_file, 'r') as f:
                    content = f.read()
                    # Extract session info and interactions
                    session_info = []
                    for line in content.split('\n'):
                        if any(key in line for key in ["=== Cursor Interaction Log:", "Started at:", "Interaction:", "ERROR:"]):
                            session_info.append(line.strip())
                    
                    if session_info:
                        recent_logs.append(f"=== Session {log_file.stem} ===\n" + "\n".join(session_info) + "\n")
            
            return "\n".join(recent_logs)
            
        except Exception as e:
            return f"Error getting recent logs: {e}"
    
    def generate_perplexity_link(self) -> str:
        """Generate a link for Perplexity to access this log with error handling"""
        try:
            # Create a compressed JSON representation of the conversation
            conversation_json = json.dumps(self.conversation)
            compressed = zlib.compress(conversation_json.encode())
            encoded = base64.urlsafe_b64encode(compressed).decode()
            
            # Create a link that includes the log file path and encoded conversation
            link = f"https://perplexity.ai/?log_file={self.log_file}&conversation={encoded}"
            return link
        except Exception as e:
            print(f"Error generating Perplexity link: {e}")
            return ""
    
    def get_current_log_path(self) -> str:
        """Get the path to the current log file"""
        return str(self.log_file)
    
    def export_to_markdown(self, output_path: Optional[Path] = None) -> Optional[Path]:
        """Export the conversation to a Markdown file with error handling"""
        try:
            if output_path is None:
                output_path = self.log_file.with_suffix('.md')
            
            with open(output_path, 'w') as f:
                # Write metadata
                f.write(f"# Cursor Interaction Log: {self.session_id}\n\n")
                f.write(f"**Project:** {self.project_name}\n")
                f.write(f"**Date:** {self.date}\n")
                f.write(f"**Started at:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Write system information
                f.write("## System Information\n\n")
                f.write(f"- **os:** {platform.system()}\n")
                f.write(f"- **os_version:** {platform.version()}\n")
                f.write(f"- **machine:** {platform.machine()}\n")
                f.write(f"- **processor:** {platform.processor()}\n")
                f.write(f"- **hostname:** {platform.node()}\n")
                f.write(f"- **python_version:** {sys.version}\n")
                f.write("\n")
                
                if self.session_goals:
                    f.write("## Session Goals\n\n")
                    for goal in self.session_goals:
                        f.write(f"- {goal}\n")
                    f.write("\n")
                
                # Write conversation
                f.write("## Conversation\n\n")
                for entry in self.conversation:
                    role = entry["role"].upper()
                    content = entry["content"]
                    timestamp = entry["timestamp"]
                    
                    # Format code blocks with triple backticks
                    if "```" in content:
                        f.write(f"**{role}** ({timestamp}):\n\n{content}\n\n")
                    else:
                        f.write(f"**{role}** ({timestamp}):\n\n{content}\n\n")
            
            return output_path
        except Exception as e:
            print(f"Error exporting to Markdown: {e}")
            return None
    
    def export_to_html(self, output_path: Optional[Path] = None) -> Optional[Path]:
        """Export the conversation to an HTML file with enhanced formatting"""
        try:
            if output_path is None:
                output_path = self.log_file.with_suffix('.html')
            
            # Add HTML header with enhanced styling
            html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cursor Interaction Log: {self.session_id}</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/themes/prism.min.css" rel="stylesheet" />
    <style>
        :root {{
            --bg-color: #ffffff;
            --text-color: #24292e;
            --border-color: #e1e4e8;
            --user-msg-bg: #f1f8ff;
            --assistant-msg-bg: #f6f8fa;
            --action-msg-bg: #fff8f2;
            --decision-msg-bg: #f6f3ff;
            --code-bg: #f6f8fa;
            --link-color: #0366d6;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            max-width: 1200px;
            margin: 0 auto;
            background: var(--bg-color);
            color: var(--text-color);
        }}
        
        .conversation {{
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}
        
        .message {{
            padding: 16px;
            border-radius: 6px;
            border: 1px solid var(--border-color);
            position: relative;
        }}
        
        .message.user {{ background: var(--user-msg-bg); }}
        .message.assistant {{ background: var(--assistant-msg-bg); }}
        .message.action {{ background: var(--action-msg-bg); }}
        .message.decision {{ background: var(--decision-msg-bg); }}
        
        .message-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 10px;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--border-color);
        }}
        
        .role-badge {{
            font-size: 12px;
            font-weight: 600;
            padding: 2px 6px;
            border-radius: 12px;
            text-transform: uppercase;
        }}
        
        .timestamp {{
            color: #666;
            font-size: 12px;
        }}
        
        .content {{
            white-space: pre-wrap;
            overflow-x: auto;
        }}
        
        .code-block {{
            background: var(--code-bg);
            border-radius: 6px;
            padding: 16px;
            margin: 10px 0;
            position: relative;
        }}
        
        .code-block .language {{
            position: absolute;
            top: 8px;
            right: 8px;
            font-size: 12px;
            color: #666;
            background: rgba(255,255,255,0.8);
            padding: 2px 6px;
            border-radius: 4px;
        }}
        
        .attachment {{
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px;
            background: var(--code-bg);
            border-radius: 4px;
            margin-top: 8px;
        }}
        
        .attachment-icon {{
            width: 16px;
            height: 16px;
            color: #666;
        }}
        
        .thread-indicator {{
            position: absolute;
            left: -20px;
            top: 0;
            bottom: 0;
            width: 2px;
            background: var(--border-color);
        }}
        
        .thread-reply {{
            margin-left: 20px;
        }}
        
        .reactions {{
            display: flex;
            gap: 8px;
            margin-top: 8px;
            padding-top: 8px;
            border-top: 1px solid var(--border-color);
        }}
        
        .reaction {{
            font-size: 12px;
            padding: 2px 6px;
            border-radius: 12px;
            background: var(--code-bg);
            color: #666;
        }}
        
        details {{
            margin: 10px 0;
        }}
        
        summary {{
            cursor: pointer;
            padding: 8px;
            background: var(--code-bg);
            border-radius: 4px;
        }}
        
        .system-info {{
            background: var(--assistant-msg-bg);
            padding: 16px;
            border-radius: 6px;
            margin-bottom: 20px;
        }}
    </style>
</head>
<body>
    <div class="system-info">
        <h1>Cursor Interaction Log: {self.session_id}</h1>
        <p><strong>Project:</strong> {self.project_name}</p>
        <p><strong>Date:</strong> {self.date}</p>
    </div>
    
    <div class="conversation">
"""
            
            # Add conversation entries with enhanced formatting
            for entry in self.conversation:
                role = entry["role"]
                content = entry["content"]
                timestamp = entry["timestamp"]
                message_id = entry["id"]
                
                # Handle threading
                thread_class = ""
                thread_indicator = ""
                if entry.get("reply_to"):
                    thread_class = "thread-reply"
                    thread_indicator = '<div class="thread-indicator"></div>'
                
                # Process code blocks
                for code_block in entry.get("code_blocks", []):
                    placeholder = f"[code:{code_block['id']}]"
                    formatted_code = f"""
                        <div class="code-block">
                            <div class="language">{code_block['language']}</div>
                            <pre><code class="language-{code_block['language']}">{html.escape(code_block['content'])}</code></pre>
                        </div>
                    """
                    content = content.replace(placeholder, formatted_code)
                
                # Process attachments
                for attachment in entry.get("attachments", []):
                    attachment_id = f"file_{self.file_attachments.index(attachment)}"
                    placeholder = f"[attachment:{attachment_id}]"
                    formatted_attachment = f"""
                        <div class="attachment">
                            <svg class="attachment-icon" viewBox="0 0 16 16">
                                <path d="M2 2.5A2.5 2.5 0 014.5 0h7A2.5 2.5 0 0114 2.5v10a2.5 2.5 0 01-2.5 2.5h-7A2.5 2.5 0 012 12.5v-10z"/>
                            </svg>
                            <a href="{attachment['path']}">{attachment['name']}</a>
                        </div>
                    """
                    content = content.replace(placeholder, formatted_attachment)
                
                # Add reactions if any
                reactions_html = ""
                if message_id in self.message_reactions:
                    reactions = self.message_reactions[message_id]
                    reactions_html = """
                        <div class="reactions">
                            {}
                        </div>
                    """.format("".join(f'<span class="reaction">{r}</span>' for r in reactions))
                
                html += f"""
                    <div class="message {role} {thread_class}" id="{message_id}">
                        {thread_indicator}
                        <div class="message-header">
                            <span class="role-badge">{role}</span>
                            <span class="timestamp">{timestamp}</span>
                        </div>
                        <div class="content">{content}</div>
                        {reactions_html}
                    </div>
                """
            
            # Close HTML
            html += """
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/prism.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/components/prism-python.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/components/prism-javascript.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/components/prism-bash.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/components/prism-json.min.js"></script>
</body>
</html>
"""
            
            # Write the complete HTML file
            with open(output_path, 'w') as f:
                f.write(html)
            
            return output_path
        except Exception as e:
            print(f"Error exporting to HTML: {e}")
            return None
    
    def export_to_json(self, output_path: Optional[Path] = None) -> Optional[Path]:
        """Export the conversation to a JSON file with error handling"""
        try:
            if output_path is None:
                output_path = self.log_file.with_suffix('.json')
            
            # Create a complete export object
            export_data = {
                "metadata": self.metadata,
                "conversation": self.conversation,
                "system_info": self.system_info,
                "export_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "export_format": "json",
                "export_version": "1.0"
            }
            
            # Write to JSON file with pretty printing
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            return output_path
        except Exception as e:
            print(f"Error exporting to JSON: {e}")
            return None
    
    def export_to_csv(self, output_path: Optional[Path] = None) -> Optional[Path]:
        """Export the conversation to a CSV file with error handling"""
        try:
            if output_path is None:
                output_path = self.log_file.with_suffix('.csv')
            
            # Prepare data for CSV
            csv_data = []
            for entry in self.conversation:
                csv_data.append({
                    "timestamp": entry["timestamp"],
                    "role": entry["role"],
                    "content": entry["content"]
                })
            
            # Write to CSV file
            with open(output_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=["timestamp", "role", "content"])
                writer.writeheader()
                writer.writerows(csv_data)
            
            return output_path
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return None
    
    def export_to_excel(self, output_path: Optional[Path] = None) -> Optional[Path]:
        """Export the conversation to an Excel file with error handling"""
        try:
            if output_path is None:
                output_path = self.log_file.with_suffix('.xlsx')
            
            # Create a DataFrame from the conversation
            df = pd.DataFrame(self.conversation)
            
            # Add metadata as a separate sheet
            metadata_df = pd.DataFrame([self.metadata])
            
            # Create Excel writer
            with pd.ExcelWriter(output_path) as writer:
                df.to_excel(writer, sheet_name='Conversation', index=False)
                metadata_df.to_excel(writer, sheet_name='Metadata', index=False)
            
            return output_path
        except Exception as e:
            print(f"Error exporting to Excel: {e}")
            return None
    
    def generate_daily_summary(self) -> str:
        """Generate a daily summary of all interactions."""
        today = datetime.now().strftime('%Y-%m-%d')
        summary = []
        
        # Executive Summary
        summary.append(f"# Executive Summary: {today}\n")
        summary.append("## Overview")
        summary.append("This document provides a comprehensive summary of today's development activities in the EverythingSwing project, including key decisions, implementations, and outcomes.\n")
        
        # Get all sessions for today
        daily_dir = os.path.join(self.base_log_dir, 'interactions', today)
        if not os.path.exists(daily_dir):
            return "\n".join(summary)
            
        sessions = []
        for f in os.listdir(daily_dir):
            if f.startswith('session_') and f.endswith('.log'):
                sessions.append(f)
        sessions.sort()
        
        # Collect all topics and actions for the day
        daily_topics = set()
        daily_actions = []
        daily_decisions = []
        daily_todos = []
        
        for session_file in sessions:
            session_id = session_file.replace('session_', '').replace('.log', '')
            session_path = os.path.join(daily_dir, session_file)
            
            if not os.path.exists(session_path):
                continue
                
            with open(session_path, 'r') as f:
                content = f.read()
                
            # Collect topics
            topics = re.findall(r'TOPIC: (.*?)(?:\n|$)', content)
            daily_topics.update(topics)
            
            # Collect actions
            actions = re.findall(r'ACTION: (.*?)(?:\n|$)', content)
            daily_actions.extend(actions)
            
            # Collect decisions
            decisions = re.findall(r'DECISION: (.*?)(?:\n|$)', content)
            daily_decisions.extend(decisions)
            
            # Collect TODOs
            todos = re.findall(r'TODO: (.*?)(?:\n|$)', content)
            daily_todos.extend(todos)
        
        # Daily Summary
        summary.append("## Daily Highlights")
        if daily_topics:
            summary.append("\n### Key Topics")
            for topic in sorted(daily_topics):
                summary.append(f"- {topic.strip()}")
        
        if daily_actions:
            summary.append("\n### Major Actions")
            for action in daily_actions:
                summary.append(f"- {action.strip()}")
        
        if daily_decisions:
            summary.append("\n### Key Decisions")
            for decision in daily_decisions:
                summary.append(f"- {decision.strip()}")
        
        if daily_todos:
            summary.append("\n### Pending Tasks")
            for todo in daily_todos:
                summary.append(f"- [ ] {todo.strip()}")
        
        # Detailed Session Reports
        summary.append("\n## Detailed Session Reports\n")
        
        for session_file in sessions:
            session_id = session_file.replace('session_', '').replace('.log', '')
            session_path = os.path.join(daily_dir, session_file)
            
            if not os.path.exists(session_path):
                continue
                
            with open(session_path, 'r') as f:
                content = f.read()
                
            # Extract session information
            summary.append(f"\n## Session {session_id}\n")
            
            # Intention/Purpose
            summary.append("### Purpose & Context")
            topics = re.findall(r'TOPIC: (.*?)(?:\n|$)', content)
            if topics:
                summary.append("Primary focus:")
                for topic in topics:
                    summary.append(f"- {topic.strip()}")
                summary.append("\nContext:")
                summary.append("This session aimed to advance the project by implementing and testing new features.")
            else:
                summary.append("General development and maintenance")
            
            # Process/Implementation
            summary.append("\n### Implementation Details")
            actions = re.findall(r'ACTION: (.*?)(?:\n|$)', content)
            if actions:
                for action in actions:
                    summary.append(f"- {action.strip()}")
            else:
                summary.append("No specific actions recorded")
            
            # Technical Details
            code_blocks = re.findall(r'```[\w]*\n(.*?)\n```', content, re.DOTALL)
            if code_blocks:
                summary.append("\n#### Technical Implementation")
                for i, block in enumerate(code_blocks, 1):
                    summary.append(f"Implementation {i}:")
                    summary.append("```")
                    summary.append(block.strip())
                    summary.append("```")
            
            # Conclusion/Outcome
            summary.append("\n### Results & Outcomes")
            decisions = re.findall(r'DECISION: (.*?)(?:\n|$)', content)
            if decisions:
                summary.append("Key outcomes:")
                for decision in decisions:
                    summary.append(f"- {decision.strip()}")
            else:
                summary.append("No specific outcomes recorded")
            
            # Next Steps/Integration
            summary.append("\n### Next Steps & Integration")
            todos = re.findall(r'TODO: (.*?)(?:\n|$)', content)
            if todos:
                summary.append("Pending tasks:")
                for todo in todos:
                    summary.append(f"- [ ] {todo.strip()}")
            else:
                summary.append("No pending tasks")
            
            # Integration Notes
            summary.append("\n### Project Integration")
            summary.append("This session's contributions:")
            if topics:
                summary.append(f"- Advanced the {topics[0].strip()} feature")
                summary.append("- Implemented new functionality")
                summary.append("- Enhanced project capabilities")
            summary.append("- Maintained code quality and documentation")
            summary.append("- Supported overall project development goals")
            
            summary.append("\n---\n")
        
        # Daily Conclusion
        summary.append("\n## Daily Conclusion")
        summary.append("\n### Summary of Progress")
        if daily_topics:
            summary.append(f"Today's work focused on {len(daily_topics)} key areas:")
            for topic in sorted(daily_topics):
                summary.append(f"- {topic.strip()}")
        
        summary.append("\n### Key Achievements")
        if daily_actions:
            summary.append("Major accomplishments:")
            for action in daily_actions:
                summary.append(f"- {action.strip()}")
        
        summary.append("\n### Project Impact")
        summary.append("Today's work contributed to the project by:")
        if daily_topics:
            summary.append("- Implementing new features and enhancements")
        summary.append("- Maintaining code quality and documentation")
        summary.append("- Supporting project development goals")
        
        if daily_todos:
            summary.append("\n### Outstanding Items")
            summary.append("The following tasks require attention:")
            for todo in daily_todos:
                summary.append(f"- [ ] {todo.strip()}")
        
        return "\n".join(summary)
    
    def generate_weekly_report(self) -> Optional[Path]:
        """Generate a weekly report summarizing the past week's activities"""
        try:
            # Calculate the date range for the past week
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            # Create a directory for the report if it doesn't exist
            report_dir = self.base_log_dir / "reports"
            report_dir.mkdir(exist_ok=True)
            
            # Generate the report filename
            report_path = report_dir / f"weekly_report_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.md"
            
            with open(report_path, 'w') as f:
                f.write(f"# Weekly Report: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}\n\n")
                
                # Get all daily directories in the date range
                daily_dirs = []
                current_date = start_date
                while current_date <= end_date:
                    date_str = current_date.strftime("%Y-%m-%d")
                    daily_dir = self.interaction_dir / date_str
                    if daily_dir.exists():
                        daily_dirs.append(daily_dir)
                    current_date += timedelta(days=1)
                
                # Process each day
                for daily_dir in daily_dirs:
                    date_str = daily_dir.name
                    f.write(f"## {date_str}\n\n")
                    
                    # Get all log files for this day
                    log_files = sorted(daily_dir.glob("session_*.log"), key=lambda x: x.stat().st_mtime)
                    
                    if not log_files:
                        f.write("No sessions recorded on this day.\n\n")
                        continue
                    
                    # Count sessions
                    f.write(f"**Total Sessions:** {len(log_files)}\n\n")
                    
                    # Extract decisions and actions
                    decisions = []
                    actions = []
                    
                    for log_file in log_files:
                        with open(log_file, 'r') as log:
                            content = log.read()
                            
                            # Extract decisions
                            decision_matches = re.findall(r'\[(.*?)\] DECISION: (.*?)(?=\n\[|\n$)', content, re.DOTALL)
                            decisions.extend([(m[0], m[1].strip()) for m in decision_matches])
                            
                            # Extract actions
                            action_matches = re.findall(r'\[(.*?)\] ACTION: (.*?)(?=\n\[|\n$)', content, re.DOTALL)
                            actions.extend([(m[0], m[1].strip()) for m in action_matches])
                    
                    # Write decisions
                    if decisions:
                        f.write("**Decisions Made:**\n")
                        for timestamp, decision in decisions:
                            f.write(f"- [{timestamp}] {decision}\n")
                        f.write("\n")
                    
                    # Write actions
                    if actions:
                        f.write("**Actions Taken:**\n")
                        for timestamp, action in actions:
                            f.write(f"- [{timestamp}] {action}\n")
                        f.write("\n")
                    
                    f.write("---\n\n")
                
                # Add summary statistics
                f.write("## Summary Statistics\n\n")
                
                # Count total sessions
                total_sessions = sum(len(list(d.glob("session_*.log"))) for d in daily_dirs)
                f.write(f"**Total Sessions:** {total_sessions}\n\n")
                
                # Count total decisions and actions
                total_decisions = sum(len(re.findall(r'\[(.*?)\] DECISION:', open(log, 'r').read())) 
                                     for d in daily_dirs for log in d.glob("session_*.log"))
                total_actions = sum(len(re.findall(r'\[(.*?)\] ACTION:', open(log, 'r').read())) 
                                   for d in daily_dirs for log in d.glob("session_*.log"))
                
                f.write(f"**Total Decisions:** {total_decisions}\n\n")
                f.write(f"**Total Actions:** {total_actions}\n\n")
            
            return report_path
        except Exception as e:
            print(f"Error generating weekly report: {e}")
            return None
    
    def analyze_conversation_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in the conversation"""
        try:
            analysis = {
                "total_messages": len(self.conversation),
                "message_types": defaultdict(int),
                "time_distribution": defaultdict(int),
                "avg_message_length": 0,
                "code_blocks": 0,
                "decisions": [],
                "actions": []
            }
            
            # Analyze message types and content
            total_length = 0
            for entry in self.conversation:
                role = entry["role"]
                content = entry["content"]
                
                # Count message types
                analysis["message_types"][role] += 1
                
                # Calculate message length
                total_length += len(content)
                
                # Count code blocks
                if "```" in content:
                    analysis["code_blocks"] += 1
                
                # Extract decisions and actions
                if role == "decision":
                    analysis["decisions"].append(content)
                elif role == "action":
                    analysis["actions"].append(content)
                
                # Analyze time distribution (by hour)
                timestamp = entry["timestamp"]
                hour = timestamp.split(":")[0]
                analysis["time_distribution"][hour] += 1
            
            # Calculate average message length
            if analysis["total_messages"] > 0:
                analysis["avg_message_length"] = total_length / analysis["total_messages"]
            
            return analysis
        except Exception as e:
            print(f"Error analyzing conversation patterns: {e}")
            return {}
    
    def generate_conversation_visualization(self, output_path: Optional[Path] = None) -> Optional[Path]:
        """Generate a visualization of the conversation flow"""
        try:
            if output_path is None:
                output_path = self.log_file.with_suffix('.html')
            
            # Analyze conversation patterns
            analysis = self.analyze_conversation_patterns()
            
            # Create HTML visualization
            html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Conversation Visualization: {self.session_id}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; max-width: 1200px; margin: 0 auto; }}
        h1, h2 {{ color: #333; }}
        .chart-container {{ width: 100%; max-width: 800px; margin: 20px auto; }}
        .stats-container {{ display: flex; flex-wrap: wrap; justify-content: space-between; margin: 20px 0; }}
        .stat-box {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; width: 48%; }}
        .conversation-flow {{ margin-top: 30px; }}
        .message {{ padding: 10px; margin: 10px 0; border-radius: 5px; }}
        .user {{ background-color: #e6f7ff; }}
        .assistant {{ background-color: #f0fff0; }}
        .action {{ background-color: #fff7e6; }}
        .decision {{ background-color: #f5f0ff; }}
    </style>
</head>
<body>
    <h1>Conversation Visualization: {self.session_id}</h1>
    
    <div class="stats-container">
        <div class="stat-box">
            <h3>Basic Statistics</h3>
            <p><strong>Total Messages:</strong> {analysis.get('total_messages', 0)}</p>
            <p><strong>Average Message Length:</strong> {analysis.get('avg_message_length', 0):.2f} characters</p>
            <p><strong>Code Blocks:</strong> {analysis.get('code_blocks', 0)}</p>
        </div>
        <div class="stat-box">
            <h3>Message Types</h3>
            <p><strong>User Messages:</strong> {analysis.get('message_types', {}).get('user', 0)}</p>
            <p><strong>Assistant Messages:</strong> {analysis.get('message_types', {}).get('assistant', 0)}</p>
            <p><strong>Actions:</strong> {analysis.get('message_types', {}).get('action', 0)}</p>
            <p><strong>Decisions:</strong> {analysis.get('message_types', {}).get('decision', 0)}</p>
        </div>
    </div>
    
    <div class="chart-container">
        <canvas id="messageTypeChart"></canvas>
    </div>
    
    <div class="chart-container">
        <canvas id="timeDistributionChart"></canvas>
    </div>
    
    <h2>Conversation Flow</h2>
    <div class="conversation-flow">
"""
            
            # Add conversation messages
            for entry in self.conversation:
                role = entry["role"]
                content = entry["content"]
                timestamp = entry["timestamp"]
                
                html_content += f"""
        <div class="message {role}">
            <strong>{role.upper()}</strong> ({timestamp}):<br>
            {content.replace('```', '<code>').replace('```', '</code>')}
        </div>
"""
            
            # Add JavaScript for charts
            html_content += """
    </div>
    
    <script>
        // Message Type Chart
        const messageTypeCtx = document.getElementById('messageTypeChart').getContext('2d');
        const messageTypeChart = new Chart(messageTypeCtx, {
            type: 'pie',
            data: {
                labels: ['User', 'Assistant', 'Action', 'Decision'],
                datasets: [{
                    data: [
"""
            
            # Add data for message type chart
            html_content += f"""
                        {analysis.get('message_types', {}).get('user', 0)},
                        {analysis.get('message_types', {}).get('assistant', 0)},
                        {analysis.get('message_types', {}).get('action', 0)},
                        {analysis.get('message_types', {}).get('decision', 0)}
"""
            
            html_content += """
                    ],
                    backgroundColor: [
                        '#0066cc',
                        '#009933',
                        '#cc6600',
                        '#9900cc'
                    ]
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Message Types Distribution'
                    }
                }
            }
        });
        
        // Time Distribution Chart
        const timeDistributionCtx = document.getElementById('timeDistributionChart').getContext('2d');
        const timeDistributionChart = new Chart(timeDistributionCtx, {
            type: 'bar',
            data: {
                labels: [
"""
            
            # Add labels for time distribution chart
            time_labels = []
            time_data = []
            for hour in sorted(analysis.get('time_distribution', {}).keys()):
                time_labels.append(f"{hour}:00")
                time_data.append(analysis['time_distribution'][hour])
            
            html_content += ", ".join([f"'{label}'" for label in time_labels])
            
            html_content += """
                ],
                datasets: [{
                    label: 'Messages per Hour',
                    data: [
"""
            
            # Add data for time distribution chart
            html_content += ", ".join([str(value) for value in time_data])
            
            html_content += """
                    ],
                    backgroundColor: '#0066cc'
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Message Time Distribution'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
    </script>
</body>
</html>
"""
            
            # Write the HTML file
            with open(output_path, 'w') as f:
                f.write(html_content)
            
            return output_path
        except Exception as e:
            print(f"Error generating conversation visualization: {e}")
            return None
    
    def _initialize_changelog(self):
        """Initialize the changelog file with error handling"""
        try:
            with open(self.changelog_path, 'w') as f:
                f.write("# Changelog\n\n")
                f.write("All notable changes to the EverythingSwing project will be documented in this file.\n\n")
                f.write("## [Unreleased]\n\n")
        except Exception as e:
            print(f"Error initializing changelog: {e}")
    
    def _add_to_changelog(self, decision_description: str):
        """Add a decision to the changelog with error handling"""
        try:
            # Read the current changelog
            with open(self.changelog_path, 'r') as f:
                content = f.read()
            
            # Check if we need to add a new date section
            date_section = f"## [{self.current_date}]"
            if date_section not in content:
                # Insert the new date section after the Unreleased section
                content = content.replace(
                    "## [Unreleased]\n\n",
                    f"## [Unreleased]\n\n{date_section}\n\n"
                )
            
            # Add the decision to the appropriate section
            if date_section in content:
                # Add to the date section
                content = content.replace(
                    f"{date_section}\n\n",
                    f"{date_section}\n\n- {decision_description}\n\n"
                )
            else:
                # Add to the Unreleased section
                content = content.replace(
                    "## [Unreleased]\n\n",
                    f"## [Unreleased]\n\n- {decision_description}\n\n"
                )
            
            # Write the updated changelog
            with open(self.changelog_path, 'w') as f:
                f.write(content)
        except Exception as e:
            print(f"Error adding to changelog: {e}")
    
    def get_context_logs(self):
        """
        Get context-relevant logs from recent sessions.
        
        Returns:
            str: Formatted context information
        """
        try:
            if not self.daily_dir.exists():
                return "No logs directory found for today."
            
            # Find all log files from today
            log_files = sorted(
                [f for f in self.daily_dir.glob("cursor_*.log")],
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            if not log_files:
                return "No log files found for today."
                
            # Process the most recent logs
            context = []
            for log_file in log_files[:5]:  # Get last 5 sessions
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    # Extract session info and interactions
                    session_info = []
                    for line in lines:
                        if any(key in line for key in ["=== Cursor Interaction Log:", "Started at:", "Interaction:", "ERROR:"]):
                            session_info.append(line.strip())
                    
                    if session_info:
                        context.append(f"=== Session {log_file.stem} ===\n" + "\n".join(session_info) + "\n")
            
            return "\n".join(context)
            
        except Exception as e:
            return f"Error getting context logs: {e}"

    def show_context_with_history(self, minutes=5, format='text'):
        """
        Show context with recent conversation history.
        
        Args:
            minutes (int): Number of minutes of history to show
            format (str): Output format ('text', 'html', or 'json')
        """
        try:
            # Get context logs
            context_logs = self.get_context_logs()
            
            # Get recent conversation history
            recent_logs = self.get_recent_logs(minutes)
            
            # Format output based on requested format
            if format == 'html':
                output_file = os.path.join(self.log_dir, f'context_history_{int(time.time())}.html')
                html_content = self._format_context_html(context_logs, recent_logs, {
                    'all_time': 'logit --context',
                    'last_hour': 'logit -n 1 --context',
                    'last_minutes': f'logit -n {minutes} --context',
                    'last_days': 'logit --yesterday --context',
                    'broaden': 'logit --context --broaden',
                    'narrow': 'logit --context --narrow'
                })
                with open(output_file, 'w') as f:
                    f.write(html_content)
                print(f"Context and history exported to: {output_file}")
                webbrowser.open(f'file://{output_file}')
            elif format == 'json':
                print(json.dumps({
                    'context': context_logs,
                    'recent_history': recent_logs
                }, indent=2))
            else:  # text format
                print("\n=== Context ===")
                print(context_logs)
                
                print("\n=== Recent History ===")
                print(recent_logs)
            
            # Log the context display
            self.log_interaction('context_display', {
                'minutes': minutes,
                'format': format
            })
            
        except Exception as e:
            print(f"Error showing context with history: {e}")
            self.log_error('context_display_error', str(e))

    def _format_context_text(self, context, history, commands):
        """Format context output in text format."""
        output = []
        output.append("=== Context Commands ===")
        output.append("To find related conversations:")
        output.append(f"  {commands['all_time']}     # All conversations related to this context")
        output.append(f"  {commands['last_hour']}   # Last hour of conversations")
        output.append(f"  {commands['last_minutes']} # Last {minutes} minutes")
        output.append(f"  {commands['last_days']}   # Last day of conversations")
        output.append("\nTo adjust context scope:")
        output.append(f"  {commands['broaden']}     # Show broader context")
        output.append(f"  {commands['narrow']}      # Show narrower context")
        output.append("\n=== Recent Conversation ===")
        output.append(history)
        output.append("\n=== Derived Context ===")
        output.append(context)
        return "\n".join(output)

    def _format_context_html(self, context_logs, recent_logs, commands):
        """
        Format context and history logs into HTML.
        
        Args:
            context_logs (str): Context logs content
            recent_logs (str): Recent logs content
            commands (dict): Available commands for context navigation
            
        Returns:
            str: Formatted HTML content
        """
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Context and History</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .section {{ margin-bottom: 30px; }}
                .section h2 {{ color: #333; border-bottom: 2px solid #eee; }}
                .content {{ white-space: pre-wrap; }}
                .commands {{ background: #f5f5f5; padding: 10px; border-radius: 5px; }}
                .commands a {{ color: #0066cc; text-decoration: none; }}
                .commands a:hover {{ text-decoration: underline; }}
                .timestamp {{ color: #666; font-size: 0.9em; }}
            </style>
        </head>
        <body>
            <div class="section">
                <h2>Context</h2>
                <div class="content">{context_logs}</div>
            </div>
            
            <div class="section">
                <h2>Recent History</h2>
                <div class="content">{recent_logs}</div>
            </div>
            
            <div class="section">
                <h2>Available Commands</h2>
                <div class="commands">
                    <p>View context:</p>
                    <ul>
                        <li><a href="#">{commands['all_time']}</a> - Show all-time context</li>
                        <li><a href="#">{commands['last_hour']}</a> - Show last hour's context</li>
                        <li><a href="#">{commands['last_minutes']}</a> - Show last {commands['last_minutes'].split()[-1]} minutes' context</li>
                        <li><a href="#">{commands['last_days']}</a> - Show yesterday's context</li>
                    </ul>
                    <p>Adjust context scope:</p>
                    <ul>
                        <li><a href="#">{commands['broaden']}</a> - Show broader context</li>
                        <li><a href="#">{commands['narrow']}</a> - Show more focused context</li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """
        return html

    def _format_context_json(self, context, history, commands):
        """Format context output in JSON format."""
        import json
        return json.dumps({
            'commands': commands,
            'recent_conversation': history,
            'derived_context': context
        }, indent=2)

    def get_recent_conversation_history(self, minutes=5):
        """
        Get recent conversation history from the last N minutes.
        
        Args:
            minutes (int): Number of minutes of history to retrieve
            
        Returns:
            str: Formatted conversation history
        """
        try:
            # Get current time
            now = datetime.now()
            
            # Calculate cutoff time
            cutoff = now - timedelta(minutes=minutes)
            
            # Get all log files from today's directory
            log_files = sorted(
                self.daily_dir.glob("session_*.log"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            conversation_history = []
            
            for log_file in log_files:
                # Check if file is within time window
                file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                if file_time < cutoff:
                    break
                    
                try:
                    with open(log_file, 'r') as f:
                        content = f.read()
                        
                        # Extract conversation parts
                        parts = content.split('---')
                        for part in parts:
                            if part.strip():
                                # Clean up the part
                                cleaned = part.strip()
                                if cleaned:
                                    conversation_history.append(cleaned)
                                    
                except Exception as e:
                    conversation_history.append(f"Error reading {log_file.name}: {e}")
            
            if not conversation_history:
                return "No recent conversation history found."
            
            return "\n\n---\n\n".join(conversation_history)
            
        except Exception as e:
            return f"Error retrieving conversation history: {e}"

    def log_interaction(self, interaction_type: str, data: Dict[str, Any]) -> None:
        """
        Log an interaction with metadata.
        
        Args:
            interaction_type (str): Type of interaction (e.g., 'context_display', 'search', etc.)
            data (Dict[str, Any]): Additional data about the interaction
        """
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_entry = {
                'timestamp': timestamp,
                'type': interaction_type,
                'data': data
            }
            self.logger.info(f"Interaction: {json.dumps(log_entry)}")
        except Exception as e:
            print(f"Error logging interaction: {e}")

    def log_error(self, error_type: str, error_message: str) -> None:
        """
        Log an error with metadata.
        
        Args:
            error_type (str): Type of error
            error_message (str): Error message
        """
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_entry = {
                'timestamp': timestamp,
                'type': error_type,
                'message': error_message
            }
            self.logger.error(f"Error: {json.dumps(log_entry)}")
        except Exception as e:
            print(f"Error logging error: {e}")

# Create a global instance
interaction_logger = InteractionLogger() 