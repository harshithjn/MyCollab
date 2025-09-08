class MyCollabApp {
    constructor() {
        this.editor = null;
        this.websocket = null;
        this.currentDocId = null;
        this.userId = this.generateUserId();
        this.username = 'Anonymous';
        this.isConnected = false;
        this.documentVersion = 0;
        this.otherUsers = new Map();
        this.pendingOperations = [];
        this.isApplyingRemoteOperation = false;
        
        this.initializeApp();
    }
    
    generateUserId() {
        return 'user_' + Math.random().toString(36).substr(2, 9);
    }
    
    initializeApp() {
        this.setupEventListeners();
        this.initializeMonacoEditor();
        this.updateUI();
        
        const docId = this.getDocumentIdFromUrl();
        if (docId) {
            setTimeout(() => {
                this.connectToWebSocket(docId);
            }, 1000);
        }
    }
    
    setupEventListeners() {
        const usernameInput = document.getElementById('username');
        usernameInput.addEventListener('input', (e) => {
            this.username = e.target.value || 'Anonymous';
        });
        
        const languageSelect = document.getElementById('language');
        languageSelect.addEventListener('change', (e) => {
            this.changeLanguage(e.target.value);
        });
    }
    
    initializeMonacoEditor() {
        require.config({ paths: { 'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.44.0/min/vs' }});
        
        require(['vs/editor/editor.main'], () => {
            this.editor = monaco.editor.create(document.getElementById('editor'), {
                value: '// Welcome to MyCollab!\n// Start typing to begin collaborative editing...\n\nfunction hello() {\n    console.log("Hello, World!");\n}',
                language: 'javascript',
                theme: 'vs-dark',
                automaticLayout: true,
                minimap: { enabled: false },
                scrollBeyondLastLine: false,
                fontSize: 14,
                lineNumbers: 'on',
                roundedSelection: false,
                scrollbar: {
                    vertical: 'auto',
                    horizontal: 'auto'
                },
                cursorStyle: 'line',
                cursorBlinking: 'blink'
            });
            
            this.setupEditorEventListeners();
        });
    }
    
    setupEditorEventListeners() {
        if (!this.editor) return;
        
        this.editor.onDidChangeModelContent((e) => {
            if (this.isApplyingRemoteOperation) return;
            
            this.handleContentChange(e);
        });
        
        this.editor.onDidChangeCursorPosition((e) => {
            this.handleCursorChange(e);
        });
        
        this.editor.onDidChangeCursorSelection((e) => {
            this.handleSelectionChange(e);
        });
    }
    
    handleContentChange(e) {
        if (!this.isConnected || !this.currentDocId) return;
        if (this.isApplyingRemoteOperation) return;
        
        const model = this.editor.getModel();
        const content = model.getValue();
        
        this.sendContentUpdate(content);
    }
    
    createOperationsFromChanges(changes, model) {
        const operations = [];
        
        for (const change of changes) {
            const range = change.range;
            const text = change.text;
            
            const startPos = model.getOffsetAt(range.startLineNumber, range.startColumn);
            const endPos = model.getOffsetAt(range.endLineNumber, range.endColumn);
            
            if (startPos > 0) {
                operations.push({
                    type: 'retain',
                    length: startPos
                });
            }
            
            if (endPos > startPos) {
                operations.push({
                    type: 'delete',
                    length: endPos - startPos
                });
            }
            
            if (text) {
                operations.push({
                    type: 'insert',
                    value: text
                });
            }
        }
        
        return operations;
    }
    
    handleCursorChange(e) {
        if (!this.isConnected) return;
        
        const position = {
            line: e.position.lineNumber,
            column: e.position.column
        };
        
        this.sendCursorUpdate(position);
        this.updateCursorPositionDisplay(position);
    }
    
    handleSelectionChange(e) {
    }
    
    sendOperation(operations) {
        if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) return;
        
        const message = {
            type: 'operation',
            operation: operations,
            version: this.documentVersion
        };
        
        this.websocket.send(JSON.stringify(message));
    }
    
    sendContentUpdate(content) {
        if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) return;
        
        const message = {
            type: 'content_update',
            content: content,
            version: this.documentVersion
        };
        
        this.websocket.send(JSON.stringify(message));
    }
    
    sendCursorUpdate(position) {
        if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) return;
        
        const message = {
            type: 'cursor_update',
            cursor_position: position
        };
        
        this.websocket.send(JSON.stringify(message));
    }
    
    connectToDocument() {
        const docId = this.getDocumentIdFromUrl() || this.generateDocumentId();
        this.connectToWebSocket(docId);
    }
    
    getDocumentIdFromUrl() {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('doc');
    }
    
    generateDocumentId() {
        return 'doc_' + Math.random().toString(36).substr(2, 9);
    }
    
    connectToWebSocket(docId) {
        this.showLoading(true);
        
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/${docId}?user_id=${this.userId}&username=${encodeURIComponent(this.username)}`;
        
        this.websocket = new WebSocket(wsUrl);
        
        this.websocket.onopen = () => {
            this.isConnected = true;
            this.currentDocId = docId;
            this.updateConnectionStatus(true);
            this.showLoading(false);
            this.updateDocumentInfo(docId);
            this.addChatMessage('system', 'Connected to document');
        };
        
        this.websocket.onmessage = (event) => {
            this.handleWebSocketMessage(JSON.parse(event.data));
        };
        
        this.websocket.onclose = () => {
            this.isConnected = false;
            this.updateConnectionStatus(false);
            this.addChatMessage('system', 'Disconnected from document');
        };
        
        this.websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.addChatMessage('system', 'Connection error occurred');
            this.showLoading(false);
        };
    }
    
    handleWebSocketMessage(message) {
        console.log('Received WebSocket message:', message);
        switch (message.type) {
            case 'document_state':
                this.handleDocumentState(message);
                break;
            case 'operation_applied':
                this.handleRemoteOperation(message);
                break;
            case 'operation_confirmed':
                this.handleOperationConfirmed(message);
                break;
            case 'content_update':
                this.handleRemoteContentUpdate(message);
                break;
            case 'user_joined':
                this.handleUserJoined(message);
                break;
            case 'user_left':
                this.handleUserLeft(message);
                break;
            case 'cursor_update':
                this.handleRemoteCursorUpdate(message);
                break;
            case 'chat_message':
                this.handleChatMessage(message);
                break;
            case 'error':
                this.handleError(message);
                break;
        }
    }
    
    handleDocumentState(message) {
        this.isApplyingRemoteOperation = true;
        
        if (this.editor) {
            this.editor.setValue(message.content);
        }
        
        this.documentVersion = message.version;
        this.isApplyingRemoteOperation = false;
    }
    
    handleRemoteOperation(message) {
        if (message.user_id === this.userId) return;
        
        this.isApplyingRemoteOperation = true;
        
        this.applyOperationToEditor(message.operation);
        
        this.documentVersion = message.version;
        this.isApplyingRemoteOperation = false;
    }
    
    applyOperationToEditor(operations) {
        if (!this.editor) return;
        
        const model = this.editor.getModel();
        let position = 0;
        
        const edits = [];
        
        for (const op of operations) {
            if (op.type === 'retain') {
                position += op.length;
            } else if (op.type === 'delete') {
                const startPos = model.getPositionAt(position);
                const endPos = model.getPositionAt(position + op.length);
                edits.push({
                    range: new monaco.Range(startPos.lineNumber, startPos.column, endPos.lineNumber, endPos.column),
                    text: ''
                });
                position += op.length;
            } else if (op.type === 'insert') {
                const pos = model.getPositionAt(position);
                edits.push({
                    range: new monaco.Range(pos.lineNumber, pos.column, pos.lineNumber, pos.column),
                    text: op.value
                });
                position += op.value.length;
            }
        }
        
        if (edits.length > 0) {
            model.pushEditOperations([], edits, () => null);
        }
    }
    
    handleOperationConfirmed(message) {
        this.documentVersion = message.version;
    }
    
    handleRemoteContentUpdate(message) {
        if (message.user_id === this.userId) return;
        
        this.isApplyingRemoteOperation = true;
        
        if (this.editor) {
            this.editor.setValue(message.content);
        }
        
        this.documentVersion = message.version;
        this.isApplyingRemoteOperation = false;
    }
    
    handleUserJoined(message) {
        console.log('User joined:', message);
        this.otherUsers.set(message.user_id, {
            id: message.user_id,
            username: message.username,
            cursor: null
        });
        
        this.updateUsersList();
        this.addChatMessage('system', `${message.username} joined the document`);
    }
    
    handleUserLeft(message) {
        console.log('User left:', message);
        this.otherUsers.delete(message.user_id);
        this.updateUsersList();
        this.addChatMessage('system', `${message.username} left the document`);
    }
    
    handleRemoteCursorUpdate(message) {
        if (message.user_id === this.userId) return;
        
        const user = this.otherUsers.get(message.user_id);
        if (user) {
            user.cursor = message.cursor_position;
            this.updateUsersList();
        }
    }
    
    handleChatMessage(message) {
        this.addChatMessage('user', message.message, message.username);
    }
    
    handleError(message) {
        console.error('Server error:', message.message);
        this.addChatMessage('system', `Error: ${message.message}`);
    }
    
    updateUsersList() {
        const usersList = document.getElementById('usersList');
        const userCount = this.otherUsers.size + 1;
        
        usersList.innerHTML = '';
        
        const currentUserDiv = document.createElement('div');
        currentUserDiv.className = 'user-item';
        currentUserDiv.innerHTML = `
            <div class="user-avatar" style="background-color: #007acc;">${this.username.charAt(0).toUpperCase()}</div>
            <div class="user-name">${this.username} (You)</div>
        `;
        usersList.appendChild(currentUserDiv);
        
        for (const [userId, user] of this.otherUsers) {
            const userDiv = document.createElement('div');
            userDiv.className = 'user-item';
            userDiv.innerHTML = `
                <div class="user-avatar" style="background-color: #4caf50;">${user.username.charAt(0).toUpperCase()}</div>
                <div class="user-name">${user.username}</div>
            `;
            usersList.appendChild(userDiv);
        }
        
        if (this.otherUsers.size === 0) {
            const noUsersDiv = document.createElement('div');
            noUsersDiv.className = 'no-users';
            noUsersDiv.textContent = 'No other users connected';
            usersList.appendChild(noUsersDiv);
        }
        
        document.getElementById('userCount').textContent = `${userCount} users`;
    }
    
    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connectionStatus');
        if (connected) {
            statusElement.textContent = 'Connected';
            statusElement.className = 'status-connected';
        } else {
            statusElement.textContent = 'Disconnected';
            statusElement.className = 'status-disconnected';
        }
    }
    
    updateDocumentInfo(docId) {
        document.getElementById('docId').textContent = `Document ID: ${docId}`;
        document.getElementById('version').textContent = `Version: ${this.documentVersion}`;
    }
    
    updateCursorPositionDisplay(position) {
        document.getElementById('cursorPosition').textContent = `Line ${position.line}, Column ${position.column}`;
    }
    
    addChatMessage(type, message, username = null) {
        const chatMessages = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${type}`;
        
        if (type === 'user' && username) {
            messageDiv.innerHTML = `<span class="username">${username}:</span>${message}`;
        } else {
            messageDiv.textContent = message;
        }
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    showLoading(show) {
        const loadingOverlay = document.getElementById('loadingOverlay');
        loadingOverlay.style.display = show ? 'flex' : 'none';
    }
    
    changeLanguage(language) {
        if (this.editor) {
            monaco.editor.setModelLanguage(this.editor.getModel(), language);
        }
    }
    
    createNewDocument() {
        const newDocId = this.generateDocumentId();
        const newUrl = `${window.location.origin}${window.location.pathname}?doc=${newDocId}`;
        window.location.href = newUrl;
    }
    
    shareDocument() {
        if (!this.currentDocId) {
            alert('Please connect to a document first');
            return;
        }
        
        const shareUrl = `${window.location.origin}${window.location.pathname}?doc=${this.currentDocId}`;
        document.getElementById('shareUrl').value = shareUrl;
        document.getElementById('shareModal').style.display = 'block';
    }
    
    copyShareUrl() {
        const shareUrlInput = document.getElementById('shareUrl');
        shareUrlInput.select();
        document.execCommand('copy');
        alert('Share URL copied to clipboard!');
    }
    
    closeShareModal() {
        document.getElementById('shareModal').style.display = 'none';
    }
    
    sendChatMessage() {
        const chatInput = document.getElementById('chatInput');
        const message = chatInput.value.trim();
        
        if (message && this.isConnected) {
            this.websocket.send(JSON.stringify({
                type: 'chat_message',
                message: message,
                username: this.username
            }));
            
            chatInput.value = '';
        }
    }
    
    handleChatKeyPress(event) {
        if (event.key === 'Enter') {
            this.sendChatMessage();
        }
    }
    
    updateUI() {
        this.updateUsersList();
        this.updateConnectionStatus(this.isConnected);
    }
}

let app;

function connectToDocument() {
    app.connectToDocument();
}

function changeLanguage() {
    const language = document.getElementById('language').value;
    app.changeLanguage(language);
}

function createNewDocument() {
    app.createNewDocument();
}

function shareDocument() {
    app.shareDocument();
}

function closeShareModal() {
    app.closeShareModal();
}

function copyShareUrl() {
    app.copyShareUrl();
}

function sendChatMessage() {
    app.sendChatMessage();
}

function handleChatKeyPress(event) {
    app.handleChatKeyPress(event);
}

document.addEventListener('DOMContentLoaded', () => {
    app = new MyCollabApp();
});