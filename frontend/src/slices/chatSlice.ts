import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';
import axios from 'axios';
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
  isTyping: boolean;
  error: string | null;
}

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
  isTyping: false,
  error: null,
};

export const sendMessageToAgent = createAsyncThunk(
  'chat/sendMessageToAgent',
  async (
    payload: { text: string; formState: FormData; history: { sender: string; text: string }[] },
    { dispatch, rejectWithValue }
  ) => {
    try {
      const chatHistory = [...payload.history, { sender: 'user', text: payload.text }];
      
      const response = await axios.post(`${API_BASE}/chat`, {
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
      });
      
      const data = response.data;
      
      // Update form state on left panel
      // Some API values might be null, sanitize before updating Redux
      const sanitizedFormState: Partial<FormData> = {};
      if (data.form_state) {
        const fs = data.form_state;
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
      
      return {
        text: data.response,
        tool_calls: data.tool_calls || []
      };
    } catch (err: any) {
      return rejectWithValue(err.response?.data?.detail || 'Could not connect to AI service');
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
      state.messages = [initialState.messages[0]];
      state.toolLogs = [];
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendMessageToAgent.pending, (state) => {
        state.isTyping = true;
        state.error = null;
      })
      .addCase(sendMessageToAgent.fulfilled, (state, action) => {
        state.isTyping = false;
        state.messages.push({
          id: `msg-${Date.now()}`,
          sender: 'assistant',
          text: action.payload.text,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        });
        state.toolLogs = action.payload.tool_calls;
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

export const { addUserMessage, clearChat } = chatSlice.actions;

export default chatSlice.reducer;
