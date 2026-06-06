"use client";

import { useRef, useState, useCallback, useEffect } from "react";
import { Mic, Square } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAppStore } from "@/lib/store";

type VoiceButtonProps = {
  onAudioReady: (blob: Blob) => void;
  disabled?: boolean;
};

export function VoiceButton({ onAudioReady, disabled }: VoiceButtonProps) {
  const { settings } = useAppStore();
  const isArabic = settings.language === "ar";

  const [isRecording, setIsRecording] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [volumeLevel, setVolumeLevel] = useState(0);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const rafRef = useRef<number>(0);

  const MAX_DURATION = 30;

  const updateVolume = useCallback(() => {
    if (!analyserRef.current) return;
    const data = new Uint8Array(analyserRef.current.frequencyBinCount);
    analyserRef.current.getByteTimeDomainData(data);
    let sum = 0;
    for (let i = 0; i < data.length; i++) {
      const value = (data[i] - 128) / 128;
      sum += value * value;
    }
    const rms = Math.sqrt(sum / data.length);
    setVolumeLevel(Math.min(rms * 3, 1));
    rafRef.current = requestAnimationFrame(updateVolume);
  }, []);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });
      streamRef.current = stream;

      const audioContext = new AudioContext();
      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      analyserRef.current = analyser;

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
          ? "audio/webm;codecs=opus"
          : "audio/webm",
      });
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        onAudioReady(blob);
      };

      mediaRecorder.start(250);
      setIsRecording(true);
      setRecordingDuration(0);

      // Volume meter
      rafRef.current = requestAnimationFrame(updateVolume);

      // Timer
      timerRef.current = setInterval(() => {
        setRecordingDuration((prev) => {
          if (prev >= MAX_DURATION - 1) {
            stopRecording();
            return MAX_DURATION;
          }
          return prev + 1;
        });
      }, 1000);
    } catch (err) {
      console.error("Voice: mic access denied", err);
    }
  }, [onAudioReady, updateVolume]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
    }
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    if (rafRef.current) {
      cancelAnimationFrame(rafRef.current);
    }
    analyserRef.current = null;
    setIsRecording(false);
    setVolumeLevel(0);
  }, []);

  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
      }
      if (timerRef.current) clearInterval(timerRef.current);
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, []);

  const handlePointerDown = (e: React.PointerEvent) => {
    e.preventDefault();
    if (disabled || isRecording) return;
    startRecording();
  };

  const handlePointerUp = (e: React.PointerEvent) => {
    e.preventDefault();
    if (!isRecording) return;
    stopRecording();
  };

  const handlePointerLeave = (e: React.PointerEvent) => {
    if (!isRecording) return;
    stopRecording();
  };

  const progress = MAX_DURATION > 0 ? recordingDuration / MAX_DURATION : 0;
  const ringColor = progress > 0.8
    ? "stroke-destructive"
    : progress > 0.5
      ? "stroke-yellow-500"
      : "stroke-primary";

  return (
    <div className="relative shrink-0">
      {/* Recording ring */}
      <svg
        className={cn(
          "absolute -inset-1.5 -rotate-90 transition-opacity",
          isRecording ? "opacity-100" : "opacity-0"
        )}
        viewBox="0 0 48 48"
        width="48"
        height="48"
      >
        <circle
          cx="24"
          cy="24"
          r="20"
          fill="none"
          stroke="currentColor"
          strokeWidth="3"
          className="text-muted stroke-muted-foreground/20"
        />
        <circle
          cx="24"
          cy="24"
          r="20"
          fill="none"
          strokeWidth="3"
          strokeLinecap="round"
          className={cn("transition-all duration-300", ringColor)}
          strokeDasharray={`${2 * Math.PI * 20}`}
          strokeDashoffset={`${2 * Math.PI * 20 * (1 - progress)}`}
        />
      </svg>

      {/* Volume ripple */}
      {isRecording && (
        <span
          className="absolute inset-0 rounded-full bg-primary/20 animate-ping"
          style={{
            transform: `scale(${1 + volumeLevel * 0.5})`,
            opacity: 0.3 + volumeLevel * 0.4,
          }}
        />
      )}

      <button
        onPointerDown={handlePointerDown}
        onPointerUp={handlePointerUp}
        onPointerLeave={handlePointerLeave}
        disabled={disabled}
        className={cn(
          "relative z-10 h-11 w-11 rounded-xl flex items-center justify-center transition-all select-none",
          isRecording
            ? "bg-destructive text-white shadow-lg shadow-destructive/30 scale-110"
            : "bg-muted/50 text-muted-foreground hover:text-primary hover:bg-muted border border-border",
          disabled && "opacity-50 cursor-not-allowed"
        )}
        title={isArabic ? (isRecording ? `${recordingDuration}s` : "اضغط للتسجيل") : isRecording ? `${recordingDuration}s` : "Press to record"}
      >
        {isRecording ? (
          <Square className="h-4 w-4" fill="currentColor" />
        ) : (
          <Mic className="h-4 w-4" />
        )}
      </button>

      {/* Duration tooltip */}
      {isRecording && (
        <span className="absolute -top-7 left-1/2 -translate-x-1/2 text-[10px] font-mono text-destructive bg-destructive/10 px-1.5 py-0.5 rounded">
          {recordingDuration}s
        </span>
      )}
    </div>
  );
}
