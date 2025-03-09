document.addEventListener("DOMContentLoaded", () => {
    const loadingScreen = document.getElementById("loading-screen");
    const homepageVideo = document.getElementById("homepage-video");
    const bannerText = document.querySelector(".banner-text");
    const progressBar = document.querySelector(".progress");
    const loadingText = document.querySelector(".loading-text");
    const skipButton = document.getElementById("skip-button");
    const waterDrop = document.getElementById("water-drop");

    let progress = 0;
    const startTime = performance.now();
    const duration = 4000;
    let animationTimeout;

    /** 產生水波動畫 **/
    const rippleDelays = [0.7, 1.4, 2, 2.5, 3];
    rippleDelays.forEach(delay => createRipple(delay));

    function createRipple(delay) {
        const ripple = document.createElement("div");
        ripple.classList.add("ripple");

        // 限制水波大小，避免過大
        const maxSize = Math.min(window.innerWidth, window.innerHeight) * 1;

        ripple.style.width = `${maxSize}px`;
        ripple.style.height = `${maxSize}px`;
        ripple.style.animationDelay = `${delay}s`;
        ripple.style.position = "absolute";
        ripple.style.top = "50%";
        ripple.style.left = "50%";
        ripple.style.transform = "translate(-50%, -50%) scale(0)";

        loadingScreen.appendChild(ripple);
    }

    /** 進度條更新 **/
    function updateProgress(now) {
        const elapsed = now - startTime;
        progress = Math.min((elapsed / duration) * 100, 100);
        progressBar.style.width = `${progress}%`;
        loadingText.textContent = `${Math.floor(progress)}%`;

        if (progress < 100) {
            requestAnimationFrame(updateProgress);
        }
    }
    requestAnimationFrame(updateProgress);

    /** 結束動畫並顯示首頁 **/
    function finishAnimation() {
        // 清除計時器，避免重複執行
        if (animationTimeout) {
            clearTimeout(animationTimeout);
        }

        progressBar.style.width = "100%";
        loadingText.textContent = "100%";
        homepageVideo.classList.add("show-video");

        // 直接隱藏 loading 畫面，避免頓一下
        loadingScreen.style.opacity = "0";  // 立即淡出
        setTimeout(() => {
            loadingScreen.style.display = "none"; // 500ms 後完全移除
            bannerText.classList.add("show");

            gsap.from(".big-title", {
                opacity: 1,
                y: 50,
                duration: 1.5,
                ease: "power3.out"
            });
            gsap.from(".sub-text", {
                opacity: 1,
                x: -30,
                duration: 1.5,
                ease: "power3.out",
                delay: 0.5
            });

            // 啟用首頁影片 Ripples.js 效果
            $("#homepage-video").ripples({
                resolution: 180,
                dropRadius: 15,
                perturbance: 0.02
            });

        }, 500); // **500ms 內結束所有 loading 動畫**

        // 讓水滴馬上消失，避免造成卡頓
        waterDrop.style.transition = "opacity 0.3s ease-in-out";
        waterDrop.style.opacity = "0";
        setTimeout(() => {
            waterDrop.style.display = "none";
        }, 300);
    }

    /** Skip 按鈕事件 **/
    if (skipButton) {
        setTimeout(() => {
            skipButton.classList.add("show");
        }, 1000);

        skipButton.addEventListener("click", () => {
            finishAnimation();
        });
    }

    // 自動結束動畫
    animationTimeout = setTimeout(finishAnimation, duration);
});