import { useState, useRef, useEffect } from 'react';
import { PageHeader, SectionCard, Spinner } from '../components/UI.jsx';
import { Send, Bot, User, Zap, RotateCcw } from 'lucide-react';

const SUGGESTED = [
  '¿Quién tiene más victorias en la historia de la F1?',
  '¿Cuál es la tasa histórica de Safety Car en Mónaco?',
  'Compara el rendimiento de Hamilton vs Schumacher',
  '¿Qué equipo tiene más campeonatos de constructores?',
  '¿Cuáles son los factores que más influyen en un podio?',
  'Analiza la fiabilidad mecánica de los equipos modernos',
];

const SYSTEM_PROMPT = `Eres un asistente experto en Fórmula 1 llamado "F1 AI". 
Tienes acceso a datos históricos de F1 desde 1950 hasta 2024, incluyendo resultados de carreras, 
standings, tiempos de vuelta, pit stops, estadísticas de pilotos y constructores.

Responde siempre en español. Sé preciso con los datos, analítico y apasionado por la F1.
Cuando no tengas datos específicos, indícalo claramente.
Usa emojis de F1 ocasionalmente para hacer las respuestas más dinámicas.
Formatea las respuestas con listas y secciones claras cuando sea apropiado.`;

export default function Chat() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: '🏎️ ¡Hola! Soy tu asistente de F1 Analytics. Puedo responderte preguntas sobre datos históricos de F1, análisis de pilotos y equipos, estadísticas de carreras y mucho más. ¿Qué quieres saber?',
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const send = async (text) => {
    const msg = text || input.trim();
    if (!msg || loading) return;
    setInput('');

    const newMessages = [...messages, { role: 'user', content: msg }];
    setMessages(newMessages);
    setLoading(true);

    try {
      // Call Anthropic API (Claude in Claude)
      const response = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: 'claude-sonnet-4-20250514',
          max_tokens: 1000,
          system: SYSTEM_PROMPT,
          messages: newMessages.map(m => ({ role: m.role, content: m.content })),
        }),
      });

      const data = await response.json();
      const reply = data.content?.map(c => c.text || '').join('') || 'Lo siento, no pude procesar tu pregunta.';

      setMessages(prev => [...prev, { role: 'assistant', content: reply }]);
    } catch (e) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '⚠️ Error al conectar con el servicio de IA. Asegúrate de que el backend está configurado con las credenciales de Azure AI.',
      }]);
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setMessages([{
      role: 'assistant',
      content: '🏎️ ¡Conversación reiniciada! ¿En qué puedo ayudarte?',
    }]);
  };

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <PageHeader title="Chat F1 AI" subtitle="Asistente conversacional con acceso a datos históricos">
        <button className="btn-ghost" onClick={reset}>
          <RotateCcw size={12} style={{ marginRight: 4 }} />
          Reiniciar
        </button>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: '#27F4D2' }}>
          <Zap size={12} />
          <span style={{ fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase' }}>Azure AI + Claude</span>
        </div>
      </PageHeader>

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', padding: '0 32px 24px' }}>
        {/* Messages */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: '20px 0',
          display: 'flex',
          flexDirection: 'column',
          gap: 16,
        }}>
          {messages.map((msg, i) => (
            <div
              key={i}
              style={{
                display: 'flex',
                gap: 12,
                alignItems: 'flex-start',
                flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
                animation: 'fadeIn 0.2s ease',
              }}
            >
              {/* Avatar */}
              <div style={{
                width: 32, height: 32,
                borderRadius: 4,
                background: msg.role === 'user' ? 'var(--f1-red)' : 'var(--f1-surface-3)',
                border: `1px solid ${msg.role === 'user' ? 'var(--f1-red)' : 'var(--f1-border)'}`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                flexShrink: 0,
              }}>
                {msg.role === 'user'
                  ? <User size={16} color="white" />
                  : <Bot size={16} color="var(--f1-red)" />}
              </div>

              {/* Bubble */}
              <div style={{
                maxWidth: '75%',
                padding: '12px 16px',
                background: msg.role === 'user' ? 'var(--f1-red)' : 'var(--f1-surface-2)',
                border: msg.role === 'user' ? 'none' : '1px solid var(--f1-border)',
                borderRadius: 4,
                borderBottomRightRadius: msg.role === 'user' ? 0 : 4,
                borderBottomLeftRadius: msg.role === 'assistant' ? 0 : 4,
                fontSize: 14,
                lineHeight: 1.65,
                color: 'var(--f1-text)',
                whiteSpace: 'pre-wrap',
              }}>
                {msg.content}
              </div>
            </div>
          ))}

          {loading && (
            <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
              <div style={{
                width: 32, height: 32,
                borderRadius: 4,
                background: 'var(--f1-surface-3)',
                border: '1px solid var(--f1-border)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <Bot size={16} color="var(--f1-red)" />
              </div>
              <div style={{
                padding: '12px 16px',
                background: 'var(--f1-surface-2)',
                border: '1px solid var(--f1-border)',
                borderRadius: 4,
                borderBottomLeftRadius: 0,
                display: 'flex', gap: 6, alignItems: 'center',
              }}>
                {[0, 1, 2].map(i => (
                  <div key={i} style={{
                    width: 6, height: 6,
                    background: 'var(--f1-red)',
                    borderRadius: '50%',
                    animation: `pulse 1.2s ease-in-out ${i * 0.2}s infinite`,
                  }} />
                ))}
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Suggestions */}
        {messages.length <= 1 && (
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 10, color: 'var(--f1-text-dim)', fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 10 }}>
              Preguntas sugeridas
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {SUGGESTED.map(s => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  style={{
                    background: 'var(--f1-surface-2)',
                    border: '1px solid var(--f1-border)',
                    color: 'var(--f1-text-muted)',
                    padding: '6px 12px',
                    borderRadius: 2,
                    fontSize: 12,
                    cursor: 'pointer',
                    fontFamily: 'Titillium Web, sans-serif',
                    transition: 'all 0.15s',
                  }}
                  onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--f1-red)'; e.currentTarget.style.color = 'var(--f1-text)'; }}
                  onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--f1-border)'; e.currentTarget.style.color = 'var(--f1-text-muted)'; }}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input */}
        <div style={{
          display: 'flex',
          gap: 10,
          padding: '16px',
          background: 'var(--f1-surface)',
          border: '1px solid var(--f1-border)',
          borderRadius: 4,
        }}>
          <input
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } }}
            placeholder="Pregunta sobre F1... (Enter para enviar)"
            className="input-f1"
            style={{ flex: 1, background: 'transparent', border: 'none', padding: '4px 0' }}
            disabled={loading}
          />
          <button
            onClick={() => send()}
            disabled={!input.trim() || loading}
            style={{
              background: input.trim() && !loading ? 'var(--f1-red)' : 'var(--f1-surface-3)',
              border: 'none',
              borderRadius: 2,
              width: 40, height: 40,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              cursor: input.trim() && !loading ? 'pointer' : 'not-allowed',
              transition: 'background 0.15s',
              flexShrink: 0,
            }}
          >
            {loading ? <Spinner size={16} /> : <Send size={16} color="white" />}
          </button>
        </div>
      </div>
    </div>
  );
}
