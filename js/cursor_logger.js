const fs = require('fs');
const path = require('path');
const os = require('os');

// Configuration
const PROJECT_NAME = "EverythingSwing";
const LOG_BASE_DIR = "/Volumes/AI_ETS_2TB/EverythingSwing/logs/cursor/interactions";
const SPECSTORY_DIR = path.join(process.cwd(), '.specstory/history');

class CursorLogger {
    constructor() {
        this.initializeLogDir();
        this.sessionId = this.generateSessionId();
        this.logData = this.initializeLogData();
    }

    generateSessionId() {
const today = new Date();
        return `${today.toISOString().split('T')[0].replace(/-/g, '')}_${String(today.getHours()).padStart(2, '0')}${String(today.getMinutes()).padStart(2, '0')}${String(today.getSeconds()).padStart(2, '0')}`;
    }

    initializeLogDir() {
        const today = new Date();
        this.logDir = path.join(LOG_BASE_DIR, today.toISOString().split('T')[0]);
        if (!fs.existsSync(this.logDir)) {
            fs.mkdirSync(this.logDir, { recursive: true });
        }
    }

    initializeLogData() {
        return {
            session_id: this.sessionId,
    project: PROJECT_NAME,
            date: new Date().toISOString().split('T')[0],
            conversation: [],
            cursor_interactions: [],
            specstory_refs: []
        };
    }

    async captureConversationHistory() {
        try {
            // Get all SpecStory history files
            const files = fs.readdirSync(SPECSTORY_DIR)
                .filter(file => file.endsWith('.md'))
                .map(file => path.join(SPECSTORY_DIR, file));

            // Sort files by modification time (newest first)
            files.sort((a, b) => {
                return fs.statSync(b).mtime.getTime() - fs.statSync(a).mtime.getTime();
            });

            // Get the most recent file
            if (files.length === 0) return [];

            const mostRecentFile = files[0];
            const content = fs.readFileSync(mostRecentFile, 'utf8');

            // Parse the markdown content to extract conversation
            const messages = [];
            let currentRole = null;
            let currentMessage = [];
            let timestamp = null;

            content.split('\n').forEach(line => {
                if (line.includes('_**User**_')) {
                    if (currentRole && currentMessage.length > 0) {
                        messages.push({
                            role: currentRole,
                            content: currentMessage.join('\n').trim(),
                            timestamp: timestamp || new Date().toISOString()
                        });
                    }
                    currentRole = 'user';
                    currentMessage = [line.replace('_**User**_', '').trim()];
                    timestamp = new Date().toISOString();
                } else if (line.includes('_**Assistant**_')) {
                    if (currentRole && currentMessage.length > 0) {
                        messages.push({
                            role: currentRole,
                            content: currentMessage.join('\n').trim(),
                            timestamp: timestamp || new Date().toISOString()
                        });
                    }
                    currentRole = 'assistant';
                    currentMessage = [line.replace('_**Assistant**_', '').trim()];
                    timestamp = new Date().toISOString();
                } else if (currentRole) {
                    currentMessage.push(line);
                }
            });

            // Add the last message if exists
            if (currentRole && currentMessage.length > 0) {
                messages.push({
                    role: currentRole,
                    content: currentMessage.join('\n').trim(),
                    timestamp: timestamp || new Date().toISOString()
                });
            }

            return messages;
        } catch (error) {
            console.error('Error reading SpecStory history:', error);
            return [];
        }
    }

    async updateSpecStoryRefs() {
        if (fs.existsSync(SPECSTORY_DIR)) {
            const files = fs.readdirSync(SPECSTORY_DIR);
            this.logData.specstory_refs = files.map(file => ({
                file,
                path: path.join(SPECSTORY_DIR, file)
            }));
        }
    }

    async logInteraction(type, details) {
        this.logData.cursor_interactions.push({
            timestamp: new Date().toISOString(),
            type,
            details
        });

        // Update conversation history
        const conversationHistory = await this.captureConversationHistory();
        this.logData.conversation = conversationHistory;
        
        // Update SpecStory references
        await this.updateSpecStoryRefs();

        // Write to log file
        const logFilePath = path.join(this.logDir, `session_${this.sessionId}.log`);
        fs.writeFileSync(logFilePath, JSON.stringify(this.logData, null, 2));

        // Generate Perplexity link
        const perplexityLink = `https://perplexity.ai/?log_file=${encodeURIComponent(logFilePath)}&conversation=${Buffer.from(JSON.stringify(this.logData)).toString('base64')}`;
        
        // Also write markdown version
        const markdownPath = logFilePath.replace('.log', '.md');
        const markdownContent = this.generateMarkdown();
        fs.writeFileSync(markdownPath, markdownContent);

        // Write HTML version
        const htmlPath = logFilePath.replace('.log', '.html');
        const htmlContent = this.generateHTML();
        fs.writeFileSync(htmlPath, htmlContent);

        return {
            logFilePath,
            perplexityLink,
            markdownPath,
            htmlPath
        };
    }

    generateMarkdown() {
        let md = `# Cursor Session Log: ${this.sessionId}\n\n`;
        md += `## Project: ${PROJECT_NAME}\n`;
        md += `Date: ${this.logData.date}\n\n`;

        md += `## Conversation History\n\n`;
        this.logData.conversation.forEach(msg => {
            const isoTime = new Date(msg.timestamp).toISOString();
            const formattedTime = new Date(msg.timestamp).toLocaleString('en-US', {
                month: '2-digit',
                day: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: true
            });
            md += `### ${msg.role}\n`;
            md += `**ISO Time:** ${isoTime} | **Local Time:** ${formattedTime}\n\n`;
            md += `${msg.content}\n\n`;
        });

        md += `## Cursor Interactions\n\n`;
        this.logData.cursor_interactions.forEach(interaction => {
            const isoTime = new Date(interaction.timestamp).toISOString();
            const formattedTime = new Date(interaction.timestamp).toLocaleString('en-US', {
                month: '2-digit',
                day: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: true
            });
            md += `- **ISO Time:** ${isoTime} | **Local Time:** ${formattedTime}\n`;
            md += `  Type: ${interaction.type}\n`;
            md += `  ${JSON.stringify(interaction.details)}\n\n`;
        });

        if (this.logData.specstory_refs.length > 0) {
            md += `## SpecStory References\n\n`;
            this.logData.specstory_refs.forEach(ref => {
                md += `- [${ref.file}](${ref.path})\n`;
            });
        }

        return md;
    }

    generateHTML() {
        let html = `
<!DOCTYPE html>
<html>
<head>
    <title>Cursor Session Log: ${this.sessionId}</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 20px auto;
            max-width: 1200px;
            line-height: 1.6;
            color: #1a1a1a;
            background: #f8f9fa;
            padding: 20px;
        }
        .message { 
            margin: 24px 0; 
            padding: 24px; 
            border-radius: 12px;
            background: #ffffff;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        .user { 
            background: #f8f9fa;
            border: 1px solid #e9ecef;
        }
        .assistant { 
            background: #ffffff;
            border: 1px solid #e9ecef;
        }
        .timestamp { 
            color: #6c757d; 
            font-size: 0.9em; 
            display: flex; 
            justify-content: space-between;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid #e9ecef;
        }
        .local-time { order: 1; }
        .iso-time { order: 2; }
        .interaction { 
            margin: 20px 0; 
            padding: 16px; 
            background: #f8f9fa; 
            border-radius: 8px;
            border: 1px solid #e9ecef;
        }
        h3 {
            margin: 0 0 16px 0;
            color: #0366d6;
            font-size: 1.1em;
            font-weight: 600;
        }
        .content {
            font-size: 1em;
            line-height: 1.6;
        }
        .markdown {
            line-height: 1.8;
        }
        .markdown p {
            margin: 16px 0;
        }
        .markdown ul, .markdown ol {
            padding-left: 24px;
            margin: 16px 0;
        }
        .markdown li {
            margin: 8px 0;
        }
        .markdown ol {
            list-style-type: decimal;
        }
        .markdown ul {
            list-style-type: disc;
        }
        pre {
            background: #f6f8fa;
            padding: 16px;
            border-radius: 6px;
            border: 1px solid #e1e4e8;
            overflow-x: auto;
            margin: 16px 0;
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
            font-size: 0.9em;
            line-height: 1.5;
        }
        code {
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
            background: #f6f8fa;
            padding: 0.2em 0.4em;
            border-radius: 3px;
            font-size: 0.9em;
            border: 1px solid #e1e4e8;
        }
        .code-block {
            position: relative;
            background: #f6f8fa;
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            margin: 16px 0;
        }
        .code-block-header {
            padding: 8px 16px;
            background: #f1f3f4;
            border-bottom: 1px solid #e1e4e8;
            border-radius: 6px 6px 0 0;
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
            font-size: 0.9em;
            color: #24292e;
        }
        .code-block pre {
            margin: 0;
            border: none;
            border-radius: 0 0 6px 6px;
        }
        .diff-add {
            background: #e6ffec;
            border-left: 4px solid #2da44e;
            padding-left: 12px;
        }
        .diff-remove {
            background: #ffebe9;
            border-left: 4px solid #cf222e;
            padding-left: 12px;
        }
        .tool-call {
            background: #f6f8fa;
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            margin: 16px 0;
            padding: 16px;
        }
        .tool-call-header {
            font-weight: 600;
            color: #0366d6;
            margin-bottom: 8px;
        }
    </style>
</head>
<body>
    <h1>Cursor Session Log: ${this.sessionId}</h1>
    <h2>Project: ${PROJECT_NAME}</h2>
    <p>Date: ${this.logData.date}</p>

    <h2>Conversation History</h2>
    ${this.logData.conversation.map(msg => {
        const isoTime = new Date(msg.timestamp).toISOString();
        const formattedTime = new Date(msg.timestamp).toLocaleString('en-US', {
            month: '2-digit',
            day: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: true
        });
        
        // Format the content based on the role
        let formattedContent = msg.content;
        if (msg.role === 'assistant') {
            // Process markdown-style content
            formattedContent = formattedContent
                // Handle code blocks with language
                .replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
                    const language = lang || '';
                    return `<div class="code-block">
                        ${language ? `<div class="code-block-header">${language}</div>` : ''}
                        <pre><code>${code.trim()}</code></pre>
                    </div>`;
                })
                // Handle inline code
                .replace(/`([^`]+)`/g, '<code>$1</code>')
                // Handle ordered lists
                .replace(/^\d+\.\s+(.+)$/gm, '<li>$1</li>')
                .replace(/(<li>.*<\/li>\n?)+/g, '<ol>$&</ol>')
                // Handle unordered lists
                .replace(/^[-*]\s+(.+)$/gm, '<li>$1</li>')
                .replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')
                // Handle paragraphs
                .replace(/\n\n/g, '</p><p>')
                // Handle line breaks
                .replace(/\n/g, '<br>')
                // Handle bold
                .replace(/\*\*([^\*]+)\*\*/g, '<strong>$1</strong>')
                // Handle italic
                .replace(/\*([^\*]+)\*/g, '<em>$1</em>')
                // Handle diff blocks
                .replace(/^\+\s*(.*)$/gm, '<div class="diff-add">$1</div>')
                .replace(/^-\s*(.*)$/gm, '<div class="diff-remove">$1</div>')
                // Handle tool calls
                .replace(/<tool-call>([\s\S]*?)<\/tool-call>/g, '<div class="tool-call"><div class="tool-call-header">Tool Call:</div>$1</div>');
                
            formattedContent = '<div class="markdown"><p>' + formattedContent + '</p></div>';
        }

        return `
        <div class="message ${msg.role}">
            <h3>${msg.role}</h3>
            <div class="timestamp">
                <span class="local-time">Local: ${formattedTime}</span>
                <span class="iso-time">ISO: ${isoTime}</span>
            </div>
            <div class="content">${formattedContent}</div>
        </div>`;
    }).join('')}

    <h2>Cursor Interactions</h2>
    ${this.logData.cursor_interactions.map(interaction => {
        const isoTime = new Date(interaction.timestamp).toISOString();
        const formattedTime = new Date(interaction.timestamp).toLocaleString('en-US', {
            month: '2-digit',
            day: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: true
        });
        return `
        <div class="interaction">
            <div class="timestamp">
                <span class="local-time">Local: ${formattedTime}</span>
                <span class="iso-time">ISO: ${isoTime}</span>
            </div>
            <div>Type: ${interaction.type}</div>
            <pre><code>${JSON.stringify(interaction.details, null, 2)}</code></pre>
        </div>`;
    }).join('')}
</body>
</html>`;

        return html;
    }

    async testLogging() {
        console.log('Testing CursorLogger...');
        
        // Log a test interaction
        const result = await this.logInteraction('test', {
            message: 'Testing cursor logger functionality'
        });
        
        console.log('\nLog files created:');
        console.log(`- Log file: ${result.logFilePath}`);
        console.log(`- Markdown: ${result.markdownPath}`);
        console.log(`- HTML: ${result.htmlPath}`);
        console.log(`\nPerplexity link:`);
        console.log(result.perplexityLink);
        
        // Display conversation history
        console.log('\nRecent conversation history:');
        const history = await this.captureConversationHistory();
        console.log(`Found ${history.length} messages`);
        
        // Display SpecStory references
        await this.updateSpecStoryRefs();
        console.log('\nSpecStory references:');
        this.logData.specstory_refs.forEach(ref => {
            console.log(`- ${ref.file}`);
        });
    }

    formatMessage(message) {
        const timestamp = new Date(message.timestamp);
        const isoTime = timestamp.toISOString();
        const formattedTime = timestamp.toLocaleTimeString('en-US', {
            hour: 'numeric',
            minute: '2-digit',
            second: '2-digit',
            fractionalSecondDigits: 3,
            hour12: true
        });
        return `[${isoTime}] [${formattedTime}] ${message.role}: ${message.content}`;
    }

    generateLogFiles() {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const date = new Date().toISOString().split('T')[0];
        const sessionId = this.sessionId || timestamp;
        const jsonLog = path.join(this.logDir, `cursor_${sessionId}.log`);
        const markdownLog = path.join(this.logDir, `cursor_${sessionId}.md`);
        const htmlLog = path.join(this.logDir, `cursor_${sessionId}.html`);

        // Write JSON log
        fs.writeFileSync(jsonLog, JSON.stringify(this.messages, null, 2));

        // Write Markdown log
        const markdownContent = this.generateMarkdown();
        fs.writeFileSync(markdownLog, markdownContent);

        // Write HTML log
        const htmlContent = this.generateHTML();
        fs.writeFileSync(htmlLog, htmlContent);

        return {
            json: jsonLog,
            markdown: markdownLog,
            html: htmlLog
        };
    }
}

const logger = new CursorLogger();

// If running directly (not required as a module)
if (require.main === module) {
    logger.testLogging().catch(console.error);
}

module.exports = logger;
