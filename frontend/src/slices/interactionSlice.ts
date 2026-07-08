import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';
import axios from 'axios';

const API_BASE = 'http://127.0.0.1:8000/api';

export interface HCP {
  id: number;
  name: string;
  specialty: string;
  clinic: string;
  email: string;
  preferences: string;
}

export interface Material {
  id: number;
  name: string;
  type: string;
  file_size: string;
}

export interface Sample {
  id: number;
  name: string;
  description: string;
}

export interface FormData {
  id?: number | null;
  hcp_id?: number | null;
  hcp_name: string;
  interaction_type: string;
  date: string;
  time: string;
  attendees: string;
  topics_discussed: string;
  sentiment: string;
  outcomes: string;
  follow_up_actions: string;
  materials_shared: string[];
  samples_distributed: string[];
}

interface InteractionState {
  formData: FormData;
  hcps: HCP[];
  materials: Material[];
  samples: Sample[];
  loading: boolean;
  error: string | null;
  isSaving: boolean;
  saveSuccess: boolean;
}

const getTodayDateString = () => {
  const d = new Date();
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

const getCurrentTimeString = () => {
  const d = new Date();
  const hours = String(d.getHours()).padStart(2, '0');
  const minutes = String(d.getMinutes()).padStart(2, '0');
  return `${hours}:${minutes}`;
};

const initialState: InteractionState = {
  formData: {
    id: null,
    hcp_id: null,
    hcp_name: '',
    interaction_type: 'Meeting',
    date: getTodayDateString(),
    time: getCurrentTimeString(),
    attendees: '',
    topics_discussed: '',
    sentiment: 'Neutral',
    outcomes: '',
    follow_up_actions: '',
    materials_shared: [],
    samples_distributed: [],
  },
  hcps: [],
  materials: [],
  samples: [],
  loading: false,
  error: null,
  isSaving: false,
  saveSuccess: false,
};

// Async Thunks
export const fetchHCPs = createAsyncThunk('interaction/fetchHCPs', async () => {
  const response = await axios.get(`${API_BASE}/hcps`);
  return response.data;
});

export const fetchMaterials = createAsyncThunk('interaction/fetchMaterials', async () => {
  const response = await axios.get(`${API_BASE}/materials`);
  return response.data;
});

export const fetchSamples = createAsyncThunk('interaction/fetchSamples', async () => {
  const response = await axios.get(`${API_BASE}/samples`);
  return response.data;
});

export const submitInteraction = createAsyncThunk(
  'interaction/submitInteraction',
  async (formData: FormData, { rejectWithValue }) => {
    try {
      const response = await axios.post(`${API_BASE}/interactions`, formData);
      return response.data;
    } catch (err: any) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to submit interaction');
    }
  }
);

const interactionSlice = createSlice({
  name: 'interaction',
  initialState,
  reducers: {
    setFormField: (
      state,
      action: PayloadAction<{ field: keyof FormData; value: any }>
    ) => {
      const { field, value } = action.payload;
      state.formData[field] = value as never;
      
      // If we are changing hcp_name directly, check if it matches an existing HCP to update hcp_id
      if (field === 'hcp_name') {
        const matched = state.hcps.find(hcp => hcp.name.toLowerCase() === value.toLowerCase());
        if (matched) {
          state.formData.hcp_id = matched.id;
        } else {
          state.formData.hcp_id = null;
        }
      }
    },
    updateFormState: (state, action: PayloadAction<Partial<FormData>>) => {
      state.formData = { ...state.formData, ...action.payload };
    },
    addMaterialShared: (state, action: PayloadAction<string>) => {
      if (!state.formData.materials_shared.includes(action.payload)) {
        state.formData.materials_shared.push(action.payload);
      }
    },
    removeMaterialShared: (state, action: PayloadAction<string>) => {
      state.formData.materials_shared = state.formData.materials_shared.filter(
        (name) => name !== action.payload
      );
    },
    addSampleDistributed: (state, action: PayloadAction<string>) => {
      if (!state.formData.samples_distributed.includes(action.payload)) {
        state.formData.samples_distributed.push(action.payload);
      }
    },
    removeSampleDistributed: (state, action: PayloadAction<string>) => {
      state.formData.samples_distributed = state.formData.samples_distributed.filter(
        (name) => name !== action.payload
      );
    },
    resetForm: (state) => {
      state.formData = {
        id: null,
        hcp_id: null,
        hcp_name: '',
        interaction_type: 'Meeting',
        date: getTodayDateString(),
        time: getCurrentTimeString(),
        attendees: '',
        topics_discussed: '',
        sentiment: 'Neutral',
        outcomes: '',
        follow_up_actions: '',
        materials_shared: [],
        samples_distributed: [],
      };
      state.saveSuccess = false;
    },
    clearSaveSuccess: (state) => {
      state.saveSuccess = false;
    }
  },
  extraReducers: (builder) => {
    builder
      // fetchHCPs
      .addCase(fetchHCPs.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchHCPs.fulfilled, (state, action) => {
        state.loading = false;
        state.hcps = action.payload;
      })
      .addCase(fetchHCPs.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch HCPs';
      })
      // fetchMaterials
      .addCase(fetchMaterials.fulfilled, (state, action) => {
        state.materials = action.payload;
      })
      // fetchSamples
      .addCase(fetchSamples.fulfilled, (state, action) => {
        state.samples = action.payload;
      })
      // submitInteraction
      .addCase(submitInteraction.pending, (state) => {
        state.isSaving = true;
        state.error = null;
        state.saveSuccess = false;
      })
      .addCase(submitInteraction.fulfilled, (state, action) => {
        state.isSaving = false;
        state.saveSuccess = true;
        state.formData.id = action.payload.interaction_id;
      })
      .addCase(submitInteraction.rejected, (state, action) => {
        state.isSaving = false;
        state.error = action.payload as string || 'Failed to save interaction';
      });
  },
});

export const {
  setFormField,
  updateFormState,
  addMaterialShared,
  removeMaterialShared,
  addSampleDistributed,
  removeSampleDistributed,
  resetForm,
  clearSaveSuccess
} = interactionSlice.actions;

export default interactionSlice.reducer;
