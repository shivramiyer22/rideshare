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
import { TabType } from './Sidebar';

interface AIPanelProps {
  activeTab: TabType;
}

export function AIPanel({ activeTab }: AIPanelProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [inputValue, setInputValue] = useState('');
  
  // Map tab names to readable page names
  const pageNames: Record<TabType, string> = {
    overview: 'Overview Dashboard',
    pricing: 'Pricing Analysis',
    forecasting: 'Demand Forecasting',
    market: 'Market Signals',
    elasticity: 'Price Elasticity',
    upload: 'Data Upload'
  };
  
  const { messages, isConnected, isTyping, sendMessage, clearMessages, threadId } = useChatbot({
    currentPage: pageNames[activeTab],
    pageData: { tab: activeTab }
  });
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
    clearMessages();
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
            <div className="text-center text-sm text-muted-foreground py-8 px-4">
              <MessageSquare size={32} className="mx-auto mb-4 opacity-50" />
              <div className="space-y-3 text-left max-w-md mx-auto">
                <p className="font-semibold text-base">👋 Welcome! I'm your AI Assistant</p>
                <p className="text-xs">I can help you with:</p>
                <ul className="text-xs space-y-1.5 pl-4">
                  <li>📊 Business objectives & progress tracking</li>
                  <li>💰 Revenue, pricing & profitability analysis</li>
                  <li>📈 Demand forecasting & trends</li>
                  <li>🏆 HWCO vs Lyft competitor comparisons</li>
                  <li>📍 Location, customer & segment insights</li>
                  <li>🎯 Strategic recommendations</li>
                </ul>
                <p className="text-xs pt-2 italic">Ask me anything about your rideshare business!</p>
              </div>
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
                <div 
                  className="text-sm whitespace-pre-wrap break-words prose prose-sm max-w-none dark:prose-invert"
                  style={{ 
                    wordBreak: 'break-word',
                    overflowWrap: 'break-word'
                  }}
                >
                  {message.content}
                </div>
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

