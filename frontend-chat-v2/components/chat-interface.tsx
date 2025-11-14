"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Send, Loader2 } from "lucide-react"
import { MessageBubble } from "@/components/message-bubble"
import { InsuranceComparison } from "@/components/insurance-comparison"
import { TaxonomyInsuranceComparison } from "@/components/taxonomy-insurance-comparison"
import { GmailIntegration } from "@/components/gmail-integration"
import { PaymentProcessor } from "@/components/payment-processor"
import { WelcomeScreen } from "@/components/welcome-screen"
import { apiClient } from "@/lib/api-client"
import { sessionManager } from "@/lib/session"
import type { Message, TripDetails } from "@/lib/types"

interface ChatInterfaceProps {
  messages: Message[]
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>
}

export function ChatInterface({ messages, setMessages }: ChatInterfaceProps) {
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [tripDetails, setTripDetails] = useState<TripDetails | undefined>()
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Auto-save messages to session whenever they change
  useEffect(() => {
    if (messages.length > 0) {
      sessionManager.saveMessages(messages)
    }
  }, [messages])

  const handlePaymentComplete = (policyNumber: string, policyName: string, amount: number) => {
    // Add success message to chat
    const successMessage: Message = {
      id: Date.now().toString(),
      role: "assistant",
      content: `✅ Payment successful! Your travel insurance is now active.\n\n**Policy Number:** ${policyNumber}\n**Policy:** ${policyName}\n**Premium:** SGD $${amount.toFixed(2)}\n\nYour policy documents will be sent to your email shortly. Have a wonderful trip! 🌏`,
    }
    setMessages((prev) => [...prev, successMessage])
  }

  const handleTripDetailsExtracted = async (tripDetails: TripDetails, message: string) => {
    console.log("Trip details extracted from Gmail:", tripDetails)
    
    // Store trip details
    setTripDetails(tripDetails)
    
    // Add user's message requesting insurance
    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: "Find insurance for this trip",
    }
    setMessages((prev) => [...prev, userMessage])
    
    // Send to backend to get policy recommendations
    setIsLoading(true)
    
    try {
      // Build conversation history with the insurance request
      const conversationHistory = [
        ...messages.map(m => ({ role: m.role, content: m.content })),
        { role: "user", content: message }
      ]

      const response = await apiClient.sendMessage(
        message,
        conversationHistory
      )
      
      console.log("Backend response:", response)
      console.log("Policy recommendations:", response.policy_recommendations)
      console.log("Eligible products:", response.eligible_products)
      console.log("Quotes:", response.quotes)
      
      // Check if we got policy recommendations in the response
      const hasRecommendations = response.policy_recommendations && response.policy_recommendations.length > 0
      const hasTaxonomyData = response.eligible_products || response.taxonomy_comparison
      const hasQuotes = response.quotes && response.quotes.length > 0
      
      let component = undefined
      
      // Show taxonomy comparison if available (preferred)
      if (hasTaxonomyData) {
        console.log("Showing TaxonomyInsuranceComparison with", response.eligible_products?.length, "products")
        console.log("Recommended product:", response.taxonomy_comparison?.recommendation)
        component = (
          <TaxonomyInsuranceComparison 
            eligibleProducts={response.eligible_products || []}
            recommendedProduct={response.taxonomy_comparison?.recommendation}
            taxonomyComparison={response.taxonomy_comparison}
            tripDetails={tripDetails}
            quotes={response.quotes}
            riskLevel={response.real_time_intelligence?.historical_claims?.destination_profile?.risk_level}
            currentMessages={[...messages, userMessage]}
            onPaymentComplete={handlePaymentComplete}
          />
        )
      }
      // Fallback to regular insurance comparison
      else if (hasRecommendations) {
        console.log("Showing InsuranceComparison with", response.policy_recommendations?.length || 0, "recommendations")
        component = (
          <InsuranceComparison 
            recommendations={response.policy_recommendations} 
            tripDetails={tripDetails}
            quotes={response.quotes}
            currentMessages={[...messages, userMessage]}
            onPaymentComplete={handlePaymentComplete}
          />
        )
      } else {
        console.warn("No insurance data found in response")
      }
      
      // Add AI response with recommendations
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response.answer || "Let me find the best insurance options for your trip...",
        component: component,
      }
      
      setMessages((prev) => [...prev, aiMessage])
    } catch (error) {
      console.error("Error getting policy recommendations:", error)
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "I apologize, but I encountered an error finding insurance options. Please try again or enter your details manually.",
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleActionSelect = (action: "gmail" | "upload" | "manual") => {
    setIsLoading(true)

    if (action === "gmail") {
      setMessages([
        {
          id: Date.now().toString(),
          role: "assistant",
          content: "Great! Let's connect to your Gmail to fetch your trip details automatically.",
          component: <GmailIntegration onTripDetailsExtracted={handleTripDetailsExtracted} />,
        },
      ])
    } else if (action === "upload") {
      setMessages([
        {
          id: Date.now().toString(),
          role: "assistant",
          content:
            "Perfect! Please upload your booking confirmation, and I'll extract all the necessary trip details for you.",
        },
      ])
    } else if (action === "manual") {
      setMessages([
        {
          id: Date.now().toString(),
          role: "assistant",
          content:
            "No problem! I'll help you enter your trip details. Let's start with your destination. Where are you traveling to?",
        },
      ])
    }

    setTimeout(() => setIsLoading(false), 500)
  }

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
    }

    const newMessages = [...messages, userMessage]
    setMessages(newMessages)
    const userInput = input
    setInput("")
    setIsLoading(true)

    try {
      // Convert messages to OpenAI format (role + content only)
      const conversationHistory = newMessages.map((msg) => ({
        role: msg.role,
        content: msg.content,
      }))

      console.log("Sending message to backend:", {
        input: userInput,
        historyLength: conversationHistory.length,
      })

      // Send message to backend using OpenAI-compatible endpoint
      const response = await apiClient.sendMessage(userInput, conversationHistory)

      console.log("Received response:", response)

      if (!response.success) {
        throw new Error(response.error || "Failed to get response")
      }

      // Parse metadata from answer if present
      let metadata: any = {}
      let cleanAnswer = response.answer || ""
      
      if (cleanAnswer.includes("[METADATA]")) {
        const metadataStart = cleanAnswer.indexOf("[METADATA]")
        const metadataEnd = cleanAnswer.indexOf("[/METADATA]")
        if (metadataStart !== -1 && metadataEnd !== -1) {
          try {
            const metadataStr = cleanAnswer.substring(metadataStart + 10, metadataEnd)
            metadata = JSON.parse(metadataStr)
            cleanAnswer = cleanAnswer.substring(0, metadataStart) + cleanAnswer.substring(metadataEnd + 11)
            cleanAnswer = cleanAnswer.trim()
            console.log("Parsed metadata:", metadata)
          } catch (e) {
            console.error("Failed to parse metadata:", e)
          }
        }
      }

      // Merge metadata into response
      const enrichedResponse = {
        ...response,
        ...metadata,
        answer: cleanAnswer
      }

      // Determine if we should show special components based on content
      let component: React.ReactNode = undefined
      const lowerInput = userInput.toLowerCase()
      const lowerAnswer = cleanAnswer.toLowerCase()

      // Check if response has taxonomy or policy data - ALWAYS show comparison
      const hasTaxonomyData = enrichedResponse.eligible_products && enrichedResponse.eligible_products.length > 0
      const hasPolicyData = (response.policy_recommendations && response.policy_recommendations.length > 0) ||
                           lowerAnswer.includes("recommended coverage") ||
                           lowerAnswer.includes("product a") || 
                           lowerAnswer.includes("product b") ||
                           lowerAnswer.includes("product c")
      
      // Show taxonomy-based insurance comparison if we have taxonomy data
      if (hasTaxonomyData) {
        console.log("Using TaxonomyInsuranceComparison with data:", {
          eligibleProducts: enrichedResponse.eligible_products,
          recommendedProduct: enrichedResponse.taxonomy_comparison?.recommendation,
          quotesCount: enrichedResponse.quotes?.length
        })
        component = (
          <TaxonomyInsuranceComparison
            tripDetails={enrichedResponse.trip_details}
            eligibleProducts={enrichedResponse.eligible_products}
            recommendedProduct={enrichedResponse.taxonomy_comparison?.recommendation}
            quotes={enrichedResponse.quotes}
            taxonomyComparison={enrichedResponse.taxonomy_comparison}
            riskLevel={enrichedResponse.real_time_intelligence?.historical_claims?.destination_profile?.risk_level}
            currentMessages={[...messages, userMessage]}
            onPaymentComplete={handlePaymentComplete}
          />
        )
      }
      // Show insurance comparison if we have policy recommendations
      else if (hasPolicyData) {
        console.log("Using InsuranceComparison (fallback)")
        component = <InsuranceComparison recommendations={enrichedResponse.policy_recommendations} tripDetails={enrichedResponse.trip_details} currentMessages={[...messages, userMessage]} onPaymentComplete={handlePaymentComplete} />
      }
      // Show Gmail integration if user mentions email/gmail
      else if (
        lowerInput.includes("email") ||
        lowerInput.includes("gmail") ||
        lowerInput.includes("booking")
      ) {
        component = <GmailIntegration onTripDetailsExtracted={handleTripDetailsExtracted} />
      }
      // Show payment if user wants to buy
      else if (
        lowerInput.includes("buy") ||
        lowerInput.includes("purchase") ||
        lowerInput.includes("payment")
      ) {
        component = <PaymentProcessor currentMessages={messages} />
      }

      // Add AI response
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: cleanAnswer || "I'm here to help! How can I assist you?",
        component,
      }

      setMessages((prev) => [...prev, aiMessage])
    } catch (error) {
      console.error("Error sending message:", error)
      
      // Show error message
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content:
          "I'm sorry, I'm having trouble connecting to the server. Please make sure the backend is running and try again.",
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const showWelcome = messages.length === 0

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      {showWelcome ? (
        <div className="flex-1 overflow-y-auto">
          <WelcomeScreen onActionSelect={handleActionSelect} />
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto px-4 py-6 md:px-8">
          <div className="max-w-[1400px] mx-auto space-y-6">
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            {isLoading && (
              <div className="flex items-center gap-2 text-muted-foreground">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span className="text-sm">AI is thinking...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>
      )}

      <div className="border-t border-border bg-background/80 backdrop-blur-sm">
        <div className="max-w-[1400px] mx-auto px-4 py-4 md:px-8 md:py-6">
          <form
            onSubmit={(e) => {
              e.preventDefault()
              handleSend()
            }}
            className="flex items-center gap-3"
          >
            <div className="flex-1 relative">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask anything..."
                className="flex-1 text-base md:text-lg py-6 md:py-7 px-6 rounded-3xl border-2 focus-visible:ring-2 focus-visible:ring-primary/20 shadow-lg"
                disabled={isLoading}
              />
            </div>
            <Button
              type="submit"
              size="icon"
              className="h-12 w-12 md:h-14 md:w-14 rounded-full shadow-lg hover:scale-105 transition-transform"
              disabled={isLoading || !input.trim()}
            >
              <Send className="w-5 h-5 md:w-6 md:h-6" />
            </Button>
          </form>
        </div>
      </div>
    </div>
  )
}
