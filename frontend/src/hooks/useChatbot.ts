import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  agent?: string;
}

// Generate a unique session ID for this browser session
const generateSessionId = () => {
  const stored = typeof window !== 'undefined' ? sessionStorage.getItem('chatbot_thread_id') : null;
  if (stored) return stored;
  
  const newId = `chat_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  if (typeof window !== 'undefined') {
    sessionStorage.setItem('chatbot_thread_id', newId);
  }
  return newId;
};

export function useChatbot() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [threadId] = useState(generateSessionId);
  const [userId] = useState('web_user'); // Could be replaced with actual user ID from auth

  // Check backend connectivity and load chat history on mount
  useEffect(() => {
    const checkConnection = async () => {
      try {
        // Test connection to backend
        const response = await axios.get(`${API_URL}/health`, { timeout: 5000 });
        if (response.status === 200) {
          setIsConnected(true);
          // Load chat history for this thread
          await loadChatHistory();
        }
      } catch (error) {
        console.error('Backend connection failed:', error);
        setIsConnected(false);
      }
    };

    checkConnection();
    
    // Check connection every 30 seconds
    const interval = setInterval(checkConnection, 30000);
    
    return () => clearInterval(interval);
  }, [threadId]);

  const loadChatHistory = useCallback(async () => {
    try {
      const response = await axios.get(`${API_URL}/api/v1/chatbot/history`, {
        params: {
          user_id: userId,
          thread_id: threadId,
          limit: 50
        }
      });

      if (response.data && Array.isArray(response.data)) {
        // Convert backend format to frontend format
        const loadedMessages: Message[] = response.data
          .reverse() // Backend returns newest first, we want oldest first
          .map((msg: any) => ({
            id: msg._id || Date.now().toString(),
            role: msg.role,
            content: msg.content,
            timestamp: new Date(msg.timestamp),
            agent: msg.agent
          }));
        
        setMessages(loadedMessages);
      }
    } catch (error) {
      console.error('Failed to load chat history:', error);
      // Don't show error to user, just start with empty history
    }
  }, [threadId, userId]);

  const sendMessage = useCallback(
    async (content: string) => {
      if (!isConnected || !content.trim()) return;

      // Add user message to UI immediately
      const userMessage: Message = {
        id: `user_${Date.now()}`,
        role: 'user',
        content,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setIsTyping(true);

      try {
        // Use streaming endpoint for better UX
        const response = await fetch(`${API_URL}/api/v1/chatbot/chat/stream`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            message: content,
            context: {
              thread_id: threadId,
              user_id: userId
            }
          }),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Read the stream
        const reader = response.body?.getReader();
        const decoder = new TextDecoder();
        
        if (!reader) {
          throw new Error('No response body');
        }

        let assistantMessageId = `assistant_${Date.now()}`;
        let fullContent = '';

        while (true) {
          const { done, value } = await reader.read();
          
          if (done) break;

          // Decode the chunk
          const chunk = decoder.decode(value);
          
          // Parse SSE format (data: {...}\n\n)
          const lines = chunk.split('\n');
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.substring(6));
                
                if (data.error) {
                  throw new Error(data.error);
                }
                
                if (data.token && !data.done) {
                  // Accumulate the token
                  fullContent += data.token;
                  
                  // Update the message in real-time
                  setMessages((prev) => {
                    const existingIndex = prev.findIndex(m => m.id === assistantMessageId);
                    
                    if (existingIndex >= 0) {
                      // Update existing message
                      const updated = [...prev];
                      updated[existingIndex] = {
                        ...updated[existingIndex],
                        content: fullContent
                      };
                      return updated;
                    } else {
                      // Create new message
                      return [...prev, {
                        id: assistantMessageId,
                        role: 'assistant',
                        content: fullContent,
                        timestamp: new Date(),
                      }];
                    }
                  });
                }
                
                if (data.done) {
                  // Stream complete
                  setIsTyping(false);
                  break;
                }
              } catch (e) {
                console.error('Error parsing SSE data:', e);
              }
            }
          }
        }

      } catch (error) {
        console.error('Failed to send message:', error);
        
        // Show error message to user
        const errorMessage: Message = {
          id: `error_${Date.now()}`,
          role: 'assistant',
          content: 'Sorry, I encountered an error processing your message. Please try again.',
          timestamp: new Date(),
        };
        
        setMessages((prev) => [...prev, errorMessage]);
      } finally {
        setIsTyping(false);
      }
    },
    [isConnected, threadId, userId]
  );

  const clearMessages = useCallback(() => {
    setMessages([]);
    // Clear session storage to start a new conversation
    if (typeof window !== 'undefined') {
      sessionStorage.removeItem('chatbot_thread_id');
    }
  }, []);

  const refreshHistory = useCallback(async () => {
    await loadChatHistory();
  }, [loadChatHistory]);

  return {
    messages,
    isConnected,
    isTyping,
    sendMessage,
    clearMessages,
    refreshHistory,
    threadId,
  };
}

