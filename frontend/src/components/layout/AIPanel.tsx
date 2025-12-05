'use client';

import React, { useState, useEffect, useRef } from 'react';
import {
  MessageSquare,
  Send,
  X,
  GripVertical,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { useChatbot } from '@/hooks/useChatbot';
import { cn } from '@/lib/utils';

export function AIPanel() {
  const [isExpanded, setIsExpanded] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const { messages, isConnected, isTyping, sendMessage, clearMessages, threadId } = useChatbot();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Resize functionality
  const [width, setWidth] = useState(320); // Default 320px (w-80)
  const [isResizing, setIsResizing] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);
  
  // Load saved width from localStorage
  useEffect(() => {
    const savedWidth = localStorage.getItem('aiPanelWidth');
    if (savedWidth) {
      setWidth(parseInt(savedWidth));
    }
  }, []);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  // Handle resize
  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;
      
      const newWidth = window.innerWidth - e.clientX;
      // Constrain width between 280px (min) and 800px (max)
      const constrainedWidth = Math.min(Math.max(newWidth, 280), 800);
      setWidth(constrainedWidth);
    };

    const handleMouseUp = () => {
      if (isResizing) {
        setIsResizing(false);
        // Save width to localStorage
        localStorage.setItem('aiPanelWidth', width.toString());
      }
    };

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isResizing, width]);

  const handleSend = () => {
    if (inputValue.trim()) {
      sendMessage(inputValue);
      setInputValue('');
    }
  };

  const handleClearChat = () => {
    if (confirm('Are you sure you want to clear the chat history?')) {
      clearMessages();
    }
  };

  return (
    <aside
      ref={panelRef}
      className={cn(
        'bg-card border-l border-border transition-none relative',
        'hidden lg:block', // Hide on mobile/tablet
      )}
      style={{ width: `${width}px` }}
    >
      {/* Resize Handle */}
      <div
        className={cn(
          'absolute left-0 top-0 bottom-0 w-1 hover:w-1.5',
          'bg-transparent hover:bg-primary/50 cursor-col-resize',
          'transition-all duration-150 group z-10',
          isResizing && 'bg-primary w-1.5'
        )}
        onMouseDown={handleMouseDown}
      >
        <div className={cn(
          'absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2',
          'opacity-0 group-hover:opacity-100 transition-opacity',
          'bg-primary text-primary-foreground rounded p-1',
          isResizing && 'opacity-100'
        )}>
          <GripVertical size={16} />
        </div>
      </div>
      
      <div className="h-full flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-[#455A64]" style={{ background: 'linear-gradient(135deg, #3E4C59 0%, #6B8AA8 100%)', marginTop: '1px' }}>
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-lg font-normal text-white truncate">Agentic AI Assistant</h2>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-white/80 hover:text-white hover:bg-white/10 flex-shrink-0"
            >
              {isExpanded ? <X size={16} /> : <MessageSquare size={16} />}
            </Button>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <div
              className={cn(
                'w-2 h-2 rounded-full flex-shrink-0',
                isConnected ? 'bg-green-400' : 'bg-red-400'
              )}
            />
            <span className="text-xs text-white/70">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
            {messages.length > 0 && (
              <button
                onClick={handleClearChat}
                className="ml-auto text-xs text-white/70 hover:text-white hover:underline"
              >
                Clear Chat
              </button>
            )}
          </div>
        </div>

        {/* Chat Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="text-center text-sm text-muted-foreground py-8">
              <MessageSquare size={32} className="mx-auto mb-2 opacity-50" />
              <p>Ask me anything about pricing,</p>
              <p>forecasting, or analytics!</p>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={cn(
                  'p-3 rounded-lg',
                  message.role === 'user'
                    ? 'bg-primary text-primary-foreground ml-4'
                    : 'bg-muted mr-4'
                )}
              >
                <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                {message.agent && (
                  <p className="text-xs opacity-70 mt-1">via {message.agent}</p>
                )}
              </div>
            ))
          )}
          {isTyping && (
            <div className="p-3 rounded-lg bg-muted mr-4">
              <div className="flex gap-1">
                <div className="w-2 h-2 rounded-full bg-muted-foreground animate-bounce" />
                <div className="w-2 h-2 rounded-full bg-muted-foreground animate-bounce" style={{ animationDelay: '0.1s' }} />
                <div className="w-2 h-2 rounded-full bg-muted-foreground animate-bounce" style={{ animationDelay: '0.2s' }} />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="p-4 border-t border-border">
          <div className="flex gap-2">
            <Input
              placeholder="Type a message..."
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSend()}
              disabled={!isConnected}
            />
            <Button
              size="icon"
              onClick={handleSend}
              disabled={!isConnected || !inputValue.trim()}
              className="flex-shrink-0"
            >
              <Send size={16} />
            </Button>
          </div>
        </div>
      </div>
    </aside>
  );
}

