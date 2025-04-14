#!/usr/bin/env python3
import argparse
import sys
from datetime import datetime
import os
import re
import json
import time
from pathlib import Path
import logging
from code.utils.interaction_logger import InteractionLogger

class LogitLogger:
    def __init__(self):
        self.start_time = datetime.now()
        self.token_count = 0
        self.modified_files = set()
        self.command_count = 0
        
        # Initialize daily directory
        self.logs_dir = Path('logs')
        self.daily_dir = self.logs_dir / datetime.now().strftime('%Y%m%d')
        self.daily_dir.mkdir(parents=True, exist_ok=True)
        
    def update_stats(self, tokens=0, file_path=None, command=False):
        self.token_count += tokens
        if file_path:
            self.modified_files.add(file_path)
        if command:
            self.command_count += 1
            
    def get_stats(self):
        elapsed_time = (datetime.now() - self.start_time).total_seconds() / 60
        return {
            'time_spent': round(elapsed_time, 1),
            'token_usage': self.token_count,
            'files_modified': len(self.modified_files),
            'commands': self.command_count
        }

    def show_context(self, export_format='text'):
        """Show context from recent logs in the specified format."""
        try:
            context = self.get_context_logs()
            
            if export_format == 'html':
                logging.info("Converting context to HTML...")
                html_content = self.convert_to_html(context)
                logging.info("Generated HTML content")
                logging.info("Saving and opening HTML file...")
                self.save_and_open_html(html_content, 'context')
                logging.info("HTML file saved and opened")
            else:
                print(context)
                
        except Exception as e:
            logging.error(f"Error in show_context: {e}", exc_info=True)
            print(f"Error showing context: {e}")
            
    def convert_to_html(self, content):
        """Convert content to HTML with styling."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Log Context</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
                    line-height: 1.6;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                    background: #f5f5f5;
                }}
                .container {{
                    background: white;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                pre {{
                    background: #f8f8f8;
                    padding: 15px;
                    border-radius: 4px;
                    overflow-x: auto;
                }}
                .session {{
                    margin-bottom: 30px;
                    border-bottom: 1px solid #eee;
                    padding-bottom: 20px;
                }}
                .timestamp {{
                    color: #666;
                    font-size: 0.9em;
                }}
                .decision, .action, .goal {{
                    margin: 10px 0;
                    padding: 10px;
                    border-left: 4px solid;
                }}
                .decision {{ border-color: #4CAF50; }}
                .action {{ border-color: #2196F3; }}
                .goal {{ border-color: #FF9800; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Log Context</h1>
                {self.markdown_to_html(content)}
            </div>
        </body>
        </html>
        """
        return html
        
    def markdown_to_html(self, content):
        """Convert markdown content to HTML."""
        import markdown
        return markdown.markdown(content)
        
    def save_and_open_html(self, html_content, prefix):
        """Save HTML content to a file and open in browser."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{prefix}_{timestamp}.html"
        
        # Save to logs directory
        html_dir = Path('logs/html')
        html_dir.mkdir(parents=True, exist_ok=True)
        html_path = html_dir / filename
        
        with open(html_path, 'w') as f:
            f.write(html_content)
            
        # Open in browser
        import webbrowser
        webbrowser.open(f'file://{html_path.absolute()}')
        
    def show_recent_logs(self):
        """Show recent logs"""
        from interaction_logger import InteractionLogger as IL
        il = IL()
        logs = il.get_recent_logs()
        print(logs)
        
    def show_today_logs(self):
        """Show today's logs"""
        from interaction_logger import InteractionLogger as IL
        il = IL()
        logs = il.get_recent_logs(1)  # Get just today's logs
        print(logs)
        
    def show_yesterday_logs(self):
        """Show yesterday's logs"""
        from interaction_logger import InteractionLogger as IL
        il = IL()
        # This is a placeholder - would need to be implemented properly
        print("Yesterday's logs functionality not yet implemented")
        
    def show_last_n_hours(self, hours):
        """Show logs from the last N hours"""
        from interaction_logger import InteractionLogger as IL
        il = IL()
        # This is a placeholder - would need to be implemented properly
        print(f"Logs from the last {hours} hours functionality not yet implemented")
        
    def export_logs(self, format):
        """Export logs in the specified format"""
        from interaction_logger import InteractionLogger as IL
        il = IL()
        if format == 'html':
            output_file = il.export_to_html()
            if output_file:
                import webbrowser
                webbrowser.open(f'file://{os.path.abspath(output_file)}')
        elif format == 'markdown':
            output_file = il.export_to_markdown()
            if output_file:
                print(f"Exported to {output_file}")
        elif format == 'json':
            output_file = il.export_to_json()
            if output_file:
                print(f"Exported to {output_file}")
                
    def set_topic(self, topic):
        """Set the current topic"""
        from interaction_logger import InteractionLogger as IL
        il = IL()
        il.start_topic_tracking(topic)
        print(f"Topic set to: {topic}")
        
    def list_topics(self):
        """List all available topics"""
        from interaction_logger import InteractionLogger as IL
        il = IL()
        topics_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs', 'cursor', 'topics')
        if os.path.exists(topics_dir):
            topics = [f.replace('.json', '') for f in os.listdir(topics_dir) if f.endswith('.json')]
            if topics:
                print("Available topics:")
                for topic in topics:
                    print(f"  - {topic}")
            else:
                print("No topics found")
        else:
            print("Topics directory not found")
            
    def set_summary(self, summary):
        """Set a summary for the current topic"""
        from interaction_logger import InteractionLogger as IL
        il = IL()
        if il.current_topic:
            topic_data = {
                'title': il.current_topic,
                'description': '',
                'summary': summary,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            il.store_topic(il.current_topic, topic_data)
            print(f"Summary set for topic: {il.current_topic}")
        else:
            print("No topic set. Use 'logit -t <topic>' to set a topic first.")
            
    def set_goals(self, goals):
        """Set goals for the current topic"""
        from interaction_logger import InteractionLogger as IL
        il = IL()
        if il.current_topic:
            topic_data = {
                'title': il.current_topic,
                'description': '',
                'goals': goals,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            il.store_topic(il.current_topic, topic_data)
            print(f"Goals set for topic: {il.current_topic}")
        else:
            print("No topic set. Use 'logit -t <topic>' to set a topic first.")

class Logger(LogitLogger):
    def __init__(self):
        super().__init__()
        self.project_name = "EverythingSwing"
        self.date = datetime.now().strftime("%Y-%m-%d")
        self.log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs', 'cursor')
        self.topics_dir = os.path.join(self.log_dir, 'topics')
        self.log_file = os.path.join(self.log_dir, f'cursor_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        os.makedirs(self.topics_dir, exist_ok=True)
        
    def store_topic(self, topic_name, topic_data):
        """Store topic data in a JSON file"""
        topic_file = os.path.join(self.topics_dir, f'{topic_name}.json')
        with open(topic_file, 'w') as f:
            json.dump(topic_data, f, indent=2)
        print(f"Topic '{topic_name}' created/updated:")
        print(f"  Title: {topic_data['title']}")
        print(f"  Description: {topic_data['description']}")
        print(f"  Version: {topic_data['version']}")
        if 'summary' in topic_data:
            print(f"  Summary: {topic_data['summary']}")
            
    def list_topics(self):
        """List all available topics"""
        topics = []
        for file in os.listdir(self.topics_dir):
            if file.endswith('.json'):
                topic_name = file[:-5]
                topic_file = os.path.join(self.topics_dir, file)
                with open(topic_file, 'r') as f:
                    topic_data = json.load(f)
                topics.append({
                    'name': topic_name,
                    'title': topic_data['title'],
                    'description': topic_data['description']
                })
        return topics

def get_option_help(option_name: str) -> str:
    """Get detailed help text for a specific option"""
    help_texts = {
        'context': """
Context Option (-c, --context)
-----------------------------
Shows context with recent conversation history.

Features:
- Displays the most relevant logs based on the current context
- Optionally accepts a topic to filter context
- Shows session timestamps and system information
- Includes conversation history when available

Example:
    logit -c                # Show context with recent history
    logit -c "Bug Fix"      # Show context for "Bug Fix" topic
    logit -c --export html  # Show context and export as HTML
""",
        'recent': """
Recent Option (-r, --recent)
---------------------------
Shows logs from the last N hours.

Features:
- Displays logs from the specified time period
- Default is 24 hours if no value is provided
- Shows session information and interactions
- Can be combined with export options

Example:
    logit -r                # Show logs from last 24 hours
    logit -r 48             # Show logs from last 48 hours
    logit -r 12 --export json  # Show logs as JSON
""",
        'today': """
Today Option (-t, --today)
-------------------------
Shows today's logs.

Features:
- Displays all logs from the current day
- Shows session information and interactions
- Can be combined with export options

Example:
    logit -t                # Show today's logs
    logit -t --export html  # Show today's logs as HTML
""",
        'yesterday': """
Yesterday Option (-y, --yesterday)
--------------------------------
Shows yesterday's logs.

Features:
- Displays all logs from the previous day
- Shows session information and interactions
- Can be combined with export options

Example:
    logit -y                # Show yesterday's logs
    logit -y --export json  # Show yesterday's logs as JSON
""",
        'summary': """
Summary Option (-s, --summary)
-----------------------------
Shows topic summaries.

Features:
- Displays summaries of all tracked topics
- Shows key decisions and actions for each topic
- Can be combined with export options

Example:
    logit -s                # Show topic summaries
    logit -s --export html  # Show summaries as HTML
""",
        'export': """
Export Option (--export)
-----------------------
Exports logs in various formats.

Supported formats:
- html: Web-friendly HTML format with styling
- json: Structured JSON format
- text: Plain text format

Example:
    logit -c --export html  # Export context as HTML
    logit -t --export json  # Export today's logs as JSON
    logit -r 48 --export text  # Export recent logs as text
""",
        'help-format': """
Help Format Option (-h, --help-format)
------------------------------------
Shows help in the specified format.

Supported formats:
- html: Web-friendly HTML format with styling
- json: Structured JSON format
- text: Plain text format (default)

Example:
    logit -h html           # Show help in HTML format
    logit --help-format json  # Show help as JSON
""",
        'topics': """
Topics Option (--topics)
-----------------------
Sets topics for the current session.

Features:
- Accepts multiple topics as space-separated arguments
- Creates or updates topic files
- Stores session metadata with the topics
- Maintains topic history across sessions

Example:
    logit --topics "Feature Implementation"  # Set a single topic
    logit --topics "Bug Fix" "UI Update"     # Set multiple topics
""",
        'goals': """
Goals Option (--goals)
---------------------
Sets goals for the current session.

Features:
- Accepts multiple goals as space-separated arguments
- Associates goals with the current session
- Tracks progress toward goals

Example:
    logit --goals "Implement login"  # Set a single goal
    logit --goals "Fix bug" "Add test"  # Set multiple goals
"""
    }
    return help_texts.get(option_name, "No detailed help available for this option.")

def get_shell_setup_command():
    """Get the shell setup command based on the current shell."""
    shell = os.environ.get('SHELL', '/bin/sh')
    shell_name = os.path.basename(shell)
    
    if shell_name == 'zsh':
        return """
# Add logit to PATH
export PATH="$PATH:$HOME/.local/bin"

# Enable logit shell integration
eval "$(logit --shell-integration)"
"""
    elif shell_name == 'bash':
        return """
# Add logit to PATH
export PATH="$PATH:$HOME/.local/bin"

# Enable logit shell integration
eval "$(logit --shell-integration)"
"""
    else:
        return f"Shell {shell_name} is not supported for automatic setup."

def get_shell_completion():
    """Get shell completion script."""
        return """
_logit_completion() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts="-c --context -r --recent -t --today -y --yesterday -s --summary --export -f --help-format --topics --list-topics --goals --set-summary"
    
    if [[ ${cur} == -* ]] ; then
    COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
    return 0
    fi
    
    case "${prev}" in
        --export)
            COMPREPLY=( $(compgen -W "html json text" -- ${cur}) )
            return 0
            ;;
        -f|--help-format)
            COMPREPLY=( $(compgen -W "html json text" -- ${cur}) )
            return 0
            ;;
        -r|--recent)
            # Suggest some common hour values
            COMPREPLY=( $(compgen -W "1 2 4 8 12 24 48 72" -- ${cur}) )
            return 0
            ;;
        --topics|--goals|--set-summary)
            # These accept multiple arguments, so no specific completions
    return 0
            ;;
    esac
}

complete -F _logit_completion logit
"""

def get_help_text(format='text'):
    """Get help text in the specified format."""
    help_text = {
        'name': 'logit',
        'version': '0.1.0',
        'description': 'A command-line tool for logging and managing cursor interactions.',
        'usage': 'logit [options]',
        'options': [
            {
                'name': '-c, --context [TOPIC]',
                'description': 'Show context with recent history. Optionally specify a topic.'
            },
            {
                'name': '-r, --recent HOURS',
                'description': 'Show logs from the last N hours (default: 24)'
            },
            {
                'name': '-t, --today',
                'description': 'Show today\'s logs'
            },
            {
                'name': '-y, --yesterday',
                'description': 'Show yesterday\'s logs'
            },
            {
                'name': '-s, --summary',
                'description': 'Show topic summaries'
            },
            {
                'name': '--export {html,json,text}',
                'description': 'Export logs in specified format'
            },
            {
                'name': '-f, --help-format {html,json,text}',
                'description': 'Show help in specified format'
            },
            {
                'name': '--topics TOPIC1 [TOPIC2 ...]',
                'description': 'Set topics for current session'
            },
            {
                'name': '--list-topics',
                'description': 'List all available topics'
            },
            {
                'name': '--goals GOAL1 [GOAL2 ...]',
                'description': 'Set goals for current session'
            },
            {
                'name': '--set-summary TEXT',
                'description': 'Set summary for current session'
            }
        ],
        'examples': [
            'logit -c "Bug Fix"                # Show context for "Bug Fix"',
            'logit -c --export html            # Show context and export as HTML',
            'logit -r 48                       # Show logs from last 48 hours',
            'logit -t                          # Show today\'s logs',
            'logit -y --export json            # Show yesterday\'s logs as JSON',
            'logit -s                          # Show topic summaries',
            'logit --topics "Feature" "Bug"    # Set multiple topics',
            'logit --list-topics               # List all topics',
            'logit --goals "Implement login"   # Set session goals',
            'logit --set-summary "Fixed login bug"  # Set session summary',
            'logit -f html                     # Show help in HTML format'
        ]
    }
    
    if format == 'json':
        return json.dumps(help_text, indent=2)
    elif format == 'html':
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>{help_text['name']} Help</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        .option {{
            margin: 10px 0;
            padding: 10px;
            background: #f5f5f5;
            border-radius: 4px;
        }}
        .example {{
            font-family: monospace;
            background: #f0f0f0;
            padding: 5px;
            border-radius: 3px;
        }}
    </style>
</head>
<body>
    <h1>{help_text['name']} v{help_text['version']}</h1>
    <p>{help_text['description']}</p>
    
    <h2>Usage</h2>
    <pre>{help_text['usage']}</pre>
    
    <h2>Options</h2>
    {''.join(f'<div class="option"><code>{opt["name"]}</code><br>{opt["description"]}</div>' for opt in help_text['options'])}
    
        <h2>Examples</h2>
    {''.join(f'<div class="example">{example}</div>' for example in help_text['examples'])}
</body>
</html>
"""
    else:  # text format
        text = [
            f"{help_text['name']} v{help_text['version']}",
            help_text['description'],
            "",
            "Usage:",
            help_text['usage'],
            "",
            "Options:"
        ]
        
        for opt in help_text['options']:
            text.append(f"  {opt['name']}")
            text.append(f"    {opt['description']}")
            text.append("")
            
        text.extend([
            "Examples:",
            *[f"  {example}" for example in help_text['examples']]
        ])
        
        return '\n'.join(text)

def create_parser():
    """Create argument parser."""
    parser = argparse.ArgumentParser(description='Cursor interaction logging tool')
    
    # Main commands
    command_group = parser.add_mutually_exclusive_group()
    command_group.add_argument('-c', '--context', nargs='?', const='all', 
                             help='Show context with recent history. Optionally specify a topic.')
    command_group.add_argument('-r', '--recent', type=int, default=24,
                             help='Show logs from the last N hours (default: 24)')
    command_group.add_argument('-t', '--today', action='store_true',
                             help='Show today\'s logs')
    command_group.add_argument('-y', '--yesterday', action='store_true',
                             help='Show yesterday\'s logs')
    command_group.add_argument('-s', '--summary', action='store_true',
                             help='Show topic summaries')
    
    # Export options
    export_group = parser.add_mutually_exclusive_group()
    export_group.add_argument('--export', choices=['html', 'json', 'text'],
                            help='Export logs in specified format')
    export_group.add_argument('-f', '--help-format', choices=['html', 'json', 'text'],
                            help='Show help in specified format')
    
    # Topic management
    parser.add_argument('--topics', nargs='+',
                       help='Set topics for current session')
    parser.add_argument('--list-topics', action='store_true',
                       help='List all topics')
    
    # Goals and summaries
    parser.add_argument('--goals', nargs='+',
                       help='Set goals for current session')
    parser.add_argument('--set-summary', nargs='+',
                       help='Set summary for current session')
    
    return parser

def show_help(format='text'):
    """Show help in the specified format."""
    help_content = get_help_text(format)
    
    if format == 'html':
        # Save to logs directory and open in browser
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"help_{timestamp}.html"
        
        # Save to logs directory
        html_dir = Path('logs/html')
        html_dir.mkdir(parents=True, exist_ok=True)
        html_path = html_dir / filename
        
        with open(html_path, 'w') as f:
            f.write(help_content)
            
        # Open in browser
        import webbrowser
        webbrowser.open(f'file://{html_path.absolute()}')
    else:
        print(help_content)

def main():
    parser = argparse.ArgumentParser(description='Cursor interaction logging tool')
    
    # Main commands
    command_group = parser.add_mutually_exclusive_group()
    command_group.add_argument('-c', '--context', nargs='?', const='all', 
                             help='Show context with recent history. Optionally specify a topic.')
    command_group.add_argument('-r', '--recent', type=int, default=24,
                             help='Show logs from the last N hours (default: 24)')
    command_group.add_argument('-t', '--today', action='store_true',
                             help='Show today\'s logs')
    command_group.add_argument('-y', '--yesterday', action='store_true',
                             help='Show yesterday\'s logs')
    command_group.add_argument('-s', '--summary', action='store_true',
                             help='Show topic summaries')
    
    # Export options
    export_group = parser.add_mutually_exclusive_group()
    export_group.add_argument('--export', choices=['html', 'json', 'text'],
                            help='Export logs in specified format')
    export_group.add_argument('-f', '--help-format', choices=['html', 'json', 'text'],
                            help='Show help in specified format')
    
    # Topic management
    parser.add_argument('--topics', nargs='+',
                       help='Set topics for current session')
    parser.add_argument('--list-topics', action='store_true',
                       help='List all topics')
    
    # Goals and summaries
    parser.add_argument('--goals', nargs='+',
                       help='Set goals for current session')
    parser.add_argument('--set-summary', nargs='+',
                       help='Set summary for current session')
    
    args = parser.parse_args()
    
    # Initialize logger
    logger = InteractionLogger()
    
    try:
        if args.help_format:
            show_help(args.help_format)
            return
            
        if args.context:
            if args.export:
                export_context(args.context, args.export)
            else:
                show_context(args.context)
                
        elif args.recent:
            if args.export:
                export_recent_logs(args.recent, args.export)
            else:
                show_recent_logs(args.recent)
                
        elif args.today:
            if args.export:
                export_today_logs(args.export)
            else:
                show_today_logs()
                
    elif args.yesterday:
            if args.export:
                export_yesterday_logs(args.export)
            else:
                show_yesterday_logs()
                
    elif args.summary:
            if args.export:
                export_summary(args.export)
            else:
                show_summary()
                
    elif args.topics:
            set_topics(args.topics)
            
        elif args.list_topics:
            list_topics()
            
    elif args.goals:
            set_goals(args.goals)
            
        elif args.set_summary:
            set_summary(args.set_summary)
            
    else:
            parser.print_help()
            
    except Exception as e:
        print(f"Error: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    main() 