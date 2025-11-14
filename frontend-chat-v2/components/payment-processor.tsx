"use client"

import type React from "react"

import { useState, useEffect, useRef } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { CreditCard, Lock, Check, Loader2, Shield } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { apiClient } from "@/lib/api-client"

interface PaymentProcessorProps {
  quoteId?: string
  policyId?: string
  policyName?: string
  premium?: number
  tripDetails?: any
  currentMessages?: any[]  // Current chat messages to preserve
  onPaymentComplete?: (policyNumber: string) => void
}

export function PaymentProcessor({ 
  quoteId = "quote_demo", 
  policyId = "Product_B", 
  policyName = "Travel Insurance",
  premium = 89.00,
  tripDetails,
  currentMessages = [],
  onPaymentComplete
}: PaymentProcessorProps) {
  const [isProcessing, setIsProcessing] = useState(false)
  const [isWaitingForPayment, setIsWaitingForPayment] = useState(false)
  const [paymentIntentId, setPaymentIntentId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null)

  const handlePayment = async () => {
    setIsProcessing(true)
    setError(null)

    try {
      // Call purchase API to create Stripe checkout
      const response = await fetch(`${apiClient.getBaseUrl()}/purchase`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          quote_id: quoteId,
          policy_id: policyId,
          policy_name: policyName,
          premium: premium,
          user_id: apiClient.getSessionId(),
          trip_details: tripDetails
        })
      })

      const data = await response.json()

      if (data.success && data.checkout_url) {
        setPaymentIntentId(data.payment_intent_id)
        
        // Open Stripe Checkout in new window
        const popup = window.open(data.checkout_url, 'stripe_checkout', 'width=600,height=700')
        
        if (!popup) {
          setError("Please allow popups for payment processing")
          return
        }
        
        // Start polling for payment completion
        setIsWaitingForPayment(true)
        startPaymentPolling(data.payment_intent_id, popup)
      } else {
        setError(data.error || "Failed to create checkout session")
      }
    } catch (err) {
      console.error("Payment error:", err)
      setError(err instanceof Error ? err.message : "Failed to process payment")
    } finally {
      setIsProcessing(false)
    }
  }

  const startPaymentPolling = (paymentId: string, popup: Window) => {
    let attempts = 0
    const maxAttempts = 120 // Poll for 2 minutes (120 * 1 second)
    
    pollIntervalRef.current = setInterval(async () => {
      attempts++
      
      // Check if popup is closed
      if (popup.closed) {
        console.log("Popup closed, checking payment status...")
      }
      
      // Check payment status
      try {
        const response = await fetch(`${apiClient.getBaseUrl()}/payment/status/${paymentId}`)
        const result = await response.json()
        
        if (result.success && result.status === 'completed') {
          // Payment completed!
          console.log("Payment completed!", result)
          
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current)
          }
          
          setIsWaitingForPayment(false)
          
          // Trigger policy issuance
          const completeResponse = await fetch(`${apiClient.getBaseUrl()}/payment/complete/${paymentId}`, {
            method: 'POST',
          })
          const completeResult = await completeResponse.json()
          
          if (completeResult.success && completeResult.policy_number && onPaymentComplete) {
            onPaymentComplete(completeResult.policy_number)
          }
        }
      } catch (error) {
        console.error("Error checking payment status:", error)
      }
      
      // Stop after max attempts or if popup closed for too long
      if (attempts >= maxAttempts || (popup.closed && attempts > 5)) {
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current)
        }
        setIsWaitingForPayment(false)
      }
    }, 1000) // Poll every second
  }

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current)
      }
    }
  }, [])

  // Show waiting for payment status
  if (isWaitingForPayment) {
    return (
      <Card className="p-6 mt-4 bg-card border-border">
        <div className="text-center space-y-4">
          <Loader2 className="w-12 h-12 animate-spin text-primary mx-auto" />
          <div>
            <h3 className="text-lg font-semibold text-foreground">Waiting for payment...</h3>
            <p className="text-sm text-muted-foreground mt-2">
              Complete your payment in the Stripe window
            </p>
          </div>
          <Button 
            variant="outline" 
            onClick={() => {
              setIsWaitingForPayment(false)
              if (pollIntervalRef.current) {
                clearInterval(pollIntervalRef.current)
              }
            }}
          >
            Cancel
          </Button>
        </div>
      </Card>
    )
  }

  return (
    <Card className="p-6 mt-4 bg-card border-border">
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-primary/20">
              <CreditCard className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-foreground">Secure Payment</h3>
              <p className="text-xs text-muted-foreground">Powered by Stripe</p>
            </div>
          </div>
          <Badge variant="outline" className="bg-accent/10 text-accent border-accent/20">
            <Lock className="w-3 h-3 mr-1" />
            Encrypted
          </Badge>
        </div>

        <div className="p-4 rounded-lg bg-accent/10 border border-accent/20">
          <div className="flex items-center gap-2 mb-2">
            <Shield className="w-4 h-4 text-accent" />
            <p className="text-xs font-medium text-accent">{policyName}</p>
          </div>
          <div className="flex justify-between items-baseline">
            <span className="text-sm text-muted-foreground">Total Premium</span>
            <span className="text-2xl font-bold text-foreground">SGD ${premium.toFixed(2)}</span>
          </div>
        </div>

        {error && (
          <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm">
            {error}
          </div>
        )}

        <div className="space-y-3">
          <Button onClick={handlePayment} className="w-full" size="lg" disabled={isProcessing}>
            {isProcessing ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Creating checkout...
              </>
            ) : (
              <>
                <CreditCard className="w-4 h-4 mr-2" />
                Pay with Stripe
              </>
            )}
          </Button>

          <p className="text-xs text-center text-muted-foreground">
            You'll be redirected to Stripe's secure checkout page
          </p>
          
          <div className="flex items-center justify-center gap-2 pt-2">
            <Lock className="w-3 h-3 text-muted-foreground" />
            <span className="text-xs text-muted-foreground">
              PCI-DSS compliant • 256-bit encryption
            </span>
          </div>
        </div>
      </div>
    </Card>
  )
}
