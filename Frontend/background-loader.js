
// ===== BACKGROUND FRAME ANIMATION =====
const TOTAL_FRAMES = 146;
const FRAME_PATH = 'assets/ezgif-frame-';
const FRAME_EXT = '.jpg';
const FPS = 24; // Standard cinematic frame rate

class FrameAnimator {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) return;

        this.canvas = document.createElement('canvas');
        this.ctx = this.canvas.getContext('2d');
        this.container.appendChild(this.canvas);

        this.images = [];
        this.loadedCount = 0;
        this.currentFrame = 0;
        this.lastFrameTime = 0;
        this.frameInterval = 1000 / FPS;

        this.resize();
        window.addEventListener('resize', () => this.resize());

        this.loadImages();
    }

    resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
        // Redraw current frame immediately on resize
        if (this.images[this.currentFrame]) {
            this.drawFrame(this.currentFrame);
        }
    }

    loadImages() {
        for (let i = 1; i <= TOTAL_FRAMES; i++) {
            const img = new Image();
            // Pad with zeros: 1 -> 001, 10 -> 010, 100 -> 100
            const frameNum = i.toString().padStart(3, '0');
            img.src = `${FRAME_PATH}${frameNum}${FRAME_EXT}`;
            img.onload = () => {
                this.loadedCount++;
                if (this.loadedCount === TOTAL_FRAMES) {
                    this.startAnimation();
                }
            };
            this.images.push(img);
        }
    }

    startAnimation() {
        this.animate(performance.now());
    }

    animate(currentTime) {
        requestAnimationFrame((t) => this.animate(t));

        const deltaTime = currentTime - this.lastFrameTime;

        if (deltaTime >= this.frameInterval) {
            this.lastFrameTime = currentTime - (deltaTime % this.frameInterval);
            this.drawFrame(this.currentFrame);
            this.currentFrame = (this.currentFrame + 1) % TOTAL_FRAMES;
        }
    }

    drawFrame(frameIndex) {
        const img = this.images[frameIndex];
        if (!img) return;

        // Calculate 'cover' fit
        const ratio = Math.max(this.canvas.width / img.width, this.canvas.height / img.height);
        const centerShift_x = (this.canvas.width - img.width * ratio) / 2;
        const centerShift_y = (this.canvas.height - img.height * ratio) / 2;

        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.ctx.drawImage(
            img,
            0, 0, img.width, img.height,
            centerShift_x, centerShift_y, img.width * ratio, img.height * ratio
        );

        // Optional: formatting overlay for "white background" feel if needed
        // this.ctx.fillStyle = 'rgba(255, 255, 255, 0.1)';
        // this.ctx.fillRect(0,0, this.canvas.width, this.canvas.height);
    }
}

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    // Check if we are on a page that needs this
    if (document.getElementById('frame-bg')) {
        new FrameAnimator('frame-bg');
    }
});
