'use client';

import { useState, useRef, useEffect } from 'react';
import ChatMessage from '@/components/ChatMessage';
import ChatInput from '@/components/ChatInput';
import PolicyCard from '@/components/PolicyCard';
import SuggestedActions from '@/components/SuggestedActions';
import AgentActivity from '@/components/AgentActivity';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  emotion?: string;
  confidence?: number;
  suggested_actions?: Array<{type: string; label: string; icon: string; data?: string}>;
  agent_activities?: Array<{agent: string; status: string; ref?: string}>;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: "👋 Hi! I'm TravelMate, your friendly travel insurance advisor. Where are you planning to travel?"
    }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => `session_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleActionClick = async (action: any) => {
    // Handle suggested action clicks
    if (action.type === 'authorize_gmail') {
      // Open Gmail OAuth in popup or new tab
      if (action.data) {
        // action.data contains the OAuth URL
        window.open(action.data, 'gmail_auth', 'width=600,height=700');
        // Note: After OAuth, user will be redirected and we'll handle the callback
        sendMessage('I\'ve opened Gmail authorization. Please grant access and I\'ll scan your emails for bookings.');
      } else {
        // Fallback to mock scanning
        sendMessage('📧 Scan my email');
      }
    } else if (action.type === 'scan_gmail') {
      sendMessage('📧 Scan my email');
    } else if (action.type === 'enter_booking_ref') {
      sendMessage('✈️ Let me enter my booking reference');
    } else if (action.type === 'lookup_booking' && action.data) {
      sendMessage(`Look up booking ${action.data}`);
    } else if (action.type === 'manual_entry') {
      sendMessage('💬 I\'ll tell you about my trip');
    }
  };

  const sendMessage = async (content: string) => {
    // Add user message
    const userMessage: Message = { role: 'user', content };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Call backend API
      const response = await fetch('http://localhost:8080/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: 'travelmate',
          messages: [...messages, userMessage].map(m => ({
            role: m.role,
            content: m.content
          })),
          session_id: sessionId,  // CRITICAL: Send session ID for persistence
          stream: false
        })
      });

      const data = await response.json();
      const assistantMessage = data.choices[0].message;
      const assistantContent = assistantMessage.content;
      
      // Extract metadata from content if present (backend sends it in special format)
      let suggested_actions: Array<{type: string; label: string; icon: string; data?: string}> | undefined;
      let agent_activities: Array<{agent: string; status: string; ref?: string}> | undefined;
      
      try {
        // Check if response contains metadata (our backend can send this)
        const metadataPattern = /\[METADATA\]([\s\S]*?)\[\/METADATA\]/;
        const metadataMatch = assistantContent.match(metadataPattern);
        if (metadataMatch) {
          const metadata = JSON.parse(metadataMatch[1]);
          suggested_actions = metadata.suggested_actions;
          agent_activities = metadata.agent_activities;
        }
      } catch (e) {
        // No metadata, that's fine
      }

      // Remove metadata from content
      const cleanContent = assistantContent.replace(/\[METADATA\][\s\S]*?\[\/METADATA\]/, '').trim();

      // Add assistant message
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: cleanContent,
        suggested_actions,
        agent_activities
      }]);
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: "Sorry, I'm having trouble connecting. Please try again!"
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-gradient-to-br from-blue-50 to-purple-50 dark:from-gray-900 dark:to-gray-800">
      {/* Main Chat Container */}
      <div className="flex-1 flex flex-col max-w-4xl mx-auto w-full">
        {/* Header */}
        <div className="bg-white dark:bg-gray-800 shadow-sm border-b dark:border-gray-700 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center text-white font-bold text-xl">
              T
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900 dark:text-white">TravelMate AI</h1>
              <p className="text-sm text-gray-500 dark:text-gray-400">Your friendly insurance advisor</p>
            </div>
          </div>
        </div>

        {/* Messages Container */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message, index) => (
            <div key={index}>
              <ChatMessage message={message} />
              {message.agent_activities && message.agent_activities.length > 0 && (
                <AgentActivity activities={message.agent_activities} />
              )}
              {message.suggested_actions && message.suggested_actions.length > 0 && (
                <SuggestedActions 
                  actions={message.suggested_actions} 
                  onActionClick={handleActionClick}
                />
              )}
            </div>
          ))}
          
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 dark:bg-gray-700 rounded-2xl px-4 py-3 max-w-[70%]">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                  <span className="ml-2 text-gray-600 dark:text-gray-300 text-sm">TravelMate is thinking...</span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input Container */}
        <div className="bg-white dark:bg-gray-800 border-t dark:border-gray-700 p-4">
          <ChatInput onSend={sendMessage} disabled={isLoading} />
        </div>
      </div>
    </div>
  );
}
