document.addEventListener('DOMContentLoaded', function () {
    const fileInput = document.getElementById('file-input');
    const fileNameDisplay = document.getElementById('file-name');
    const dropArea = document.getElementById('drop-area');

    // 處理檔案選擇
    fileInput.addEventListener('change', function() {
        const file = fileInput.files[0];
        if (file) {
            fileNameDisplay.textContent = file.name;
            fileNameDisplay.classList.add('active');  // **新增 active class**
        } else {
            fileNameDisplay.textContent = "Drop music files here, or click to select";
            fileNameDisplay.classList.remove('active');  // **移除 active class**
        }
    });
     // 確保選取到按鈕
    const loginButtons = document.querySelectorAll(".user-account");

    if (loginButtons.length === 0) {
         console.error("❌ user-account not found!");
         return;
    }
 
    const username = localStorage.getItem("username");
    const username1 = localStorage.getItem("username");

    if (username) {
        // ✅ 使用者已登入，變更按鈕為 username 並綁定登出功能
        loginButtons.forEach(button => {
            button.textContent = username;
            button.href = "#"; // 避免點擊後跳轉
            button.removeEventListener("click", handleLoginClick); // **先移除登錄事件**
            button.addEventListener("click", handleLogoutClick); // **綁定登出**
        });

    } else {
        // ✅ 使用者未登入時，按鈕變回 Login 並指向登入頁
        loginButtons.forEach(button => {
            button.textContent = "Login";
            button.href = "/log_in";
            button.removeEventListener("click", handleLogoutClick); // **先移除登出事件**
            button.addEventListener("click", handleLoginClick); // **綁定登入**
        });
    }

    // ✅ 登出功能（確認是否要登出）
    function handleLogoutClick(event) {
        event.preventDefault();
        const confirmLogout = confirm("確定要登出嗎？");
        if (confirmLogout) {
            localStorage.removeItem("username");

            // **登出後恢復成 Login 狀態**
            loginButtons.forEach(button => {
                button.textContent = "Login";
                button.href = "https://whalesignal.onrender.com/log_in";
                button.removeEventListener("click", handleLogoutClick); // **移除登出監聽**
                button.addEventListener("click", handleLoginClick); // **恢復登入監聽**
            });
        }
    }

    // ✅ 登入功能（點擊時前往登入頁面）
    function handleLoginClick(event) {
        // 這裡不需要 `preventDefault()`，因為我們希望它能夠跳轉
        window.location.href = "/log_in";
    }
    



    // 監聽拖放區域的事件
    dropArea.addEventListener('dragover', function(event) {
        event.preventDefault();  // 防止默認行為（防止打開檔案）
        dropArea.classList.add('dragover');  // 當拖曳進來時改變背景顏色
    });

    dropArea.addEventListener('dragleave', function() {
        dropArea.classList.remove('dragover');  // 拖曳離開時移除背景顏色
    });

    dropArea.addEventListener('drop', function(event) {
        event.preventDefault();  // 防止默認行為（防止打開檔案）

        // 確認拖曳進來的是 .wav 檔案
        const files = event.dataTransfer.files;
        if (files.length > 0) {
            const file = files[0];
            if (file.type === "audio/wav") {
                fileNameDisplay.textContent = file.name;  // 顯示檔案名稱
                fileNameDisplay.classList.add('active');  // 顯示 active class
                // 手動觸發 <input> 的 change 事件
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(file);
                fileInput.files = dataTransfer.files;
            } else {
                fileNameDisplay.textContent = "Only .wav files are allowed";  // 只允許 .wav 檔案
                fileNameDisplay.classList.remove('active'); 
            }
        }
    });
});
// document.addEventListener("DOMContentLoaded", function () {
//     const loadingScreen = document.getElementById("loading-screen");
//     const homepageVideo = document.getElementById("homepage-video");
//     const bannerText = document.querySelector(".banner-text");
//     const progressBar = document.querySelector(".progress");
//     const loadingText = document.querySelector(".loading-text");

//     // 確保背景影片顯示
//     homepageVideo.style.opacity = "1";
//     homepageVideo.style.visibility = "visible";

//     // **讀條動畫**
//     let progress = 0;
//     const interval = setInterval(() => {
//         if (progress >= 100) {
//             clearInterval(interval);
//         } else {
//             progress += 1;
//             progressBar.style.width = progress + "%";
//             loadingText.textContent = progress + "%";
//         }
//     }, 40); // 5 秒內跑滿 100%

//     setTimeout(() => {
//         homepageVideo.classList.add("show-video");

//         setTimeout(() => {
//             loadingScreen.classList.add("fade-out");

//             setTimeout(() => {
//                 loadingScreen.style.display = "none"; // 完全隱藏 loading 畫面
//                 bannerText.classList.add("fade-in");  // 顯示標題
//             }, 800);
//         }, 1000);
//     }, 2000);
// });



document.addEventListener('DOMContentLoaded', function () {
    const premiumLink = document.getElementById("analysis");
    const analysisLinks = document.querySelectorAll(".analysis-btn");

    analysisLinks.forEach(link => {
        link.addEventListener("click", function (event) {
            event.preventDefault(); // 阻止預設跳轉行為
            
            const username = localStorage.getItem("username");
            if (!username) {
                alert("請先登入"); 
                return;
            }

            fetch(`/check_user_records?username=${username}`)
                .then(response => response.json())
                .then(data => {
                    if (!data.has_records) {
                        alert("Please upload file first!");
                    } else {
                        window.location.href = "/analysis";
                    }
                })
                .catch(error => {
                    console.error("Error checking user records:", error);
                });
        });
    });
});