import { useRef, useState } from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';

// Matches the reference-corpus filming rig (see docs/build-plan.md, Phase 1a):
// side-on, ~1.1m camera height, ~4m from the contact point. An amateur clip
// shot at a wildly different angle/distance can't be compared fairly against
// shots normalized from that rig, so we guide the player toward the same
// framing rather than trying to correct for it after the fact.
const FRAMING_GUIDE_TEXT =
  'Stand side-on to the camera. Phone at chest height, about 4m back — ' +
  'line your whole body up inside the frame.';

type CaptureState = 'idle' | 'recording' | 'reviewing';

export default function CaptureScreen({
  onClipCaptured,
}: {
  onClipCaptured: (uri: string) => void;
}) {
  const [permission, requestPermission] = useCameraPermissions();
  const [state, setState] = useState<CaptureState>('idle');
  const cameraRef = useRef<CameraView>(null);

  if (!permission) {
    return <View style={styles.container} />;
  }

  if (!permission.granted) {
    return (
      <View style={styles.container}>
        <Text style={styles.guideText}>
          DinkIQ needs camera access to record your shot.
        </Text>
        <TouchableOpacity style={styles.recordButton} onPress={requestPermission}>
          <Text style={styles.recordButtonText}>Grant access</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const startRecording = async () => {
    if (!cameraRef.current) return;
    setState('recording');
    try {
      const video = await cameraRef.current.recordAsync({ maxDuration: 8 });
      if (video?.uri) {
        setState('reviewing');
        onClipCaptured(video.uri);
      } else {
        setState('idle');
      }
    } catch (err) {
      console.error('Recording failed', err);
      setState('idle');
    }
  };

  const stopRecording = () => {
    cameraRef.current?.stopRecording();
  };

  return (
    <View style={styles.container}>
      <CameraView
        ref={cameraRef}
        style={StyleSheet.absoluteFill}
        facing="back"
        mode="video"
        videoQuality="1080p"
      />

      {/* Framing overlay: reject bad clips at capture, not after. */}
      <View pointerEvents="none" style={styles.overlay}>
        <View style={styles.silhouetteBox} />
      </View>

      <View style={styles.guideBar}>
        <Text style={styles.guideText}>{FRAMING_GUIDE_TEXT}</Text>
      </View>

      <View style={styles.controls}>
        <TouchableOpacity
          style={[styles.recordButton, state === 'recording' && styles.recordButtonActive]}
          onPress={state === 'recording' ? stopRecording : startRecording}
        >
          <Text
            style={[styles.recordButtonText, state === 'recording' && styles.recordButtonTextActive]}
          >
            {state === 'recording' ? 'Stop' : 'Record shot'}
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  overlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    alignItems: 'center',
    justifyContent: 'center',
  },
  silhouetteBox: {
    width: '55%',
    height: '80%',
    borderWidth: 2,
    borderColor: 'rgba(255,255,255,0.6)',
    borderStyle: 'dashed',
    borderRadius: 12,
  },
  guideBar: {
    position: 'absolute',
    top: 60,
    left: 16,
    right: 16,
    padding: 12,
    borderRadius: 8,
    backgroundColor: 'rgba(0,0,0,0.6)',
  },
  guideText: {
    color: '#fff',
    textAlign: 'center',
    fontSize: 14,
  },
  controls: {
    position: 'absolute',
    bottom: 48,
    left: 0,
    right: 0,
    alignItems: 'center',
  },
  recordButton: {
    paddingVertical: 14,
    paddingHorizontal: 32,
    borderRadius: 32,
    backgroundColor: '#e63946',
  },
  recordButtonActive: {
    backgroundColor: '#fff',
  },
  recordButtonText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 16,
  },
  recordButtonTextActive: {
    color: '#e63946',
  },
});
