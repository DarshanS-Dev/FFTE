import React, { useEffect, useRef } from 'react';
import { motion, useScroll, useSpring, useTransform, useInView } from 'framer-motion';
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

const ShowcaseSection = () => {
    const nodes = [
        { height: '60%', x: '15%' },
        { height: '40%', x: '30%' },
        { height: '75%', x: '50%' },
        { height: '35%', x: '65%' },
        { height: '55%', x: '85%' },
    ];

    return (
        <section className="py-12 px-4 md:px-12 bg-background relative z-10">
            {/* Rounded Background Block */}
            <div className="relative w-full max-w-6xl mx-auto bg-[#F2F6F4] rounded-[50px] md:rounded-[80px] py-16 md:py-24 px-6 overflow-hidden border border-black/5">

                {/* Device Frame */}
                <motion.div
                    initial={{ y: 50, opacity: 0 }}
                    whileInView={{ y: 0, opacity: 1 }}
                    transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
                    className="relative max-w-5xl mx-auto"
                >
                    {/* Outer Shadow */}
                    <div className="absolute -inset-10 bg-black/5 blur-[100px] rounded-full pointer-events-none" />

                    {/* Black Bezel */}
                    <div className="relative bg-black p-4 md:p-7 rounded-[40px] md:rounded-[70px] shadow-[0_50px_100px_-20px_rgba(0,0,0,0.3)] ring-1 ring-white/10">
                        {/* Inner Screen */}
                        <div className="relative aspect-[16/10] bg-zinc-900 rounded-[30px] md:rounded-[50px] overflow-hidden">
                            {/* Full-bleed Landscape Image */}
                            <img
                                src="assets/test.jpeg"
                                alt="Landscape Visualization"
                                className="absolute inset-0 w-full h-full object-cover"
                            />

                            {/* Dark Overlay for UI legibility */}
                            <div className="absolute inset-0 bg-black/20" />

                            {/* UI Overlays */}

                            {/* Top Left: Status */}
                            <div className="absolute top-10 left-10 text-white z-30">
                                <div className="text-[10px] md:text-xs font-mono opacity-50 mb-2 uppercase tracking-widest">System / Core / Metrics</div>
                                <div className="flex items-start gap-4">
                                    <span className="text-5xl md:text-7xl font-black leading-none tracking-tighter">78%</span>
                                    <div className="max-w-[100px] leading-tight mt-1">
                                        <span className="text-[10px] md:text-xs font-mono font-bold uppercase opacity-90">Efficiency Improvements</span>
                                    </div>
                                </div>
                            </div>

                            {/* Top Right: Pill */}
                            <div className="absolute top-10 right-10 z-30">
                                <div className="bg-white/10 backdrop-blur-md border border-white/20 px-5 py-2 rounded-full text-white font-mono text-[10px] md:text-xs flex items-center gap-3">
                                    All Regions (33)
                                    <div className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse" />
                                </div>
                            </div>

                            {/* Upper Middle: Timeline */}
                            <div className="absolute top-[35%] left-1/2 -translate-x-1/2 w-[70%] z-30">
                                <div className="relative h-[2px] bg-white/20 rounded-full">
                                    <div className="absolute inset-0 flex justify-between -top-8 text-[10px] font-mono text-white/50 tracking-widest">
                                        <span>2021</span>
                                        <span>2022</span>
                                        <span>2023</span>
                                        <span>2024</span>
                                    </div>
                                    {/* Tick marks */}
                                    <div className="absolute inset-0 flex justify-between px-0">
                                        {[...Array(4)].map((_, i) => (
                                            <div key={i} className="w-[2px] h-3 bg-white/30 -translate-y-[5.5px]" />
                                        ))}
                                    </div>
                                    <motion.div
                                        initial={{ width: 0 }}
                                        whileInView={{ width: '85%' }}
                                        transition={{ duration: 2, delay: 0.5 }}
                                        className="absolute top-0 left-0 h-full bg-white shadow-[0_0_15px_white]"
                                    />
                                </div>
                            </div>

                            {/* Lower Area: Vertical Nodes */}
                            <div className="absolute bottom-0 inset-x-0 h-1/2 z-30 px-12 md:px-24">
                                <div className="relative w-full h-full">
                                    {nodes.map((node, i) => (
                                        <motion.div
                                            key={i}
                                            initial={{ height: 0, opacity: 0 }}
                                            whileInView={{ height: node.height, opacity: 1 }}
                                            transition={{ duration: 1, delay: 0.8 + (i * 0.1) }}
                                            className="absolute bottom-16 flex flex-col items-center group"
                                            style={{ left: node.x }}
                                        >
                                            <div className="w-2.5 h-2.5 bg-white rounded-sm shadow-[0_0_15px_white]" />
                                            <div className="w-[1px] flex-grow bg-white/30" />
                                            <div className="w-2.5 h-2.5 bg-white/40 rounded-sm" />
                                        </motion.div>
                                    ))}
                                </div>
                            </div>

                            {/* Subtle Reflection */}
                            <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/5 to-black/20 pointer-events-none" />
                        </div>
                    </div>
                </motion.div>
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
                <div className="flex h-full gap-2">
                    <a href="http://localhost:5173" onMouseEnter={() => playHoverSound()} onClick={() => playClickSound()} className="h-full flex items-center px-6 text-xs font-bold tracking-widest bg-[#FF0000] text-white">00 HOME</a>
                    <a href="http://localhost:3000/command-center.html" onMouseEnter={() => playHoverSound()} onClick={() => playClickSound()} className="h-full flex items-center px-6 text-xs font-bold tracking-widest text-[#888] hover:text-white hover:bg-white/5 transition-all">01 COMMAND CENTER</a>
                    <a href="http://localhost:3000/the-lab.html" onMouseEnter={() => playHoverSound()} onClick={() => playClickSound()} className="h-full flex items-center px-6 text-xs font-bold tracking-widest text-[#888] hover:text-white hover:bg-white/5 transition-all">02 THE LAB</a>
                    <a href="http://localhost:3000/war-room.html" onMouseEnter={() => playHoverSound()} onClick={() => playClickSound()} className="h-full flex items-center px-6 text-xs font-bold tracking-widest text-[#888] hover:text-white hover:bg-white/5 transition-all">03 WAR ROOM</a>
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
                            run python app.py
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

            {/* Showcase Section */}
            <ShowcaseSection />

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
