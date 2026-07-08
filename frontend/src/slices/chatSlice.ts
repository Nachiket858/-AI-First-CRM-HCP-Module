import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';
import { updateFormState } from './interactionSlice';
import type { FormData } from './interactionSlice';

const API_BASE = 'http://127.0.0.1:8000/api';

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
}

export interface ToolLog {
  tool_name: string;
  arguments: string;
  result: string;
}

interface ChatState {
  messages: ChatMessage[];
  toolLogs: ToolLog[];
  threadId: string;
  isTyping: boolean;
  error: string | null;
}

const generateThreadId = () => `thread_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;

const initialState: ChatState = {
  messages: [
    {
      id: 'welcome',
      sender: 'assistant',
      text: 'Hello! I am your AI Assistant. Log interaction details here (e.g., "Met Dr. Sarah Jenkins, discussed Prodo-X efficacy, positive sentiment, shared brochure") or ask for assistance.',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ],
  toolLogs: [],
  threadId: generateThreadId(),
  isTyping: false,
  error: null,
};

export const sendMessageToAgent = createAsyncThunk(
  'chat/sendMessageToAgent',
  async (
    payload: { text: string; formState: FormData; history: { sender: string; text: string }[]; threadId: string },
    { dispatch, rejectWithValue }
  ) => {
    try {
      const chatHistory = [...payload.history, { sender: 'user', text: payload.text }];
      
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          thread_id: payload.threadId,
          messages: chatHistory.map(m => ({ sender: m.sender, text: m.text })),
          form_state: {
            id: payload.formState.id,
            hcp_id: payload.formState.hcp_id,
            hcp_name: payload.formState.hcp_name,
            interaction_type: payload.formState.interaction_type,
            date: payload.formState.date,
            time: payload.formState.time,
            attendees: payload.formState.attendees,
            topics_discussed: payload.formState.topics_discussed,
            sentiment: payload.formState.sentiment,
            outcomes: payload.formState.outcomes,
            follow_up_actions: payload.formState.follow_up_actions,
            materials_shared: payload.formState.materials_shared,
            samples_distributed: payload.formState.samples_distributed
          }
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to connect to AI service');
      }
      
      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('Response stream not readable');
      }
      
      const assistantMessageId = `msg-${Date.now()}`;
      let hasStartedAssistantMessage = false;
      
      const decoder = new TextDecoder();
      let streamBuffer = '';
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        streamBuffer += decoder.decode(value, { stream: true });
        const lines = streamBuffer.split('\n');
        
        // Save the last partial line back to the buffer
        streamBuffer = lines.pop() || '';
        
        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const data = JSON.parse(line);
            if (data.type === 'token') {
              if (!hasStartedAssistantMessage) {
                dispatch(startAssistantMessage({ id: assistantMessageId }));
                hasStartedAssistantMessage = true;
              }
              dispatch(appendAssistantToken({ id: assistantMessageId, token: data.content }));
            } else if (data.type === 'form_state') {
              const fs = data.content;
              const sanitizedFormState: Partial<FormData> = {};
              if (fs) {
                sanitizedFormState.hcp_id = fs.hcp_id;
                sanitizedFormState.hcp_name = fs.hcp_name || '';
                sanitizedFormState.interaction_type = fs.interaction_type || 'Meeting';
                sanitizedFormState.date = fs.date || '';
                sanitizedFormState.time = fs.time || '';
                sanitizedFormState.attendees = fs.attendees || '';
                sanitizedFormState.topics_discussed = fs.topics_discussed || '';
                sanitizedFormState.sentiment = fs.sentiment || 'Neutral';
                sanitizedFormState.outcomes = fs.outcomes || '';
                sanitizedFormState.follow_up_actions = fs.follow_up_actions || '';
                sanitizedFormState.materials_shared = fs.materials_shared || [];
                sanitizedFormState.samples_distributed = fs.samples_distributed || [];
              }
              dispatch(updateFormState(sanitizedFormState));
            } else if (data.type === 'tool_logs') {
              dispatch(setToolLogs(data.content || []));
            }
          } catch (e) {
            console.error('Error parsing streaming line:', e, line);
          }
        }
      }
      
      return { id: assistantMessageId };
    } catch (err: any) {
      return rejectWithValue(err.message || 'Could not connect to AI service');
    }
  }
);

const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    addUserMessage: (state, action: PayloadAction<string>) => {
      state.messages.push({
        id: `msg-${Date.now()}`,
        sender: 'user',
        text: action.payload,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      });
      state.toolLogs = []; // Reset logs for new interaction
    },
    clearChat: (state) => {
      state.messages = [
        {
          ...initialState.messages[0],
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ];
      state.toolLogs = [];
      state.threadId = generateThreadId();
    },
    startAssistantMessage: (state, action: PayloadAction<{ id: string }>) => {
      state.messages.push({
        id: action.payload.id,
        sender: 'assistant',
        text: '',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      });
    },
    appendAssistantToken: (state, action: PayloadAction<{ id: string; token: string }>) => {
      const msg = state.messages.find(m => m.id === action.payload.id);
      if (msg) {
        msg.text += action.payload.token;
      }
    },
    setToolLogs: (state, action: PayloadAction<ToolLog[]>) => {
      state.toolLogs = action.payload;
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendMessageToAgent.pending, (state) => {
        state.isTyping = true;
        state.error = null;
      })
      .addCase(sendMessageToAgent.fulfilled, (state) => {
        state.isTyping = false;
      })
      .addCase(sendMessageToAgent.rejected, (state, action) => {
        state.isTyping = false;
        state.error = action.payload as string || 'An error occurred';
        state.messages.push({
          id: `msg-${Date.now()}`,
          sender: 'assistant',
          text: `⚠️ **Error:** ${action.payload || 'Failed to get response. Is the backend server running?'}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        });
      });
  },
});

export const {
  addUserMessage,
  clearChat,
  startAssistantMessage,
  appendAssistantToken,
  setToolLogs
} = chatSlice.actions;

export default chatSlice.reducer;
