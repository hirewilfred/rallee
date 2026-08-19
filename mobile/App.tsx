import { useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaView, StyleSheet } from 'react-native';

import CaptureScreen from './src/screens/CaptureScreen';
import ResultsScreen, { CoachingResult } from './src/screens/ResultsScreen';

type Screen = 'capture' | 'results';

export default function App() {
  const [screen, setScreen] = useState<Screen>('capture');
  const [result, setResult] = useState<CoachingResult | null>(null);

  const handleClipCaptured = async (uri: string) => {
    setScreen('results');
    setResult(null);
    // TODO: upload `uri` to Supabase storage, trigger the pipeline
    // (pipeline/main.py), and set the real CoachingResult once the
    // backend endpoint exists. See docs/build-plan.md Phase 2.
    console.log('Clip captured:', uri);
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="light" />
      {screen === 'capture' ? (
        <CaptureScreen onClipCaptured={handleClipCaptured} />
      ) : (
        <ResultsScreen
          result={result}
          onAnalyzeAnother={() => {
            setResult(null);
            setScreen('capture');
          }}
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
});
