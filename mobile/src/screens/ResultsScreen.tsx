import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

// Placeholder shape until the pipeline API is wired up (see pipeline/main.py
// and pipeline/datatypes.py CoachingResult). Matches the pipeline's output
// so swapping the mock for a real fetch is a one-line change.
export type CoachingFault = {
  featureName: string;
  severity: number;
  explanation: string;
};

export type CoachingResult = {
  summary: string;
  faults: CoachingFault[];
  drill: string;
};

export default function ResultsScreen({
  result,
  onAnalyzeAnother,
}: {
  result: CoachingResult | null;
  onAnalyzeAnother: () => void;
}) {
  if (!result) {
    return (
      <View style={styles.container}>
        <Text style={styles.summary}>Analyzing your shot...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.summary}>{result.summary}</Text>

      {result.faults.length === 0 ? (
        <Text style={styles.clean}>Nothing stands out here — clean shot.</Text>
      ) : (
        result.faults.map((fault) => (
          <View key={fault.featureName} style={styles.faultCard}>
            <Text style={styles.faultName}>{fault.featureName.replace(/_/g, ' ')}</Text>
            <Text style={styles.faultExplanation}>{fault.explanation}</Text>
          </View>
        ))
      )}

      {result.drill ? (
        <View style={styles.drillCard}>
          <Text style={styles.drillLabel}>Drill</Text>
          <Text style={styles.drillText}>{result.drill}</Text>
        </View>
      ) : null}

      <TouchableOpacity style={styles.button} onPress={onAnalyzeAnother}>
        <Text style={styles.buttonText}>Analyze another shot</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  content: {
    padding: 20,
    gap: 16,
  },
  summary: {
    fontSize: 18,
    fontWeight: '600',
  },
  clean: {
    fontSize: 15,
    color: '#2a9d8f',
  },
  faultCard: {
    padding: 12,
    borderRadius: 8,
    backgroundColor: '#f4f4f4',
  },
  faultName: {
    fontSize: 15,
    fontWeight: '600',
    textTransform: 'capitalize',
  },
  faultExplanation: {
    fontSize: 14,
    color: '#444',
    marginTop: 4,
  },
  drillCard: {
    padding: 12,
    borderRadius: 8,
    backgroundColor: '#fff3cd',
  },
  drillLabel: {
    fontSize: 13,
    fontWeight: '700',
    color: '#856404',
  },
  drillText: {
    fontSize: 14,
    color: '#856404',
    marginTop: 4,
  },
  button: {
    marginTop: 8,
    paddingVertical: 14,
    borderRadius: 32,
    backgroundColor: '#e63946',
    alignItems: 'center',
  },
  buttonText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 16,
  },
});
