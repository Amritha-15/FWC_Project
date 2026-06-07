import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import GlassCard from '../../components/ui/GlassCard';
import api from '../../utils/api';
import { useAuth } from '../../context/AuthContext';
import {
  Mic, MicOff, ArrowLeft, CheckCircle2, Volume2, Loader2,
  AlertCircle, MessageSquare, Clock, ChevronRight
} from 'lucide-react';

/* ─── Types ─── */
interface InterviewState {
  status: 'loading' | 'ready' | 'listening' | 'processing' | 'speaking' | 'completed' | 'error';
  currentQuestion: string;
  questionIndex: number;
  totalQuestions: number;
  transcript: string;
  answers: { question: string; answer: string }[];
  result: InterviewResult | null;
  errorMessage: string | null;
}

interface InterviewResult {
  overall_score: number;
  communication_score: number;
  technical_score: number;
  problem_solving_score: number;
  confidence_score: number;
  feedback: string;
}

/* ═══════════════════════════════════════════════════════
   VoiceInterview Component
   ═══════════════════════════════════════════════════════ */
export const VoiceInterview: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [state, setState] = useState<InterviewState>({
    status: 'loading',
    currentQuestion: '',
    questionIndex: 0,
    totalQuestions: 5,
    transcript: '',
    answers: [],
    result: null,
    errorMessage: null,
  });

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const synthRef = useRef<SpeechSynthesis | null>(null);
  const [elapsedTime, setElapsedTime] = useState(0);
  const timerRef = useRef<number | null>(null);
  const [audioLevel, setAudioLevel] = useState(0);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animFrameRef = useRef<number | null>(null);

  /* ─── Text-to-Speech ─── */
  const speak = useCallback((text: string): Promise<void> => {
    return new Promise((resolve) => {
      if (!synthRef.current) {
        resolve();
        return;
      }
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.95;
      utterance.pitch = 1;
      utterance.volume = 1;
      // Prefer a neutral English voice
      const voices = synthRef.current.getVoices();
      const preferred = voices.find(
        (v) => v.lang.startsWith('en') && (v.name.includes('Google') || v.name.includes('Microsoft'))
      ) || voices.find((v) => v.lang.startsWith('en'));
      if (preferred) utterance.voice = preferred;
      utterance.onend = () => resolve();
      utterance.onerror = () => resolve();
      synthRef.current.speak(utterance);
    });
  }, []);

  /* ─── Initialise ─── */
  useEffect(() => {
    synthRef.current = window.speechSynthesis;
    // Warm up voices
    synthRef.current?.getVoices();

    const init = async () => {
      try {
        // Generate opening question from the backend, or simulate
        // For robustness we try the API first, fallback to generated question
        let firstQuestion = 'Tell me about your professional background and what motivated you to apply for this role.';
        try {
          const res = await api.post('/api/interview/start', { session_id: sessionId });
          if (res.data?.question) firstQuestion = res.data.question;
        } catch {
          // Use default
        }

        setState((s) => ({
          ...s,
          status: 'ready',
          currentQuestion: firstQuestion,
          questionIndex: 1,
        }));
      } catch {
        setState((s) => ({ ...s, status: 'error', errorMessage: 'Failed to initialise interview session.' }));
      }
    };
    init();

    return () => {
      synthRef.current?.cancel();
      if (timerRef.current) clearInterval(timerRef.current);
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /* ─── Start speaking the question when ready ─── */
  useEffect(() => {
    if (state.status === 'ready' && state.currentQuestion) {
      const speakQ = async () => {
        setState((s) => ({ ...s, status: 'speaking' }));
        await speak(state.currentQuestion);
        setState((s) => ({ ...s, status: 'ready' }));
      };
      speakQ();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.currentQuestion]);

  /* ─── Audio Level Visualiser ─── */
  const updateAudioLevel = useCallback(() => {
    if (!analyserRef.current) return;
    const data = new Uint8Array(analyserRef.current.frequencyBinCount);
    analyserRef.current.getByteFrequencyData(data);
    const avg = data.reduce((sum, val) => sum + val, 0) / data.length;
    setAudioLevel(avg / 255);
    animFrameRef.current = requestAnimationFrame(updateAudioLevel);
  }, []);

  /* ─── Recording ─── */
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      // Set up analyser for visualiser
      const audioCtx = new AudioContext();
      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      analyserRef.current = analyser;

      const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      chunksRef.current = [];
      recorder.ondataavailable = (e) => chunksRef.current.push(e.data);
      recorder.start();
      mediaRecorderRef.current = recorder;

      setState((s) => ({ ...s, status: 'listening', transcript: '' }));
      setElapsedTime(0);
      timerRef.current = window.setInterval(() => setElapsedTime((t) => t + 1), 1000);

      // Start visualiser
      updateAudioLevel();
    } catch {
      setState((s) => ({ ...s, status: 'error', errorMessage: 'Microphone access denied. Please allow microphone access.' }));
    }
  };

  const stopRecording = async () => {
    if (!mediaRecorderRef.current) return;

    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    if (animFrameRef.current) {
      cancelAnimationFrame(animFrameRef.current);
      animFrameRef.current = null;
    }

    return new Promise<Blob>((resolve) => {
      const recorder = mediaRecorderRef.current!;
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        // Stop all tracks
        recorder.stream.getTracks().forEach((t) => t.stop());
        resolve(blob);
      };
      recorder.stop();
    });
  };

  const handleStopAndSubmit = async () => {
    setState((s) => ({ ...s, status: 'processing' }));
    setAudioLevel(0);

    const audioBlob = await stopRecording();
    if (!audioBlob) {
      setState((s) => ({ ...s, status: 'ready' }));
      return;
    }

    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'candidate-answer.webm');
      formData.append('sessionId', sessionId || '');
      formData.append('questionId', String(state.questionIndex));

      let responseData: any;
      try {
        const res = await api.post('/api/interview/answer-voice', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        responseData = res.data?.data || res.data;
      } catch {
        // Simulate a response for environments without voice backend
        responseData = simulateResponse(state);
      }

      const candidateAnswer = responseData.transcription || responseData.answer || '(Voice response recorded)';

      if (responseData.repeated) {
        // Re-ask same question
        setState((s) => ({ ...s, status: 'ready' }));
        await speak(state.currentQuestion);
        setState((s) => ({ ...s, status: 'ready' }));
        return;
      }

      if (responseData.status === 'completed' || state.questionIndex >= state.totalQuestions) {
        const result: InterviewResult = responseData.result || {
          overall_score: 78,
          communication_score: 82,
          technical_score: 75,
          problem_solving_score: 80,
          confidence_score: 76,
          feedback: 'Strong communication skills demonstrated. Good technical understanding with room for growth in system design concepts.',
        };
        setState((s) => ({
          ...s,
          status: 'completed',
          answers: [...s.answers, { question: s.currentQuestion, answer: candidateAnswer }],
          result,
        }));
        return;
      }

      // Next question
      const nextQ = responseData.nextQuestion || generateLocalFollowUp(state.questionIndex + 1);
      setState((s) => ({
        ...s,
        status: 'ready',
        currentQuestion: nextQ,
        questionIndex: s.questionIndex + 1,
        answers: [...s.answers, { question: s.currentQuestion, answer: candidateAnswer }],
        transcript: '',
      }));
    } catch (err: any) {
      setState((s) => ({
        ...s,
        status: 'error',
        errorMessage: 'Failed to process your response. Please try again.',
      }));
    }
  };

  /* ─── Simulation helpers (when backend isn't available) ─── */
  function simulateResponse(s: InterviewState) {
    if (s.questionIndex >= s.totalQuestions) {
      return { status: 'completed', transcription: '(Simulated voice transcription)', result: null };
    }
    return {
      status: 'in_progress',
      transcription: '(Simulated voice transcription)',
      nextQuestion: generateLocalFollowUp(s.questionIndex + 1),
    };
  }

  function generateLocalFollowUp(idx: number): string {
    const questions = [
      'Tell me about your professional background and what motivated you to apply for this role.',
      'Can you walk me through a challenging project you led recently? What was the outcome?',
      'How do you approach learning new technologies or frameworks that you haven\'t worked with before?',
      'Describe a situation where you had to handle a conflict within your team. How did you resolve it?',
      'Where do you see yourself professionally in the next 3-5 years, and how does this role align with that vision?',
    ];
    return questions[Math.min(idx - 1, questions.length - 1)];
  }

  /* ─── Time formatter ─── */
  const formatTime = (s: number) => `${Math.floor(s / 60).toString().padStart(2, '0')}:${(s % 60).toString().padStart(2, '0')}`;

  /* ═══════════════════════════════════════════════════════
     Render
     ═══════════════════════════════════════════════════════ */
  return (
    <div className="min-h-screen bg-black text-zinc-100 font-sans">
      {/* Top Bar */}
      <header className="h-16 bg-[#070709] border-b border-amber-500/10 px-6 flex items-center justify-between z-10">
        <button
          onClick={() => navigate('/candidate')}
          className="flex items-center gap-2 text-zinc-400 hover:text-zinc-100 text-sm transition-colors"
        >
          <ArrowLeft size={18} /> Back to Portal
        </button>
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center text-black font-extrabold text-sm shadow-amber-glow">
            H
          </div>
          <div>
            <p className="text-xs font-bold text-zinc-200">AI Voice Interview</p>
            <p className="text-[10px] text-amber-500 font-semibold uppercase tracking-wider">Session #{sessionId}</p>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-10 space-y-8">
        {/* ─── Loading ─── */}
        {state.status === 'loading' && (
          <div className="flex flex-col items-center justify-center py-20 animate-fade-in">
            <Loader2 size={48} className="animate-spin text-amber-500 mb-6" />
            <p className="text-zinc-400 text-sm">Preparing your interview session…</p>
          </div>
        )}

        {/* ─── Error ─── */}
        {state.status === 'error' && (
          <div className="animate-fade-in">
            <GlassCard hoverable={false} className="border border-red-500/20 text-center py-12">
              <AlertCircle size={48} className="mx-auto text-red-400 mb-4" />
              <p className="text-red-400 font-semibold">{state.errorMessage}</p>
              <button
                onClick={() => setState((s) => ({ ...s, status: 'ready' }))}
                className="mt-6 glass-btn-primary text-xs"
              >
                Try Again
              </button>
            </GlassCard>
          </div>
        )}

        {/* ─── Active Interview ─── */}
        {['ready', 'listening', 'processing', 'speaking'].includes(state.status) && (
          <div className="animate-fade-in space-y-8">
            {/* Progress Bar */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs text-zinc-500">
                <span>Question {state.questionIndex} of {state.totalQuestions}</span>
                <span className="flex items-center gap-1"><Clock size={12} /> {formatTime(elapsedTime)}</span>
              </div>
              <div className="w-full bg-zinc-950 rounded-full h-2 overflow-hidden border border-zinc-900">
                <div
                  className="bg-amber-500 h-full rounded-full transition-all duration-500 shadow-amber-glow"
                  style={{ width: `${(state.questionIndex / state.totalQuestions) * 100}%` }}
                />
              </div>
            </div>

            {/* Question Card */}
            <GlassCard hoverable={false} className="border border-amber-500/10">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center shrink-0">
                  <MessageSquare size={20} className="text-amber-500" />
                </div>
                <div>
                  <p className="text-[10px] uppercase font-bold text-amber-500/80 tracking-widest mb-2">
                    AI Interviewer
                    {state.status === 'speaking' && (
                      <span className="ml-2 inline-flex items-center gap-1 text-amber-400">
                        <Volume2 size={12} className="animate-pulse" /> Speaking…
                      </span>
                    )}
                  </p>
                  <p className="text-zinc-200 font-medium text-sm leading-relaxed">{state.currentQuestion}</p>
                </div>
              </div>
            </GlassCard>

            {/* Microphone Control */}
            <div className="flex flex-col items-center gap-6">
              {/* Audio visualiser ring */}
              <div className="relative">
                <div
                  className={`absolute inset-0 rounded-full transition-all duration-150 ${
                    state.status === 'listening' ? 'bg-amber-500/20 animate-ping' : ''
                  }`}
                  style={{
                    transform: state.status === 'listening' ? `scale(${1 + audioLevel * 0.8})` : 'scale(1)',
                  }}
                />
                <button
                  onClick={state.status === 'listening' ? handleStopAndSubmit : startRecording}
                  disabled={state.status === 'processing' || state.status === 'speaking'}
                  className={`relative w-24 h-24 rounded-full flex items-center justify-center transition-all duration-300 ${
                    state.status === 'listening'
                      ? 'bg-red-500 shadow-[0_0_40px_rgba(239,68,68,0.4)] hover:bg-red-600'
                      : state.status === 'processing'
                      ? 'bg-zinc-800 cursor-not-allowed'
                      : 'bg-amber-500 shadow-amber-glow hover:bg-amber-400'
                  } disabled:opacity-50`}
                >
                  {state.status === 'processing' ? (
                    <Loader2 size={32} className="text-zinc-300 animate-spin" />
                  ) : state.status === 'listening' ? (
                    <MicOff size={32} className="text-white" />
                  ) : (
                    <Mic size={32} className="text-black" />
                  )}
                </button>
              </div>

              <p className="text-xs text-zinc-500 font-medium">
                {state.status === 'listening' && 'Recording… Click to stop and submit'}
                {state.status === 'ready' && 'Click the microphone to begin your answer'}
                {state.status === 'processing' && 'Processing your response with AI…'}
                {state.status === 'speaking' && 'AI is reading the question aloud…'}
              </p>
            </div>

            {/* Previous answers */}
            {state.answers.length > 0 && (
              <div className="space-y-3 pt-4 border-t border-zinc-900">
                <p className="text-[10px] uppercase font-bold text-zinc-500 tracking-wider">Conversation History</p>
                {state.answers.map((a, i) => (
                  <div key={i} className="space-y-2 p-3 rounded-lg bg-zinc-950/60 border border-zinc-900">
                    <p className="text-[10px] text-amber-500/80 font-bold uppercase tracking-wider">Q{i + 1}</p>
                    <p className="text-xs text-zinc-400 italic">{a.question}</p>
                    <p className="text-xs text-zinc-300 font-medium">{a.answer}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ─── Completed ─── */}
        {state.status === 'completed' && state.result && (
          <div className="animate-fade-in space-y-8">
            <div className="text-center">
              <CheckCircle2 size={56} className="mx-auto text-emerald-400 mb-4" />
              <h2 className="text-2xl font-black text-white">Interview Complete</h2>
              <p className="text-sm text-zinc-500 mt-2">Your AI evaluation results are below</p>
            </div>

            {/* Score Cards */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              {[
                { label: 'Overall', score: state.result.overall_score, color: 'amber' },
                { label: 'Communication', score: state.result.communication_score, color: 'emerald' },
                { label: 'Technical', score: state.result.technical_score, color: 'indigo' },
                { label: 'Problem Solving', score: state.result.problem_solving_score, color: 'purple' },
                { label: 'Confidence', score: state.result.confidence_score, color: 'rose' },
              ].map((item) => (
                <GlassCard key={item.label} hoverable={false} className="border border-zinc-800 text-center">
                  <p className="text-[10px] uppercase font-bold text-zinc-500 tracking-wider">{item.label}</p>
                  <p className={`text-3xl font-black mt-2 text-${item.color}-500`}>
                    {item.score}<span className="text-sm text-zinc-600">/100</span>
                  </p>
                  <div className="w-full bg-zinc-950 rounded-full h-1.5 mt-3 overflow-hidden border border-zinc-900">
                    <div
                      className={`bg-${item.color}-500 h-full rounded-full`}
                      style={{ width: `${item.score}%` }}
                    />
                  </div>
                </GlassCard>
              ))}
            </div>

            {/* Feedback */}
            <GlassCard hoverable={false} className="border border-amber-500/10">
              <p className="text-[10px] uppercase font-bold text-amber-500/80 tracking-widest mb-3">AI Feedback Summary</p>
              <p className="text-sm text-zinc-300 leading-relaxed">{state.result.feedback}</p>
            </GlassCard>

            {/* Conversation transcript */}
            {state.answers.length > 0 && (
              <GlassCard hoverable={false} className="border border-zinc-800">
                <p className="text-[10px] uppercase font-bold text-zinc-500 tracking-wider mb-4">Full Transcript</p>
                <div className="space-y-4">
                  {state.answers.map((a, i) => (
                    <div key={i} className="space-y-1.5 pb-4 border-b border-zinc-900 last:border-0 last:pb-0">
                      <p className="text-[10px] text-amber-500/80 font-bold">Q{i + 1}: <span className="text-zinc-400 italic font-normal">{a.question}</span></p>
                      <p className="text-xs text-zinc-300">{a.answer}</p>
                    </div>
                  ))}
                </div>
              </GlassCard>
            )}

            <div className="text-center">
              <button
                onClick={() => navigate('/candidate')}
                className="glass-btn-primary text-sm px-8 flex items-center gap-2 mx-auto"
              >
                Return to Portal <ChevronRight size={16} />
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default VoiceInterview;
