interface Policy {
  name: string;
  price: number;
  recommended?: boolean;
  medical_coverage?: number;
  benefits?: string[];
  why?: string;
}

export default function PolicyCard({ policy }: { policy: Policy }) {
  return (
    <div className={`rounded-xl border-2 p-5 transition-all hover:shadow-lg ${
      policy.recommended
        ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/20 dark:border-purple-400'
        : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800'
    }`}>
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="text-lg font-bold text-gray-900 dark:text-white">{policy.name}</h3>
          {policy.recommended && (
            <span className="inline-block mt-1 px-2 py-1 text-xs font-semibold bg-purple-500 text-white rounded-full">
              ⭐ Recommended
            </span>
          )}
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-gray-900 dark:text-white">
            SGD ${policy.price.toFixed(2)}
          </div>
        </div>
      </div>

      {policy.medical_coverage && (
        <div className="mb-3 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
          <div className="text-sm text-gray-600 dark:text-gray-400">Medical Coverage</div>
          <div className="text-lg font-bold text-blue-700 dark:text-blue-400">
            Up to ${policy.medical_coverage.toLocaleString()}
          </div>
        </div>
      )}

      {policy.benefits && policy.benefits.length > 0 && (
        <div className="space-y-2 mb-3">
          {policy.benefits.map((benefit, idx) => (
            <div key={idx} className="flex items-center gap-2">
              <div className="w-5 h-5 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
                <svg className="w-3 h-3 text-green-600 dark:text-green-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              </div>
              <span className="text-sm text-gray-700 dark:text-gray-300">{benefit}</span>
            </div>
          ))}
        </div>
      )}

      {policy.why && (
        <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
          <div className="text-sm text-gray-600 dark:text-gray-400">
            <span className="font-semibold">Why this policy:</span> {policy.why}
          </div>
        </div>
      )}

      <button className="mt-4 w-full py-2 px-4 rounded-lg bg-gradient-to-r from-blue-500 to-purple-500 text-white font-medium hover:from-blue-600 hover:to-purple-600 transition-all shadow-lg hover:shadow-xl">
        Get Quote
      </button>
    </div>
  );
}

