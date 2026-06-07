import React, { useState, useRef, useEffect, useCallback } from 'react';
import { X, Mic, MicOff, Type, Send, Loader2, CheckCircle, AlertCircle, ChevronRight } from 'lucide-react';
import api from '../../utils/api';

// ─── Types ────────────────────────────────────────────────────────────────────

type Mode = 'voice' | 'text';
type Stage = 'mode-select' | 'intro' | 'interview' | 'submitting' | 'done' | 'error';

interface TranscriptEntry {
    role: 'ai' | 'candidate';
    content: string;
    questionIndex?: number;
}

interface AIInterviewProps {
    applicationId: number;
    candidateName: string;
    jobTitle: string;
    onClose: () => void;
    onComplete?: () => void;
    /** Pass true when this application already has a completed interview result */
    interviewCompleted?: boolean;
}

// ─── Recording hook ───────────────────────────────────────────────────────────

function useAudioRecorder() {
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const chunksRef = useRef<Blob[]>([]);
    const [recording, setRecording] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const start = useCallback(async () => {
        try {
            // mediaDevices is undefined on non-secure (non-HTTPS / non-localhost) origins
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                setError(
                    'Microphone unavailable. This feature requires a secure connection. ' +
                    'Please open the app via https:// or http://localhost instead of an IP address.'
                );
                return;
            }
            // Use relaxed constraints — let the browser pick any available audio source
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: false,
                    noiseSuppression: false,
                    sampleRate: 16000,
                }
            }).catch(() =>
                // Fallback: bare minimum request, no constraints at all
                navigator.mediaDevices.getUserMedia({ audio: true })
            );
            // Pick the first mimeType this browser actually supports
            const MIME_TYPES = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/mp4'];
            const mimeType = MIME_TYPES.find(m => MediaRecorder.isTypeSupported(m)) || '';
            const mr = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
            chunksRef.current = [];
            mr.ondataavailable = e => { if (e.data.size > 0) chunksRef.current.push(e.data); };
            mr.start();
            mediaRecorderRef.current = mr;
            setRecording(true);
            setError(null);
        } catch (e: any) {
            if (e.name === 'NotAllowedError') {
                setError('Microphone access denied. Please allow microphone in your browser settings and try again.');
            } else if (e.name === 'NotFoundError') {
                setError('No microphone found. Please connect a microphone and try again.');
            } else if (e.name === 'NotSupportedError' || e.name === 'SecurityError') {
                setError(
                    'Microphone blocked: this feature requires HTTPS or localhost. ' +
                    'Open the app via http://localhost:PORT or ask your admin to enable HTTPS.'
                );
            } else if (e.name === 'NotReadableError' || (e.message || '').includes('Could not start audio')) {
                setError(
                    'Could not access microphone — it may be in use by another app (Zoom, Teams, etc.). ' +
                    'Close other apps using the mic and try again, or use Text mode.'
                );
            } else {
                setError(`Microphone error (${e.name}): ${e.message}. Close other apps using the mic, or switch to Text mode.`);
            }
        }
    }, []);

    const stop = useCallback((): Promise<Blob> => {
        return new Promise(resolve => {
            const mr = mediaRecorderRef.current;
            if (!mr) { resolve(new Blob()); return; }
            mr.onstop = () => {
                // Use the actual mimeType the recorder was created with
                const mimeType = mr.mimeType || 'audio/webm';
                const blob = new Blob(chunksRef.current, { type: mimeType });
                mr.stream.getTracks().forEach(t => t.stop());
                resolve(blob);
            };
            mr.stop();
            setRecording(false);
        });
    }, []);

    return { recording, error, start, stop };
}

// ─── Component ────────────────────────────────────────────────────────────────

const AIInterview: React.FC<AIInterviewProps> = ({
    applicationId, candidateName, jobTitle, onClose, onComplete, interviewCompleted
}) => {
    const [mode, setMode] = useState<Mode>('text');
    // If the interview was already completed before this modal opened, jump straight to done
    const [stage, setStage] = useState<Stage>(interviewCompleted ? 'done' : 'mode-select');
    const [questions, setQuestions] = useState<string[]>([]);
    const [currentQ, setCurrentQ] = useState(0);
    const [transcript, setTranscript] = useState<TranscriptEntry[]>([]);
    const [textAnswer, setTextAnswer] = useState('');
    const [statusMsg, setStatusMsg] = useState('');
    const [loading, setLoading] = useState(false);
    const [scores, setScores] = useState<any>(null);
    const [transcribing, setTranscribing] = useState(false);

    const { recording, error: micError, start: startRec, stop: stopRec } = useAudioRecorder();
    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [transcript, stage]);

    // ── Fetch questions ──────────────────────────────────────────────────────────
    const loadQuestions = async () => {
        setLoading(true);
        setStatusMsg('AI is reading your resume and preparing questions…');
        try {
            const res = await api.post('/api/ai/generate-questions', { application_id: applicationId });
            setQuestions(res.data.questions);
            setStage('intro');
        } catch (e: any) {
            setStage('error');
            setStatusMsg('Failed to generate questions. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    // ── Start interview ──────────────────────────────────────────────────────────
    const startInterview = () => {
        setStage('interview');
        setTranscript([{ role: 'ai', content: questions[0], questionIndex: 0 }]);
    };

    // ── Submit text answer ───────────────────────────────────────────────────────
    const submitTextAnswer = async () => {
        if (!textAnswer.trim()) return;
        const answer = textAnswer.trim();
        setTextAnswer('');
        await processAnswer(answer);
    };

    // ── Voice: stop and transcribe ───────────────────────────────────────────────
    const stopAndTranscribe = async () => {
        const blob = await stopRec();
        setTranscribing(true);
        setStatusMsg('Transcribing your answer…');
        try {
            const formData = new FormData();
            // Use the correct extension for the blob's actual mimeType
            const ext = blob.type.includes('ogg') ? 'ogg' : blob.type.includes('mp4') ? 'mp4' : 'webm';
            formData.append('audio', blob, `answer.${ext}`);
            const res = await api.post('/api/ai/transcribe', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });
            const text = res.data.transcript || '';
            if (!text.trim()) {
                setStatusMsg('Could not hear anything. Please try again.');
                return;
            }
            await processAnswer(text);
        } catch (e: any) {
            setStatusMsg('Transcription failed. Please try again or switch to text mode.');
        } finally {
            setTranscribing(false);
            setStatusMsg('');
        }
    };

    // ── Process answer & advance ─────────────────────────────────────────────────
    const processAnswer = async (answer: string) => {
        const newTranscript: TranscriptEntry[] = [
            ...transcript,
            { role: 'candidate', content: answer, questionIndex: currentQ },
        ];

        const nextQ = currentQ + 1;
        if (nextQ < questions.length) {
            newTranscript.push({ role: 'ai', content: questions[nextQ], questionIndex: nextQ });
            setTranscript(newTranscript);
            setCurrentQ(nextQ);
        } else {
            setTranscript(newTranscript);
            await submitInterview(newTranscript);
        }
    };

    // ── Submit full transcript for evaluation ────────────────────────────────────
    const submitInterview = async (fullTranscript: TranscriptEntry[]) => {
        setStage('submitting');
        setStatusMsg('AI is evaluating your interview…');
        try {
            const payload = fullTranscript.map(t => ({
                role: t.role === 'ai' ? 'assistant' : 'user',
                content: t.content,
            }));
            const res = await api.post('/api/ai/evaluate-interview', {
                application_id: applicationId,
                transcript: payload,
            });
            setScores(res.data?.interview || res.data);
            setStage('done');
            if (onComplete) onComplete();
        } catch (e: any) {
            setStage('error');
            setStatusMsg('Failed to evaluate interview. Your answers were recorded.');
        }
    };

    // ─── Renders ─────────────────────────────────────────────────────────────────

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
            style={{ background: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(6px)' }}
            onClick={onClose}
        >
            <div
                className="relative w-full max-w-2xl rounded-2xl overflow-hidden flex flex-col"
                style={{
                    background: 'linear-gradient(145deg, #0f0f14 0%, #141420 100%)',
                    border: '1px solid rgba(255,255,255,0.06)',
                    maxHeight: '90vh',
                    boxShadow: '0 25px 80px rgba(0,0,0,0.8), 0 0 0 1px rgba(99,102,241,0.1)',
                }}
                onClick={e => e.stopPropagation()}
            >
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-white/5">
                    <div>
                        <p className="text-xs text-indigo-400 font-bold uppercase tracking-widest mb-0.5">AI Interview</p>
                        <h3 className="text-white font-bold text-base">{candidateName} · {jobTitle}</h3>
                    </div>
                    <button onClick={onClose} className="text-zinc-500 hover:text-white transition-colors p-1">
                        <X size={18} />
                    </button>
                </div>

                {/* Body */}
                <div className="flex-1 overflow-y-auto">

                    {/* ── Mode Select ── */}
                    {stage === 'mode-select' && (
                        <div className="p-8 flex flex-col items-center justify-center gap-6 min-h-[320px]">
                            <div className="text-center">
                                <p className="text-2xl font-bold text-white mb-2">Ready for your AI Interview?</p>
                                <p className="text-sm text-zinc-400">The AI will ask 3 questions based on your resume. Choose how you'd like to answer.</p>
                            </div>
                            <div className="grid grid-cols-2 gap-4 w-full max-w-sm">
                                {/* Voice */}
                                <button
                                    onClick={() => { setMode('voice'); loadQuestions(); }}
                                    className="group flex flex-col items-center gap-3 p-6 rounded-xl border transition-all"
                                    style={{ background: 'rgba(99,102,241,0.06)', borderColor: 'rgba(99,102,241,0.2)' }}
                                    onMouseEnter={e => (e.currentTarget.style.borderColor = 'rgba(99,102,241,0.5)')}
                                    onMouseLeave={e => (e.currentTarget.style.borderColor = 'rgba(99,102,241,0.2)')}
                                >
                                    <div className="w-12 h-12 rounded-full flex items-center justify-center" style={{ background: 'rgba(99,102,241,0.15)' }}>
                                        <Mic size={22} className="text-indigo-400" />
                                    </div>
                                    <div className="text-center">
                                        <p className="text-white font-bold text-sm">Voice</p>
                                        <p className="text-zinc-500 text-xs mt-0.5">Speak your answers</p>
                                    </div>
                                </button>

                                {/* Text */}
                                <button
                                    onClick={() => { setMode('text'); loadQuestions(); }}
                                    className="group flex flex-col items-center gap-3 p-6 rounded-xl border transition-all"
                                    style={{ background: 'rgba(16,185,129,0.06)', borderColor: 'rgba(16,185,129,0.2)' }}
                                    onMouseEnter={e => (e.currentTarget.style.borderColor = 'rgba(16,185,129,0.5)')}
                                    onMouseLeave={e => (e.currentTarget.style.borderColor = 'rgba(16,185,129,0.2)')}
                                >
                                    <div className="w-12 h-12 rounded-full flex items-center justify-center" style={{ background: 'rgba(16,185,129,0.12)' }}>
                                        <Type size={22} className="text-emerald-400" />
                                    </div>
                                    <div className="text-center">
                                        <p className="text-white font-bold text-sm">Text</p>
                                        <p className="text-zinc-500 text-xs mt-0.5">Type your answers</p>
                                    </div>
                                </button>
                            </div>
                        </div>
                    )}

                    {/* ── Loading overlay ── */}
                    {stage === 'mode-select' && loading && (
                        <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-black/60 backdrop-blur-sm">
                            <Loader2 size={28} className="animate-spin text-indigo-400" />
                            <p className="text-sm text-zinc-300">{statusMsg}</p>
                        </div>
                    )}

                    {/* ── Intro ── */}
                    {stage === 'intro' && (
                        <div className="p-8 flex flex-col gap-5">
                            <div>
                                <p className="text-white font-bold text-lg mb-1">Interview prepared ✓</p>
                                <p className="text-zinc-400 text-sm">
                                    {mode === 'voice'
                                        ? "You'll speak your answers. Press the mic button to record, then stop when done."
                                        : 'Type your answers and press Send or hit Enter.'}
                                    {' '}Take your time — there's no time limit per question.
                                </p>
                            </div>
                            <div className="space-y-3">
                                <p className="text-xs text-zinc-500 uppercase font-bold tracking-wider">Your 3 questions</p>
                                {questions.map((q, i) => (
                                    <div key={i} className="flex gap-3 p-3 rounded-lg" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)' }}>
                                        <span className="text-indigo-400 font-black text-sm min-w-[20px]">Q{i + 1}</span>
                                        <p className="text-zinc-300 text-sm">{q}</p>
                                    </div>
                                ))}
                            </div>
                            <button
                                onClick={startInterview}
                                className="flex items-center justify-center gap-2 py-3 px-6 rounded-xl font-bold text-sm transition-all"
                                style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', color: 'white' }}
                            >
                                Start Interview <ChevronRight size={16} />
                            </button>
                        </div>
                    )}

                    {/* ── Interview ── */}
                    {stage === 'interview' && (
                        <div className="flex flex-col h-full">
                            {/* Progress */}
                            <div className="px-6 pt-4 pb-2">
                                <div className="flex items-center justify-between mb-1.5">
                                    <p className="text-xs text-zinc-500">Question {currentQ + 1} of {questions.length}</p>
                                    <p className="text-xs text-zinc-500">{mode === 'voice' ? '🎤 Voice mode' : '⌨️ Text mode'}</p>
                                </div>
                                <div className="h-1 rounded-full bg-white/5 overflow-hidden">
                                    <div
                                        className="h-full rounded-full transition-all duration-500"
                                        style={{ width: `${(currentQ / questions.length) * 100}%`, background: 'linear-gradient(90deg, #6366f1, #8b5cf6)' }}
                                    />
                                </div>
                            </div>

                            {/* Chat transcript */}
                            <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4" style={{ minHeight: '240px', maxHeight: '360px' }}>
                                {transcript.map((entry, idx) => (
                                    <div key={idx} className={`flex ${entry.role === 'candidate' ? 'justify-end' : 'justify-start'}`}>
                                        {entry.role === 'ai' && (
                                            <div className="flex gap-2 max-w-[85%]">
                                                <div className="w-7 h-7 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-bold mt-0.5"
                                                    style={{ background: 'rgba(99,102,241,0.2)', color: '#a5b4fc' }}>AI</div>
                                                <div className="px-4 py-3 rounded-2xl rounded-tl-sm text-sm text-zinc-200 leading-relaxed"
                                                    style={{ background: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.15)' }}>
                                                    {entry.content}
                                                </div>
                                            </div>
                                        )}
                                        {entry.role === 'candidate' && (
                                            <div className="max-w-[85%] px-4 py-3 rounded-2xl rounded-tr-sm text-sm text-white leading-relaxed"
                                                style={{ background: 'rgba(16,185,129,0.15)', border: '1px solid rgba(16,185,129,0.2)' }}>
                                                {entry.content}
                                            </div>
                                        )}
                                    </div>
                                ))}

                                {(transcribing || statusMsg) && (
                                    <div className="flex justify-center">
                                        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs text-zinc-400"
                                            style={{ background: 'rgba(255,255,255,0.05)' }}>
                                            {transcribing && <Loader2 size={12} className="animate-spin" />}
                                            {statusMsg || 'Transcribing…'}
                                        </div>
                                    </div>
                                )}

                                {micError && (
                                    <div className="flex items-center gap-2 text-xs text-red-400 px-2">
                                        <AlertCircle size={12} /> {micError}
                                    </div>
                                )}

                                <div ref={bottomRef} />
                            </div>

                            {/* Input area */}
                            <div className="px-6 pb-6 pt-2 border-t border-white/5">
                                {mode === 'text' ? (
                                    <div className="flex gap-2">
                                        <textarea
                                            className="flex-1 rounded-xl px-4 py-3 text-sm text-white resize-none focus:outline-none focus:ring-1"
                                            style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)', minHeight: '72px' }}
                                            placeholder="Type your answer here…"
                                            value={textAnswer}
                                            onChange={e => setTextAnswer(e.target.value)}
                                            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submitTextAnswer(); } }}
                                        />
                                        <button
                                            onClick={submitTextAnswer}
                                            disabled={!textAnswer.trim()}
                                            className="self-end p-3 rounded-xl transition-all disabled:opacity-30"
                                            style={{ background: 'rgba(99,102,241,0.2)', color: '#a5b4fc' }}
                                        >
                                            <Send size={18} />
                                        </button>
                                    </div>
                                ) : (
                                    <div className="flex flex-col items-center gap-3">
                                        {!recording && !transcribing && (
                                            <button
                                                onClick={startRec}
                                                className="flex items-center gap-2 px-6 py-3 rounded-xl font-bold text-sm transition-all"
                                                style={{ background: 'rgba(99,102,241,0.15)', border: '1px solid rgba(99,102,241,0.3)', color: '#a5b4fc' }}
                                            >
                                                <Mic size={16} /> Start Recording
                                            </button>
                                        )}
                                        {recording && (
                                            <button
                                                onClick={stopAndTranscribe}
                                                className="flex items-center gap-2 px-6 py-3 rounded-xl font-bold text-sm animate-pulse"
                                                style={{ background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.4)', color: '#fca5a5' }}
                                            >
                                                <MicOff size={16} /> Stop Recording
                                            </button>
                                        )}
                                        {transcribing && (
                                            <div className="flex items-center gap-2 text-sm text-zinc-400">
                                                <Loader2 size={14} className="animate-spin" /> Transcribing with Whisper…
                                            </div>
                                        )}
                                        <p className="text-xs text-zinc-600">Press Stop when you finish your answer</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* ── Submitting ── */}
                    {stage === 'submitting' && (
                        <div className="flex flex-col items-center justify-center gap-4 p-10 min-h-[280px]">
                            <Loader2 size={36} className="animate-spin text-indigo-400" />
                            <p className="text-white font-bold">Evaluating your interview…</p>
                            <p className="text-zinc-500 text-sm text-center">AI is analysing your answers against the job requirements. This takes about 10 seconds.</p>
                        </div>
                    )}

                    {/* ── Done ── */}
                    {stage === 'done' && (
                        <div className="p-8 flex flex-col gap-6">
                            <div className="flex items-center gap-3">
                                <CheckCircle size={24} className="text-emerald-400 flex-shrink-0" />
                                <div>
                                    <p className="text-white font-bold text-lg">
                                        {interviewCompleted && !scores ? 'Interview Already Completed' : 'Interview Complete!'}
                                    </p>
                                    <p className="text-zinc-400 text-sm">
                                        {interviewCompleted && !scores
                                            ? 'You have already submitted your interview. HR is reviewing your results.'
                                            : 'Your results have been sent to HR for review.'}
                                    </p>
                                </div>
                            </div>

                            {scores && (
                                <div className="grid grid-cols-2 gap-3">
                                    {[
                                        { label: 'Overall', value: scores.overall_score, color: '#a5b4fc' },
                                        { label: 'Communication', value: scores.communication_score, color: '#6ee7b7' },
                                        { label: 'Technical', value: scores.technical_score, color: '#fcd34d' },
                                        { label: 'Problem Solving', value: scores.problem_solving_score, color: '#f9a8d4' },
                                    ].map(s => (
                                        <div key={s.label} className="p-4 rounded-xl text-center"
                                            style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
                                            <p className="text-2xl font-black" style={{ color: s.color }}>
                                                {s.value !== undefined && s.value !== null ? Number(s.value).toFixed(1) : '—'}
                                            </p>
                                            <p className="text-[10px] text-zinc-500 uppercase font-bold mt-1">{s.label}</p>
                                        </div>
                                    ))}
                                </div>
                            )}

                            {scores?.ai_feedback && (
                                <div className="p-4 rounded-xl text-sm text-zinc-300 leading-relaxed"
                                    style={{ background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.15)' }}>
                                    <p className="text-xs text-indigo-400 font-bold uppercase mb-2">AI Feedback</p>
                                    {scores.ai_feedback}
                                </div>
                            )}

                            <button
                                onClick={onClose}
                                className="py-3 px-6 rounded-xl font-bold text-sm text-white transition-all"
                                style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }}
                            >
                                Close
                            </button>
                        </div>
                    )}

                    {/* ── Error ── */}
                    {stage === 'error' && (
                        <div className="flex flex-col items-center justify-center gap-4 p-10 min-h-[280px]">
                            <AlertCircle size={36} className="text-red-400" />
                            <p className="text-white font-bold">Something went wrong</p>
                            <p className="text-zinc-400 text-sm text-center">{statusMsg}</p>
                            <button
                                onClick={() => setStage('mode-select')}
                                className="px-5 py-2 rounded-xl text-sm font-bold text-white"
                                style={{ background: 'rgba(99,102,241,0.2)', border: '1px solid rgba(99,102,241,0.3)' }}
                            >
                                Try Again
                            </button>
                        </div>
                    )}

                </div>
            </div>
        </div>
    );
};

export default AIInterview;