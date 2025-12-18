import { useState, useEffect, useRef } from 'react';
import { Send, Trash2, Settings, Copy, Download, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';
import { playgroundAPI } from '@/services/api';

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  latency?: number;
}

interface Model {
  id: string;
  name: string;
  context: number;
}

interface Provider {
  provider: string;
  models: Model[];
}

interface Preset {
  id: string;
  name: string;
  system_prompt: string;
  temperature: number;
  max_tokens: number;
}

export function PlaygroundPage() {
  const { toast } = useToast();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  
  // Model settings
  const [providers, setProviders] = useState<Provider[]>([]);
  const [selectedProvider, setSelectedProvider] = useState('gemini');
  const [selectedModel, setSelectedModel] = useState('gemini-1.5-flash');
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(2048);
  const [systemPrompt, setSystemPrompt] = useState('You are a helpful AI assistant.');
  const [useStreaming, setUseStreaming] = useState(true);
  
  // Presets
  const [presets, setPresets] = useState<Preset[]>([]);
  const [selectedPreset, setSelectedPreset] = useState<string>('');
  
  // Stats
  const [totalTokens, setTotalTokens] = useState(0);
  const [avgLatency, setAvgLatency] = useState(0);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // Load models and presets
  useEffect(() => {
    loadModels();
    loadPresets();
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent]);

  const loadModels = async () => {
    try {
      const data = await playgroundAPI.getModels();
      setProviders(data.models);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load models',
        variant: 'destructive',
      });
    }
  };

  const loadPresets = async () => {
    try {
      const data = await playgroundAPI.getPresets();
      setPresets(data.presets);
    } catch (error) {
      console.error('Failed to load presets:', error);
    }
  };

  const applyPreset = (presetId: string) => {
    const preset = presets.find(p => p.id === presetId);
    if (preset) {
      setSystemPrompt(preset.system_prompt);
      setTemperature(preset.temperature);
      setMaxTokens(preset.max_tokens);
      setSelectedPreset(presetId);
      toast({
        title: 'Preset Applied',
        description: `Applied ${preset.name} preset`,
      });
    }
  };

  const connectWebSocket = () => {
    const token = localStorage.getItem('access_token');
    const wsUrl = `ws://localhost:8000/api/v1/playground/ws/chat`;
    
    wsRef.current = new WebSocket(wsUrl);
    
    wsRef.current.onopen = () => {
      console.log('WebSocket connected');
    };
    
    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'chunk') {
        setStreamingContent(prev => prev + data.content);
      } else if (data.type === 'complete') {
        const assistantMessage: Message = {
          role: 'assistant',
          content: data.content,
          timestamp: new Date(),
          latency: data.latency_ms,
        };
        setMessages(prev => [...prev, assistantMessage]);
        setStreamingContent('');
        setIsLoading(false);
        
        // Update stats
        setAvgLatency(prev => (prev + data.latency_ms) / 2);
      } else if (data.type === 'error') {
        toast({
          title: 'Error',
          description: data.error,
          variant: 'destructive',
        });
        setIsLoading(false);
        setStreamingContent('');
      }
    };
    
    wsRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      toast({
        title: 'Connection Error',
        description: 'Failed to connect to server',
        variant: 'destructive',
      });
      setIsLoading(false);
    };
  };

  const sendMessage = async () => {
    if (!input.trim()) return;
    
    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date(),
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    
    const requestMessages = messages.map(m => ({
      role: m.role,
      content: m.content,
    }));
    requestMessages.push({ role: 'user', content: userMessage.content });

    if (useStreaming) {
      // WebSocket streaming
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        connectWebSocket();
        // Wait for connection
        await new Promise(resolve => setTimeout(resolve, 500));
      }
      
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          messages: requestMessages,
          model: selectedModel,
          provider: selectedProvider,
          temperature,
          max_tokens: maxTokens,
          system_prompt: systemPrompt,
          stream: true,
        }));
      }
    } else {
      // Regular HTTP request
      try {
        const response = await playgroundAPI.chat({
          messages: requestMessages,
          model: selectedModel,
          provider: selectedProvider,
          temperature,
          max_tokens: maxTokens,
          system_prompt: systemPrompt,
          stream: false,
        });
        
        const assistantMessage: Message = {
          role: 'assistant',
          content: response.content,
          timestamp: new Date(),
          latency: response.latency_ms,
        };
        
        setMessages(prev => [...prev, assistantMessage]);
        setIsLoading(false);
      } catch (error: any) {
        toast({
          title: 'Error',
          description: error.response?.data?.detail || 'Failed to send message',
          variant: 'destructive',
        });
        setIsLoading(false);
      }
    }
  };

  const clearChat = () => {
    setMessages([]);
    setStreamingContent('');
    setTotalTokens(0);
    setAvgLatency(0);
  };

  const exportChat = () => {
    const chatContent = messages.map(m => 
      `[${m.role.toUpperCase()}] ${m.content}\n\n`
    ).join('');
    
    const blob = new Blob([chatContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chat-${new Date().toISOString()}.txt`;
    a.click();
  };

  const copyMessage = (content: string) => {
    navigator.clipboard.writeText(content);
    toast({
      title: 'Copied',
      description: 'Message copied to clipboard',
    });
  };

  const currentModels = providers.find(p => p.provider === selectedProvider)?.models || [];

  return (
    <div className="flex h-[calc(100vh-4rem)] gap-4 p-4">
      {/* Chat Area */}
      <div className="flex-1 flex flex-col">
        <Card className="flex-1 flex flex-col">
          <CardHeader className="border-b flex flex-row items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5" />
              <CardTitle>LLM Playground</CardTitle>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline">
                {messages.length} messages
              </Badge>
              {avgLatency > 0 && (
                <Badge variant="secondary">
                  Avg: {avgLatency.toFixed(0)}ms
                </Badge>
              )}
              <Button
                variant="outline"
                size="sm"
                onClick={exportChat}
                disabled={messages.length === 0}
              >
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={clearChat}
                disabled={messages.length === 0}
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Clear
              </Button>
            </div>
          </CardHeader>
          
          <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 && (
              <div className="flex items-center justify-center h-full text-muted-foreground">
                <div className="text-center">
                  <Sparkles className="h-12 w-12 mx-auto mb-4 opacity-20" />
                  <p className="text-lg font-medium">Start a conversation</p>
                  <p className="text-sm">Select a model and send a message to begin</p>
                </div>
              </div>
            )}
            
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg p-4 ${
                    message.role === 'user'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <span className="font-semibold text-sm">
                      {message.role === 'user' ? 'You' : 'Assistant'}
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-6 w-6 p-0"
                      onClick={() => copyMessage(message.content)}
                    >
                      <Copy className="h-3 w-3" />
                    </Button>
                  </div>
                  <p className="whitespace-pre-wrap">{message.content}</p>
                  {message.latency && (
                    <p className="text-xs opacity-70 mt-2">
                      {message.latency}ms
                    </p>
                  )}
                </div>
              </div>
            ))}
            
            {/* Streaming message */}
            {streamingContent && (
              <div className="flex justify-start">
                <div className="max-w-[80%] rounded-lg p-4 bg-muted">
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <span className="font-semibold text-sm">Assistant</span>
                    <div className="h-4 w-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                  </div>
                  <p className="whitespace-pre-wrap">{streamingContent}</p>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </CardContent>
          
          {/* Input Area */}
          <div className="border-t p-4">
            <div className="flex gap-2">
              <Textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                  }
                }}
                placeholder="Type your message... (Shift+Enter for new line)"
                className="min-h-[60px] resize-none"
                disabled={isLoading}
              />
              <Button
                onClick={sendMessage}
                disabled={isLoading || !input.trim()}
                size="lg"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </Card>
      </div>

      {/* Settings Sidebar */}
      <Card className="w-80 overflow-y-auto">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Configuration
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <Tabs defaultValue="model">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="model">Model</TabsTrigger>
              <TabsTrigger value="presets">Presets</TabsTrigger>
            </TabsList>
            
            <TabsContent value="model" className="space-y-4">
              {/* Provider Selection */}
              <div className="space-y-2">
                <Label>Provider</Label>
                <Select value={selectedProvider} onValueChange={setSelectedProvider}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {providers.map((provider) => (
                      <SelectItem key={provider.provider} value={provider.provider}>
                        {provider.provider.charAt(0).toUpperCase() + provider.provider.slice(1)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Model Selection */}
              <div className="space-y-2">
                <Label>Model</Label>
                <Select value={selectedModel} onValueChange={setSelectedModel}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {currentModels.map((model) => (
                      <SelectItem key={model.id} value={model.id}>
                        {model.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Temperature */}
              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>Temperature</Label>
                  <span className="text-sm text-muted-foreground">{temperature}</span>
                </div>
                <Slider
                  value={[temperature]}
                  onValueChange={([value]) => setTemperature(value)}
                  min={0}
                  max={2}
                  step={0.1}
                />
                <p className="text-xs text-muted-foreground">
                  Higher = more creative, Lower = more focused
                </p>
              </div>

              {/* Max Tokens */}
              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>Max Tokens</Label>
                  <span className="text-sm text-muted-foreground">{maxTokens}</span>
                </div>
                <Slider
                  value={[maxTokens]}
                  onValueChange={([value]) => setMaxTokens(value)}
                  min={256}
                  max={8192}
                  step={256}
                />
              </div>

              {/* System Prompt */}
              <div className="space-y-2">
                <Label>System Prompt</Label>
                <Textarea
                  value={systemPrompt}
                  onChange={(e) => setSystemPrompt(e.target.value)}
                  placeholder="Enter system prompt..."
                  className="min-h-[100px]"
                />
              </div>

              {/* Streaming Toggle */}
              <div className="flex items-center justify-between">
                <Label>Enable Streaming</Label>
                <input
                  type="checkbox"
                  checked={useStreaming}
                  onChange={(e) => setUseStreaming(e.target.checked)}
                  className="h-4 w-4"
                />
              </div>
            </TabsContent>
            
            <TabsContent value="presets" className="space-y-4">
              {presets.map((preset) => (
                <Card
                  key={preset.id}
                  className={`cursor-pointer transition-colors hover:bg-accent ${
                    selectedPreset === preset.id ? 'border-primary' : ''
                  }`}
                  onClick={() => applyPreset(preset.id)}
                >
                  <CardContent className="pt-4">
                    <h4 className="font-semibold mb-2">{preset.name}</h4>
                    <p className="text-sm text-muted-foreground line-clamp-3">
                      {preset.system_prompt}
                    </p>
                    <div className="flex gap-2 mt-2">
                      <Badge variant="secondary">Temp: {preset.temperature}</Badge>
                      <Badge variant="secondary">Tokens: {preset.max_tokens}</Badge>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}