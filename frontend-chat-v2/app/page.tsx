"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { ChatInterface } from "@/components/chat-interface"
import { Header } from "@/components/header"
import { sessionManager } from "@/lib/session"
import type { Message } from "@/lib/types"

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([])

  useEffect(() => {
    // Load conversation from session on mount
    const savedMessages = sessionManager.loadMessages()
    if (savedMessages.length > 0) {
      setMessages(savedMessages)
    }
  }, [])

  return (
    <div className="flex flex-col h-screen bg-background">
      <Header />
      <ChatInterface messages={messages} setMessages={setMessages} />
    </div>
  )
}
