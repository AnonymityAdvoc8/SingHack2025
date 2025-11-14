"use client"

import { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Mail, Check, Loader2, Calendar, MapPin, Users, AlertCircle, Sparkles } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { apiClient } from "@/lib/api-client"
import type { GmailBooking, TripDetails } from "@/lib/types"

interface GmailIntegrationProps {
  onTripDetailsExtracted?: (tripDetails: TripDetails, message: string) => void
}

export function GmailIntegration({ onTripDetailsExtracted }: GmailIntegrationProps) {
  const [isConnecting, setIsConnecting] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [extractedData, setExtractedData] = useState<GmailBooking[]>([])
  const [error, setError] = useState<string | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)

  // Check if already connected on mount
  useEffect(() => {
    checkGmailStatus()
  }, [])

  const checkGmailStatus = async () => {
    try {
      const status = await apiClient.checkGmailStatus()
      if (status.authorized && status.bookings && status.bookings.length > 0) {
        setIsConnected(true)
        setExtractedData(status.bookings)
      }
    } catch (error) {
      console.error("Error checking Gmail status:", error)
    }
  }

  const handleConnect = async () => {
    setIsConnecting(true)
    setError(null)

    try {
      // Get authorization URL from backend
      const authData = await apiClient.getGmailAuthUrl()
      
      if (!authData || !authData.authorization_url) {
        throw new Error("Failed to get authorization URL")
      }

      // Open OAuth popup
      const width = 600
      const height = 700
      const left = window.screen.width / 2 - width / 2
      const top = window.screen.height / 2 - height / 2
      
      const popup = window.open(
        authData.authorization_url,
        "Gmail Authorization",
        `width=${width},height=${height},left=${left},top=${top}`
      )

      // Poll for completion
      const pollInterval = setInterval(async () => {
        try {
          // Check if popup is closed
          if (popup && popup.closed) {
            clearInterval(pollInterval)
            
            // Check if authorization was successful
            const status = await apiClient.checkGmailStatus()
            
            if (status.authorized) {
              setIsConnected(true)
              setIsConnecting(false)
              
              // Wait a bit for bookings to be scanned
              setTimeout(async () => {
                const updatedStatus = await apiClient.checkGmailStatus()
                if (updatedStatus.bookings && updatedStatus.bookings.length > 0) {
                  setExtractedData(updatedStatus.bookings)
                }
              }, 2000)
            } else {
              setIsConnecting(false)
              setError("Authorization was cancelled or failed")
            }
          }
        } catch (error) {
          console.error("Error polling for authorization:", error)
        }
      }, 1000)

      // Timeout after 5 minutes
      setTimeout(() => {
        clearInterval(pollInterval)
        if (isConnecting) {
          setIsConnecting(false)
          setError("Authorization timed out")
        }
      }, 300000)
    } catch (error) {
      console.error("Error connecting to Gmail:", error)
      setIsConnecting(false)
      setError(error instanceof Error ? error.message : "Failed to connect to Gmail")
    }
  }

  const handleUseDetails = () => {
    if (!extractedData || extractedData.length === 0) return
    
    setIsProcessing(true)

    // Extract trip details from the first booking (or combine multiple)
    const primaryBooking = extractedData[0]
    const data = primaryBooking.extracted_data

    // Get dates from either flight or hotel booking
    const departureDate = data.departure_date || data.departure || data.check_in
    const returnDate = data.return_date || data.return || data.check_out

    // Get destination (prefer from flight if available)
    let destination = data.destination || "Japan"
    const flightBooking = extractedData.find(b => b.booking_type === "flight")
    if (flightBooking?.extracted_data.route) {
      const route = flightBooking.extracted_data.route
      if (route.includes("NRT") || route.includes("HND")) {
        destination = "Japan"
      } else if (route.includes("HKG")) {
        destination = "Hong Kong"
      } else if (route.includes("BKK")) {
        destination = "Thailand"
      }
    }

    // Build trip details object
    const tripDetails: TripDetails = {
      destination: destination,
      departure_date: departureDate,
      return_date: returnDate,
      num_travelers: data.travelers || 1,
    }

    // Calculate trip duration
    let duration = ""
    let days = 0
    if (departureDate && returnDate) {
      const start = new Date(departureDate)
      const end = new Date(returnDate)
      days = Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24))
      duration = days > 1 ? `${days} days` : `${days} day`
    }

    // Create a natural language message that clearly requests insurance recommendations
    const message = `I'm traveling to ${destination} from ${departureDate} to ${returnDate} (${duration}). I need travel insurance for ${data.travelers || 1} traveler${data.travelers !== 1 ? 's' : ''}. Please recommend suitable insurance policies.`

    // Call the callback to notify parent component
    if (onTripDetailsExtracted) {
      onTripDetailsExtracted(tripDetails, message)
    }

    setTimeout(() => setIsProcessing(false), 500)
  }

  return (
    <Card className="p-6 mt-4 bg-card border-border">
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-accent/20">
              <Mail className="w-5 h-5 text-accent" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-foreground">Gmail Integration</h3>
              <p className="text-xs text-muted-foreground">Extract trip details from your emails</p>
            </div>
          </div>
          {isConnected && (
            <Badge variant="outline" className="bg-accent/10 text-accent border-accent/20">
              <Check className="w-3 h-3 mr-1" />
              Connected
            </Badge>
          )}
        </div>

        {!isConnected && !isConnecting && (
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground">
              Connect your Gmail to automatically extract flight bookings, hotel reservations, and travel dates.
            </p>
            {error && (
              <div className="flex items-center gap-2 p-3 rounded-lg bg-destructive/10 text-destructive text-sm">
                <AlertCircle className="w-4 h-4" />
                <span>{error}</span>
              </div>
            )}
            <Button onClick={handleConnect} className="w-full">
              <Mail className="w-4 h-4 mr-2" />
              Connect Gmail Account
            </Button>
          </div>
        )}

        {isConnecting && (
          <div className="flex items-center justify-center py-8">
            <div className="text-center space-y-3">
              <Loader2 className="w-8 h-8 animate-spin text-primary mx-auto" />
              <p className="text-sm text-muted-foreground">Connecting to Gmail...</p>
            </div>
          </div>
        )}

        {isConnected && !extractedData && (
          <div className="flex items-center justify-center py-8">
            <div className="text-center space-y-3">
              <Loader2 className="w-8 h-8 animate-spin text-primary mx-auto" />
              <p className="text-sm text-muted-foreground">Analyzing your emails...</p>
            </div>
          </div>
        )}

        {extractedData && extractedData.length > 0 && (
          <div className="space-y-4">
            {(() => {
              // Check if all bookings are for the same trip (same dates)
              const firstDates = extractedData[0].extracted_data.departure_date || extractedData[0].extracted_data.departure
              const allSameTrip = extractedData.every(b => 
                (b.extracted_data.departure_date || b.extracted_data.departure) === firstDates
              )
              
              if (allSameTrip && extractedData.length > 1) {
                // Single trip with multiple components
                const firstBooking = extractedData[0]
                const data = firstBooking.extracted_data
                const departureDate = data.departure_date || data.departure
                const returnDate = data.return_date || data.return
                
                // Calculate destination from flight
                let destination = "Tokyo"
                const flightBooking = extractedData.find(b => b.booking_type === "flight")
                if (flightBooking?.extracted_data.route) {
                  const route = flightBooking.extracted_data.route
                  if (route.includes("NRT") || route.includes("HND")) destination = "Tokyo"
                  else if (route.includes("HKG")) destination = "Hong Kong"
                }
                
                // Calculate duration
                let duration = ""
                if (departureDate && returnDate) {
                  const start = new Date(departureDate)
                  const end = new Date(returnDate)
                  const days = Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24))
                  duration = `${days} days`
                }
                
                return (
                  <>
                    <div className="p-4 rounded-lg bg-gradient-to-br from-accent/20 to-accent/10 border border-accent/30">
                      <div className="flex items-start gap-3 mb-3">
                        <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-accent/30">
                          <Check className="w-5 h-5 text-accent" />
                        </div>
                        <div className="flex-1">
                          <h4 className="text-sm font-semibold text-foreground mb-1">Trip to {destination}</h4>
                          <p className="text-xs text-muted-foreground">
                            {departureDate} to {returnDate} {duration && `• ${duration}`}
                          </p>
                        </div>
                      </div>
                      
                      <div className="space-y-2 pl-13">
                        {extractedData.map((booking) => {
                          const bookingData = booking.extracted_data
                          if (booking.booking_type === "flight") {
                            return (
                              <div key={booking.email_id} className="flex items-center gap-2 text-sm">
                                <span className="text-lg">✈️</span>
                                <span className="text-foreground">
                                  {bookingData.airline || "Flight"}: {bookingData.route}
                                </span>
                              </div>
                            )
                          } else if (booking.booking_type === "hotel") {
                            return (
                              <div key={booking.email_id} className="flex items-center gap-2 text-sm">
                                <span className="text-lg">🏨</span>
                                <span className="text-foreground">
                                  {bookingData.hotel} • {bookingData.nights} nights
                                </span>
                              </div>
                            )
                          }
                          return null
                        })}
                      </div>
                    </div>
                    <p className="text-xs text-center text-muted-foreground">
                      We found {extractedData.length} bookings for this trip
                    </p>
                  </>
                )
              } else {
                // Multiple separate trips or single booking
                return (
                  <>
                    <p className="text-xs font-medium text-accent">Found {extractedData.length} booking(s)</p>
                    {extractedData.map((booking, index) => (
                      <div key={booking.email_id} className="p-4 rounded-lg bg-accent/10 border border-accent/20">
                        <div className="mb-2">
                          <Badge variant="outline" className="text-xs">
                            {booking.booking_type}
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground mb-3">{booking.subject}</p>
                        <div className="space-y-3">
                          {booking.extracted_data.destination && (
                            <div className="flex items-center gap-3">
                              <MapPin className="w-4 h-4 text-muted-foreground" />
                              <div>
                                <p className="text-xs text-muted-foreground">Destination</p>
                                <p className="text-sm font-medium text-foreground">
                                  {booking.extracted_data.destination}
                                </p>
                              </div>
                            </div>
                          )}
                          {booking.extracted_data.departure_date && (
                            <div className="flex items-center gap-3">
                              <Calendar className="w-4 h-4 text-muted-foreground" />
                              <div>
                                <p className="text-xs text-muted-foreground">Travel Dates</p>
                                <p className="text-sm font-medium text-foreground">
                                  {booking.extracted_data.departure_date}
                                  {booking.extracted_data.return_date && ` - ${booking.extracted_data.return_date}`}
                                </p>
                              </div>
                            </div>
                          )}
                          {booking.extracted_data.travelers && (
                            <div className="flex items-center gap-3">
                              <Users className="w-4 h-4 text-muted-foreground" />
                              <div>
                                <p className="text-xs text-muted-foreground">Travelers</p>
                                <p className="text-sm font-medium text-foreground">
                                  {booking.extracted_data.travelers} people
                                </p>
                              </div>
                            </div>
                          )}
                          {booking.extracted_data.confirmation_code && (
                            <div className="flex items-center gap-3">
                              <Check className="w-4 h-4 text-muted-foreground" />
                              <div>
                                <p className="text-xs text-muted-foreground">Confirmation</p>
                                <p className="text-sm font-medium text-foreground">
                                  {booking.extracted_data.confirmation_code}
                                </p>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </>
                )
              }
            })()}
            <Button 
              onClick={handleUseDetails} 
              disabled={isProcessing}
              className="w-full"
            >
              {isProcessing ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Finding insurance options...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 mr-2" />
                  Find Insurance for This Trip
                </>
              )}
            </Button>
          </div>
        )}
        
        {isConnected && extractedData.length === 0 && !isConnecting && (
          <div className="text-center py-4">
            <p className="text-sm text-muted-foreground">
              No travel bookings found in your email. Try entering your trip details manually.
            </p>
          </div>
        )}
      </div>
    </Card>
  )
}
