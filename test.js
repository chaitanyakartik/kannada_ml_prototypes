class InformaticsBotClient {
  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
    this.chatHistory = [];
    this.metadata = {
      language: 'EN',
      user_id: null,
      district: null
    };
  }

  setMetadata(metadata) {
    this.metadata = { ...this.metadata, ...metadata };
  }

  async sendMessage(message) {
    try {
      const response = await fetch(`${this.baseUrl}/infomatics_bot/generate_response`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: message,
          chat_history: this.chatHistory,
          metadata: this.metadata
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Handle error responses
      if (data.error) {
        console.error('Bot error:', data.error);
        return null;
      }

      // Update chat history for next call
      if (data.chat_history) {
        this.chatHistory = data.chat_history;
      }

      return {
        answer: data.answer,
        source: data.source_reference
      };
    } catch (error) {
      console.error('Request failed:', error);
      return null;
    }
  }

  clearHistory() {
    this.chatHistory = [];
  }
}

// Usage Example
const bot = new InformaticsBotClient();

// Set user metadata
bot.setMetadata({
  language: 'EN',
  user_id: 'user_12345',
  district: 'Bangalore Urban',
  regions: {
    state: { name: 'Karnataka' },
    district: { name: 'Bangalore Urban' }
  }
});

// First question
const response1 = await bot.sendMessage('What documents are needed for a driving license?');
console.log(response1.answer);
console.log('Source:', response1.source);

// Follow-up question (maintains context)
const response2 = await bot.sendMessage('What is the fee for this?');
console.log(response2.answer);

// Clear conversation and start fresh
bot.clearHistory();