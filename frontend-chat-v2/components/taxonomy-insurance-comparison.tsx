"use client"

import { useState } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Check, X, Shield, Heart, Luggage, Plane, Sparkles } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { TripDetailsCard } from "@/components/trip-details-card"
import { PaymentProcessor } from "@/components/payment-processor"

interface TaxonomyInsuranceComparisonProps {
  tripDetails?: any
  eligibleProducts?: string[]  // ["Product A", "Product B"]
  recommendedProduct?: string   // "Product B"
  quotes?: any[]  // Real pricing from Ancileo API
  taxonomyComparison?: any  // Full taxonomy comparison data
  riskLevel?: string
  currentMessages?: any[]  // Current chat messages to preserve during payment
  onPaymentComplete?: (policyNumber: string, policyName: string, amount: number) => void
}

// Map Product A/B/C to display names and details
const PRODUCT_DETAILS: Record<string, {
  displayName: string
  subtitle: string
  benefits: { medical?: number, cancellation?: number, baggage?: number }
}> = {
  "Product A": {
    displayName: "Scootsurance",
    subtitle: "Scootsurance",
    benefits: { medical: 70000, cancellation: 1000, baggage: 2000 }
  },
  "Product B": {
    displayName: "TravelEasy Standard",
    subtitle: "TravelEasy",
    benefits: { medical: 500000, cancellation: 5000, baggage: 3000 }
  },
  "Product C": {
    displayName: "TravelEasy Pre-Existing",
    subtitle: "TravelEasy Pre-Ex",
    benefits: { medical: 300000, cancellation: 3000, baggage: 2000 }
  }
}

const commonFeatures = ["24/7 Emergency Assistance", "Travel Delay Coverage", "COVID-19 Coverage", "Worldwide Coverage"]

export function TaxonomyInsuranceComparison({
  tripDetails,
  eligibleProducts = [],
  recommendedProduct,
  quotes = [],
  taxonomyComparison,
  riskLevel,
  currentMessages = [],
  onPaymentComplete
}: TaxonomyInsuranceComparisonProps) {
  const [selectedPolicyForPurchase, setSelectedPolicyForPurchase] = useState<string | null>(null)

  // Get pricing for a product from quotes array
  const getProductPrice = (productKey: string): number | null => {
    const quote = quotes?.find(q => q.product_key === productKey && q.is_real_pricing)
    return quote?.premium || null
  }

  // Get product data from taxonomy comparison
  const getProductData = (productKey: string) => {
    if (!taxonomyComparison || !taxonomyComparison.products) return null
    return taxonomyComparison.products[productKey]
  }

  // Get benefit coverage from taxonomy - FIXED
  const getBenefitCoverage = (productKey: string, benefitName: string): string => {
    const productData = getProductData(productKey)
    if (!productData) {
      // Fallback to hardcoded values
      const details = PRODUCT_DETAILS[productKey]
      if (!details) return "N/A"
      
      if (benefitName === "medical" && details.benefits.medical) {
        return `$${(details.benefits.medical / 1000)}K`
      }
      if (benefitName === "cancellation" && details.benefits.cancellation) {
        return `$${details.benefits.cancellation.toLocaleString()}`
      }
      if (benefitName === "baggage" && details.benefits.baggage) {
        return `$${details.benefits.baggage.toLocaleString()}`
      }
      return "N/A"
    }

    // Get from taxonomy Layer 2 benefits
    const benefits = productData.layer_2_benefits || []
    const benefit = benefits.find((b: any) => 
      b.benefit_name?.toLowerCase().includes(benefitName.toLowerCase())
    )
    
    if (!benefit) return "N/A"
    
    const coverage = benefit.parameters?.coverage_limit
    if (coverage) {
      if (coverage >= 1000) {
        return `$${(coverage / 1000)}K`
      }
      return `$${coverage.toLocaleString()}`
    }
    
    return "Included"
  }

  // Products to display
  const productsToDisplay = eligibleProducts.length > 0 
    ? eligibleProducts 
    : ["Product A", "Product B", "Product C"]

  return (
    <div className="w-full mx-auto space-y-8 mt-6">
      {/* Trip Details Card */}
      {tripDetails && (
        <TripDetailsCard tripDetails={tripDetails} riskLevel={riskLevel} />
      )}

      {/* All Plans Include */}
      <Card className="p-12 bg-accent/10 border-2 border-accent/20 rounded-3xl shadow-md">
        <h3 className="text-2xl font-bold text-foreground mb-6 flex items-center gap-3">
          <Shield className="w-8 h-8 text-accent" />
          All Plans Include
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {commonFeatures.map((feature) => (
            <div key={feature} className="flex items-center gap-3 text-lg text-foreground">
              <Check className="w-6 h-6 text-accent shrink-0" />
              <span>{feature}</span>
            </div>
          ))}
        </div>
      </Card>

      {/* Policy Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
        {productsToDisplay.map((productKey) => {
          const details = PRODUCT_DETAILS[productKey]
          if (!details) return null

          const isRecommended = productKey === recommendedProduct
          const pricing = getProductPrice(productKey)
          const isEligible = eligibleProducts.includes(productKey)

          return (
            <Card
              key={productKey}
              className={`relative overflow-hidden rounded-3xl shadow-lg min-h-[700px] flex flex-col ${
                isRecommended 
                  ? "border-2 border-primary ring-4 ring-primary/20" 
                  : isEligible 
                    ? "border-2 border-accent" 
                    : "border-2 opacity-60"
              }`}
            >
              {isRecommended && (
                <div className="absolute top-0 right-0">
                  <Badge className="rounded-none rounded-bl-2xl bg-primary text-primary-foreground px-6 py-3 text-base font-semibold flex items-center gap-2">
                    <Sparkles className="w-4 h-4" />
                    Recommended
                  </Badge>
                </div>
              )}
              
              {!isEligible && (
                <div className="absolute top-0 left-0 right-0 bg-red-500/10 border-b-2 border-red-500/20 px-6 py-2 text-center">
                  <span className="text-sm font-semibold text-red-600">Not Eligible</span>
                </div>
              )}

              <div className="p-12 space-y-8 flex-1 flex flex-col">
                <div>
                  <h3 className="text-3xl font-bold text-foreground">{details.displayName}</h3>
                  <div className="mt-2">
                    <Badge variant="outline" className="text-sm">
                      {details.subtitle}
                    </Badge>
                  </div>
                  
                  {/* Real Pricing from Ancileo API */}
                  {pricing && isEligible && (
                    <div className="mt-4">
                      <span className="text-5xl font-bold text-foreground">${pricing.toFixed(2)}</span>
                      <span className="text-lg text-muted-foreground ml-2">/trip</span>
                      <div className="mt-2">
                        <Badge variant="secondary" className="text-xs">
                          <Plane className="w-3 h-3 mr-1" />
                          Real-time pricing
                        </Badge>
                      </div>
                    </div>
                  )}
                  
                  {/* No pricing available */}
                  {!pricing && isEligible && (
                    <div className="mt-4 text-sm text-muted-foreground">
                      Quote available
                    </div>
                  )}
                </div>

                <div className="space-y-6 pt-6 border-t-2 border-border flex-1">
                  {/* Medical Coverage */}
                  <div className="flex items-start gap-4">
                    <Heart className="w-7 h-7 text-accent shrink-0 mt-1" />
                    <div className="flex-1">
                      <p className="text-base text-muted-foreground font-medium">Medical Coverage</p>
                      <p className="text-xl font-semibold text-foreground mt-2">
                        {getBenefitCoverage(productKey, "medical")}
                      </p>
                    </div>
                  </div>

                  {/* Trip Cancellation */}
                  <div className="flex items-start gap-4">
                    <X className="w-7 h-7 text-accent shrink-0 mt-1" />
                    <div className="flex-1">
                      <p className="text-base text-muted-foreground font-medium">Trip Cancellation</p>
                      <p className="text-xl font-semibold text-foreground mt-2">
                        {getBenefitCoverage(productKey, "cancellation")}
                      </p>
                    </div>
                  </div>

                  {/* Baggage Loss */}
                  <div className="flex items-start gap-4">
                    <Luggage className="w-7 h-7 text-accent shrink-0 mt-1" />
                    <div className="flex-1">
                      <p className="text-base text-muted-foreground font-medium">Baggage Loss</p>
                      <p className="text-xl font-semibold text-foreground mt-2">
                        {getBenefitCoverage(productKey, "baggage")}
                      </p>
                    </div>
                  </div>

                  {/* Emergency Evacuation */}
                  <div className="flex items-center justify-between py-3">
                    <span className="text-base text-muted-foreground font-medium">Emergency Evacuation</span>
                    {isEligible ? (
                      <Check className="w-7 h-7 text-accent" />
                    ) : (
                      <X className="w-7 h-7 text-muted-foreground" />
                    )}
                  </div>

                  {/* Adventure Sports */}
                  <div className="flex items-center justify-between py-3">
                    <span className="text-base text-muted-foreground font-medium">Adventure Sports</span>
                    {isEligible ? (
                      <Check className="w-7 h-7 text-accent" />
                    ) : (
                      <X className="w-7 h-7 text-muted-foreground" />
                    )}
                  </div>
                </div>

                <Button
                  className="w-full h-14 text-lg font-semibold rounded-2xl mt-auto"
                  variant={isRecommended ? "default" : isEligible ? "outline" : "ghost"}
                  disabled={!isEligible}
                  onClick={() => isEligible && setSelectedPolicyForPurchase(productKey)}
                >
                  {isEligible ? `Buy ${details.displayName}` : "Not Eligible"}
                </Button>
              </div>
            </Card>
          )
        })}
      </div>

      {/* Payment Processor - Shows when a policy is selected */}
      {selectedPolicyForPurchase && (() => {
        const selectedDetails = PRODUCT_DETAILS[selectedPolicyForPurchase]
        const selectedPrice = getProductPrice(selectedPolicyForPurchase)
        const selectedQuote = quotes?.find(q => q.product_key === selectedPolicyForPurchase)
        
        return (
          <div className="mt-8">
            <PaymentProcessor 
              quoteId={selectedQuote?.quote_id || "demo_quote"}
              policyId={selectedPolicyForPurchase}
              policyName={selectedDetails?.displayName || "Travel Insurance"}
              premium={selectedPrice || 0}
              tripDetails={tripDetails}
              currentMessages={currentMessages}
              onPaymentComplete={(policyNumber) => {
                if (onPaymentComplete) {
                  onPaymentComplete(policyNumber, selectedDetails?.displayName || "Travel Insurance", selectedPrice || 0)
                }
              }}
            />
          </div>
        )
      })()}
    </div>
  )
}
