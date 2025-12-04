'use client';

import React, { useState } from 'react';
import {
  Database,
  MessageSquare,
  BarChart3,
  DollarSign,
  TrendingUp,
  Lightbulb,
  Send,
  X,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { useChatbot } from '@/hooks/useChatbot';
import { cn } from '@/lib/utils';

const agents = [
  {
    id: 'data-ingestion',
    name: 'Data Ingestion',
    icon: Database,
    color: 'text-blue-500',
    status: 'active' as const,
  },
  {
    id: 'orchestrator',
    name: 'Orchestrator',
    icon: MessageSquare,
    color: 'text-purple-500',
    status: 'active' as const,
  },
  {
    id: 'analysis',
    name: 'Analysis',
    icon: BarChart3,
    color: 'text-green-500',
    status: 'active' as const,
  },
  {
    id: 'pricing',
    name: 'Pricing',
    icon: DollarSign,
    color: 'text-yellow-500',
    status: 'active' as const,
  },
  {
    id: 'forecasting',
    name: 'Forecasting',
    icon: TrendingUp,
    color: 'text-orange-500',
    status: 'active' as const,
  },
  {
    id: 'recommendation',
    name: 'Recommendation',
    icon: Lightbulb,
    color: 'text-red-500',
    status: 'active' as const,
  },
];

export function AIPanel() {
  const [isExpanded, setIsExpanded] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const { messages, isConnected, isTyping, sendMessage } = useChatbot();

  const handleSend = () => {
    if (inputValue.trim()) {
      sendMessage(inputValue);
      setInputValue('');
    }
  };

  return (
    <aside
      className={cn(
        'bg-card border-l border-border transition-all duration-300',
        'hidden lg:block', // Hide on mobile/tablet
        isExpanded ? 'w-96' : 'w-80'
      )}
    >
      <div className="h-full flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-[#455A64]" style={{ background: 'linear-gradient(135deg, #3E4C59 0%, #6B8AA8 100%)', marginTop: '1px' }}>
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-lg font-normal text-white">Agentic AI Assistant</h2>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-white/80 hover:text-white hover:bg-white/10"
            >
              {isExpanded ? <X size={16} /> : <MessageSquare size={16} />}
            </Button>
          </div>
          <div className="flex items-center gap-2">
            <div
              className={cn(
                'w-2 h-2 rounded-full',
                isConnected ? 'bg-green-400' : 'bg-red-400'
              )}
            />
            <span className="text-xs text-white/70">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>

        {/* AI Agents Grid */}
        <div className="p-4 border-b border-border">
          <h3 className="text-sm font-medium mb-3">Active Agents</h3>
          <div className="grid grid-cols-2 gap-2">
            {agents.map((agent) => {
              const Icon = agent.icon;
              return (
                <div
                  key={agent.id}
                  className="p-3 rounded-lg hover:opacity-90 transition-all cursor-pointer"
                  style={{
                    background: 'linear-gradient(135deg, #3E4C59 0%, #6B8AA8 100%)',
                    boxShadow: '4px 4px 8px rgba(0, 0, 0, 0.15), -2px -2px 6px rgba(255, 255, 255, 0.1)',
                  }}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <Icon size={16} className="text-white" />
                    <Badge
                      variant={agent.status === 'active' ? 'success' : 'secondary'}
                      className="text-[10px] px-1 py-0"
                    >
                      {agent.status}
                    </Badge>
                  </div>
                  <p className="text-xs font-medium text-white">{agent.name}</p>
                </div>
              );
            })}
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
                <p className="text-sm">{message.content}</p>
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
                <div className="w-2 h-2 rounded-full bg-muted-foreground animate-bounce delay-100" />
                <div className="w-2 h-2 rounded-full bg-muted-foreground animate-bounce delay-200" />
              </div>
            </div>
          )}
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
            >
              <Send size={16} />
            </Button>
          </div>
        </div>
      </div>
    </aside>
  );
}

