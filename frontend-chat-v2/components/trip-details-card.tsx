"use client"

import { Card } from "@/components/ui/card"
import { MapPin, Calendar, Users, Activity, DollarSign } from "lucide-react"

interface TripDetailsCardProps {
  tripDetails?: any
  riskLevel?: string
}

export function TripDetailsCard({ tripDetails, riskLevel }: TripDetailsCardProps) {
  if (!tripDetails) return null

  const destination = tripDetails.destination_country || tripDetails.destination
  const duration = tripDetails.trip_duration_days
  const departureDate = tripDetails.departure_date
  const returnDate = tripDetails.return_date
  const travelers = tripDetails.travelers || []
  const activities = tripDetails.planned_activities || tripDetails.activities || []
  const purpose = tripDetails.trip_purpose

  return (
    <Card className="p-8 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-950/20 dark:to-indigo-950/20 border-2 border-blue-200 dark:border-blue-800 rounded-3xl shadow-lg">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-2xl font-bold text-foreground flex items-center gap-3">
          <MapPin className="w-7 h-7 text-blue-600" />
          Your Trip to {destination}
        </h3>
        {riskLevel && (
          <div className="px-4 py-2 bg-white dark:bg-gray-800 rounded-full shadow-sm">
            <span className="text-sm font-semibold">
              Risk Level: <span className={`${riskLevel === 'LOW' ? 'text-green-600' : riskLevel === 'MEDIUM' ? 'text-yellow-600' : 'text-red-600'}`}>{riskLevel}</span>
            </span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {duration && (
          <div className="flex items-center gap-3">
            <Calendar className="w-6 h-6 text-blue-600 shrink-0" />
            <div>
              <p className="text-sm text-muted-foreground">Duration</p>
              <p className="text-lg font-semibold text-foreground">{duration} days</p>
            </div>
          </div>
        )}

        {departureDate && (
          <div className="flex items-center gap-3">
            <Calendar className="w-6 h-6 text-blue-600 shrink-0" />
            <div>
              <p className="text-sm text-muted-foreground">Dates</p>
              <p className="text-base font-semibold text-foreground">
                {new Date(departureDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                {returnDate && ` - ${new Date(returnDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`}
              </p>
            </div>
          </div>
        )}

        {travelers.length > 0 && (
          <div className="flex items-center gap-3">
            <Users className="w-6 h-6 text-blue-600 shrink-0" />
            <div>
              <p className="text-sm text-muted-foreground">Travelers</p>
              <p className="text-lg font-semibold text-foreground">
                {travelers.length} {travelers.length === 1 ? 'person' : 'people'}
                {travelers[0]?.age && ` (${travelers[0].age} years)`}
              </p>
            </div>
          </div>
        )}

        {activities.length > 0 && activities[0] !== 'general' && (
          <div className="flex items-center gap-3">
            <Activity className="w-6 h-6 text-blue-600 shrink-0" />
            <div>
              <p className="text-sm text-muted-foreground">Activities</p>
              <p className="text-base font-semibold text-foreground capitalize">
                {activities.join(', ')}
              </p>
            </div>
          </div>
        )}

        {purpose && (
          <div className="flex items-center gap-3">
            <DollarSign className="w-6 h-6 text-blue-600 shrink-0" />
            <div>
              <p className="text-sm text-muted-foreground">Purpose</p>
              <p className="text-base font-semibold text-foreground capitalize">{purpose}</p>
            </div>
          </div>
        )}
      </div>
    </Card>
  )
}

