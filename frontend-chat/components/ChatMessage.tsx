import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  emotion?: string;
  confidence?: number;
}

export default function ChatMessage({ message }: { message: Message }) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-[75%] ${
        isUser
          ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white'
          : 'bg-white dark:bg-gray-800 shadow-md border border-gray-200 dark:border-gray-700'
      } rounded-2xl px-5 py-3`}>
        {!isUser && (
          <div className="flex items-center gap-2 mb-2 pb-2 border-b border-gray-200 dark:border-gray-700">
            <div className="w-6 h-6 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center text-white font-bold text-xs">
              T
            </div>
            <span className="text-sm font-semibold text-gray-900 dark:text-white">TravelMate</span>
            {message.emotion && message.emotion !== 'neutral' && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300">
                {getEmotionEmoji(message.emotion)} {message.emotion}
              </span>
            )}
          </div>
        )}
        
        <div className={`prose prose-sm max-w-none ${
          isUser ? 'prose-invert' : 'dark:prose-invert'
        }`}>
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {message.content}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
}

function getEmotionEmoji(emotion: string): string {
  const emojiMap: Record<string, string> = {
    'stressed': '😰',
    'worried': '😟',
    'excited': '🤩',
    'frustrated': '😤',
    'skeptical': '🤔',
    'neutral': '😊'
  };
  return emojiMap[emotion] || '😊';
}

