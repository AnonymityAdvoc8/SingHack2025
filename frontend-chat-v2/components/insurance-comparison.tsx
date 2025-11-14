"use client"

import { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Check, X, Shield, Heart, Luggage, Loader2, Plane } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { TripDetailsCard } from "@/components/trip-details-card"
import { PaymentProcessor } from "@/components/payment-processor"
import { apiClient } from "@/lib/api-client"
import type { PolicyRecommendation, TripDetails } from "@/lib/types"

interface InsuranceComparisonProps {
  recommendations?: PolicyRecommendation[]
  tripDetails?: TripDetails
  quotes?: any[]  // Real pricing from Ancileo API
  taxonomyProducts?: string[]  // Product A, B, C
  taxonomyRecommendation?: string  // Recommended product
  riskLevel?: string
  currentMessages?: any[]  // Current chat messages to preserve during payment
  onPaymentComplete?: (policyNumber: string, policyName: string, amount: number) => void
}

const commonFeatures = ["24/7 Emergency Assistance", "Travel Delay Coverage", "COVID-19 Coverage", "Worldwide Coverage"]

// Map Product A/B/C to display names
const PRODUCT_NAME_MAP: Record<string, string> = {
  "Product A": "Scootsurance",
  "Product B": "TravelEasy Standard",
  "Product C": "TravelEasy Pre-Existing"
}

export function InsuranceComparison({ 
  recommendations, 
  tripDetails, 
  quotes, 
  taxonomyProducts, 
  taxonomyRecommendation,
  riskLevel,
  currentMessages = [],
  onPaymentComplete
}: InsuranceComparisonProps) {
  const [plans, setPlans] = useState<PolicyRecommendation[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [detailedPolicies, setDetailedPolicies] = useState<any[]>([])
  const [selectedPolicyForPurchase, setSelectedPolicyForPurchase] = useState<string | null>(null)
  const [taxonomyData, setTaxonomyData] = useState<any>(null)

  useEffect(() => {
    if (recommendations && recommendations.length > 0) {
      setPlans(recommendations)
      // Fetch detailed policy information
      fetchDetailedPolicies(recommendations)
    } else {
      // If no recommendations provided, fetch default policies
      fetchDefaultPolicies()
    }
  }, [recommendations])

  const fetchDefaultPolicies = async () => {
    setIsLoading(true)
    try {
      const policies = await apiClient.getPolicies()
      // Convert to recommendations format
      const defaultRecommendations = policies.slice(0, 3).map((policy, index) => ({
        policy_id: policy.policy_id,
        policy_name: policy.policy_name,
        product_type: policy.product_type,
        premium: undefined,
        coverage_score: undefined,
        reasoning: undefined,
      }))
      setPlans(defaultRecommendations)
      setDetailedPolicies(policies.slice(0, 3))
    } catch (error) {
      console.error("Error fetching policies:", error)
    } finally {
      setIsLoading(false)
    }
  }

  const fetchDetailedPolicies = async (recs: PolicyRecommendation[]) => {
    setIsLoading(true)
    try {
      const detailed = await Promise.all(
        recs.map((rec) => apiClient.getPolicy(rec.policy_id))
      )
      setDetailedPolicies(detailed.filter((p) => p !== null))
    } catch (error) {
      console.error("Error fetching detailed policies:", error)
    } finally {
      setIsLoading(false)
    }
  }

  const getBenefitValue = (policy: any, benefitName: string): string => {
    if (!policy || !policy.benefits) return "N/A"
    const benefit = policy.benefits.find(
      (b: any) => b.benefit_name.toLowerCase().includes(benefitName.toLowerCase())
    )
    if (!benefit) return "N/A"
    if (benefit.coverage_amount) {
      return `$${benefit.coverage_amount.toLocaleString()}`
    }
    return benefit.coverage_description || "Included"
  }

  const hasBenefit = (policy: any, benefitName: string): boolean => {
    if (!policy || !policy.benefits) return false
    return policy.benefits.some((b: any) =>
      b.benefit_name.toLowerCase().includes(benefitName.toLowerCase())
    )
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    )
  }
  return (
    <div className="w-full mx-auto space-y-8 mt-6 min-h-[1000px]">
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

      <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
        {plans.map((plan, index) => {
          const detailedPolicy = detailedPolicies[index]
          const isRecommended = plan.coverage_score && plan.coverage_score > 0.7

          return (
            <Card
              key={plan.policy_id}
              className={`relative overflow-hidden rounded-3xl shadow-lg min-h-[700px] flex flex-col ${isRecommended ? "border-2 border-primary ring-4 ring-primary/20" : "border-2"}`}
            >
              {isRecommended && (
                <div className="absolute top-0 right-0">
                  <Badge className="rounded-none rounded-bl-2xl bg-primary text-primary-foreground px-6 py-3 text-base font-semibold">
                    Recommended
                  </Badge>
                </div>
              )}
              <div className="p-12 space-y-8 flex-1 flex flex-col">
                <div>
                  <h3 className="text-3xl font-bold text-foreground">{plan.policy_name}</h3>
                  <div className="mt-2">
                    <Badge variant="outline" className="text-sm">
                      {plan.product_type}
                    </Badge>
                  </div>
                  {plan.premium && (
                    <div className="mt-4">
                      <span className="text-5xl font-bold text-foreground">${plan.premium}</span>
                      <span className="text-lg text-muted-foreground ml-2">/trip</span>
                    </div>
                  )}
                  {plan.reasoning && (
                    <p className="text-sm text-muted-foreground mt-3 italic">{plan.reasoning}</p>
                  )}
                </div>

                <div className="space-y-6 pt-6 border-t-2 border-border flex-1">
                  {detailedPolicy && (
                    <>
                      <div className="flex items-start gap-4">
                        <Heart className="w-7 h-7 text-accent shrink-0 mt-1" />
                        <div className="flex-1">
                          <p className="text-base text-muted-foreground font-medium">Medical Coverage</p>
                          <p className="text-xl font-semibold text-foreground mt-2">
                            {getBenefitValue(detailedPolicy, "medical")}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-start gap-4">
                        <X className="w-7 h-7 text-accent shrink-0 mt-1" />
                        <div className="flex-1">
                          <p className="text-base text-muted-foreground font-medium">Trip Cancellation</p>
                          <p className="text-xl font-semibold text-foreground mt-2">
                            {getBenefitValue(detailedPolicy, "cancellation")}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-start gap-4">
                        <Luggage className="w-7 h-7 text-accent shrink-0 mt-1" />
                        <div className="flex-1">
                          <p className="text-base text-muted-foreground font-medium">Baggage Loss</p>
                          <p className="text-xl font-semibold text-foreground mt-2">
                            {getBenefitValue(detailedPolicy, "baggage")}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center justify-between py-3">
                        <span className="text-base text-muted-foreground font-medium">Emergency Evacuation</span>
                        {hasBenefit(detailedPolicy, "evacuation") ? (
                          <Check className="w-7 h-7 text-accent" />
                        ) : (
                          <X className="w-7 h-7 text-muted-foreground" />
                        )}
                      </div>

                      <div className="flex items-center justify-between py-3">
                        <span className="text-base text-muted-foreground font-medium">Adventure Sports</span>
                        {hasBenefit(detailedPolicy, "adventure") || hasBenefit(detailedPolicy, "sports") ? (
                          <Check className="w-7 h-7 text-accent" />
                        ) : (
                          <X className="w-7 h-7 text-muted-foreground" />
                        )}
                      </div>
                    </>
                  )}
                </div>

                <Button
                  className="w-full h-14 text-lg font-semibold rounded-2xl mt-auto"
                  variant={isRecommended ? "default" : "outline"}
                  onClick={() => setSelectedPolicyForPurchase(plan.policy_id)}
                >
                  Buy {plan.policy_name}
                </Button>
              </div>
            </Card>
          )
        })}
      </div>

      {/* Payment Processor - Shows when a policy is selected */}
      {selectedPolicyForPurchase && (() => {
        const selectedPlan = plans.find(p => p.policy_id === selectedPolicyForPurchase)
        const selectedQuote = quotes?.find(q => q.policy_id === selectedPolicyForPurchase || q.product_key === selectedPolicyForPurchase)
        const selectedPremium = selectedQuote?.premium || selectedPlan?.premium || 0
        
        return (
          <div className="mt-8">
            <PaymentProcessor 
              quoteId={selectedQuote?.quote_id || "demo_quote"}
              policyId={selectedPlan?.policy_id || selectedPolicyForPurchase}
              policyName={selectedPlan?.policy_name || "Travel Insurance"}
              premium={selectedPremium}
              tripDetails={tripDetails}
              currentMessages={currentMessages}
              onPaymentComplete={(policyNumber) => {
                if (onPaymentComplete) {
                  onPaymentComplete(policyNumber, selectedPlan?.policy_name || "Travel Insurance", selectedPremium)
                }
              }}
            />
          </div>
        )
      })()}
    </div>
  )
}
