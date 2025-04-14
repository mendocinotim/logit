# Logit

A comprehensive logging tool for tracking cursor interactions and managing conversation context in development environments.

## Features

- Command-line interface for viewing and exporting logs
- Conversation context tracking
- Cursor interaction logging
- Enhanced logging capabilities with various export formats
- JavaScript integration for browser-based logging

## Directory Structure

```
logit/
├── src/
│   ├── logit.py                    # Main CLI implementation
│   ├── interaction_logger.py       # Core logging functionality
│   ├── cursor_logger.py           # Cursor-specific logging
│   ├── enhanced_logger.py         # Advanced logging features
│   ├── log_current_conversation.py # Current conversation logging
│   └── tests/                     # Test files
├── configs/
│   └── logit_config.json         # Configuration settings
├── js/
│   └── cursor_logger.js          # JavaScript integration
└── scripts/
    └── install_dependencies.sh    # Installation script
```

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/mendocinotim/logit.git
   ```

2. Install dependencies:
   ```bash
   cd logit
   ./scripts/install_dependencies.sh
   ```

3. Install the package:
   ```bash
   pip install -e .
   ```

## Usage

Basic commands:
```bash
logit --help                 # Show help
logit -c "query"            # Show context for a specific query
logit --export html         # Export logs to HTML format
```

## Configuration

Edit `configs/logit_config.json` to customize:
- Logging preferences
- Export formats
- Context tracking settings

## Testing

Run the test suite:
```bash
python -m pytest src/test_*.py
```

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request 