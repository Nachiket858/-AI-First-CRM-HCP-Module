import { configureStore } from '@reduxjs/toolkit';
import interactionReducer from './slices/interactionSlice';
import chatReducer from './slices/chatSlice';

export const store = configureStore({
  reducer: {
    interaction: interactionReducer,
    chat: chatReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
