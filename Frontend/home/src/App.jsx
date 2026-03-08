import React, { useEffect, useRef, useState } from 'react';
import { motion, useScroll, useSpring, useTransform, useInView, AnimatePresence } from 'framer-motion';
import { Plane, Bird, Zap, Target, Terminal as TerminalIcon, Copy, ChevronRight, Activity, ShieldAlert } from 'lucide-react';

// --- Custom Graphics (Created based on Process) ---

const DiscoveryGraphic = () => (
    <div className="relative w-full h-[300px] flex items-center justify-center">
        <svg viewBox="0 0 200 100" className="w-full max-w-md drop-shadow-[0_0_15px_rgba(255,255,255,0.2)]">
            <motion.path
                d="M20,50 L100,20 L180,50 L100,80 Z"
                fill="none" stroke="white" strokeWidth="0.5"
                initial={{ pathLength: 0, opacity: 0 }}
                animate={{ pathLength: 1, opacity: 0.3 }}
                transition={{ duration: 2, repeat: Infinity }}
            />
            <motion.path
                d="M100,20 L100,80 M20,50 L180,50"
                fill="none" stroke="white" strokeWidth="0.2"
                initial={{ opacity: 0 }}
                animate={{ opacity: 0.1 }}
            />
            {/* Scanning Line */}
            <motion.rect
                x="20" y="20" width="1" height="60" fill="#FF0000"
                animate={{ x: [20, 180, 20] }}
                transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                className="opacity-50"
            />
        </svg>
        <div className="absolute inset-0 bg-gradient-to-t from-background via-transparent to-background pointer-events-none" />
    </div>
);

const InputGenGraphic = () => (
    <div className="relative w-full h-[300px] flex items-center justify-center">
        <div className="grid grid-cols-6 gap-2 opacity-20">
            {[...Array(24)].map((_, i) => (
                <motion.div
                    key={i}
                    initial={{ scale: 0, opacity: 0 }}
                    whileInView={{ scale: 1, opacity: 1 }}
                    animate={{
                        backgroundColor: i % 3 === 0 ? "#FF0000" : "#FFFFFF",
                        opacity: [0.2, 0.5, 0.2]
                    }}
                    transition={{ delay: i * 0.05, duration: 2, repeat: Infinity }}
                    className="w-8 h-8 border border-white/20 flex items-center justify-center font-mono text-[10px]"
                >
                    {Math.random() > 0.5 ? '1' : '0'}
                </motion.div>
            ))}
        </div>
        <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
            className="absolute w-40 h-40 border-2 border-dashed border-security/30 rounded-full"
        />
        <Target className="absolute w-12 h-12 text-white" />
    </div>
);

const ExecutionGraphic = () => (
    <div className="relative w-full h-[300px] flex items-center justify-center overflow-hidden">
        <motion.div
            animate={{ scale: [1, 1.5, 1], opacity: [0.1, 0.3, 0.1] }}
            transition={{ duration: 2, repeat: Infinity }}
            className="absolute w-64 h-64 bg-security rounded-full blur-[80px]"
        />
        <div className="flex gap-4">
            {[...Array(5)].map((_, i) => (
                <motion.div
                    key={i}
                    animate={{ height: [20, 100, 20], opacity: [0.2, 1, 0.2] }}
                    transition={{ delay: i * 0.2, duration: 1, repeat: Infinity }}
                    className="w-2 bg-white"
                />
            ))}
        </div>
        <Zap className="absolute w-16 h-16 text-security" />
    </div>
);

const ReportingGraphic = () => (
    <div className="relative w-full h-[300px] flex items-center justify-center">
        <svg viewBox="0 0 100 100" className="w-40 h-40">
            <motion.circle
                cx="50" cy="50" r="40"
                fill="none" stroke="white" strokeWidth="0.5"
                strokeDasharray="5,5"
                animate={{ rotate: 360 }}
                transition={{ duration: 10, repeat: Infinity, ease: "linear" }}
            />
            <motion.path
                d="M30,70 L50,30 L70,70"
                fill="none" stroke="#FF0000" strokeWidth="2"
                initial={{ pathLength: 0 }}
                whileInView={{ pathLength: 1 }}
                transition={{ duration: 1.5 }}
            />
        </svg>
        <div className="absolute translate-y-12 font-mono text-[10px] text-security animate-pulse">
            REPORT GENERATED // 100%
        </div>
    </div>
);

const ProcessStep = ({ number, title, desc, icon: Icon, illustration: Illustration, index }) => {
    const ref = useRef(null);
    const isInView = useInView(ref, { once: false, amount: 0.5 });

    return (
        <div ref={ref} className={`relative flex items-center w-full min-h-[60vh] py-20 ${index % 2 === 0 ? 'flex-row' : 'flex-row-reverse'}`}>
            <div className={`w-1/2 flex flex-col ${index % 2 === 0 ? 'pr-24 items-end text-right' : 'pl-24 items-start text-left'}`}>
                <motion.span
                    initial={{ opacity: 0, x: index % 2 === 0 ? 50 : -50 }}
                    animate={isInView ? { opacity: 1, x: 0 } : { opacity: 0, x: index % 2 === 0 ? 50 : -50 }}
                    transition={{ duration: 0.6, delay: 0.2 }}
                    className="text-security font-mono text-2xl font-bold mb-2"
                >
                    {number}
                </motion.span>
                <motion.h3
                    initial={{ opacity: 0, y: 20 }}
                    animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
                    transition={{ duration: 0.6, delay: 0.3 }}
                    className="text-5xl font-black tracking-tighter mb-4 uppercase"
                >
                    {title}
                </motion.h3>
                <motion.p
                    initial={{ opacity: 0 }}
                    animate={isInView ? { opacity: 0.6, y: 0 } : { opacity: 0 }}
                    transition={{ duration: 0.6, delay: 0.4 }}
                    className="text-xl max-w-md leading-tight font-mono"
                >
                    {desc}
                </motion.p>
            </div>

            {/* Illustration on the other side */}
            <div className="w-1/2 flex items-center justify-center p-12">
                <motion.div
                    initial={{ opacity: 0, scale: 0.8 }}
                    whileInView={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.8 }}
                    className="w-full"
                >
                    <Illustration />
                </motion.div>
            </div>

            {/* Vertical Line Anchor */}
            <div className="absolute left-1/2 -translate-x-1/2 flex items-center justify-center z-10">
                <motion.div
                    animate={isInView ? {
                        scale: [1, 1.2, 1],
                        backgroundColor: ["#FFFFFF", "#FF0000", "#FFFFFF"]
                    } : { scale: 1 }}
                    className="w-12 h-12 bg-foreground rounded-full flex items-center justify-center border-4 border-background shadow-[0_0_20px_rgba(255,255,255,0.3)]"
                >
                    <Icon className="w-6 h-6 text-background" />
                </motion.div>
            </div>
        </div>
    );
};

const Terminal = () => {
    return (
        <div className="w-full max-w-4xl mx-auto mt-20 bg-[#0A0A0A] border border-foreground/20 rounded-lg overflow-hidden shadow-2xl border-glow-red">
            <div className="bg-[#1A1A1A] px-4 py-2 flex items-center gap-2 border-b border-foreground/10">
                <div className="w-3 h-3 rounded-full bg-red-500" />
                <div className="w-3 h-3 rounded-full bg-yellow-500" />
                <div className="w-3 h-3 rounded-full bg-green-500" />
                <span className="ml-4 font-mono text-xs opacity-40">ffte --output /divide</span>
            </div>
            <div className="p-6 font-mono text-sm leading-relaxed overflow-x-auto">
                <div className="text-gray-400 mb-2 font-bold mb-4">
                    [<span className="text-blue-400">INFO</span>] Initializing FFTE v1.0.4...<br />
                    [<span className="text-blue-400">INFO</span>] Loaded OpenAPI spec: <span className="text-white underline">/api/v1/math.json</span><br />
                    [<span className="text-blue-400">INFO</span>] Generating 452 edge-case payloads for path: <span className="text-white">/divide</span>
                </div>

                <div className="text-security font-bold mb-4 animate-pulse">
                    !!! CRITICAL FAILURE DETECTED !!!<br />
                    Path: POST /divide<br />
                    Input: {'{ "numerator": 1, "denominator": 0 }'}<br />
                    Status: 500 Internal Server Error<br />
                    Error: ZeroDivisionError: division by zero
                </div>

                <div className="mt-6 p-4 border border-security bg-security/5 rounded">
                    <div className="flex justify-between items-center mb-2">
                        <span className="text-security uppercase text-xs font-black tracking-widest">Reproduce failure</span>
                        <Copy className="w-4 h-4 text-security cursor-pointer" />
                    </div>
                    <code className="text-white break-all">
                        {`curl -X POST "https://api.target.com/divide" -H "Content-Type: application/json" -d '{"numerator": 1, "denominator": 0}'`}
                    </code>
                </div>
            </div>
        </div>
    );
};

const ImageSequence = () => {
    const [images, setImages] = React.useState([]);
    const [frameIndex, setFrameIndex] = React.useState(0);
    const canvasRef = useRef(null);
    const totalFrames = 190;
    const startFrame = 3;

    useEffect(() => {
        // Preload images
        const preloadedImages = [];
        for (let i = startFrame; i <= startFrame + totalFrames - 1; i++) {
            const img = new Image();
            const frameNum = String(i).padStart(3, '0');
            img.src = `assets/hero_page/ezgif-frame-${frameNum}.jpg`;
            preloadedImages.push(img);
        }
        setImages(preloadedImages);
    }, []);

    useEffect(() => {
        if (images.length === 0) return;

        let animationFrameId;
        let lastTime = 0;
        const fps = 24;
        const interval = 1000 / fps;

        const animate = (time) => {
            if (time - lastTime >= interval) {
                setFrameIndex((prevIndex) => (prevIndex + 1) % totalFrames);
                lastTime = time;
            }
            animationFrameId = requestAnimationFrame(animate);
        };

        animationFrameId = requestAnimationFrame(animate);
        return () => cancelAnimationFrame(animationFrameId);
    }, [images]);

    useEffect(() => {
        if (canvasRef.current && images[frameIndex]) {
            const canvas = canvasRef.current;
            const context = canvas.getContext('2d');
            const currentFrame = images[frameIndex];

            // Handle retina displays
            const dpr = window.devicePixelRatio || 1;
            canvas.width = canvas.clientWidth * dpr;
            canvas.height = canvas.clientHeight * dpr;
            context.scale(dpr, dpr);

            // Draw image covering the canvas (object-fit: cover equivalent)
            const imgRatio = currentFrame.width / currentFrame.height;
            const canvasRatio = canvas.clientWidth / canvas.clientHeight;
            let drawWidth, drawHeight, offsetX, offsetY;

            if (imgRatio > canvasRatio) {
                drawHeight = canvas.clientHeight;
                drawWidth = canvas.clientHeight * imgRatio;
                offsetX = (canvas.clientWidth - drawWidth) / 2;
                offsetY = 0;
            } else {
                drawWidth = canvas.clientWidth;
                drawHeight = canvas.clientWidth / imgRatio;
                offsetX = 0;
                offsetY = (canvas.clientHeight - drawHeight) / 2;
            }

            context.clearRect(0, 0, canvas.width, canvas.height);
            context.drawImage(currentFrame, offsetX, offsetY, drawWidth, drawHeight);
        }
    }, [frameIndex, images]);

    return (
        <canvas
            ref={canvasRef}
            className="absolute inset-0 w-full h-full pointer-events-none opacity-40 mix-blend-screen"
            style={{ filter: 'grayscale(1) brightness(1.1) contrast(1.2)' }}
        />
    );
};

const MarqueeTicker = () => {
    const tags = ["#OPENAPI", "#FUZZING", "#PYTHON3.10", "#FASTAPI", "#EDGE_CASES", "#CURL", "#SECURITY", "#DEVTOOLS"];

    return (
        <div className="w-full bg-foreground py-4 overflow-hidden whitespace-nowrap border-y border-foreground/20">
            <motion.div
                animate={{ x: [0, -1000] }}
                transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                className="flex gap-12 text-background font-mono font-bold text-xl"
            >
                {[...tags, ...tags, ...tags].map((tag, i) => (
                    <span key={i} className="flex items-center gap-4">
                        {tag}
                        <span className="w-2 h-2 bg-background rounded-full" />
                    </span>
                ))}
            </motion.div>
        </div>
    );
};

// --- Showcase Section (Device & UI) ---

const ShowcaseCarousel = () => {
    const [index, setIndex] = useState(0);
    const data = [
        {
            title: "Discover lethal API",
            desc: "vulnerabilities",
            color: "#FF0000",
            img1: "assets/workflow.png",
            img2: "assets/hero_page/ezgif-frame-003.jpg"
        },
        {
            title: "Simulate controlled",
            desc: "digital chaos",
            color: "#FF5533",
            img1: "assets/test.jpeg",
            img2: "assets/hero_page/ezgif-frame-100.jpg"
        },
        {
            title: "Reproduce crashes",
            desc: "with one click",
            color: "#6040FF",
            img1: "assets/hero_page/ezgif-frame-050.jpg",
            img2: "assets/hero_page/ezgif-frame-150.jpg"
        }
    ];

    useEffect(() => {
        const timer = setInterval(() => {
            setIndex((prev) => (prev + 1) % data.length);
        }, 5000);
        return () => clearInterval(timer);
    }, [data.length]);

    return (
        <section className="relative min-h-[70vh] flex items-center bg-background text-foreground py-24 overflow-hidden">
            <div className="max-w-7xl mx-auto px-8 w-full grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
                {/* Left Side: Text and Indicators */}
                <div className="flex flex-col gap-8 order-2 md:order-1">
                    <div className="flex flex-col">
                        <motion.h2
                            key={`title-${index}`}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="text-5xl md:text-7xl font-black tracking-tighter text-white uppercase"
                        >
                            {data[index].title}
                        </motion.h2>
                        <div className="overflow-hidden">
                            <AnimatePresence mode="wait">
                                <motion.div
                                    key={`desc-${index}`}
                                    initial={{ opacity: 0, y: 50 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, y: -50 }}
                                    transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
                                    className="text-5xl md:text-7xl font-black italic tracking-tighter uppercase"
                                    style={{ color: data[index].color }}
                                >
                                    {data[index].desc}
                                </motion.div>
                            </AnimatePresence>
                        </div>
                    </div>

                    {/* Dot Indicators */}
                    <div className="flex gap-4">
                        {data.map((_, i) => (
                            <motion.div
                                key={i}
                                onClick={() => setIndex(i)}
                                animate={{
                                    scale: i === index ? 1.3 : 1,
                                    backgroundColor: i === index ? data[i].color : "rgba(255,255,255,0.1)",
                                    width: i === index ? 24 : 12
                                }}
                                className="h-3 rounded-full cursor-pointer transition-all duration-500"
                            />
                        ))}
                    </div>

                    <div className="flex gap-6 items-center mt-4">
                        <motion.button
                            whileHover={{ scale: 1.05, backgroundColor: "#FF0000" }}
                            whileTap={{ scale: 0.95 }}
                            onClick={() => window.location.href = 'http://localhost:3000/command-center.html'}
                            className="px-10 py-5 bg-foreground text-background rounded-full font-black text-xl tracking-widest uppercase hover:text-white transition-all shadow-[0_0_30px_rgba(255,255,255,0.1)]"
                        >
                            Launch Engine
                        </motion.button>
                        <button
                            className="text-lg font-bold border-b-2 border-white/10 hover:border-white transition-all text-white/60 hover:text-white"
                            onClick={() => window.location.href = 'http://localhost:3000/auth.html'}
                        >
                            I already have an account
                        </button>
                    </div>
                </div>

                {/* Right Side: Floating Animated Cards */}
                <div className="relative h-[500px] md:h-[700px] order-1 md:order-2 flex items-center justify-center">
                    <AnimatePresence mode="wait">
                        <motion.div
                            key={`container-${index}`}
                            className="relative w-full h-full flex items-center justify-center"
                        >
                            {/* Larger Background Card */}
                            <motion.div
                                initial={{ opacity: 0, scale: 0.8, x: 100, rotate: 10 }}
                                animate={{ opacity: 1, scale: 1, x: 0, rotate: 5 }}
                                exit={{ opacity: 0, scale: 0.8, x: -100, rotate: -10 }}
                                transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
                                className="absolute w-[80%] h-[75%] rounded-[60px] overflow-hidden shadow-[0_60px_100px_-20px_rgba(0,0,0,0.5)] border-[12px] border-white/5 z-0"
                            >
                                <img src={data[index].img1} className="w-full h-full object-cover transition-transform duration-[2000ms] hover:scale-110" alt="FFTE Visualization" />
                                <div className="absolute top-10 left-10">
                                    <div className="bg-background/40 backdrop-blur-xl p-6 rounded-[30px] border border-white/10 shadow-2xl">
                                        <Activity className="text-white w-10 h-10" />
                                    </div>
                                </div>
                            </motion.div>

                            {/* Smaller Overlapping Foreground Card */}
                            <motion.div
                                initial={{ opacity: 0, scale: 0.5, y: 150, rotate: -20 }}
                                animate={{ opacity: 1, scale: 1, y: 100, x: -80, rotate: -5 }}
                                exit={{ opacity: 0, scale: 0.5, y: -150, rotate: 20 }}
                                transition={{ duration: 0.9, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
                                className="absolute w-[65%] h-[55%] rounded-[50px] overflow-hidden shadow-[0_40px_80px_-15px_rgba(0,0,0,0.6)] border-[10px] border-white/10 z-10"
                            >
                                <img src={data[index].img2} className="w-full h-full object-cover brightness-75 transition-transform duration-[2000ms] hover:scale-110" alt="FFTE Analysis" />
                                <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-background via-background/20 to-transparent p-10">
                                    <div className="flex items-center gap-4">
                                        <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
                                        <div className="font-mono text-white text-sm font-black tracking-[0.2em] uppercase">
                                            Lethal Signal // Live
                                        </div>
                                    </div>
                                </div>
                            </motion.div>

                            {/* Floating Version Tag */}
                            <motion.div
                                initial={{ opacity: 0, scale: 0 }}
                                animate={{ opacity: 1, scale: 1 }}
                                transition={{ delay: 0.5 }}
                                className="absolute top-20 right-0 bg-white text-black px-6 py-3 rounded-full font-mono text-xs font-bold tracking-widest uppercase z-20 shadow-xl"
                            >
                                FFTE v1.0.0
                            </motion.div>
                        </motion.div>
                    </AnimatePresence>
                </div>
            </div>
        </section>
    );
};

/* Sound Effects - High Noir Audio System */
const audioCtx = typeof window !== 'undefined' ? new (window.AudioContext || window.webkitAudioContext)() : null;

// Helper to resume context if needed
const resumeAudio = () => {
    if (audioCtx && audioCtx.state === 'suspended') {
        audioCtx.resume();
    }
};

const playClickSound = () => {
    if (!audioCtx) return;
    resumeAudio();

    const t = audioCtx.currentTime;

    // Primary Impact
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();

    osc.type = 'sine';
    osc.frequency.setValueAtTime(800, t);
    osc.frequency.exponentialRampToValueAtTime(100, t + 0.1);

    gain.gain.setValueAtTime(0.1, t);
    gain.gain.exponentialRampToValueAtTime(0.001, t + 0.1);

    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start(t);
    osc.stop(t + 0.1);

    // High frequency tick for crispness
    const osc2 = audioCtx.createOscillator();
    const gain2 = audioCtx.createGain();

    osc2.type = 'square';
    osc2.frequency.setValueAtTime(3000, t);
    osc2.frequency.exponentialRampToValueAtTime(1000, t + 0.05);

    gain2.gain.setValueAtTime(0.05, t);
    gain2.gain.exponentialRampToValueAtTime(0.001, t + 0.05);

    osc2.connect(gain2);
    gain2.connect(audioCtx.destination);
    osc2.start(t);
    osc2.stop(t + 0.05);
};

const playHoverSound = () => {
    if (!audioCtx) return;
    resumeAudio();

    const t = audioCtx.currentTime;
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();

    osc.type = 'sine';
    osc.frequency.setValueAtTime(1200, t);
    osc.frequency.exponentialRampToValueAtTime(800, t + 0.05);

    gain.gain.setValueAtTime(0.02, t);
    gain.gain.linearRampToValueAtTime(0, t + 0.05);

    osc.connect(gain);
    gain.connect(audioCtx.destination);

    osc.start(t);
    osc.stop(t + 0.05);
};

const playProcessingSound = () => {
    if (!audioCtx) return;
    resumeAudio();

    const t = audioCtx.currentTime;

    // Digital data stream sound
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    const filter = audioCtx.createBiquadFilter();

    // Modulated sawtooth for "computing" texture
    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(100, t);
    osc.frequency.linearRampToValueAtTime(500, t + 0.15); // Sweep up

    filter.type = 'lowpass';
    filter.frequency.setValueAtTime(500, t);
    filter.frequency.linearRampToValueAtTime(2000, t + 0.15); // Open filter

    gain.gain.setValueAtTime(0.05, t);
    gain.gain.exponentialRampToValueAtTime(0.001, t + 0.2);

    osc.connect(filter);
    filter.connect(gain);
    gain.connect(audioCtx.destination);

    osc.start(t);
    osc.stop(t + 0.2);
};

// --- Main App ---

export default function App() {
    const { scrollYProgress } = useScroll();
    const scaleX = useSpring(scrollYProgress, {
        stiffness: 100,
        damping: 30,
        restDelta: 0.001
    });

    const isCookieSet = typeof document !== 'undefined' && document.cookie.includes('ffte_auth_sync=1');
    const isLocalSet = typeof localStorage !== 'undefined' && !!localStorage.getItem('ffte_user');
    const isLoggedIn = isCookieSet || (isLocalSet && window.location.port !== '5173');

    // Nuke dirty local storage state from port 5173 isolating bugs
    if (!isCookieSet && isLocalSet && typeof localStorage !== 'undefined') {
        localStorage.removeItem('ffte_user');
    }

    return (
        <div className="min-h-screen selection:bg-security selection:text-white bg-background text-foreground">
            {/* Progress Line */}
            <motion.div
                className="fixed top-0 left-1/2 -ml-[2px] w-[4px] h-full bg-foreground/10 z-0 origin-top"
                style={{ scaleY: scrollYProgress }}
            />
            <div className="fixed top-0 left-1/2 -ml-[2px] w-[4px] h-full bg-foreground/5 z-[-1]" />

            {/* Navigation - High Noir */}
            <nav className="fixed top-0 w-full h-[60px] flex justify-between items-center px-8 z-[1000] bg-black border-b border-[#1A1A1A]">
                <div className="flex items-center gap-3">
                    <img src="assets/logo.png" alt="FFTE" className="h-12 w-auto" />
                </div>
                <div className="flex h-full gap-[0.5rem]">
                    <a href="http://localhost:5173/" onMouseEnter={() => playHoverSound()} onClick={() => playClickSound()} className="h-full flex items-center px-6 text-[0.75rem] font-bold tracking-[0.1em] uppercase bg-[#FF0000] text-white transition-all">00 HOME</a>
                    <a href="http://localhost:3000/command-center.html" onMouseEnter={() => playHoverSound()} onClick={() => playClickSound()} className="h-full flex items-center px-6 text-[0.75rem] font-bold tracking-[0.1em] text-[#888888] hover:text-white hover:bg-white/5 transition-all uppercase">01 COMMAND CENTER</a>
                    <a href="http://localhost:3000/the-lab.html" onMouseEnter={() => playHoverSound()} onClick={() => playClickSound()} className="h-full flex items-center px-6 text-[0.75rem] font-bold tracking-[0.1em] text-[#888888] hover:text-white hover:bg-white/5 transition-all uppercase">02 THE LAB</a>
                    <a href="http://localhost:3000/war-room.html" onMouseEnter={() => playHoverSound()} onClick={() => playClickSound()} className="h-full flex items-center px-6 text-[0.75rem] font-bold tracking-[0.1em] text-[#888888] hover:text-white hover:bg-white/5 transition-all uppercase">03 WAR ROOM</a>

                    {isLoggedIn ? (
                        <>
                            <a href="http://localhost:3000/profile.html" onMouseEnter={() => playHoverSound()} onClick={() => playClickSound()} className="h-full flex items-center px-6 text-[0.75rem] font-bold tracking-[0.1em] text-[#888888] hover:text-white hover:bg-white/5 transition-all uppercase">04 PROFILE</a>
                            <a href="#" onMouseEnter={() => playHoverSound()} onClick={(e) => { e.preventDefault(); playClickSound(); localStorage.removeItem('ffte_user'); document.cookie = "ffte_auth_sync=; path=/; max-age=0"; window.location.href = 'http://localhost:3000/auth.html'; }} className="h-full flex items-center px-6 text-[0.75rem] font-bold tracking-[0.1em] text-[#FF0000] border-l border-[#333] ml-2 hover:bg-white/5 transition-all uppercase">LOGOUT</a>
                        </>
                    ) : (
                        <a href="http://localhost:3000/auth.html" onMouseEnter={() => playHoverSound()} onClick={() => playClickSound()} className="h-full flex items-center px-6 text-[0.75rem] font-bold tracking-[0.1em] text-[#FF0000] border-l border-[#333] ml-2 hover:bg-white/5 transition-all uppercase">LOGIN</a>
                    )}
                </div>
            </nav>

            {/* Hero Section */}
            <section className="relative h-screen flex flex-col items-center justify-center text-center px-4 overflow-hidden">
                {/* Image Sequence background */}
                <ImageSequence />

                {/* Background Text */}
                <motion.div
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 0.1, scale: 1 }}
                    transition={{ duration: 1.5 }}
                    className="absolute pointer-events-none select-none font-black text-[30vw] tracking-tighter text-white leading-none z-0"
                >
                    FAILURE
                </motion.div>

                <div className="relative z-10 flex flex-col items-center justify-center">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.8 }}
                        className="flex flex-col items-center"
                    >
                        <div className="p-2 border-2 border-security mb-6">
                            <ShieldAlert className="w-12 h-12 text-security" />
                        </div>
                        <h1 className="text-7xl md:text-9xl font-black tracking-tighter leading-none uppercase mb-6">
                            FFTE: THE FAILURE-FIRST TESTING ENGINE
                        </h1>
                        <p className="text-xl md:text-2xl font-mono text-white/60 max-w-3xl mb-12">
                            Automatically discover, attack, and reproduce API crashes before your users do.
                        </p>

                        <motion.button
                            whileHover={{ scale: 1.05, backgroundColor: "#FF0000", color: "#FFFFFF" }}
                            whileTap={{ scale: 0.95 }}
                            onClick={() => playClickSound()}
                            onMouseEnter={() => playHoverSound()}
                            className="bg-foreground text-background font-mono px-8 py-4 flex items-center gap-4 text-xl font-bold group hover:cursor-pointer"
                        >
                            <span className="opacity-40">$</span>
                            start engine
                            <ChevronRight className="w-6 h-6 group-hover:translate-x-1 transition-transform" />
                        </motion.button>
                    </motion.div>
                </div>

                {/* Bottom indicator */}
                <motion.div
                    animate={{ y: [0, 10, 0] }}
                    transition={{ duration: 2, repeat: Infinity }}
                    className="absolute bottom-10 left-1/2 -translate-x-1/2 opacity-30"
                >
                    <div className="w-[1px] h-20 bg-foreground" />
                </motion.div>
            </section>

            {/* Marquee */}
            <MarqueeTicker />

            {/* Showcase Carousel */}
            <ShowcaseCarousel />

            {/* Feature Section (Vertical Timeline) */}
            <section className="relative py-40 px-4 max-w-7xl mx-auto">
                <ProcessStep
                    number="01"
                    title="DISCOVERY"
                    desc="Parsing OpenAPI specs into attack surfaces. We map every endpoint, parameter, and schema to identify potential vulnerabilities."
                    icon={Plane}
                    illustration={DiscoveryGraphic}
                    index={0}
                />
                <ProcessStep
                    number="02"
                    title="INPUT GEN"
                    desc="Generating lethal edge-case payloads. Using aggressive fuzzer strategies to create inputs that break developer assumptions."
                    icon={Bird}
                    illustration={InputGenGraphic}
                    index={1}
                />
                <ProcessStep
                    number="03"
                    title="EXECUTION"
                    desc="Blasting real HTTP requests at the target. Real-time stress testing with high concurrency and deep state validation."
                    icon={Zap}
                    illustration={ExecutionGraphic}
                    index={2}
                />
                <ProcessStep
                    number="04"
                    title="REPORTING"
                    desc="Exporting failures as instant, reproducible curl commands. Minimize triage time with one-click reproduction."
                    icon={Target}
                    illustration={ReportingGraphic}
                    index={3}
                />
            </section>

            {/* Output Section */}
            <section className="py-40 bg-foreground/5 relative overflow-hidden">
                {/* Wireframe bg */}
                <div className="absolute inset-0 grid grid-cols-12 gap-0 opacity-5 pointer-events-none">
                    {[...Array(144)].map((_, i) => (
                        <div key={i} className="border border-foreground aspect-square" />
                    ))}
                </div>

                <div className="relative z-10 px-4">
                    <div className="text-center mb-16">
                        <h2 className="text-5xl font-black mb-4">LETHAL SIGNAL</h2>
                        <p className="font-mono text-white/40">Visualizing the break point in real-time.</p>
                    </div>
                    <Terminal />
                </div>
            </section>

            {/* Quote Section */}
            <section className="py-60 px-4 text-center">
                <motion.blockquote
                    initial={{ opacity: 0, scale: 0.9 }}
                    whileInView={{ opacity: 1, scale: 1 }}
                    className="text-4xl md:text-7xl font-black tracking-tighter uppercase leading-tight italic"
                >
                    "FFTE doesn’t guess bugs. <br />
                    <span className="text-security">It forces them to reveal themselves."</span>
                </motion.blockquote>
            </section>

            {/* Footer */}
            <footer className="p-20 border-t border-white/10 text-center font-mono text-sm opacity-40">
                <p>&copy; 2024 FAILURE-FIRST TESTING ENGINE. ALL RIGHTS RESERVED. // HIGH NOIR EDITION</p>
            </footer>
        </div>
    );
}
