interface AgentActivityProps {
  activities: Array<{
    agent: string;
    status: string;
    ref?: string;
  }>;
}

export default function AgentActivity({ activities }: AgentActivityProps) {
  if (!activities || activities.length === 0) {
    return null;
  }

  const getAgentInfo = (agent: string) => {
    const agentMap: Record<string, { name: string; icon: string; color: string }> = {
      discovery: { name: 'Discovery Agent', icon: '🔍', color: 'blue' },
      gmail: { name: 'Email Scanner', icon: '📧', color: 'purple' },
      flight_api: { name: 'Flight Lookup', icon: '✈️', color: 'green' },
      risk_analyst: { name: 'Risk Analyst', icon: '📊', color: 'orange' },
      quote_generator: { name: 'Quote Generator', icon: '💰', color: 'yellow' },
    };
    return agentMap[agent] || { name: agent, icon: '🤖', color: 'gray' };
  };

  const getStatusText = (status: string) => {
    const statusMap: Record<string, string> = {
      searching: 'Searching...',
      analyzing: 'Analyzing...',
      looking_up: 'Looking up booking...',
      fetching: 'Fetching data...',
      calculating: 'Calculating...',
      complete: 'Complete!',
    };
    return statusMap[status] || status;
  };

  return (
    <div className="my-3 p-3 rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
      <div className="text-xs font-semibold text-blue-700 dark:text-blue-400 mb-2">
        🤖 Agents Working:
      </div>
      <div className="space-y-2">
        {activities.map((activity, index) => {
          const info = getAgentInfo(activity.agent);
          return (
            <div
              key={index}
              className="flex items-center gap-2 text-sm"
            >
              <span className="text-lg">{info.icon}</span>
              <span className="font-medium text-gray-700 dark:text-gray-300">
                {info.name}:
              </span>
              <span className="text-gray-600 dark:text-gray-400">
                {getStatusText(activity.status)}
              </span>
              {activity.ref && (
                <span className="text-xs px-2 py-0.5 rounded bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300">
                  {activity.ref}
                </span>
              )}
              <div className="ml-auto">
                <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

