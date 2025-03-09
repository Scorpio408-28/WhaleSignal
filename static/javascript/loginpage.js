document.addEventListener("DOMContentLoaded", () => {
    console.log("✅ JavaScript Loaded!");

    const tabBtns = document.querySelectorAll(".tab-btn");
    const submitBtn = document.querySelector(".submit-btn");
    const loginFields = document.querySelectorAll(".login-field input");
    const signupFields = document.querySelectorAll(".signup-field input");
    const loginForm = document.getElementById("loginForm");
    const emailInput = document.getElementById("signup-email");
    const passwordInput = document.getElementById("signup-password");
    const confirmPasswordInput = document.getElementById("signup-confirm-password");

    let isSignup = false;
    
    // 清除驗證狀態
    function clearValidation() {
        const allInputs = document.querySelectorAll('.input-group');
        allInputs.forEach(group => {
            group.classList.remove('valid', 'error');
            const errorMessage = group.querySelector('.error-message');
            if (errorMessage) {
                errorMessage.textContent = '';
            }
        });
    }

    // 驗證電子郵件
    function validateEmail(email) {
        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailPattern.test(email);
    }

    // 驗證密碼
    function validatePassword(password) {
        return password.length >= 6;
    }

    // 驗證輸入欄位
    function validateInput(input) {
        const inputGroup = input.parentElement;
        const errorMessage = inputGroup.querySelector('.error-message');
        const value = input.value.trim();

        inputGroup.classList.remove('valid', 'error');
        if (errorMessage) {
            errorMessage.textContent = '';
        }

        if (value === '') {
            inputGroup.classList.add('error');
            if (errorMessage) {
                errorMessage.textContent = '此欄位為必填';
            }
            return false;
        }

        if (input.type === 'email') {
            if (!validateEmail(value)) {
                inputGroup.classList.add('error');
                if (errorMessage) {
                    errorMessage.textContent = '請輸入有效的電子郵件地址';
                }
                return false;
            }
        }

        if (input.type === 'password') {
            if (input.id.includes('signup') && !validatePassword(value)) {
                inputGroup.classList.add('error');
                if (errorMessage) {
                    errorMessage.textContent = '密碼長度至少需要6個字元';
                }
                return false;
            }

            if (input.id === 'signup-confirm-password') {
                const password = document.getElementById('signup-password').value;
                if (value !== password) {
                    inputGroup.classList.add('error');
                    if (errorMessage) {
                        errorMessage.textContent = '密碼不一致';
                    }
                    return false;
                }
            }
        }

        inputGroup.classList.add('valid');
        return true;
    }

    // 切換登入 & 註冊
    tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            tabBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");

            isSignup = btn.dataset.tab === "signup";
            submitBtn.textContent = isSignup ? "Create an Account" : "Log In";
            loginForm.setAttribute("action", isSignup ? "/create_account" : "/log_in");

            // 切換顯示的欄位
            loginFields.forEach(field => {
                field.parentElement.style.display = isSignup ? "none" : "block";
                field.disabled = isSignup;
                field.required = !isSignup;
            });

            signupFields.forEach(field => {
                field.parentElement.style.display = isSignup ? "block" : "none";
                field.disabled = !isSignup;
                field.required = isSignup;
            });

            clearValidation();
            loginForm.reset();
        });
    });

    // 即時驗證
    const allInputs = [...loginFields, ...signupFields];
    allInputs.forEach(input => {
        input.addEventListener('input', () => {
            validateInput(input);
            
            // 當密碼改變時，重新驗證確認密碼
            if (input.id === 'signup-password') {
                const confirmPassword = document.getElementById('signup-confirm-password');
                if (confirmPassword.value) {
                    validateInput(confirmPassword);
                }
            }
        });

        input.addEventListener('blur', () => {
            validateInput(input);
        });
    });

    // 🔹 處理表單提交
    loginForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        let isValid = true;
        const activeInputs = isSignup ? signupFields : loginFields;
        
        activeInputs.forEach(input => {
            if (!validateInput(input)) {
                isValid = false;
            }
        });

        if (!isValid) {
            return;
        }

        submitBtn.disabled = true;
        submitBtn.textContent = "Processing... ⏳";

        try {
            const formData = new FormData(loginForm);
            const action = loginForm.getAttribute("action");

            const response = await fetch(action, {
                method: "POST",
                body: formData
            });

            // 🛠 **這裡新增：判斷伺服器回傳的 HTTP 狀態碼**
            if (response.status === 401) {
                alert("❌ 帳號或密碼錯誤！");
                return;
            }

            if (!response.ok) throw new Error(`HTTP 錯誤！狀態碼: ${response.status}`);

            const contentType = response.headers.get("content-type");
            if (!contentType || !contentType.includes("application/json")) {
                throw new Error("❌ 伺服器回應非 JSON 格式");
            }

            const data = await response.json();
            console.log("✅ 伺服器回應:", data);
            alert(data.message);

            if (data.status === "success") {
                localStorage.setItem("username", data.username);
                localStorage.setItem("permission", data.permission);
                window.location.href = data.redirect;
            }
        } catch (error) {
            console.error("❌ 發生錯誤:", error);
            alert("伺服器錯誤，請稍後再試！");
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = isSignup ? "Create an Account" : "Log In";
        }
    });
});
