import sys
import copy
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QWidget, QDialog, QLabel, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QSizePolicy, QGridLayout, QGroupBox,
    QFrame, QScrollArea, QSpinBox, QAbstractSpinBox, QComboBox,
    QColorDialog,
)
from PyQt6.QtGui import (
    QFont, QFontMetrics, QKeySequence, QShortcut, QIcon, QPalette, QColor, QGuiApplication
)
from PyQt6.QtCore import Qt, QTimer, QUrl, QElapsedTimer, QObject, pyqtSignal
from PyQt6.QtMultimedia import QSoundEffect


# ================== Asset helpers ==================
def _exe_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _meipass_dir() -> Path | None:
    mp = getattr(sys, "_MEIPASS", None)
    return Path(mp) if mp else None


def find_asset_first(name: str) -> str | None:
    candidates: list[Path] = []
    exe_dir = _exe_dir()
    candidates += [exe_dir / "assets" / name, exe_dir / name]

    cwd = Path.cwd()
    candidates += [cwd / "assets" / name, cwd / name]

    mp = _meipass_dir()
    if mp:
        candidates += [mp / "assets" / name, mp / name]

    for p in candidates:
        try:
            if p.exists():
                return str(p.resolve())
        except Exception:
            pass
    return None


# ================== Time dialog ==================
class TimeDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Set time")
        self.seconds = 0
        self.setFixedSize(420, 230)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        title = QLabel("Thời gian (m:s hoặc giây):")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        layout.addWidget(title)

        self.input = QLineEdit("03:30")
        self.input.setPlaceholderText("VD: 3:30 hoặc 210")
        self.input.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        layout.addWidget(self.input)

        preset = QHBoxLayout()
        for t in ["03:30", "03:00", "01:00", "00:30"]:
            b = QPushButton(t)
            b.clicked.connect(lambda _, v=t: self.input.setText(v))
            preset.addWidget(b)
        layout.addLayout(preset)

        row = QHBoxLayout()
        ok = QPushButton("OK")
        ok.setStyleSheet("background:#2ecc71; color:white; border-radius:10px; padding:6px 10px; font-weight:800;")
        ok.clicked.connect(self.apply)
        cancel = QPushButton("Cancel")
        cancel.setStyleSheet("background:#e74c3c; color:white; border-radius:10px; padding:6px 10px; font-weight:800;")
        cancel.clicked.connect(self.reject)
        row.addWidget(ok)
        row.addWidget(cancel)
        layout.addLayout(row)

        for seq, slot in [("Return", self.apply), ("Enter", self.apply), ("Esc", self.reject)]:
            sc = QShortcut(QKeySequence(seq), self, slot)
            sc.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)

    def apply(self):
        t = self.input.text().strip().lower()
        try:
            if ":" in t:
                m, s = t.split(":")
                self.seconds = int(m) * 60 + int(s)
            else:
                self.seconds = int(t)
        except Exception:
            self.seconds = 0
        self.accept()


# ================== Screen select dialog ==================
class ScreenSelectDialog(QDialog):
    def __init__(self, parent=None, current_index: int | None = None):
        super().__init__(parent)
        self.setWindowTitle("Chọn màn hình hiển thị")
        self.setFixedSize(520, 190)
        self.selected_index: int | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 12)
        root.setSpacing(10)

        title = QLabel("Chọn màn hình để mở DISPLAY:")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        root.addWidget(title)

        self.cb = QComboBox()
        self.cb.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))

        self._screens = QGuiApplication.screens()
        for i, s in enumerate(self._screens):
            g = s.geometry()
            name = s.name() or f"Screen {i+1}"
            text = f"[{i}] {name} — {g.width()}x{g.height()} @ ({g.x()},{g.y()})"
            self.cb.addItem(text, i)

        if current_index is not None and 0 <= current_index < self.cb.count():
            self.cb.setCurrentIndex(current_index)

        root.addWidget(self.cb)

        hint = QLabel("Tip: Nếu có 2 màn hình, bạn có thể chọn màn hình phụ để chiếu.")
        hint.setStyleSheet("color:#444;")
        root.addWidget(hint)

        row = QHBoxLayout()
        row.addStretch(1)

        ok = QPushButton("OK")
        ok.setStyleSheet("background:#2ecc71; color:white; border-radius:10px; padding:6px 14px; font-weight:900;")
        cancel = QPushButton("Cancel")
        cancel.setStyleSheet("background:#e74c3c; color:white; border-radius:10px; padding:6px 14px; font-weight:900;")
        ok.clicked.connect(self._accept)
        cancel.clicked.connect(self.reject)
        row.addWidget(ok)
        row.addWidget(cancel)
        root.addLayout(row)

        for seq, slot in [("Return", self._accept), ("Enter", self._accept), ("Esc", self.reject)]:
            sc = QShortcut(QKeySequence(seq), self, slot)
            sc.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)

    def _accept(self):
        self.selected_index = int(self.cb.currentData())
        self.accept()


# ================== Compact counter:  [-] [spinbox] [+] ==================
class CounterControl(QWidget):
    valueChanged = pyqtSignal(int)

    def __init__(
        self,
        value: int = 0,
        min_value: int = 0,
        max_value: int = 99,
        step: int = 1,
        spin_w: int | None = None,
    ):
        super().__init__()
        self._min = int(min_value)
        self._max = int(max_value)
        self._step = int(step)

        BTN_W = 30
        BTN_H = 30
        SPIN_W = BTN_W if spin_w is None else max(30, int(spin_w))

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        self.btnMinus = QPushButton("−")
        self.btnPlus = QPushButton("+")

        btn_style = f"""
            QPushButton{{
                background:#2f3b46;
                color:white;
                font-weight:900;
                border-radius:8px;
                min-width:{BTN_W}px;
                min-height:{BTN_H}px;
                padding:0px;
            }}
            QPushButton:pressed{{ background:#25303a; }}
        """
        self.btnMinus.setStyleSheet(btn_style)
        self.btnPlus.setStyleSheet(btn_style)

        self.spin = QSpinBox()
        self.spin.setRange(self._min, self._max)
        self.spin.setSingleStep(self._step)
        self.spin.setValue(int(value))
        self.spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin.setFixedSize(SPIN_W, BTN_H)
        self.spin.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        self.spin.setStyleSheet("""
            QSpinBox{
                background:white;
                color:#111;
                border:1px solid #c7c7c7;
                border-radius:8px;
                padding-bottom:1px;
            }
            QSpinBox:focus{
                border:1px solid #6aa9ff;
            }
        """)

        root.addWidget(self.btnMinus)
        root.addWidget(self.spin)
        root.addWidget(self.btnPlus)

        self.btnMinus.clicked.connect(self._minus)
        self.btnPlus.clicked.connect(self._plus)
        self.spin.valueChanged.connect(lambda v: self.valueChanged.emit(int(v)))

    def value(self) -> int:
        return int(self.spin.value())

    def setValue(self, v: int, emit_signal: bool = False):
        v = max(self._min, min(self._max, int(v)))
        if v == self.spin.value():
            return
        self.spin.blockSignals(True)
        self.spin.setValue(v)
        self.spin.blockSignals(False)
        if emit_signal:
            self.valueChanged.emit(int(v))

    def setRange(self, min_v: int, max_v: int, clamp_current: bool = True):
        min_v = int(min_v)
        max_v = int(max_v)
        if max_v < min_v:
            max_v = min_v

        self._min = min_v
        self._max = max_v

        self.spin.blockSignals(True)
        self.spin.setRange(self._min, self._max)
        if clamp_current:
            if self.spin.value() < self._min:
                self.spin.setValue(self._min)
            elif self.spin.value() > self._max:
                self.spin.setValue(self._max)
        self.spin.blockSignals(False)

    def _minus(self):
        self.setValue(self.value() - self._step, emit_signal=True)

    def _plus(self):
        self.setValue(self.value() + self._step, emit_signal=True)


# ================== Controller: treasures -> score ==================
class MatchController(QObject):
    scoreboardChanged = pyqtSignal(str, int, str, int)  # team1, score1, team2, score2 (DISPLAY SCORE)
    timeTextChanged = pyqtSignal(str)
    stateChanged = pyqtSignal(bool, bool)

    teamColorChanged = pyqtSignal(int, str)  # team, color_hex

    DEFAULT_POINTS = {
        "stone":   {1: 5,  2: 7,  3: 10},
        "gold":    {1: 15, 2: 17, 3: 20},
        "diamond": {1: 30, 2: 32, 3: 35},
    }

    # quota theo mỗi đội (2 bên độc lập)
    MAX_TREASURES_PER_TEAM = {
        "stone": 4,
        "gold": 3,
        "diamond": 2,
    }

    # ✅ MỖI KHO (K1/K2/K3) TỔNG (ĐÁ+VÀNG+KIM CƯƠNG) TỐI ĐA 3
    MAX_PER_KHO_TOTAL = 3

    def __init__(self):
        super().__init__()
        self.team1 = "ĐỘI ĐỎ"
        self.team2 = "ĐỘI XANH"

        # ✅ tách riêng độ dài tên từng đội (bạn đổi số ở đây)
        self.team_name_maxlen = {
            1: 60,  # Đội 1 tối đa 40 ký tự
            2: 60,  # Đội 2 tối đa 60 ký tự
        }

        self.team_colors = {
            1: "#e74c3c",
            2: "#1e73be",
        }

        self.points = copy.deepcopy(self.DEFAULT_POINTS)

        self.counts = {
            1: {"stone": {1: 0, 2: 0, 3: 0}, "gold": {1: 0, 2: 0, 3: 0}, "diamond": {1: 0, 2: 0, 3: 0}},
            2: {"stone": {1: 0, 2: 0, 3: 0}, "gold": {1: 0, 2: 0, 3: 0}, "diamond": {1: 0, 2: 0, 3: 0}},
        }

        self.penalty_minus5 = {1: 0, 2: 0}   # không giới hạn (>=0)
        self.bonus_plus5 = {1: 0, 2: 0}      # ✅ không giới hạn (>=0)

        self.abs_winner: int | None = None

        # ----- timer -----
        self.seconds = 0
        self.running = False
        self.paused = False
        self.elapsed = QElapsedTimer()
        self.end_epoch_ms = None
        self.remaining_ms_pause = 0

        self.played3 = False
        self.playedEnd = False
        self.sound3 = self._load_sound_any(["3.wav", "3s.wav"])
        self.soundEnd = self._load_sound_any(["end.wav"])

        self.timer_ms = QTimer()
        self.timer_ms.timeout.connect(self._tick)
        self.timer_ms.start(100)

        # đảm bảo tên mặc định cũng tuân maxlen
        self.set_team_names(self.team1, self.team2)

    @staticmethod
    def _fmt(sec: int) -> str:
        m, s = divmod(max(0, int(sec)), 60)
        return f"{m:02d}:{s:02d}"

    def _load_sound_any(self, candidates: list[str]):
        full = None
        for name in candidates:
            full = find_asset_first(name)
            if full:
                break
        if not full:
            return None
        s = QSoundEffect()
        s.setSource(QUrl.fromLocalFile(full))
        s.setLoopCount(1)
        s.setVolume(0.9)
        return s

    # -------- colors --------
    def get_team_color(self, team: int) -> str:
        return str(self.team_colors.get(int(team), "#333333"))

    def set_team_color(self, team: int, color_hex: str):
        team = int(team)
        qc = QColor((color_hex or "").strip())
        if not qc.isValid():
            return
        new_hex = qc.name()
        if self.team_colors.get(team) == new_hex:
            return
        self.team_colors[team] = new_hex
        self.teamColorChanged.emit(team, new_hex)

    # -------- kho / quota helpers --------
    def team_capacity_for_type(self, team: int, treasure_type: str) -> int:
        _ = team
        return int(self.MAX_TREASURES_PER_TEAM.get(treasure_type, 999))

    def kho_other_types_sum(self, team: int, kho: int, exclude_type: str) -> int:
        total = 0
        for t in ("stone", "gold", "diamond"):
            if t == exclude_type:
                continue
            total += int(self.counts[team][t][kho])
        return int(total)

    def kho_free_space_for_type(self, team: int, kho: int, treasure_type: str) -> int:
        """
        Số chỗ tối đa còn lại trong kho (theo rule tổng kho <= 3),
        dành cho treasure_type (tức là 3 - (2 loại còn lại)).
        """
        other = self.kho_other_types_sum(team, kho, treasure_type)
        return max(0, int(self.MAX_PER_KHO_TOTAL) - int(other))

    # -------- scoring --------
    def compute_score(self, team: int) -> int:
        total = 0
        for t in ("stone", "gold", "diamond"):
            for kho in (1, 2, 3):
                c = int(self.counts[team][t][kho])
                total += c * int(self.points[t][kho])
        total -= int(self.penalty_minus5[team]) * 5
        total += int(self.bonus_plus5[team]) * 5
        return total

    def get_display_scores(self) -> tuple[int, int]:
        real1 = self.compute_score(1)
        real2 = self.compute_score(2)
        if self.abs_winner == 1:
            return (1, 0)
        if self.abs_winner == 2:
            return (0, 1)
        return (real1, real2)

    def get_totals(self, team: int, treasure_type: str) -> tuple[int, int, int, int]:
        k1 = int(self.counts[team][treasure_type][1])
        k2 = int(self.counts[team][treasure_type][2])
        k3 = int(self.counts[team][treasure_type][3])
        return (k1 + k2 + k3, k1, k2, k3)

    # -------- emits --------
    def _freeze_timer_now(self):
        if not self.running:
            return

        if (not self.paused) and (self.end_epoch_ms is not None):
            now = self.elapsed.elapsed()
            remaining_ms = max(0, int(self.end_epoch_ms - now))
            self.seconds = int(remaining_ms // 1000)

        self.running = False
        self.paused = False
        self.end_epoch_ms = None
        self.remaining_ms_pause = 0

    def _emit_all(self):
        s1, s2 = self.get_display_scores()
        self.scoreboardChanged.emit(self.team1, int(s1), self.team2, int(s2))
        self.timeTextChanged.emit(self._fmt(self.seconds))
        self.stateChanged.emit(self.running, self.paused)

    # -------- public api --------
    def set_team_names(self, t1: str, t2: str):
        # ✅ normalize + clamp tách riêng theo từng đội
        def norm(s: str, maxlen: int) -> str:
            s = " ".join((s or "").strip().split())  # gom nhiều space thành 1
            if maxlen is not None and int(maxlen) > 0 and len(s) > int(maxlen):
                s = s[: int(maxlen)]
            return s

        m1 = int(self.team_name_maxlen.get(1, 80))
        m2 = int(self.team_name_maxlen.get(2, 80))

        self.team1 = norm(t1, m1) or "ĐỘI 1"
        self.team2 = norm(t2, m2) or "ĐỘI 2"
        self._emit_all()

    def set_count(self, team: int, treasure_type: str, kho: int, value: int):
        """
        Clamp theo 2 rule:
        (1) quota theo LOẠI trong đội: K1+K2+K3 <= MAX_TREASURES_PER_TEAM[type]
        (2) quota theo KHO trong đội: (stone+gold+diamond) tại Kx <= 3
        """
        team = int(team)
        kho = int(kho)
        value = max(0, int(value))

        # rule (1): theo loại
        cap_type = int(self.team_capacity_for_type(team, treasure_type))
        other_khos_same_type = 0
        for k in (1, 2, 3):
            if k != kho:
                other_khos_same_type += int(self.counts[team][treasure_type][k])
        max_by_type = max(0, cap_type - other_khos_same_type)

        # rule (2): theo kho (tổng kho <= 3)
        max_by_kho = int(self.kho_free_space_for_type(team, kho, treasure_type))

        allowed_here = max(0, min(max_by_type, max_by_kho))
        value = min(value, allowed_here)

        self.counts[team][treasure_type][kho] = value
        self._emit_all()

    def set_penalty_minus5(self, team: int, value: int):
        self.penalty_minus5[team] = max(0, int(value))
        self._emit_all()

    def set_bonus_plus5(self, team: int, value: int):
        # ✅ không giới hạn, chỉ clamp >= 0
        self.bonus_plus5[team] = max(0, int(value))
        self._emit_all()

    def reset_scoring_and_coeff(self):
        self.points = copy.deepcopy(self.DEFAULT_POINTS)
        for team in (1, 2):
            for t in ("stone", "gold", "diamond"):
                for kho in (1, 2, 3):
                    self.counts[team][t][kho] = 0
            self.penalty_minus5[team] = 0
            self.bonus_plus5[team] = 0
        self.abs_winner = None
        self._emit_all()

    def check_absolute_team(self, team: int) -> bool:
        kho_total = {1: 0, 2: 0, 3: 0}
        total_all = 0
        for kho in (1, 2, 3):
            for t in ("stone", "gold", "diamond"):
                kho_total[kho] += int(self.counts[team][t][kho])
            total_all += kho_total[kho]

        cond1 = (kho_total[1] >= 1 and kho_total[2] >= 1 and kho_total[3] >= 1)
        cond2 = (kho_total[1] == 3 or kho_total[2] == 3 or kho_total[3] == 3)
        cond3 = (total_all >= 6)
        return bool(cond1 and cond2 and cond3)

    def set_absolute_win(self, winner: int | None):
        if winner in (1, 2):
            self._freeze_timer_now()
        self.abs_winner = winner
        self._emit_all()

    def set_time_seconds(self, seconds: int):
        self.abs_winner = None
        self.seconds = max(0, int(seconds))
        self.running = False
        self.paused = False
        self.end_epoch_ms = None
        self.remaining_ms_pause = 0
        self.played3 = False
        self.playedEnd = False
        self._emit_all()

    def start(self):
        if self.abs_winner is not None:
            return
        if self.seconds <= 0:
            return
        self.running = True
        self.paused = False
        self.played3 = False
        self.playedEnd = False
        self.elapsed.restart()
        self.end_epoch_ms = self.elapsed.elapsed() + self.seconds * 1000
        self.stateChanged.emit(self.running, self.paused)

    def reset_timer_only(self):
        self.abs_winner = None
        self.set_time_seconds(0)

    def force_pause(self):
        if self.abs_winner is not None:
            return
        if self.running and not self.paused:
            now = self.elapsed.elapsed()
            self.remaining_ms_pause = max(0, int(self.end_epoch_ms - now)) if self.end_epoch_ms else self.seconds * 1000
            self.seconds = int(self.remaining_ms_pause // 1000)
            self.paused = True
            self.timeTextChanged.emit(self._fmt(self.seconds))
            self.stateChanged.emit(self.running, self.paused)

    def resume(self):
        if self.abs_winner is not None:
            return
        if self.running and self.paused:
            remain = max(0, int(self.remaining_ms_pause))
            self.elapsed.restart()
            self.end_epoch_ms = self.elapsed.elapsed() + remain
            self.paused = False
            self.stateChanged.emit(self.running, self.paused)

    def toggle_pause(self):
        if self.abs_winner is not None:
            return
        if not self.running:
            return
        if self.paused:
            self.resume()
        else:
            self.force_pause()

    def _tick(self):
        if self.abs_winner is not None:
            return

        if self.running and (not self.paused) and self.end_epoch_ms is not None:
            now = self.elapsed.elapsed()
            remaining_ms = max(0, self.end_epoch_ms - now)

            if 0 < remaining_ms <= 4000 and (not self.played3) and self.sound3:
                self.sound3.stop()
                self.sound3.play()
                self.played3 = True

            sec_disp = remaining_ms // 1000
            if int(sec_disp) != int(self.seconds):
                self.seconds = int(sec_disp)
                self.timeTextChanged.emit(self._fmt(self.seconds))

            if remaining_ms <= 0:
                if (not self.playedEnd) and self.soundEnd:
                    self.soundEnd.stop()
                    self.soundEnd.play()
                    self.playedEnd = True

                self.running = False
                self.paused = False
                self.seconds = 0
                self.end_epoch_ms = None
                self.timeTextChanged.emit(self._fmt(self.seconds))
                self.stateChanged.emit(self.running, self.paused)


# ================== Display window (fullscreen) ==================
class DisplayWindow(QWidget):
    BG = "#CFE8FF"

    def __init__(self, c: MatchController):
        super().__init__()
        self.c = c
        self.setWindowTitle("DISPLAY")
        self.setStyleSheet(f"QWidget{{ background:{self.BG}; }} QLabel{{ color:#111; }}")

        self.fullTeam1 = c.team1
        self.fullTeam2 = c.team2

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 18, 24, 24)
        root.setSpacing(16)

        self.scoreRowWidget = QWidget()
        row = QHBoxLayout(self.scoreRowWidget)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)

        # LEFT
        self.leftWrap = QWidget()
        l = QVBoxLayout(self.leftWrap)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(10)
        l.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)

        self.card1 = QFrame()
        c1 = QVBoxLayout(self.card1)
        c1.setContentsMargins(0, 0, 0, 0)
        c1.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lblScore1 = QLabel("0")
        self.lblScore1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lblScore1.setStyleSheet("color:white; font-weight:1000;")
        c1.addWidget(self.lblScore1)

        self.lblTeam1 = QLabel(self.fullTeam1)
        self.lblTeam1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lblTeam1.setStyleSheet("color:#111; font-weight:1000;")
        self.lblTeam1.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        l.addWidget(self.card1, 0, Qt.AlignmentFlag.AlignHCenter)
        l.addWidget(self.lblTeam1, 0, Qt.AlignmentFlag.AlignHCenter)

        # RIGHT
        self.rightWrap = QWidget()
        r = QVBoxLayout(self.rightWrap)
        r.setContentsMargins(0, 0, 0, 0)
        r.setSpacing(10)
        r.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)

        self.card2 = QFrame()
        c2 = QVBoxLayout(self.card2)
        c2.setContentsMargins(0, 0, 0, 0)
        c2.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lblScore2 = QLabel("0")
        self.lblScore2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lblScore2.setStyleSheet("color:white; font-weight:1000;")
        c2.addWidget(self.lblScore2)

        self.lblTeam2 = QLabel(self.fullTeam2)
        self.lblTeam2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lblTeam2.setStyleSheet("color:#111; font-weight:1000;")
        self.lblTeam2.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        r.addWidget(self.card2, 0, Qt.AlignmentFlag.AlignHCenter)
        r.addWidget(self.lblTeam2, 0, Qt.AlignmentFlag.AlignHCenter)

        row.addWidget(self.leftWrap, 1)
        row.addWidget(self.rightWrap, 1)
        root.addWidget(self.scoreRowWidget, 0)

        # BIG TIMER
        self.timerLabel = QLabel("00:00")
        self.timerLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timerLabel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.timerLabel.setStyleSheet("color:#111; font-weight:1000;")
        root.addWidget(self.timerLabel, 1)

        root.setStretch(0, 4)
        root.setStretch(1, 10)

        self.c.scoreboardChanged.connect(self.onScoreboard)
        self.c.timeTextChanged.connect(self.onTimeText)
        self.c.teamColorChanged.connect(self.onTeamColorChanged)

        self._apply_team_colors()

        s1, s2 = self.c.get_display_scores()
        self.onScoreboard(self.c.team1, s1, self.c.team2, s2)
        self.onTimeText(self.c._fmt(self.c.seconds))

        QTimer.singleShot(0, self._fit_layout)

        for seq, slot in [
            ("Esc", self.close),
            ("F11", self.showFullScreen),
            ("F", self.showFullScreen),
            ("Q", self.close),
        ]:
            sc = QShortcut(QKeySequence(seq), self, slot)
            sc.setContext(Qt.ShortcutContext.ApplicationShortcut)

    def _apply_team_colors(self):
        col1 = self.c.get_team_color(1)
        col2 = self.c.get_team_color(2)
        self.card1.setStyleSheet(f"QFrame{{ background:{col1}; border-radius:22px; }}")
        self.card2.setStyleSheet(f"QFrame{{ background:{col2}; border-radius:22px; }}")

    def onTeamColorChanged(self, team: int, color_hex: str):
        _ = team
        _ = color_hex
        self._apply_team_colors()
        QTimer.singleShot(0, self._fit_layout)

    def show_on_screen(self, screen_index: int | None = None):
        screens = QGuiApplication.screens()
        if not screens:
            self.showFullScreen()
            return

        if screen_index is None:
            screen_index = 1 if len(screens) >= 2 else 0

        if screen_index < 0 or screen_index >= len(screens):
            screen_index = 0

        g = screens[screen_index].geometry()
        self.setGeometry(g)
        self.move(g.topLeft())
        self.showFullScreen()
        self.raise_()
        self.activateWindow()

    def _elide_name(self, label: QLabel, full_text: str):
        w = label.contentsRect().width() + 60
        if w < 80:
            label.setText(full_text)
            return
        fm = QFontMetrics(label.font())
        label.setText(fm.elidedText(full_text, Qt.TextElideMode.ElideRight, w))

    def onScoreboard(self, team1, score1, team2, score2):
        self.fullTeam1 = team1
        self.fullTeam2 = team2
        self.lblScore1.setText(str(score1))
        self.lblScore2.setText(str(score2))
        QTimer.singleShot(0, self._fit_layout)

    def onTimeText(self, text: str):
        self.timerLabel.setText(text)
        QTimer.singleShot(0, self._fit_layout)

    def resizeEvent(self, event):
        QTimer.singleShot(0, self._fit_layout)
        super().resizeEvent(event)

    def _fit_layout(self):
        w = max(1, self.width())
        h = max(1, self.height())

        card_w = max(260, int(w * 0.26))
        card_h = max(150, int(h * 0.20))
        self.card1.setFixedSize(card_w, card_h)
        self.card2.setFixedSize(card_w, card_h)

        score_pt = max(52, int(card_h * 0.52))
        team_pt = max(28, int(h * 0.055))

        self.lblScore1.setFont(QFont("Segoe UI", score_pt, QFont.Weight.Bold))
        self.lblScore2.setFont(QFont("Segoe UI", score_pt, QFont.Weight.Bold))
        self.lblTeam1.setFont(QFont("Segoe UI", team_pt, QFont.Weight.Bold))
        self.lblTeam2.setFont(QFont("Segoe UI", team_pt, QFont.Weight.Bold))

        team_h = max(44, int(team_pt * 1.75))
        self.lblTeam1.setFixedHeight(team_h)
        self.lblTeam2.setFixedHeight(team_h)
        self.scoreRowWidget.setFixedHeight(card_h + team_h + 22)

        text = self.timerLabel.text() or "00:00"
        rect = self.timerLabel.contentsRect()
        avail_w = max(10, rect.width())
        avail_h = max(10, rect.height())

        lo, hi = 10, max(12, avail_h)
        best = lo
        while lo <= hi:
            mid = (lo + hi) // 2
            f = QFont("Segoe UI", int(mid), QFont.Weight.Bold)
            fm = QFontMetrics(f)
            if fm.horizontalAdvance(text) <= avail_w and fm.height() <= avail_h:
                best = mid
                lo = mid + 1
            else:
                hi = mid - 1

        best = int(best * 0.90)
        self.timerLabel.setFont(QFont("Segoe UI", max(10, best), QFont.Weight.Bold))

        # mỗi label đã “tách riêng” nên elide theo từng đội độc lập
        self._elide_name(self.lblTeam1, self.fullTeam1)
        self._elide_name(self.lblTeam2, self.fullTeam2)


# ================== Treasure block ==================
class TreasureBlock(QWidget):
    def __init__(self, title: str, emoji: str, team: int, ttype: str, controller: MatchController, color: str):
        super().__init__()
        self.team = int(team)
        self.ttype = str(ttype)
        self.c = controller
        self.title = title
        self.emoji = emoji
        self._color = str(color)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        self.header = QLabel(f"{self.emoji} {self.title}: 0")
        self.header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.header)
        self.set_header_color(self._color)

        row = QHBoxLayout()
        row.setContentsMargins(4, 2, 4, 6)
        row.setSpacing(10)

        def mk_kho(tag: str):
            wrap = QWidget()
            wrap.setStyleSheet("background:#f5f7fb; border-radius:12px;")
            v = QVBoxLayout(wrap)
            v.setContentsMargins(10, 8, 10, 10)
            v.setSpacing(6)

            lab = QLabel(tag)
            lab.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lab.setStyleSheet("font-weight:900; color:#111;")

            # ✅ UI: mỗi kho tối đa 3 (controller sẽ clamp thêm theo rule tổng kho)
            ct = CounterControl(0, 0, 3, 1)
            v.addWidget(lab)
            v.addWidget(ct, 0, Qt.AlignmentFlag.AlignCenter)
            return wrap, ct

        w1, self.ct1 = mk_kho("K1")
        w2, self.ct2 = mk_kho("K2")
        w3, self.ct3 = mk_kho("K3")

        row.addWidget(w1, 1)
        row.addWidget(w2, 1)
        row.addWidget(w3, 1)
        root.addLayout(row)

        def cap_type_total() -> int:
            return int(self.c.team_capacity_for_type(self.team, self.ttype))

        def free_in_kho(kho: int) -> int:
            return int(self.c.kho_free_space_for_type(self.team, kho, self.ttype))

        def update_dynamic_limits(k1: int, k2: int, k3: int):
            cap = cap_type_total()

            # max theo quota loại
            m1_by_type = max(0, cap - (k2 + k3))
            m2_by_type = max(0, cap - (k1 + k3))
            m3_by_type = max(0, cap - (k1 + k2))

            # max theo quota kho tổng <= 3
            m1_by_kho = free_in_kho(1)
            m2_by_kho = free_in_kho(2)
            m3_by_kho = free_in_kho(3)

            m1 = min(m1_by_type, m1_by_kho, 3)
            m2 = min(m2_by_type, m2_by_kho, 3)
            m3 = min(m3_by_type, m3_by_kho, 3)

            self.ct1.setRange(0, m1, clamp_current=True)
            self.ct2.setRange(0, m2, clamp_current=True)
            self.ct3.setRange(0, m3, clamp_current=True)

        def sync_from_controller():
            total, k1, k2, k3 = self.c.get_totals(self.team, self.ttype)
            self.ct1.setValue(k1, emit_signal=False)
            self.ct2.setValue(k2, emit_signal=False)
            self.ct3.setValue(k3, emit_signal=False)
            update_dynamic_limits(k1, k2, k3)

            max_team = int(self.c.MAX_TREASURES_PER_TEAM.get(self.ttype, 0))
            self.header.setText(f"{self.emoji} {self.title}: {total}/{max_team}")

        def apply_kho(kho: int, v: int):
            k1 = self.ct1.value()
            k2 = self.ct2.value()
            k3 = self.ct3.value()

            cap = cap_type_total()
            v = max(0, int(v))

            if kho == 1:
                other_same_type = k2 + k3
            elif kho == 2:
                other_same_type = k1 + k3
            else:
                other_same_type = k1 + k2

            allowed_by_type = max(0, cap - other_same_type)
            allowed_by_kho = free_in_kho(kho)
            allowed = min(allowed_by_type, allowed_by_kho, 3)

            v2 = min(v, allowed)

            if kho == 1:
                self.ct1.setValue(v2, emit_signal=False)
                k1 = v2
            elif kho == 2:
                self.ct2.setValue(v2, emit_signal=False)
                k2 = v2
            else:
                self.ct3.setValue(v2, emit_signal=False)
                k3 = v2

            update_dynamic_limits(k1, k2, k3)
            self.c.set_count(self.team, self.ttype, kho, v2)
            sync_from_controller()

        self.ct1.valueChanged.connect(lambda v: apply_kho(1, v))
        self.ct2.valueChanged.connect(lambda v: apply_kho(2, v))
        self.ct3.valueChanged.connect(lambda v: apply_kho(3, v))

        self.c.scoreboardChanged.connect(lambda *_: sync_from_controller())
        sync_from_controller()

    def set_header_color(self, color: str):
        self._color = str(color)
        self.header.setStyleSheet(f"""
            QLabel{{
                background:{self._color};
                color:white;
                font-weight:800;
                border-radius:12px;
                padding:6px 10px;
                min-height:34px;
            }}
        """)


# ================== Team panel ==================
class TeamPanel(QGroupBox):
    def __init__(self, team: int, controller: MatchController):
        super().__init__()
        self.team = int(team)
        self.c = controller

        self.setTitle(f"Đội {self.team}")

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        top = QGridLayout()
        top.setHorizontalSpacing(10)
        top.setVerticalSpacing(8)

        self.inName = QLineEdit(self.c.team1 if self.team == 1 else self.c.team2)
        self.inName.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))

        # ✅ max length tách riêng từng đội (lấy từ controller)
        maxlen = int(self.c.team_name_maxlen.get(self.team, 80))
        self.inName.setMaxLength(maxlen)
        # nếu text có sẵn vượt quá maxlen, cắt luôn cho chắc
        if len(self.inName.text()) > maxlen:
            self.inName.setText(self.inName.text()[:maxlen])

        self.inName.setClearButtonEnabled(True)
        self.inName.setToolTip(self.inName.text())
        self.inName.textChanged.connect(self.inName.setToolTip)

        self.lblScore = QLabel("0")
        self.lblScore.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lblScore.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.lblScore.setStyleSheet("background:#f7f8fb; color:#111; border:1px solid #e0e3e8; border-radius:12px; padding:8px 10px;")

        self.btnAbsolute = QPushButton("Tuyệt đối")
        self.btnAbsolute.setStyleSheet("background:#f1c40f; color:#111;")
        self.btnAbsolute.clicked.connect(self._toggle_absolute)

        self.btnColor = QPushButton("Màu")
        self.btnColor.setFixedWidth(70)
        self.btnColor.clicked.connect(self._pick_color)

        top.addWidget(QLabel("Tên đội"), 0, 0)
        top.addWidget(self.inName,        0, 1)
        top.addWidget(QLabel("Tổng điểm"),0, 2)
        top.addWidget(self.lblScore,      0, 3)
        top.addWidget(self.btnAbsolute,   0, 4)
        top.addWidget(self.btnColor,      0, 5)
        root.addLayout(top)

        adj_row = QHBoxLayout()
        adj_row.setSpacing(14)

        pen_label = QLabel("Lỗi −5:")
        pen_label.setStyleSheet("font-weight:900; color:#111;")
        self.penCounter = CounterControl(0, 0, 2147483647, 1, spin_w=80)
        self.penCounter.valueChanged.connect(lambda v: self.c.set_penalty_minus5(self.team, v))

        bonus_label = QLabel("Về +5:")
        bonus_label.setStyleSheet("font-weight:900; color:#111;")
        # ✅ bonus +5 KHÔNG GIỚI HẠN
        self.bonusCounter = CounterControl(0, 0, 2147483647, 1, spin_w=80)
        self.bonusCounter.valueChanged.connect(lambda v: self.c.set_bonus_plus5(self.team, v))

        adj_row.addWidget(pen_label)
        adj_row.addWidget(self.penCounter, 0)
        adj_row.addSpacing(12)
        adj_row.addWidget(bonus_label)
        adj_row.addWidget(self.bonusCounter, 0)
        adj_row.addStretch(1)
        root.addLayout(adj_row)

        col = self.c.get_team_color(self.team)
        self.blockStone = TreasureBlock("ĐÁ", "🪨", self.team, "stone", controller, col)
        self.blockGold  = TreasureBlock("VÀNG", "🟡", self.team, "gold", controller, col)
        self.blockDia   = TreasureBlock("KIM CƯƠNG", "💎", self.team, "diamond", controller, col)

        root.addWidget(self.blockStone)
        root.addWidget(self.blockGold)
        root.addWidget(self.blockDia)

        self.c.scoreboardChanged.connect(self._on_scoreboard)
        self.c.teamColorChanged.connect(self._on_team_color_changed)

        self._apply_theme(col)
        self._sync_adjusters()

        s1, s2 = self.c.get_display_scores()
        self._on_scoreboard(self.c.team1, s1, self.c.team2, s2)

    def _build_stylesheet(self, border_color: str) -> str:
        bc = border_color
        return f"""
            QGroupBox {{
                font-weight:900;
                color:#111;
                border:2px solid {bc};
                border-radius:14px;
                margin-top:10px;
                background:#ffffff;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left:12px;
                padding:0 6px;
            }}
            QLineEdit {{
                background:white;
                color:#111;
                border:1px solid #c7c7c7;
                border-radius:10px;
                padding:6px 10px;
                min-height:32px;
            }}
            QLabel {{ color:#111; }}
        """

    def _apply_theme(self, color: str):
        color = str(color)
        self.setStyleSheet(self._build_stylesheet(color))
        self.btnColor.setStyleSheet(f"background:{color}; color:white; font-weight:900; border-radius:12px;")
        self.blockStone.set_header_color(color)
        self.blockGold.set_header_color(color)
        self.blockDia.set_header_color(color)

    def _pick_color(self):
        cur = QColor(self.c.get_team_color(self.team))
        picked = QColorDialog.getColor(cur, self, f"Chọn màu cho Đội {self.team}")
        if not picked.isValid():
            return
        self.c.set_team_color(self.team, picked.name())

    def _on_team_color_changed(self, team: int, color_hex: str):
        if int(team) != int(self.team):
            return
        self._apply_theme(color_hex)

    def _toggle_absolute(self):
        # toggle tuyệt đối: bật / tắt (luôn cho phép)
        if self.c.abs_winner == self.team:
            self.c.set_absolute_win(None)
            return
        if self.c.abs_winner is None:
            self.c.set_absolute_win(self.team)
            return
        return

    def _sync_adjusters(self):
        self.penCounter.setValue(int(self.c.penalty_minus5[self.team]), emit_signal=False)
        self.bonusCounter.setValue(int(self.c.bonus_plus5[self.team]), emit_signal=False)

        if self.c.abs_winner is None:
            self.btnAbsolute.setText("Tuyệt đối")
            self.btnAbsolute.setEnabled(True)
        elif self.c.abs_winner == self.team:
            self.btnAbsolute.setText("Hủy tuyệt đối")
            self.btnAbsolute.setEnabled(True)
        else:
            self.btnAbsolute.setText("Đội kia tuyệt đối")
            self.btnAbsolute.setEnabled(False)

    def _on_scoreboard(self, team1, score1, team2, score2):
        self.lblScore.setText(str(score1 if self.team == 1 else score2))
        self._sync_adjusters()


# ================== Control window ==================
class ControlWindow(QWidget):
    def __init__(self, c: MatchController):
        super().__init__()
        self.c = c
        self.display: DisplayWindow | None = None
        self.display_screen_index: int | None = None

        self.setWindowTitle("CONTROL PANEL")
        self.resize(1200, 780)
        self.setMinimumSize(980, 620)

        self.setStyleSheet("""
            QWidget { background:#f3f6fb; color:#111; }
            QLabel { color:#111; }
            QPushButton {
                border-radius:12px;
                padding:6px 10px;
                min-height:34px;
                font-weight:900;
            }
        """)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 10, 10, 10)
        outer.setSpacing(10)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer.addWidget(self.scroll, 1)

        self.content = QWidget()
        self.scroll.setWidget(self.content)

        root = QVBoxLayout(self.content)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)

        rowTeams = QHBoxLayout()
        rowTeams.setSpacing(10)

        self.teamPanel1 = TeamPanel(1, c)
        self.teamPanel2 = TeamPanel(2, c)
        rowTeams.addWidget(self.teamPanel1, 1)
        rowTeams.addWidget(self.teamPanel2, 1)
        root.addLayout(rowTeams)

        box = QGroupBox("⏱️ Timer / Display")
        box.setStyleSheet("""
            QGroupBox {
                font-weight:900;
                color:#111;
                border:1px solid #d8dbe0;
                border-radius:14px;
                margin-top:10px;
                background:#ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left:12px;
                padding:0 6px;
            }
        """)
        bl = QVBoxLayout(box)
        bl.setContentsMargins(12, 12, 12, 12)
        bl.setSpacing(10)

        top = QHBoxLayout()
        top.setSpacing(10)

        self.lblTimeNow = QLabel("00:00")
        self.lblTimeNow.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.lblTimeNow.setStyleSheet("background:#f7f8fb; color:#111; border:1px solid #e0e3e8; border-radius:12px; padding:8px 10px;")

        self.btnSetTime = QPushButton("Set")
        self.btnSetTime.setStyleSheet("background:#8e44ad; color:white;")

        self.btnStart = QPushButton("Start")
        self.btnStart.setStyleSheet("background:#2ecc71; color:white;")

        self.btnPause = QPushButton("Pause")
        self.btnPause.setStyleSheet("background:#1e73be; color:white;")

        self.btnResetTimer = QPushButton("Reset Timer")
        self.btnResetTimer.setStyleSheet("background:#e74c3c; color:white;")

        self.btnResetScore = QPushButton("Reset Điểm")
        self.btnResetScore.setStyleSheet("background:#34495e; color:white;")

        self.btnChooseScreen = QPushButton("Chọn màn hình")
        self.btnChooseScreen.setStyleSheet("background:#0f172a; color:white;")

        self.lblScreen = QLabel("Screen: Auto")
        self.lblScreen.setStyleSheet("background:#eef2ff; border:1px solid #dbeafe; border-radius:12px; padding:8px 10px; font-weight:900;")

        self.btnOpenDisplay = QPushButton("Open Display")
        self.btnOpenDisplay.setStyleSheet("background:#111; color:white;")

        self.btnCloseDisplay = QPushButton("Close Display")
        self.btnCloseDisplay.setStyleSheet("background:#555; color:white;")

        top.addWidget(QLabel("Time:"))
        top.addWidget(self.lblTimeNow, 0)
        top.addStretch(1)
        top.addWidget(self.btnSetTime)
        top.addWidget(self.btnStart)
        top.addWidget(self.btnPause)
        top.addWidget(self.btnResetTimer)
        top.addSpacing(10)
        top.addWidget(self.btnResetScore)
        top.addSpacing(10)
        top.addWidget(self.btnChooseScreen)
        top.addWidget(self.lblScreen, 0)
        top.addSpacing(10)
        top.addWidget(self.btnOpenDisplay)
        top.addWidget(self.btnCloseDisplay)

        bl.addLayout(top)

        preset = QHBoxLayout()
        preset.setSpacing(8)

        def mk_preset(text: str, seconds: int):
            b = QPushButton(text)
            b.setStyleSheet("background:#2f3b46; color:white;")
            b.clicked.connect(lambda: self.c.set_time_seconds(seconds))
            return b

        preset.addWidget(mk_preset("03:30", 3 * 60 + 30))
        preset.addWidget(mk_preset("03:00", 3 * 60))
        preset.addWidget(mk_preset("01:00", 60))
        preset.addWidget(mk_preset("00:30", 30))
        preset.addStretch(1)

        bl.addLayout(preset)
        root.addWidget(box)

        self.btnSetTime.clicked.connect(self.set_time_dialog)
        self.btnStart.clicked.connect(self.c.start)
        self.btnPause.clicked.connect(self.c.toggle_pause)
        self.btnResetTimer.clicked.connect(self.c.reset_timer_only)
        self.btnResetScore.clicked.connect(self.c.reset_scoring_and_coeff)
        self.btnChooseScreen.clicked.connect(self.choose_screen)
        self.btnOpenDisplay.clicked.connect(self.open_display)
        self.btnCloseDisplay.clicked.connect(self.close_display)

        self.c.timeTextChanged.connect(self.on_time)
        self.c.stateChanged.connect(self.on_state)

        self.teamPanel1.inName.editingFinished.connect(self.apply_names)
        self.teamPanel2.inName.editingFinished.connect(self.apply_names)

        self.on_time(self.c._fmt(self.c.seconds))
        self._update_screen_label()

        for seq, slot in [
            ("Space", self.c.toggle_pause),
            ("S", self.c.start),
            ("P", self.c.force_pause),
            ("C", self.c.resume),
            ("R", self.c.reset_timer_only),
            ("D", self.open_display),
            ("Q", self.close),
        ]:
            sc = QShortcut(QKeySequence(seq), self, slot)
            sc.setContext(Qt.ShortcutContext.ApplicationShortcut)

    def _update_screen_label(self):
        screens = QGuiApplication.screens()
        if not screens:
            self.lblScreen.setText("Screen: N/A")
            return

        if self.display_screen_index is None:
            idx = 1 if len(screens) >= 2 else 0
            self.lblScreen.setText(f"Screen: Auto → [{idx}]")
        else:
            self.lblScreen.setText(f"Screen: [{self.display_screen_index}]")

    def apply_names(self):
        self.c.set_team_names(self.teamPanel1.inName.text(), self.teamPanel2.inName.text())

    def set_time_dialog(self):
        dlg = TimeDialog()
        if dlg.exec():
            self.c.set_time_seconds(dlg.seconds)

    def on_time(self, text: str):
        self.lblTimeNow.setText(text)

    def on_state(self, running: bool, paused: bool):
        if not running:
            self.btnPause.setText("Pause")
        else:
            self.btnPause.setText("Continue" if paused else "Pause")

    def choose_screen(self):
        screens = QGuiApplication.screens()
        if not screens:
            self.display_screen_index = None
            self._update_screen_label()
            return

        dlg = ScreenSelectDialog(self, current_index=self.display_screen_index)
        if dlg.exec() and dlg.selected_index is not None:
            self.display_screen_index = int(dlg.selected_index)
        self._update_screen_label()

        if self.display is not None and self.display.isVisible():
            self.display.show_on_screen(self.display_screen_index)

    def open_display(self):
        self.apply_names()

        screens = QGuiApplication.screens()
        if screens and len(screens) >= 2 and self.display_screen_index is None:
            dlg = ScreenSelectDialog(self, current_index=1)
            if dlg.exec() and dlg.selected_index is not None:
                self.display_screen_index = int(dlg.selected_index)
            else:
                self.display_screen_index = 1
            self._update_screen_label()

        if self.display is None:
            self.display = DisplayWindow(self.c)

        self.display.show_on_screen(self.display_screen_index)

    def close_display(self):
        if self.display is not None:
            self.display.close()
            self.display = None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window, QColor("#f3f6fb"))
    pal.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))
    pal.setColor(QPalette.ColorRole.AlternateBase, QColor("#f5f7fb"))
    pal.setColor(QPalette.ColorRole.Text, QColor("#111111"))
    pal.setColor(QPalette.ColorRole.WindowText, QColor("#111111"))
    pal.setColor(QPalette.ColorRole.ButtonText, QColor("#111111"))
    pal.setColor(QPalette.ColorRole.ToolTipText, QColor("#111111"))
    app.setPalette(pal)

    app.setFont(QFont("Segoe UI", 10))

    icon_path = find_asset_first("timer.ico")
    if icon_path:
        app.setWindowIcon(QIcon(icon_path))

    c = MatchController()
    c.set_time_seconds(3 * 60 + 30)

    win = ControlWindow(c)
    win.show()

    sys.exit(app.exec())
