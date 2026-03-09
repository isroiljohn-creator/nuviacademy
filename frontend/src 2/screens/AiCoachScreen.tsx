import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useUser } from '@/contexts/UserContext';
import { useLanguage } from '@/contexts/LanguageContext';
import axios from 'axios';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

// API URL is handled by axios baseURL in UserContext

export const AiCoachScreen: React.FC = () => {
  const { profile, todayLog, canUseFeature } = useUser();
  const { t } = useLanguage();
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Salom! 👋 Men YASHA AI murabbiyiman. Sizga ovqatlanish, mashq yoki sog\'lom turmush tarzi bo\'yicha yordam bera olaman. Savolingizni yozing!'
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Token topilmadi. Qayta kiring.');
      }

      const response = await axios.post('/coach/chat', {
        messages: messages.concat(userMessage).map(m => ({
          id: m.id,
          role: m.role,
          content: m.content
        })),
        userContext: {
          name: profile?.name,
          age: profile?.age,
          goal: profile?.goal,
          todayWater: todayLog?.water_ml,
          todaySteps: todayLog?.steps,
        }
      }, {
        headers: { 'Authorization': `Bearer ${token}` },
        timeout: 30000
      });

      let replyText = 'Tushunarsiz javob.';
      if (response?.data?.reply && typeof response.data.reply === 'string') {
        replyText = response.data.reply;
      }

      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: replyText
      }]);
    } catch (error: any) {
      console.error('Chat error:', error);
      console.error('Error response:', error.response);
      console.error('Error data:', error.response?.data);

      let errorMsg = 'Uzr, xatolik yuz berdi. Qayta urinib ko\'ring.';

      if (error.response?.status === 401) {
        errorMsg = 'Tizimga qayta kiring.';
      } else if (error.response?.status === 429) {
        errorMsg = 'Juda ko\'p so\'rov yuborildi. Bir oz kuting.';
      } else if (error.response?.status === 422) {
        // Validation error
        errorMsg = 'Ma\'lumotlar noto\'g\'ri. Qayta urinib ko\'ring.';
      } else if (error.code === 'ECONNABORTED') {
        errorMsg = 'So\'rov juda uzoq davom etdi. Qayta urinib ko\'ring.';
      } else if (error.response?.data?.detail) {
        // Handle both string and array detail
        const detail = error.response.data.detail;
        if (typeof detail === 'string') {
          errorMsg = `Xatolik: ${detail}`;
        } else if (Array.isArray(detail)) {
          errorMsg = `Xatolik: ${detail.map((d: any) => d.msg || d).join(', ')}`;
        } else {
          errorMsg = `Xatolik: ${JSON.stringify(detail)}`;
        }
      }

      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: errorMsg
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // Quick questions with template answers
  const quickQuestions = [
    { q: 'Qanday ovqatlanishim kerak?', a: 'Sog\'lom ovqatlanish uchun:\n• Har kuni 5 xil rang sabzavot va meva\n• Oq go\'sht va baliq\n• To\'liq don mahsulotlari\n• Yetarlicha suv (2-2.5 litr)\n• Kam shakar va tuz' },
    { q: 'Qanday mashq qilishim kerak?', a: 'Kunlik mashqlar:\n• 30 daqiqa yurish yoki yugurish\n• 10 daqiqa cho\'zilish\n• Haftada 3 kun kuch mashqlari\n• Har kuni faol bo\'ling' },
    { q: 'Vaznni qanday yo\'qotish mumkin?', a: 'Vazn yo\'qotish uchun:\n• Kaloriya kamligini saqlang\n• Ko\'proq harakat qiling\n• Suv ko\'p iching\n• Uyqu rejimini saqlang\n• Sabr qiling - oyiga 2-3 kg yetarli' },
    { q: 'Qancha suv ichish kerak?', a: 'Suv rejasi:\n• Kuniga 2-2.5 litr\n• Mashqdan oldin va keyin\n• Har xil ovqat oldidan 30 daqiqa\n• Suvni bir oz-ozdan iching' },
    { q: 'Qachon mashq qilish yaxshi?', a: 'Eng yaxshi vaqt:\n• Ertalab - energiya uchun\n• Kechqurun - stress uchun\n• Sizga qulay vaqt - eng muhimi\n• Har doim bir xil vaqtda' }
  ];

  const handleQuickQuestion = (question: string, answer: string) => {
    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: question
    };

    const assistantMsg: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: answer
    };

    setMessages(prev => [...prev, userMsg, assistantMsg]);
  };

  return (
    <div className="h-screen bg-background flex flex-col">
      {/* Header */}
      <div className="px-4 pt-6 pb-4 border-b border-border/50">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center">
            <Bot className="w-6 h-6 text-primary" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-foreground">AI Murabbiy</h1>
            <p className="text-sm text-muted-foreground">Shaxsiy maslahat</p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message, index) => (
          <div key={message.id}>
            <div className={`flex gap-3 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${message.role === 'user' ? 'bg-primary' : 'bg-primary/20'
                }`}>
                {message.role === 'user' ? (
                  <User className="w-4 h-4 text-primary-foreground" />
                ) : (
                  <Bot className="w-4 h-4 text-primary" />
                )}
              </div>
              <div className={`max-w-[85%] p-3 rounded-2xl ${message.role === 'user'
                ? 'bg-primary text-primary-foreground rounded-br-md'
                : 'bg-card border border-border/50 text-foreground rounded-bl-md'
                }`}>
                <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
              </div>
            </div>

            {/* Quick questions after first assistant message */}
            {index === 0 && message.role === 'assistant' && (
              <div className="mt-3 flex flex-wrap gap-2">
                {quickQuestions.map((item, i) => (
                  <button
                    key={i}
                    onClick={() => handleQuickQuestion(item.q, item.a)}
                    className="px-3 py-2 bg-card border border-border/50 rounded-full text-xs text-foreground hover:bg-muted transition-colors"
                  >
                    {item.q}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
              <Bot className="w-4 h-4 text-primary" />
            </div>
            <div className="bg-card border border-border/50 p-4 rounded-2xl rounded-bl-md">
              <div className="flex gap-1.5">
                <span className="w-1.5 h-1.5 bg-primary/50 rounded-full animate-bounce" />
                <span className="w-1.5 h-1.5 bg-primary/50 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-1.5 h-1.5 bg-primary/50 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input - Fixed spacing */}
      <div className="px-4 pb-20 pt-3 border-t border-border/50 bg-background">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={canUseFeature('ai_chat') ? "Savolingizni yozing..." : "Faqat Plus/Pro tarifida mavjud 🔒"}
            className="flex-1 h-12 px-4 rounded-full bg-card border border-border/50 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 disabled:opacity-50 disabled:bg-muted"
            disabled={isLoading || !canUseFeature('ai_chat')}
          />
          <Button
            size="icon"
            onClick={sendMessage}
            disabled={!input.trim() || isLoading || !canUseFeature('ai_chat')}
            className="w-12 h-12 rounded-full"
          >
            {canUseFeature('ai_chat') ? <Send className="w-5 h-5" /> : <div className="w-5 h-5 text-muted-foreground">🔒</div>}
          </Button>
        </div>
      </div>
    </div>
  );
};
