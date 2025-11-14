"use client"

import { Mail, Upload, Edit3 } from "lucide-react"
import { Card } from "@/components/ui/card"

interface WelcomeScreenProps {
  onActionSelect: (action: "gmail" | "upload" | "manual") => void
}

export function WelcomeScreen({ onActionSelect }: WelcomeScreenProps) {
  const actions = [
    {
      id: "gmail" as const,
      icon: Mail,
      title: "Connect to Gmail",
      description: "Automatically fetch your trip details from booking confirmations",
      gradient: "from-blue-500/10 to-purple-500/10",
      iconBg: "bg-gradient-to-br from-blue-500 to-purple-500",
    },
    {
      id: "upload" as const,
      icon: Upload,
      title: "Upload Booking",
      description: "Upload your travel booking confirmation document",
      gradient: "from-coral-500/10 to-orange-500/10",
      iconBg: "bg-gradient-to-br from-coral-500 to-orange-500",
    },
    {
      id: "manual" as const,
      icon: Edit3,
      title: "Enter Trip Details",
      description: "Manually enter your travel information",
      gradient: "from-teal-500/10 to-cyan-500/10",
      iconBg: "bg-gradient-to-br from-teal-500 to-cyan-500",
    },
  ]

  return (
    <div className="flex flex-col items-center justify-center px-4 py-8 md:py-12">
      <div className="max-w-4xl w-full mx-auto text-center space-y-8 md:space-y-12">
        {/* Hero Section */}
        <div className="space-y-4 md:space-y-6">
          <div className="flex justify-center">
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-br from-blue-500 via-purple-500 to-coral-500 rounded-full blur-2xl opacity-30 animate-pulse" />
              <div className="relative w-20 h-20 md:w-24 md:h-24 lg:w-32 lg:h-32 rounded-full bg-gradient-to-br from-blue-500 via-purple-500 to-coral-500 shadow-2xl flex items-center justify-center">
                <div className="w-16 h-16 md:w-20 md:h-20 lg:w-28 lg:h-28 rounded-full bg-background flex items-center justify-center">
                  <span className="text-3xl md:text-4xl lg:text-5xl">✈️</span>
                </div>
              </div>
            </div>
          </div>

          <div className="space-y-2 md:space-y-3">
            <h1 className="text-3xl md:text-4xl lg:text-5xl xl:text-6xl font-bold text-balance">
              Hi there, <span className="text-primary">Traveler</span>
            </h1>
            <p className="text-lg md:text-xl lg:text-2xl xl:text-3xl text-muted-foreground text-balance">
              Ready to protect your <span className="text-coral-600 dark:text-coral-400 font-semibold">journey?</span>
            </p>
          </div>
        </div>

        {/* Action Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6">
          {actions.map((action) => {
            const Icon = action.icon
            return (
              <Card
                key={action.id}
                onClick={() => onActionSelect(action.id)}
                className={`group relative overflow-hidden cursor-pointer transition-all duration-300 hover:scale-105 hover:shadow-2xl border-2 hover:border-primary/50 bg-gradient-to-br ${action.gradient} backdrop-blur-sm p-6 md:p-8`}
              >
                <div className="space-y-4">
                  <div className="flex justify-center">
                    <div
                      className={`${action.iconBg} w-14 h-14 md:w-16 md:h-16 rounded-2xl flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-300`}
                    >
                      <Icon className="w-7 h-7 md:w-8 md:h-8 text-white" />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <h3 className="text-lg md:text-xl font-bold text-foreground">{action.title}</h3>
                    <p className="text-sm md:text-base text-muted-foreground leading-relaxed">{action.description}</p>
                  </div>
                </div>
              </Card>
            )
          })}
        </div>
      </div>
    </div>
  )
}
