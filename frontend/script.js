// Healthcare AI Frontend JavaScript
class HealthcareAI {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8000';
        this.currentMode = 'chat';
        this.conversationId = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.checkBackendConnection();
        this.autoResizeTextarea();
    }

    bindEvents() {
        // Mode switching
        document.getElementById('chatToggle').addEventListener('click', () => this.switchMode('chat'));
        document.getElementById('searchToggle').addEventListener('click', () => this.switchMode('search'));

        // Chat functionality
        document.getElementById('sendButton').addEventListener('click', () => this.sendChatMessage());
        document.getElementById('chatInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendChatMessage();
            }
        });

        // Search functionality
        document.getElementById('searchButton').addEventListener('click', () => this.performSearch());
        document.getElementById('searchInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.performSearch();
            }
        });

        // Auto-resize textarea
        document.getElementById('chatInput').addEventListener('input', () => this.autoResizeTextarea());
    }

    async checkBackendConnection() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/health`);
            const data = await response.json();
            
            if (data.status === 'healthy') {
                this.updateConnectionStatus(true);
                this.showToast('Backend connected successfully!', 'success');
            } else {
                this.updateConnectionStatus(false);
                this.showToast('Backend connection issue', 'error');
            }
        } catch (error) {
            console.error('Backend connection failed:', error);
            this.updateConnectionStatus(false);
            this.showToast('Cannot connect to backend server', 'error');
        }
    }

    updateConnectionStatus(connected) {
        const statusElement = document.querySelector('.footer-status span:last-child');
        const statusDot = document.querySelector('.status-dot');
        
        if (connected) {
            statusElement.textContent = 'Backend Connected';
            statusDot.style.background = '#27ae60';
        } else {
            statusElement.textContent = 'Backend Disconnected';
            statusDot.style.background = '#e74c3c';
        }
    }

    switchMode(mode) {
        this.currentMode = mode;
        const chatContainer = document.getElementById('chatContainer');
        const searchContainer = document.getElementById('searchContainer');
        const chatToggle = document.getElementById('chatToggle');
        const searchToggle = document.getElementById('searchToggle');

        if (mode === 'chat') {
            chatContainer.style.display = 'flex';
            searchContainer.style.display = 'none';
            chatToggle.classList.add('btn-primary');
            chatToggle.classList.remove('btn-outline');
            searchToggle.classList.add('btn-outline');
            searchToggle.classList.remove('btn-primary');
        } else {
            chatContainer.style.display = 'none';
            searchContainer.style.display = 'block';
            searchToggle.classList.add('btn-primary');
            searchToggle.classList.remove('btn-outline');
            chatToggle.classList.add('btn-outline');
            chatToggle.classList.remove('btn-primary');
        }
    }

    async sendChatMessage() {
        const input = document.getElementById('chatInput');
        const message = input.value.trim();
        
        if (!message) return;

        // Add user message to chat
        this.addMessage(message, 'user');
        input.value = '';
        this.autoResizeTextarea();

        // Show loading
        this.showLoading();

        try {
            const response = await fetch(`${this.apiBaseUrl}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    conversation_id: this.conversationId
                })
            });

            const data = await response.json();
            
            if (response.ok) {
                // Add AI response to chat
                this.addMessage(data.response, 'ai');
                this.conversationId = data.conversation_id;
                
                // Show citations if any
                if (data.citations && data.citations.length > 0) {
                    this.addCitations(data.citations);
                }
            } else {
                throw new Error(data.detail || 'Failed to get response');
            }
        } catch (error) {
            console.error('Chat error:', error);
            this.addMessage('Sorry, I encountered an error. Please try again.', 'ai');
            this.showToast('Failed to send message', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async performSearch() {
        const input = document.getElementById('searchInput');
        const query = input.value.trim();
        
        if (!query) return;

        const yearFilter = document.getElementById('yearFilter').value;
        const categoryFilter = document.getElementById('categoryFilter').value;

        this.showLoading();

        try {
            const requestBody = {
                query: query
            };

            if (yearFilter || categoryFilter) {
                requestBody.filters = {};
                if (yearFilter) requestBody.filters.year = yearFilter;
                if (categoryFilter) requestBody.filters.category = categoryFilter;
            }

            const response = await fetch(`${this.apiBaseUrl}/search`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody)
            });

            const data = await response.json();
            
            if (response.ok) {
                this.displaySearchResults(data.results, query);
            } else {
                throw new Error(data.detail || 'Search failed');
            }
        } catch (error) {
            console.error('Search error:', error);
            this.showToast('Search failed. Please try again.', 'error');
            this.displaySearchResults([], query);
        } finally {
            this.hideLoading();
        }
    }

    addMessage(content, sender) {
        const messagesContainer = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = sender === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';

        const messageText = document.createElement('div');
        messageText.className = 'message-text';
        messageText.textContent = content;

        const messageTime = document.createElement('div');
        messageTime.className = 'message-time';
        messageTime.textContent = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});

        messageContent.appendChild(messageText);
        messageContent.appendChild(messageTime);
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);

        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    addCitations(citations) {
        const messagesContainer = document.getElementById('chatMessages');
        const citationsDiv = document.createElement('div');
        citationsDiv.className = 'message ai-message';
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = '<i class="fas fa-book"></i>';

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';

        const messageText = document.createElement('div');
        messageText.className = 'message-text';
        
        if (citations && citations.length > 0) {
            messageText.innerHTML = `
                <strong>📚 Sources & Citations:</strong><br>
                ${citations.map(citation => {
                    const source = citation.source || 'Unknown';
                    const title = citation.title || citation.id;
                    const doi = citation.doi && citation.doi !== 'No DOI' && citation.doi !== 'Local Database';
                    const pmid = citation.pmid;
                    
                    let links = '';
                    if (doi) {
                        links += `<a href="https://doi.org/${citation.doi}" target="_blank" style="color: #007bff; font-size: 0.9em;">DOI</a> `;
                    }
                    if (pmid) {
                        links += `<a href="https://pubmed.ncbi.nlm.nih.gov/${pmid}/" target="_blank" style="color: #007bff; font-size: 0.9em;">PMID</a> `;
                    }
                    
                    return `
                        <div style="margin: 5px 0; padding: 5px; border-left: 3px solid #3498db; background: #f8f9fa;">
                            <strong>${title}</strong>
                            ${source ? `<span style="color: #6c757d; font-size: 0.8em;"> (${source})</span>` : ''}<br>
                            ${links}
                        </div>
                    `;
                }).join('')}
            `;
        } else {
            messageText.innerHTML = '<em>No citations available for this response.</em>';
        }

        messageContent.appendChild(messageText);
        citationsDiv.appendChild(avatar);
        citationsDiv.appendChild(messageContent);

        messagesContainer.appendChild(citationsDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    displaySearchResults(results, query) {
        const resultsContainer = document.getElementById('searchResults');
        
        if (!results || results.length === 0) {
            resultsContainer.innerHTML = `
                <div class="no-results">
                    <i class="fas fa-search"></i>
                    <p>No results found for "${query}"</p>
                    <small>Try different keywords or check your spelling</small>
                </div>
            `;
            return;
        }

        // Count real vs local results
        const realResults = results.filter(r => r.source === 'PubMed');
        const localResults = results.filter(r => r.source === 'Local');

        resultsContainer.innerHTML = `
            <div style="margin-bottom: 1rem; color: #6c757d;">
                <i class="fas fa-info-circle"></i>
                Found ${results.length} result${results.length !== 1 ? 's' : ''} for "${query}"
                ${realResults.length > 0 ? `<span style="color: #28a745; margin-left: 10px;"><i class="fas fa-check-circle"></i> ${realResults.length} from PubMed</span>` : ''}
                ${localResults.length > 0 ? `<span style="color: #17a2b8; margin-left: 10px;"><i class="fas fa-database"></i> ${localResults.length} from local database</span>` : ''}
            </div>
        `;

        results.forEach(result => {
            const resultDiv = document.createElement('div');
            resultDiv.className = 'search-result-item';
            
            // Add source indicator
            const sourceBadge = result.source === 'PubMed' 
                ? '<span style="background: #28a745; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.7em; margin-left: 5px;">PubMed</span>'
                : '<span style="background: #17a2b8; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.7em; margin-left: 5px;">Local</span>';
            
            // Format DOI link properly
            const doiLink = result.doi && result.doi !== 'No DOI' && result.doi !== 'Local Database'
                ? `<a href="https://doi.org/${result.doi}" class="result-doi" target="_blank" style="color: #007bff;">
                    DOI: ${result.doi}
                   </a>`
                : result.doi;
            
            // Add PMID link for PubMed results
            const pmidLink = result.pmid 
                ? `<a href="${result.url}" target="_blank" style="color: #007bff; margin-left: 10px;">
                    PMID: ${result.pmid}
                   </a>`
                : '';
            
            resultDiv.innerHTML = `
                <div class="result-title">
                    ${result.title}
                    ${sourceBadge}
                </div>
                <div class="result-authors">${result.authors ? result.authors.join(', ') : 'Unknown Authors'}</div>
                <div class="result-abstract">${result.abstract}</div>
                <div class="result-meta">
                    <span>${result.year || 'Unknown Year'}</span>
                    ${doiLink}
                    ${pmidLink}
                </div>
            `;
            resultsContainer.appendChild(resultDiv);
        });
    }

    async viewCitation(citationId) {
        this.showLoading();
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/citations/${citationId}`);
            const data = await response.json();
            
            if (response.ok) {
                this.showCitationModal(data);
            } else {
                throw new Error(data.detail || 'Failed to load citation');
            }
        } catch (error) {
            console.error('Citation error:', error);
            this.showToast('Failed to load citation details', 'error');
        } finally {
            this.hideLoading();
        }
    }

    showCitationModal(citation) {
        // Create modal HTML (simplified version)
        const modal = document.createElement('div');
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 2000;
        `;
        
        modal.innerHTML = `
            <div style="
                background: white;
                padding: 2rem;
                border-radius: 16px;
                max-width: 600px;
                max-height: 80vh;
                overflow-y: auto;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
            ">
                <h3 style="margin-bottom: 1rem; color: #2c3e50;">${citation.title}</h3>
                <p><strong>Authors:</strong> ${citation.authors}</p>
                <p><strong>Journal:</strong> ${citation.journal}</p>
                <p><strong>Year:</strong> ${citation.year}</p>
                <p><strong>DOI:</strong> <a href="${citation.url}" target="_blank">${citation.doi}</a></p>
                <p><strong>Verified:</strong> ${citation.verified ? '✅ Yes' : '❌ No'}</p>
                <button onclick="this.closest('div[style*=\"position: fixed\"]').remove()" 
                        style="
                            margin-top: 1rem;
                            padding: 0.5rem 1rem;
                            background: #3498db;
                            color: white;
                            border: none;
                            border-radius: 8px;
                            cursor: pointer;
                        ">
                    Close
                </button>
            </div>
        `;
        
        document.body.appendChild(modal);
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }

    autoResizeTextarea() {
        const textarea = document.getElementById('chatInput');
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }

    showLoading() {
        document.getElementById('loadingOverlay').classList.add('show');
    }

    hideLoading() {
        document.getElementById('loadingOverlay').classList.remove('show');
    }

    showToast(message, type = 'success') {
        const toast = document.getElementById('toast');
        const icon = toast.querySelector('.toast-icon');
        const messageElement = toast.querySelector('.toast-message');
        
        // Set icon based on type
        if (type === 'success') {
            icon.className = 'toast-icon fas fa-check-circle';
            toast.className = 'toast success';
        } else {
            icon.className = 'toast-icon fas fa-exclamation-circle';
            toast.className = 'toast error';
        }
        
        messageElement.textContent = message;
        toast.classList.add('show');
        
        // Auto hide after 3 seconds
        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }
}

// Initialize the application
const app = new HealthcareAI();

// Make app globally available for citation viewing
window.app = app;
