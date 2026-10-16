import sys
import threading
from PySide6.QtWidgets import QMainWindow, QApplication, QLabel, QLineEdit, QWidget, QVBoxLayout, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtGui import QColor
from pynput import keyboard
from ai import ask_groq_response
from PySide6.QtNetwork import QLocalServer, QLocalSocket

STYLE = """
#card {
    background-color: rgba(24, 24, 28, 235);
    border: 1px solid rgba(255, 255, 255, 30);
    border-radius: 16px;
}
QLineEdit {
    background-color: rgba(255, 255, 255, 14);
    border: 1px solid rgba(255, 255, 255, 25);
    border-radius: 10px;
    padding: 10px 14px;
    color: white;
    font-size: 15px;
    selection-background-color: #6c8cff;
}
QLineEdit:focus { border: 1px solid #6c8cff; }
#question { color: rgba(255, 255, 255, 140); font-size: 12px; }
#answer   { color: white; font-size: 15px; }
#hint     { color: rgba(255, 255, 255, 80); font-size: 11px; }
"""
SERVER_NAME = "universal_ai_overlay"
def send_toggle():
    sock = QLocalSocket()
    sock.connectToServer(SERVER_NAME)       
    if sock.waitForConnected(500):         
        sock.disconnectFromServer()
        return True
    return False

class HotkeyListener(QObject):
    #ctrl + space listener
    triggered = Signal()

    def __init__(self):
        super().__init__()
        self._listener = keyboard.GlobalHotKeys({"<ctrl>+<space>" : self.triggered.emit})
        self._listener.start()
class Bridge(QObject):
    chunk = Signal(int, str)    # request id, text piece
    failed = Signal(int, str)

class OverlayWindow(QWidget):
    WIDTH = 520
    def __init__(self):
        super().__init__()
        self._request_id = 0
        self.bridge = Bridge()
        self.bridge.chunk.connect(self.on_chunk)
        self.bridge.failed.connect(self.on_error)
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(self.WIDTH)
        self.setStyleSheet(STYLE)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        self.card = QWidget()
        self.card.setObjectName("card")
        shadow = QGraphicsDropShadowEffect(blurRadius=30, xOffset=0, yOffset=6)
        shadow.setColor(QColor(0, 0, 0, 160))
        self.card.setGraphicsEffect(shadow)
        outer.addWidget(self.card)

        layout = QVBoxLayout(self.card)
        layout.setContentsMargins(16, 16, 16, 12)
        layout.setSpacing(8)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Ask anything...")
        self.input.returnPressed.connect(self.submit)
        layout.addWidget(self.input)

        self.question = QLabel("")
        self.question.setWordWrap(True)
        self.question.hide()
        layout.addWidget(self.question)

        self.answer = QLabel("")
        self.answer.setObjectName("answer")
        self.answer.setWordWrap(True)
        self.answer.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.answer.hide()
        layout.addWidget(self.answer)

        hint = QLabel("Enter to ask . Esc to close . Ctrl + Space to toggle")
        hint.setObjectName("hint")
        hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint)

    def toggle(self):
        if self.isVisible():
            self.hide_overlay()
        else:
            self.show_overlay()

    def show_overlay(self):
        self.adjustSize()
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.center().x() - self.width() // 2, screen.top() + 120)
        self.show()
        self.raise_()
        self.activateWindow()
        self.input.setFocus()
        self.input.selectAll()

    def hide_overlay(self):
        self.hide()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide_overlay()
        else:
            super().keyPressEvent(event)

    def submit(self):
        text = self.input.text().strip()
        if not text:
            return

        self.question.setText(text)
        self.question.show()
        self.answer.setText("Thinking...")
        self.answer.show()
        self.input.clear()
        self._resize()

        self._request_id += 1
        self._first_chunk = True
        threading.Thread(
            target=self._run_request, args=(self._request_id, text), daemon=True
        ).start()

    def _run_request(self, request_id, question):
        try:
            for piece in ask_groq_response(question):
                if request_id != self._request_id:   # a newer question replaced this one
                    return
                self.bridge.chunk.emit(request_id, piece)
        except Exception as e:
            self.bridge.failed.emit(request_id, f"Something went wrong: {e}")

    def on_chunk(self, request_id, piece):
        if request_id != self._request_id:   # stale answer from an older question
            return
        if self._first_chunk:
            self.answer.setText("")
            self._first_chunk = False
        self.answer.setText(self.answer.text() + piece)
        self._resize()

    def on_error(self, request_id, message):
        if request_id != self._request_id:
            return
        self.answer.setText(message)
        self._resize()

    def _resize(self):
        self.layout().activate()
        self.adjustSize()

if __name__ == '__main__':
    app = QApplication(sys.argv)

    if "--toggle" in sys.argv:
        sys.exit(0 if send_toggle() else 1)

    app.setQuitOnLastWindowClosed(False)

    window = OverlayWindow()

    QLocalServer.removeServer(SERVER_NAME)
    server = QLocalServer()
    server.listen(SERVER_NAME)
    server.newConnection.connect(lambda: (server.nextPendingConnection(), window.toggle()))

    print("Universal AI running.")
    sys.exit(app.exec())