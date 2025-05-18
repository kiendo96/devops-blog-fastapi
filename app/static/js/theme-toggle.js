document.addEventListener('DOMContentLoaded', () => {
    const themeToggleButton = document.getElementById('theme-toggle');
    const currentTheme = localStorage.getItem('theme') || 'light'; // Mặc định là light

    // Áp dụng theme đã lưu khi tải trang
    if (currentTheme === 'dark') {
        document.body.classList.add('dark-mode');
        if (themeToggleButton) {
            // Cập nhật icon của nút nếu cần (ví dụ: từ mặt trời sang mặt trăng)
            themeToggleButton.innerHTML = '<i class="fas fa-sun"></i>'; // Icon mặt trời (để chuyển sang sáng)
        }
    } else {
        if (themeToggleButton) {
            themeToggleButton.innerHTML = '<i class="fas fa-moon"></i>'; // Icon mặt trăng (để chuyển sang tối)
        }
    }

    if (themeToggleButton) {
        themeToggleButton.addEventListener('click', () => {
            document.body.classList.toggle('dark-mode');

            let theme = 'light';
            if (document.body.classList.contains('dark-mode')) {
                theme = 'dark';
                themeToggleButton.innerHTML = '<i class="fas fa-sun"></i>';
            } else {
                themeToggleButton.innerHTML = '<i class="fas fa-moon"></i>';
            }
            localStorage.setItem('theme', theme);
        });
    }
});