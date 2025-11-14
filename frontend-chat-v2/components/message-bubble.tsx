"use client"

import type React from "react"

import { cn } from "@/lib/utils"
import { Bot, User } from "lucide-react"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  component?: React.ReactNode
}

interface MessageBubbleProps {
  message: Message
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user"

  return (
    <div className={cn("flex gap-4", isUser && "flex-row-reverse")}>
      <div
        className={cn(
          "flex items-center justify-center w-12 h-12 rounded-full shrink-0 shadow-md",
          isUser ? "bg-primary" : "bg-accent",
        )}
      >
        {isUser ? (
          <User className="w-6 h-6 text-primary-foreground" />
        ) : (
          <Bot className="w-6 h-6 text-accent-foreground" />
        )}
      </div>
      <div
        className={cn(
          "flex flex-col gap-3",
          isUser ? "max-w-[85%] md:max-w-[75%] items-end" : message.component ? "w-full" : "max-w-[85%] md:max-w-[95%]",
        )}
      >
        <div
          className={cn(
            "rounded-3xl px-6 py-4 shadow-sm",
            isUser ? "bg-primary text-primary-foreground" : "bg-card border-2 border-border text-card-foreground",
          )}
        >
          <p className="text-base leading-relaxed">{message.content}</p>
        </div>
        {message.component && <div className="w-full">{message.component}</div>}
      </div>
    </div>
  )
}
