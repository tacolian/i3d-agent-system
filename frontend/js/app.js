/**
 * I3D CAD Agent System — Frontend Application
 * 对接后端 FastAPI 接口
 */

// ========================================
// 配置与状态
// ========================================
const CONFIG = {
    API_BASE_URL: localStorage.getItem('api_base_url') || '',
    DEFAULT_TENANT: 'shenfa',
    SUPPORTED_TENANTS: ['shenfa', 'meidi', 'dongjiang', 'huabei'],
};

const STATE = {
    tenantId: localStorage.getItem('tenant_id') || '',
    userId: localStorage.getItem('user_id') || '',
    sessionId: localStorage.getItem('session_id') || '',
    sessions: JSON.parse(localStorage.getItem('sessions') || '[]'),
    messages: [],
    streamEnabled: localStorage.getItem('stream_enabled') !== 'false',
    maxResults: parseInt(localStorage.getItem('max_results') || '10'),
    temperature: parseFloat(localStorage.getItem('temperature') || '0.7'),
    enableRag: localStorage.getItem('enable_rag') !== 'false',
    currentFile: null,
    isStreaming: false,
    eventSource: null,
};

// 工具函数
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);
const uuid = () => crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
const now = () => new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });

function getApiUrl(path) {
    const base = CONFIG.API_BASE_URL || window.location.origin;
    return `${base.replace(/\/$/, '')}${path}`;
}

function getHeaders() {
    const headers = {
        'Content-Type': 'application/json',
        'X-Tenant-ID': STATE.tenantId,
    };
    if (STATE.userId) headers['X-User-ID'] = STATE.userId;
    headers['X-Request-ID'] = uuid();
    return headers;
}

// ========================================
// Toast 提示
// ========================================
function showToast(message, type = 'info') {
    const toast = $('#toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    setTimeout(() => toast.classList.remove('show'), 3000);
}

// ========================================
// 租户选择
// ========================================
function initTenantSelector() {
    const overlay = $('#tenant-overlay');
    const app = $('#app');

    // 如果已有租户，直接跳过
    if (STATE.tenantId && CONFIG.SUPPORTED_TENANTS.includes(STATE.tenantId)) {
        overlay.classList.add('hidden');
        app.classList.remove('hidden');
        onTenantSelected(STATE.tenantId);
        return;
    }

    $$('.tenant-card').forEach(card => {
        card.addEventListener('click', () => {
            const tenant = card.dataset.tenant;
            STATE.tenantId = tenant;
            localStorage.setItem('tenant_id', tenant);
            overlay.classList.add('hidden');
            app.classList.remove('hidden');
            onTenantSelected(tenant);
        });
    });
}

function onTenantSelected(tenant) {
    $('#current-tenant').textContent = tenant;
    document.title = `I3D · ${tenant.toUpperCase()}`;
    loadSettings();
    renderSessions();
    checkHealth();
    showToast(`已切换到租户: ${tenant}`, 'success');
}

// ========================================
// 导航
// ========================================
function initNavigation() {
    $$('.nav-item').forEach(item => {
        item.addEventListener('click', () => {
            const view = item.dataset.view;
            $$('.nav-item').forEach(n => n.classList.remove('active'));
            item.classList.add('active');
            $$('.view').forEach(v => v.classList.remove('active'));
            $(`#view-${view}`).classList.add('active');
            if (view === 'status') checkHealth();
        });
    });
}

// ========================================
// 聊天功能
// ========================================
function initChat() {
    const input = $('#chat-input');
    const sendBtn = $('#btn-send');
    const newChatBtn = $('#btn-new-chat');
    const clearBtn = $('#btn-clear');
    const streamToggle = $('#btn-stream-toggle');
    const streamIndicator = $('#stream-indicator');
    const fileInput = $('#chat-file-input');

    // 输入框自动高度
    input.addEventListener('input', () => {
        input.style.height = 'auto';
        input.style.height = Math.min(input.scrollHeight, 120) + 'px';
    });

    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    sendBtn.addEventListener('click', sendMessage);

    newChatBtn.addEventListener('click', startNewChat);
    clearBtn.addEventListener('click', () => {
        STATE.messages = [];
        STATE.sessionId = '';
        localStorage.removeItem('session_id');
        renderMessages();
    });

    streamToggle.addEventListener('click', () => {
        STATE.streamEnabled = !STATE.streamEnabled;
        streamIndicator.classList.toggle('active', STATE.streamEnabled);
        localStorage.setItem('stream_enabled', STATE.streamEnabled);
        showToast(STATE.streamEnabled ? '流式响应已开启' : '流式响应已关闭');
    });

    // 快捷按钮
    $$('.quick-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            input.value = btn.dataset.prompt;
            input.style.height = 'auto';
            input.style.height = Math.min(input.scrollHeight, 120) + 'px';
            input.focus();
        });
    });

    // 文件选择
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            STATE.currentFile = file;
            $('#file-name').textContent = `📎 ${file.name}`;
        }
    });

    streamIndicator.classList.toggle('active', STATE.streamEnabled);
}

function startNewChat() {
    STATE.sessionId = '';
    STATE.messages = [];
    localStorage.removeItem('session_id');
    renderMessages();
    $('#chat-input').focus();
}

function addMessage(role, content, extra = {}) {
    const msg = {
        id: uuid(),
        role,
        content,
        timestamp: now(),
        ...extra,
    };
    STATE.messages.push(msg);
    renderMessages();
    return msg;
}

function updateMessage(id, updater) {
    const msg = STATE.messages.find(m => m.id === id);
    if (msg) {
        Object.assign(msg, updater);
        renderMessages();
    }
}

function renderMessages() {
    const container = $('#chat-messages');
    if (STATE.messages.length === 0) {
        container.innerHTML = `
            <div class="welcome-screen" id="welcome-screen">
                <div class="welcome-content">
                    <div class="welcome-mark">I3D</div>
                    <h2 class="welcome-title">CAD 智能检索 Agent</h2>
                    <p class="welcome-desc">
                        基于多 Agent 协作与 RAG 技术，提供 3D 模型的<br>
                        智能检索、分析、推荐与问答服务
                    </p>
                    <div class="welcome-capabilities">
                        <div class="capability"><div class="cap-icon">◈</div><div class="cap-text">混合检索</div></div>
                        <div class="capability"><div class="cap-icon">◉</div><div class="cap-text">智能分析</div></div>
                        <div class="capability"><div class="cap-icon">▣</div><div class="cap-text">流式响应</div></div>
                        <div class="capability"><div class="cap-icon">◆</div><div class="cap-text">多租户隔离</div></div>
                    </div>
                </div>
            </div>
        `;
        return;
    }

    container.innerHTML = STATE.messages.map(msg => renderMessageBubble(msg)).join('');
    container.scrollTop = container.scrollHeight;
}

function renderMessageBubble(msg) {
    const avatar = msg.role === 'user' ? '你' : 'AI';
    const roleClass = msg.role;
    let extraHtml = '';

    if (msg.searchResults && msg.searchResults.length) {
        extraHtml += `<div class="search-results">
            <div class="search-results-title">检索结果</div>
            ${msg.searchResults.map(r => `
                <div class="search-result-item">
                    <span class="result-score">${(r.similarity * 100).toFixed(1)}%</span>
                    <div class="result-info">
                        <div class="result-name">${escapeHtml(r.file_name || r.item_code || '未知')}</div>
                        <div class="result-meta">${escapeHtml(r.file_path || '')}</div>
                    </div>
                </div>
            `).join('')}
        </div>`;
    }

    if (msg.toolCalls && msg.toolCalls.length) {
        extraHtml += msg.toolCalls.map(tc => `
            <div class="tool-call">
                <div class="tool-call-name">⚙ ${escapeHtml(tc.tool_name)}</div>
                <div class="tool-call-args">${escapeHtml(JSON.stringify(tc.arguments, null, 2))}</div>
            </div>
        `).join('');
    }

    const contentHtml = msg.role === 'assistant'
        ? formatMarkdown(msg.content)
        : escapeHtml(msg.content);

    return `
        <div class="message ${roleClass}" data-id="${msg.id}">
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">
                <div class="message-header">
                    <span>${msg.role === 'user' ? '用户' : 'Agent'}</span>
                    <span>${msg.timestamp}</span>
                </div>
                <div class="message-bubble">${contentHtml}${extraHtml}</div>
            </div>
        </div>
    `;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatMarkdown(text) {
    if (!text) return '';
    let html = escapeHtml(text);
    // 代码块
    html = html.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
    // 行内代码
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    // 粗体
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    // 斜体
    html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    // 列表
    html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');
    // 段落
    html = html.split('\n\n').map(p => p.trim() ? `<p>${p}</p>` : '').join('');
    return html;
}

async function sendMessage() {
    const input = $('#chat-input');
    const sendBtn = $('#btn-send');
    const query = input.value.trim();
    if (!query || STATE.isStreaming) return;

    // 如果有文件，先上传
    if (STATE.currentFile) {
        await uploadFile(STATE.currentFile);
        STATE.currentFile = null;
        $('#file-name').textContent = '';
    }

    // 用户消息
    addMessage('user', query);
    input.value = '';
    input.style.height = 'auto';
    sendBtn.disabled = true;

    // 创建 assistant 占位消息
    const assistantMsg = addMessage('assistant', '', { streaming: true });

    if (STATE.streamEnabled) {
        await sendStreamRequest(query, assistantMsg.id);
    } else {
        await sendNonStreamRequest(query, assistantMsg.id);
    }

    sendBtn.disabled = false;
    saveSession();
}

async function sendStreamRequest(query, msgId) {
    STATE.isStreaming = true;
    const ctrl = new AbortController();
    let fullContent = '';

    try {
        const response = await fetch(getApiUrl('/api/chat/stream'), {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({
                query,
                session_id: STATE.sessionId || undefined,
                tenant_context: {
                    tenant_id: STATE.tenantId,
                    user_id: STATE.userId || undefined,
                },
                stream: true,
                max_results: STATE.maxResults,
                enable_rag: STATE.enableRag,
                temperature: STATE.temperature,
            }),
            signal: ctrl.signal,
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || `HTTP ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                const trimmed = line.trim();
                if (!trimmed.startsWith('data: ')) continue;
                const data = trimmed.slice(6);
                if (data === '[DONE]') continue;

                try {
                    const chunk = JSON.parse(data);
                    if (chunk.chunk_type === 'content' && chunk.content) {
                        // 后端返回完整响应（非增量），直接替换
                        fullContent = chunk.content;
                        updateMessage(msgId, { content: fullContent, streaming: true });
                    } else if (chunk.chunk_type === 'tool_call' && chunk.tool_call) {
                        const msg = STATE.messages.find(m => m.id === msgId);
                        if (msg) {
                            msg.toolCalls = msg.toolCalls || [];
                            msg.toolCalls.push(chunk.tool_call);
                            renderMessages();
                        }
                    } else if (chunk.chunk_type === 'metadata' && chunk.metadata) {
                        if (chunk.metadata.session_id) {
                            STATE.sessionId = chunk.metadata.session_id;
                            localStorage.setItem('session_id', STATE.sessionId);
                        }
                        if (chunk.metadata.search_results) {
                            updateMessage(msgId, { searchResults: chunk.metadata.search_results });
                        }
                    } else if (chunk.chunk_type === 'error') {
                        updateMessage(msgId, { content: fullContent + '\n[错误] ' + (chunk.error || '未知错误'), streaming: false });
                    }
                } catch (e) {
                    // 忽略解析错误
                }
            }
        }

        updateMessage(msgId, { content: fullContent || '（无响应内容）', streaming: false });
    } catch (err) {
        if (err.name !== 'AbortError') {
            updateMessage(msgId, { content: `[请求失败] ${err.message}`, streaming: false, error: true });
            showToast(err.message, 'error');
        }
    } finally {
        STATE.isStreaming = false;
    }
}

async function sendNonStreamRequest(query, msgId) {
    try {
        const response = await fetch(getApiUrl('/api/chat/'), {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({
                query,
                session_id: STATE.sessionId || undefined,
                tenant_context: {
                    tenant_id: STATE.tenantId,
                    user_id: STATE.userId || undefined,
                },
                stream: false,
                max_results: STATE.maxResults,
                enable_rag: STATE.enableRag,
                temperature: STATE.temperature,
            }),
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || `HTTP ${response.status}`);
        }

        const data = await response.json();
        const resp = data.response || {};

        if (resp.session_id) {
            STATE.sessionId = resp.session_id;
            localStorage.setItem('session_id', STATE.sessionId);
        }

        updateMessage(msgId, {
            content: resp.response || '（无响应内容）',
            searchResults: resp.search_results,
            toolCalls: resp.tool_calls,
            streaming: false,
        });
    } catch (err) {
        updateMessage(msgId, { content: `[请求失败] ${err.message}`, streaming: false, error: true });
        showToast(err.message, 'error');
    }
}

function saveSession() {
    if (!STATE.sessionId) return;
    const existing = STATE.sessions.find(s => s.id === STATE.sessionId);
    const preview = STATE.messages.find(m => m.role === 'user')?.content?.slice(0, 30) || '新会话';
    if (existing) {
        existing.preview = preview;
        existing.updated = Date.now();
    } else {
        STATE.sessions.unshift({ id: STATE.sessionId, preview, updated: Date.now() });
    }
    localStorage.setItem('sessions', JSON.stringify(STATE.sessions.slice(0, 20)));
    renderSessions();
}

function renderSessions() {
    const list = $('#session-list');
    if (!list) return;
    if (STATE.sessions.length === 0) {
        list.innerHTML = '<div style="color:var(--text-muted);font-size:0.75rem;padding:0.5rem;">暂无历史会话</div>';
        return;
    }
    list.innerHTML = STATE.sessions.map(s => `
        <button class="session-item ${s.id === STATE.sessionId ? 'active' : ''}" data-session="${s.id}">
            <div>${escapeHtml(s.preview)}...</div>
            <span class="session-time">${new Date(s.updated).toLocaleDateString()}</span>
        </button>
    `).join('');

    $$('.session-item').forEach(item => {
        item.addEventListener('click', () => {
            STATE.sessionId = item.dataset.session;
            localStorage.setItem('session_id', STATE.sessionId);
            STATE.messages = []; // 简化处理，实际应从服务端加载
            renderMessages();
            renderSessions();
            showToast('已切换会话');
        });
    });
}

// ========================================
// 文档上传
// ========================================
function initUpload() {
    const dropzone = $('#dropzone');
    const uploadInput = $('#upload-input');
    const btnSelect = $('.btn-select-file');

    btnSelect.addEventListener('click', () => uploadInput.click());
    dropzone.addEventListener('click', () => uploadInput.click());

    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
    });
    dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
        handleFiles(e.dataTransfer.files);
    });

    uploadInput.addEventListener('change', (e) => handleFiles(e.target.files));
}

function handleFiles(files) {
    Array.from(files).forEach(file => {
        if (file.size > 10 * 1024 * 1024) {
            showToast(`文件过大: ${file.name}`, 'error');
            return;
        }
        uploadFile(file);
    });
}

async function uploadFile(file) {
    const id = uuid();
    const resultContainer = $('#upload-results');

    const item = document.createElement('div');
    item.className = 'upload-file-item';
    item.id = `upload-${id}`;
    item.innerHTML = `
        <div class="file-icon">▤</div>
        <div class="file-info">
            <div class="file-name">${escapeHtml(file.name)}</div>
            <div class="file-size">${(file.size / 1024).toFixed(1)} KB</div>
        </div>
        <span class="file-status pending">等待中</span>
    `;
    resultContainer.prepend(item);

    const statusEl = item.querySelector('.file-status');
    statusEl.className = 'file-status uploading';
    statusEl.textContent = '上传中...';

    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(getApiUrl('/api/documents/upload'), {
            method: 'POST',
            headers: {
                'X-Tenant-ID': STATE.tenantId,
                'X-Request-ID': uuid(),
            },
            body: formData,
        });

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            throw new Error(data.detail || '上传失败');
        }

        statusEl.className = 'file-status success';
        statusEl.textContent = `✓ ${data.chunks_processed || 0} 块`;
        showToast(`上传成功: ${file.name}`, 'success');
    } catch (err) {
        statusEl.className = 'file-status error';
        statusEl.textContent = '失败';
        showToast(err.message, 'error');
    }
}

// ========================================
// 健康检查
// ========================================
async function checkHealth() {
    const indicator = $('#status-indicator');
    const grid = $('#status-grid');

    try {
        const response = await fetch(getApiUrl('/health/'), {
            headers: { 'X-Tenant-ID': STATE.tenantId },
        });
        const data = await response.json().catch(() => ({}));

        if (data.status === 'healthy') {
            indicator.className = 'badge-indicator online';
        } else if (data.status === 'degraded') {
            indicator.className = 'badge-indicator';
            indicator.style.background = '#f59e0b';
        } else {
            indicator.className = 'badge-indicator offline';
        }

        if (grid) {
            const services = data.services || {};
            grid.innerHTML = Object.entries(services).map(([name, status]) => `
                <div class="status-card">
                    <div class="status-card-header">
                        <span class="status-card-name">${name}</span>
                        <span class="status-card-indicator ${status}"></span>
                    </div>
                    <div class="status-card-value">${status === 'healthy' ? '正常' : '异常'}</div>
                    <div class="status-card-detail">${new Date(data.timestamp).toLocaleTimeString()}</div>
                </div>
            `).join('') + `
                <div class="status-card">
                    <div class="status-card-header">
                        <span class="status-card-name">version</span>
                    </div>
                    <div class="status-card-value">${data.version || '-'}</div>
                    <div class="status-card-detail">${data.status || 'unknown'}</div>
                </div>
            `;
        }

        $('#api-base-url').textContent = getApiUrl('');
        $('#status-tenant').textContent = STATE.tenantId;
        $('#status-session').textContent = STATE.sessionId || '-';
    } catch (err) {
        indicator.className = 'badge-indicator offline';
        if (grid) {
            grid.innerHTML = `<div class="status-card" style="grid-column:1/-1;text-align:center;color:var(--text-muted);padding:2rem;">
                无法连接到后端服务<br><span style="font-size:0.75rem;">${err.message}</span>
            </div>`;
        }
    }
}

// ========================================
// 设置面板
// ========================================
function initSettings() {
    const panel = $('#settings-panel');
    const btnOpen = $('#btn-settings');
    const btnClose = $('#btn-close-settings');
    const btnSave = $('#btn-save-settings');
    const backdrop = $('.settings-backdrop');

    btnOpen.addEventListener('click', () => {
        loadSettings();
        panel.classList.add('open');
    });

    const close = () => panel.classList.remove('open');
    btnClose.addEventListener('click', close);
    backdrop.addEventListener('click', close);

    btnSave.addEventListener('click', () => {
        const apiUrl = $('#setting-api-url').value.trim();
        const userId = $('#setting-user-id').value.trim();
        const maxResults = parseInt($('#setting-max-results').value) || 10;
        const temperature = parseFloat($('#setting-temperature').value) || 0.7;
        const enableRag = $('#setting-rag').checked;

        CONFIG.API_BASE_URL = apiUrl;
        STATE.userId = userId;
        STATE.maxResults = maxResults;
        STATE.temperature = temperature;
        STATE.enableRag = enableRag;

        localStorage.setItem('api_base_url', apiUrl);
        localStorage.setItem('user_id', userId);
        localStorage.setItem('max_results', maxResults);
        localStorage.setItem('temperature', temperature);
        localStorage.setItem('enable_rag', enableRag);

        close();
        showToast('设置已保存', 'success');
    });

    $('#setting-temperature').addEventListener('input', (e) => {
        $('#temp-value').textContent = e.target.value;
    });
}

function loadSettings() {
    $('#setting-api-url').value = CONFIG.API_BASE_URL;
    $('#setting-user-id').value = STATE.userId;
    $('#setting-max-results').value = STATE.maxResults;
    $('#setting-temperature').value = STATE.temperature;
    $('#temp-value').textContent = STATE.temperature;
    $('#setting-rag').checked = STATE.enableRag;
}

// ========================================
// 初始化
// ========================================
document.addEventListener('DOMContentLoaded', () => {
    initTenantSelector();
    initNavigation();
    initChat();
    initUpload();
    initSettings();

    // 定时健康检查
    setInterval(checkHealth, 30000);
});
