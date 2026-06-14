# Adam Prism Mobile (React Native + Expo)

[PHASE3] Native mobile client for Adam Prism using React Native + Expo.

## Features
- ✅ Cross-platform (iOS + Android)
- ✅ Secure token storage (expo-secure-store)
- ✅ JWT auth with backend
- ✅ Chat with streaming-ready architecture
- ✅ Offline-first (zustand state management)
- ✅ TypeScript throughout

## Quick Start

### Prerequisites
- Node.js 18+
- iOS Simulator (macOS) or Android Emulator
- Expo Go app on your phone (for quick testing)

### Setup
```bash
cd frontend/mobile-app-expo
npm install
npx expo start
```

Then:
- Press `i` for iOS simulator
- Press `a` for Android emulator
- Scan QR code with Expo Go app on your phone

### Configuration

Set the API URL in `.env`:
```bash
EXPO_PUBLIC_API_URL=http://your-server:8000
```

For local development with the API running locally:
- **iOS Simulator:** Use `http://localhost:8000`
- **Android Emulator:** Use `http://10.0.2.2:8000` (special IP for host)
- **Physical device:** Use your machine's LAN IP (e.g., `http://192.168.1.100:8000`)

## Building for Production

### Android (APK/AAB)
```bash
npm install -g eas-cli
eas build --platform android
```

### iOS (IPA)
```bash
eas build --platform ios
```

### Over-the-Air Updates
```bash
eas update --branch production
```

## Architecture

```
src/
├── lib/              # API client, auth store, state management
│   ├── api.ts        # HTTP client with retry logic
│   ├── auth.ts       # Auth state with secure token storage
│   └── chat.ts       # Chat state management
├── screens/          # Top-level screens
│   ├── ChatScreen.tsx
│   └── LoginScreen.tsx
├── components/       # Reusable UI components
└── App.tsx           # Entry point with auth routing
```

## Tech Stack
- **Expo 52** - React Native framework
- **TypeScript** - Type safety
- **Zustand** - State management
- **Expo Router** - File-based routing (ready to add)
- **TanStack Query** - Server state (ready to add)
- **expo-secure-store** - Encrypted token storage
- **MMKV** - Fast local storage (ready to add)
