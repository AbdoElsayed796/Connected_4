import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QComboBox, 
                             QSpinBox, QGroupBox, QGridLayout, QFrame, QMessageBox)
from PyQt5.QtCore import Qt, QTimer, QPoint, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QBrush, QLinearGradient

class GameCell(QFrame):
    """Custom widget for game board cells with animation"""
    clicked = pyqtSignal(int)
    
    def __init__(self, row, col):
        super().__init__()
        self.row = row
        self.col = col
        self.value = 0  # 0: empty, 1: player, 2: AI
        self.is_highlighted = False
        self.is_last_move = False
        self.setFixedSize(80, 80)
        self.setFrameStyle(QFrame.Box)
        
    def setValue(self, value):
        self.value = value
        self.update()
        
    def setHighlighted(self, highlighted):
        self.is_highlighted = highlighted
        self.update()
        
    def setLastMove(self, is_last):
        self.is_last_move = is_last
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw cell background with gradient
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(30, 60, 114))
        gradient.setColorAt(1, QColor(20, 40, 80))
        painter.fillRect(self.rect(), gradient)
        
        # Draw border
        painter.setPen(QPen(QColor(40, 70, 120), 2))
        painter.drawRect(self.rect())
        
        # Draw piece
        if self.value != 0:
            center_x = self.width() // 2
            center_y = self.height() // 2
            radius = 30
            
            # Create gradient for piece
            piece_gradient = QLinearGradient(center_x - radius, center_y - radius, 
                                            center_x + radius, center_y + radius)
            
            if self.value == 1:  # Player (Yellow)
                piece_gradient.setColorAt(0, QColor(255, 235, 59))
                piece_gradient.setColorAt(1, QColor(255, 193, 7))
                border_color = QColor(230, 180, 0)
            else:  # AI (Red)
                piece_gradient.setColorAt(0, QColor(244, 67, 54))
                piece_gradient.setColorAt(1, QColor(198, 40, 40))
                border_color = QColor(180, 30, 30)
            
            # Draw piece shadow
            painter.setBrush(QColor(0, 0, 0, 50))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(center_x - radius + 2, center_y - radius + 2, 
                              radius * 2, radius * 2)
            
            # Draw piece
            painter.setBrush(QBrush(piece_gradient))
            painter.setPen(QPen(border_color, 3))
            painter.drawEllipse(center_x - radius, center_y - radius, 
                              radius * 2, radius * 2)
            
            # Add highlight if it's the last move
            if self.is_last_move:
                painter.setPen(QPen(QColor(255, 255, 255), 4))
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(center_x - radius - 5, center_y - radius - 5, 
                                  radius * 2 + 10, radius * 2 + 10)
        else:
            # Draw empty slot
            center_x = self.width() // 2
            center_y = self.height() // 2
            radius = 30
            
            painter.setBrush(QColor(10, 20, 40))
            painter.setPen(QPen(QColor(50, 80, 130), 2))
            painter.drawEllipse(center_x - radius, center_y - radius, 
                              radius * 2, radius * 2)
        
        # Highlight on hover
        if self.is_highlighted:
            painter.setBrush(QColor(255, 255, 255, 30))
            painter.setPen(Qt.NoPen)
            painter.drawRect(self.rect())
    
    def mousePressEvent(self, event):
        if self.value == 0:  # Only if cell is empty
            self.clicked.emit(self.col)


class ColumnButton(QPushButton):
    """Hoverable column button with visual feedback"""
    def __init__(self, col):
        super().__init__()
        self.col = col
        self.setFixedSize(80, 40)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3a7bc8, stop:1 #2962b3);
                border: 2px solid #1e4d8b;
                border-radius: 8px;
                color: white;
                font-size: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4a8bd8, stop:1 #3972c3);
                border: 2px solid #2e5d9b;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2962b3, stop:1 #1e4d8b);
            }
        """)
        self.setText("▼")


class Connect4GUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ROWS = 6
        self.COLS = 7
        self.board = [[0 for _ in range(self.COLS)] for _ in range(self.ROWS)]
        self.current_player = 1
        self.game_started = False
        self.game_over = False
        self.scores = {'player': 0, 'ai': 0}
        self.last_move = None
        
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('Connect 4 - AI Game')
        self.setFixedSize(1000, 750)
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f2027, stop:0.5 #203a43, stop:1 #2c5364);
            }
        """)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Left panel - Settings and Info
        left_panel = self.createLeftPanel()
        main_layout.addWidget(left_panel)
        
        # Right panel - Game Board
        right_panel = self.createGameBoard()
        main_layout.addWidget(right_panel)
        
    def createLeftPanel(self):
        panel = QWidget()
        panel.setFixedWidth(280)
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        
        # Title
        title = QLabel('🎮 CONNECT 4')
        title.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: bold;
                color: #ffffff;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 10px;
            }
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Settings Group
        settings_group = self.createSettingsGroup()
        layout.addWidget(settings_group)
        
        # Score Display
        score_group = self.createScoreGroup()
        layout.addWidget(score_group)
        
        # Current Turn Display
        self.turn_label = QLabel('🎯 Player\'s Turn')
        self.turn_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: white;
                background: rgba(255, 193, 7, 0.2);
                border: 2px solid #FFC107;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        self.turn_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.turn_label)
        
        # Control Buttons
        button_layout = QVBoxLayout()
        button_layout.setSpacing(10)
        
        self.start_btn = QPushButton('🚀 Start New Game')
        self.start_btn.clicked.connect(self.startNewGame)
        self.styleButton(self.start_btn, '#4CAF50', '#45a049')
        button_layout.addWidget(self.start_btn)
        
        self.reset_btn = QPushButton('🔄 Reset Game')
        self.reset_btn.clicked.connect(self.resetGame)
        self.reset_btn.setEnabled(False)
        self.styleButton(self.reset_btn, '#2196F3', '#1976D2')
        button_layout.addWidget(self.reset_btn)
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        return panel
    
    def createSettingsGroup(self):
        group = QGroupBox('⚙️ Game Settings')
        group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: white;
                border: 2px solid #667eea;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                background: rgba(102, 126, 234, 0.1);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        # Algorithm Selection
        algo_layout = QVBoxLayout()
        algo_label = QLabel('Algorithm:')
        algo_label.setStyleSheet('color: white; font-size: 14px;')
        self.algo_combo = QComboBox()
        self.algo_combo.addItems(['Minimax', 'Alpha-Beta Pruning', 'Expected Minimax'])
        self.algo_combo.setCurrentIndex(1)
        self.styleComboBox(self.algo_combo)
        algo_layout.addWidget(algo_label)
        algo_layout.addWidget(self.algo_combo)
        layout.addLayout(algo_layout)
        
        # Depth Selection
        depth_layout = QVBoxLayout()
        depth_label = QLabel('Search Depth (K):')
        depth_label.setStyleSheet('color: white; font-size: 14px;')
        self.depth_spin = QSpinBox()
        self.depth_spin.setRange(1, 10)
        self.depth_spin.setValue(4)
        self.styleSpinBox(self.depth_spin)
        depth_layout.addWidget(depth_label)
        depth_layout.addWidget(self.depth_spin)
        layout.addLayout(depth_layout)
        
        group.setLayout(layout)
        return group
    
    def createScoreGroup(self):
        group = QGroupBox('🏆 Score Board')
        group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: white;
                border: 2px solid #764ba2;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                background: rgba(118, 75, 162, 0.1);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Player Score
        player_layout = QHBoxLayout()
        player_icon = QLabel('👤')
        player_icon.setStyleSheet('font-size: 24px;')
        player_text = QLabel('Player:')
        player_text.setStyleSheet('color: white; font-size: 14px;')
        self.player_score = QLabel('0')
        self.player_score.setStyleSheet("""
            QLabel {
                color: #FFC107;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        player_layout.addWidget(player_icon)
        player_layout.addWidget(player_text)
        player_layout.addStretch()
        player_layout.addWidget(self.player_score)
        layout.addLayout(player_layout)
        
        # AI Score
        ai_layout = QHBoxLayout()
        ai_icon = QLabel('🤖')
        ai_icon.setStyleSheet('font-size: 24px;')
        ai_text = QLabel('AI:')
        ai_text.setStyleSheet('color: white; font-size: 14px;')
        self.ai_score = QLabel('0')
        self.ai_score.setStyleSheet("""
            QLabel {
                color: #F44336;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        ai_layout.addWidget(ai_icon)
        ai_layout.addWidget(ai_text)
        ai_layout.addStretch()
        ai_layout.addWidget(self.ai_score)
        layout.addLayout(ai_layout)
        
        group.setLayout(layout)
        return group
    
    def createGameBoard(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)
        
        # Game status label
        self.status_label = QLabel('Press "Start New Game" to begin!')
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                color: white;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 12px;
            }
        """)
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Column buttons
        col_layout = QHBoxLayout()
        col_layout.setSpacing(0)
        self.col_buttons = []
        for col in range(self.COLS):
            btn = ColumnButton(col)
            btn.clicked.connect(lambda checked, c=col: self.makeMove(c))
            btn.setEnabled(False)
            self.col_buttons.append(btn)
            col_layout.addWidget(btn)
        layout.addLayout(col_layout)
        
        # Game board
        board_widget = QWidget()
        board_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e3c72, stop:1 #2a5298);
                border-radius: 15px;
                border: 3px solid #667eea;
            }
        """)
        board_layout = QGridLayout(board_widget)
        board_layout.setSpacing(2)
        board_layout.setContentsMargins(10, 10, 10, 10)
        
        self.cells = []
        for row in range(self.ROWS):
            row_cells = []
            for col in range(self.COLS):
                cell = GameCell(row, col)
                cell.clicked.connect(self.makeMove)
                board_layout.addWidget(cell, row, col)
                row_cells.append(cell)
            self.cells.append(row_cells)
        
        layout.addWidget(board_widget)
        
        return panel
    
    def styleButton(self, btn, color, hover_color):
        btn.setFixedHeight(45)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {color};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
            }}
            QPushButton:hover {{
                background: {hover_color};
            }}
            QPushButton:pressed {{
                background: {color};
                padding-top: 12px;
            }}
            QPushButton:disabled {{
                background: #555555;
                color: #888888;
            }}
        """)
    
    def styleComboBox(self, combo):
        combo.setStyleSheet("""
            QComboBox {
                background: rgba(255, 255, 255, 0.1);
                color: white;
                border: 2px solid #667eea;
                border-radius: 5px;
                padding: 8px;
                font-size: 13px;
            }
            QComboBox:hover {
                border: 2px solid #764ba2;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background: #2c3e50;
                color: white;
                selection-background-color: #667eea;
            }
        """)
    
    def styleSpinBox(self, spin):
        spin.setStyleSheet("""
            QSpinBox {
                background: rgba(255, 255, 255, 0.1);
                color: white;
                border: 2px solid #667eea;
                border-radius: 5px;
                padding: 8px;
                font-size: 13px;
            }
            QSpinBox:hover {
                border: 2px solid #764ba2;
            }
        """)
    
    def startNewGame(self):
        self.game_started = True
        self.game_over = False
        self.current_player = 1
        self.board = [[0 for _ in range(self.COLS)] for _ in range(self.ROWS)]
        self.last_move = None
        
        # Update UI
        for row in self.cells:
            for cell in row:
                cell.setValue(0)
                cell.setLastMove(False)
        
        for btn in self.col_buttons:
            btn.setEnabled(True)
        
        self.reset_btn.setEnabled(True)
        self.algo_combo.setEnabled(False)
        self.depth_spin.setEnabled(False)
        
        self.status_label.setText('🎮 Game Started! Make your move!')
        self.updateTurnLabel()
    
    def resetGame(self):
        self.game_started = False
        self.game_over = False
        self.current_player = 1
        self.board = [[0 for _ in range(self.COLS)] for _ in range(self.ROWS)]
        self.last_move = None
        
        # Reset UI
        for row in self.cells:
            for cell in row:
                cell.setValue(0)
                cell.setLastMove(False)
        
        for btn in self.col_buttons:
            btn.setEnabled(False)
        
        self.reset_btn.setEnabled(False)
        self.algo_combo.setEnabled(True)
        self.depth_spin.setEnabled(True)
        
        self.status_label.setText('Press "Start New Game" to begin!')
        self.turn_label.setText('🎯 Waiting to start...')
    
    def makeMove(self, col):
        """Handle player move - YOU WILL CONNECT THIS TO YOUR AI CODE"""
        if not self.game_started or self.game_over:
            return
        
        # Find the lowest empty row in the column
        row = self.findLowestEmptyRow(col)
        if row == -1:
            self.status_label.setText('⚠️ Column is full! Choose another column.')
            return
        
        # Place piece (this is where you'll integrate your game logic)
        self.board[row][col] = self.current_player
        self.cells[row][col].setValue(self.current_player)
        
        # Highlight last move
        if self.last_move:
            self.cells[self.last_move[0]][self.last_move[1]].setLastMove(False)
        self.last_move = (row, col)
        self.cells[row][col].setLastMove(True)
        
        # Update status
        self.status_label.setText(f'{"Player" if self.current_player == 1 else "AI"} placed at column {col + 1}')
        
        # TODO: CHECK FOR WIN/CONNECT-4 HERE
        # TODO: CALL YOUR AI ALGORITHM HERE
        # TODO: UPDATE SCORES
        
        # Switch player
        self.current_player = 2 if self.current_player == 1 else 1
        self.updateTurnLabel()
        
        # Simulate AI move after short delay (you'll replace this with actual AI)
        if self.current_player == 2:
            QTimer.singleShot(500, self.makeAIMove)
    
    def makeAIMove(self):
        """Placeholder for AI move - YOU WILL IMPLEMENT YOUR AI ALGORITHM HERE"""
        if not self.game_started or self.game_over:
            return
        
        # TODO: CALL YOUR MINIMAX/ALPHA-BETA/EXPECTED MINIMAX HERE
        # For now, just make a random valid move
        import random
        valid_cols = [c for c in range(self.COLS) if self.findLowestEmptyRow(c) != -1]
        if valid_cols:
            col = random.choice(valid_cols)
            self.makeMove(col)
    
    def findLowestEmptyRow(self, col):
        """Find the lowest empty row in a column"""
        for row in range(self.ROWS - 1, -1, -1):
            if self.board[row][col] == 0:
                return row
        return -1
    
    def updateTurnLabel(self):
        if self.current_player == 1:
            self.turn_label.setText('🎯 Player\'s Turn')
            self.turn_label.setStyleSheet("""
                QLabel {
                    font-size: 18px;
                    font-weight: bold;
                    color: white;
                    background: rgba(255, 193, 7, 0.2);
                    border: 2px solid #FFC107;
                    border-radius: 8px;
                    padding: 12px;
                }
            """)
        else:
            self.turn_label.setText('🤖 AI is thinking...')
            self.turn_label.setStyleSheet("""
                QLabel {
                    font-size: 18px;
                    font-weight: bold;
                    color: white;
                    background: rgba(244, 67, 54, 0.2);
                    border: 2px solid #F44336;
                    border-radius: 8px;
                    padding: 12px;
                }
            """)
    
    def getSettings(self):
        """Get current game settings - USE THIS IN YOUR AI CODE"""
        return {
            'algorithm': self.algo_combo.currentText(),
            'depth': self.depth_spin.value()
        }
    
    def updateScore(self, player_score, ai_score):
        """Update score display - CALL THIS FROM YOUR GAME LOGIC"""
        self.player_score.setText(str(player_score))
        self.ai_score.setText(str(ai_score))
    
    def showGameOver(self, message):
        """Show game over dialog"""
        self.game_over = True
        for btn in self.col_buttons:
            btn.setEnabled(False)
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle('Game Over')
        msg_box.setText(message)
        msg_box.setStyleSheet("""
            QMessageBox {
                background: #2c3e50;
            }
            QMessageBox QLabel {
                color: white;
                font-size: 16px;
            }
            QPushButton {
                background: #667eea;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #764ba2;
            }
        """)
        msg_box.exec_()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern look
    
    window = Connect4GUI()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()