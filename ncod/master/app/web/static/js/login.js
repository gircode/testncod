document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const errorMessage = document.getElementById('errorMessage');
    const refreshCaptcha = document.getElementById('refreshCaptcha');
    const captchaImage = document.getElementById('captchaImage');
    
    // 刷新验证码的点击次数计数
    let refreshCount = 0;
    
    // 刷新验证码
    refreshCaptcha.addEventListener('click', function() {
        if (refreshCount >= 1) {
            errorMessage.textContent = '验证码刷新次数已达上限';
            return;
        }
        
        captchaImage.src = '/api/auth/captcha?' + new Date().getTime();
        refreshCount++;
        
        if (refreshCount >= 1) {
            refreshCaptcha.disabled = true;
            refreshCaptcha.style.opacity = '0.5';
        }
    });
    
    // 处理表单提交
    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(loginForm);
        const username = formData.get('username');
        const password = formData.get('password');
        const captcha = formData.get('captcha');
        
        // 表单验证
        if (!username || !password || !captcha) {
            errorMessage.textContent = '请填写所有必填项';
            return;
        }
        
        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username: username,
                    password: password,
                    captcha: captcha
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // 登录成功，跳转到主页
                window.location.href = '/dashboard';
            } else {
                // 显示错误信息
                errorMessage.textContent = data.message || '登录失败，请重试';
                
                // 如果是验证码错误，刷新验证码
                if (data.code === 'INVALID_CAPTCHA') {
                    captchaImage.src = '/api/auth/captcha?' + new Date().getTime();
                    document.getElementById('captcha').value = '';
                    refreshCount = 0;
                    refreshCaptcha.disabled = false;
                    refreshCaptcha.style.opacity = '1';
                }
            }
        } catch (error) {
            errorMessage.textContent = '网络错误，请稍后重试';
            console.error('Login error:', error);
        }
    });
}); 