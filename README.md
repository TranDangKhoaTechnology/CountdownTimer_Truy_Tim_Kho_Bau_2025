# CountdownTimer — Treasure Hunt 2025 ⏳🤖🏴‍☠️

Một ứng dụng **PyQt6** được xây dựng cho **UNETI Mini Robot Contest**, do **Khoa Điện & Tự động hoá (UNETI)** tổ chức, dùng trong mini game **“Treasure Hunt 2025”**.  
A **PyQt6** app built for the **UNETI Mini Robot Contest**, organized by the **Department of Electrical Engineering & Automation (UNETI)**, used in the mini game **“Treasure Hunt 2025”**.

Ứng dụng bao gồm:  
The app includes:
- **BẢNG ĐIỀU KHIỂN (CONTROL PANEL)** (dành cho BTC): điều khiển bộ đếm thời gian, đặt tên đội, và cộng/trừ điểm.  
  **CONTROL PANEL** (for the organizers): control the timer, set team names, and score points.
- **MÀN HÌNH HIỂN THỊ (DISPLAY)** (toàn màn hình cho máy chiếu): hiển thị **đồng hồ đếm ngược + bảng điểm** trên màn hình lớn.  
  **DISPLAY** (fullscreen projector view): show **countdown timer + scoreboard** on a big screen.

---

## Tính năng chính
## Key features

- **Hai cửa sổ**
  - **BẢNG ĐIỀU KHIỂN (CONTROL PANEL)**: chỉnh tên đội, tăng/giảm điểm, đặt thời gian, chọn màn hình hiển thị, mở/đóng Display.
  - **MÀN HÌNH HIỂN THỊ (DISPLAY - fullscreen)**: hiển thị **2 đội + điểm + thời gian**.  
- **Two windows**
  - **CONTROL PANEL**: edit team names, adjust score, set timer, choose display monitor, open/close Display.
  - **DISPLAY (fullscreen)**: shows **2 teams + score + timer**.

- **Chấm điểm theo kho báu**
  - 3 loại kho báu: **STONE / GOLD / DIAMOND**
  - 3 kho (cache): **K1 / K2 / K3**  
    > **K1 = Cache 1 (Kho 1)**, **K2 = Cache 2 (Kho 2)**, **K3 = Cache 3 (Kho 3)**.
  - Mỗi kho có giới hạn tổng (stone + gold + diamond) tối đa **3**.
  - Mỗi đội có hạn mức theo loại (mặc định): **stone 4**, **gold 3**, **diamond 2**.  
- **Treasure-based scoring**
  - 3 treasure types: **STONE / GOLD / DIAMOND**
  - 3 treasure caches (kho): **K1 / K2 / K3**  
    > **K1 = Cache 1 (Kho 1)**, **K2 = Cache 2 (Kho 2)**, **K3 = Cache 3 (Kho 3)**.
  - Each cache has a total limit (stone + gold + diamond) of **max 3**.
  - Each team has per-type quotas (default): **stone 4**, **gold 3**, **diamond 2**.

- **Điểm mặc định**
  - Stone: K1=5, K2=7, K3=10
  - Gold: K1=15, K2=17, K3=20
  - Diamond: K1=30, K2=32, K3=35  
- **Default points**
  - Stone: K1=5, K2=7, K3=10
  - Gold: K1=15, K2=17, K3=20
  - Diamond: K1=30, K2=32, K3=35

- **Điều chỉnh nhanh**
  - Phạt **−5** (không giới hạn)
  - Thưởng **+5** (không giới hạn)
  - Nút **“Absolute win”** để ép kết quả hiển thị thành 1–0 / 0–1 (hữu ích để chốt thắng tuyệt đối).  
- **Quick adjustments**
  - **−5** penalty (unlimited)
  - **+5** bonus (unlimited)
  - **“Absolute win”** button to force the displayed result to 1–0 / 0–1 (useful to finalize an absolute win).

- **Bộ đếm thời gian**
  - Đặt thời gian dạng `m:s` hoặc nhập **giây**
  - Preset nhanh: 03:30 / 03:00 / 01:00 / 00:30
  - Phát âm thanh ở **3 giây cuối** và khi **hết giờ** (nếu có file âm thanh).  
- **Timer**
  - Set time as `m:s` or input **seconds**
  - Quick presets: 03:30 / 03:00 / 01:00 / 00:30
  - Plays a sound in the **last 3 seconds** and when **time is up** (if audio files exist).

- **Hỗ trợ trình chiếu**
  - Chọn màn hình để mở Display toàn màn hình (phù hợp máy 2 màn hình).
  - Display sẽ mở fullscreen trên màn hình đã chọn.  
- **Presentation support**
  - Choose which monitor to use for the fullscreen Display (for dual-screen setups).
  - Display opens fullscreen on the selected monitor.

---

## Yêu cầu
## Requirements

- Python **3.10+**
- Dependencies được liệt kê trong `requirements.txt` (đã có sẵn trong repo).  
- Python **3.10+**
- Dependencies are listed in `requirements.txt` (already included in this repo).

Cài đặt dependencies:  
Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Chạy chương trình
## Run

```bash
python main.py
```

---

## Thư mục assets (icon + audio)
## Assets folder (icon + audio)

Ứng dụng sẽ tìm assets trong `./assets/` (và cũng hỗ trợ đường dẫn khi build thành exe).  
The app searches for assets in `./assets/` (and also supports bundled paths when built into an exe).

Cấu trúc gợi ý:  
Suggested structure:

```text
CountdownTimer_Truy_Tim_Kho_Bau_2025/
├─ main.py
├─ requirements.txt
└─ assets/
   ├─ timer.ico            # icon ứng dụng (tuỳ chọn) / app icon (optional)
   ├─ 3.wav (or 3s.wav)    # âm thanh 3 giây cuối (tuỳ chọn) / last-3-seconds sound (optional)
   └─ end.wav              # âm thanh hết giờ (tuỳ chọn) / time-up sound (optional)
```

---

## Hướng dẫn nhanh (BTC)
## Quick usage (Organizers)

1. Mở ứng dụng → đặt **Team Names** trong CONTROL PANEL.  
   Launch the app → set **Team Names** in the CONTROL PANEL.
2. Nhấn **Set** để đặt thời gian (hoặc chọn preset).  
   Press **Set** to set the timer (or pick a preset).
3. Nhấn **Open Display** để mở cửa sổ máy chiếu fullscreen.  
   Press **Open Display** to open the fullscreen projector window.
4. Nhấn **Start** để chạy đếm ngược.  
   Press **Start** to run the countdown.
5. Trong lúc thi đấu:
   - Cộng kho báu cho từng đội theo kho (K1/K2/K3) và loại (stone/gold/diamond).
   - Dùng **−5 / +5** khi cần.
   - Nếu dùng 2 màn hình, hãy chọn màn hình đích trước khi mở Display.  
   During the match:
   - Add treasures for each team by cache (K1/K2/K3) and type (stone/gold/diamond).
   - Use **−5 / +5** if needed.
   - If using two monitors, select the target screen before opening Display.
6. Dùng **Pause/Continue** để tạm dừng/tiếp tục.  
   Use **Pause/Continue** to pause/resume.

---

## Phím tắt
## Keyboard shortcuts

### BẢNG ĐIỀU KHIỂN (CONTROL PANEL)
### CONTROL PANEL
- `Space`: Tạm dừng / Tiếp tục  
  `Space`: Pause / Continue
- `S`: Bắt đầu  
  `S`: Start
- `P`: Tạm dừng (ép tạm dừng)  
  `P`: Pause (force pause)
- `C`: Tiếp tục (resume)  
  `C`: Continue (resume)
- `R`: Reset Timer  
  `R`: Reset Timer
- `D`: Mở Display  
  `D`: Open Display
- `Q`: Thoát ứng dụng  
  `Q`: Quit app

### MÀN HÌNH HIỂN THỊ (DISPLAY)
### DISPLAY
- `F` hoặc `F11`: Toàn màn hình  
  `F` or `F11`: Fullscreen
- `Esc` hoặc `Q`: Đóng Display  
  `Esc` or `Q`: Close Display

---

## Build file chạy độc lập (PyInstaller) — tuỳ chọn
## Build standalone (PyInstaller) — optional

Cài PyInstaller:  
Install PyInstaller:

```bash
pip install pyinstaller
```

Build (Windows):

```bash
pyinstaller --noconsole --onefile ^
  --add-data "assets;assets" ^
  --icon "assets/timer.ico" ^
  main.py
```

Build (macOS/Linux):

```bash
pyinstaller --noconsole --onefile \
  --add-data "assets:assets" \
  --icon "assets/timer.ico" \
  main.py
```

---

## Demo — Ảnh chụp màn hình
## Demo — Screenshots

> Những ảnh này minh hoạ giao diện ứng dụng: CONTROL PANEL, DISPLAY (fullscreen), và hộp thoại chọn màn hình.  
> These screenshots illustrate how the app looks: the CONTROL PANEL, the DISPLAY (fullscreen), and the Screen Select dialog.

### DISPLAY (toàn màn hình)
### DISPLAY (fullscreen)
<p align="center">
  <a href="assets/1.png">
    <img src="assets/1.png" alt="DISPLAY fullscreen" width="1100" />
  </a>
</p>
<p align="center"><em>DISPLAY (fullscreen) — đồng hồ lớn và bảng điểm, tối ưu cho máy chiếu.</em></p>
<p align="center"><em>DISPLAY (fullscreen) — large clock and scoreboard intended for projector output.</em></p>

### Control panel & Screen Select
### Control panel & Screen Select
<p align="center">
  <a href="assets/3.png">
    <img src="assets/3.png" alt="Control Panel" width="540" />
  </a>
  &nbsp;&nbsp;
  <a href="assets/2.png">
    <img src="assets/2.png" alt="Screen Select dialog" width="540" />
  </a>
</p>
<p align="center"><em>Bên trái: Control Panel — đặt đội, thời gian và điểm. — Bên phải: hộp thoại "Screen Select" để chọn màn hình hiển thị.</em></p>
<p align="center"><em>Left: Control Panel — set teams, time and scores. — Right: "Screen Select" dialog for choosing the target monitor.</em></p>

---

## Giấy phép
## License

Dự án này sử dụng **MIT License** — xem file [LICENSE](LICENSE) để biết chi tiết.  
This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
