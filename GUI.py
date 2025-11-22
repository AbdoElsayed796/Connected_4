import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QComboBox, 
                             QSpinBox, QGroupBox, QGridLayout, QFrame, QMessageBox,
                             QTextEdit, QGraphicsView, QGraphicsScene, 
                             QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsTextItem,
                             QSplitter)
from PyQt5.QtCore import Qt, QTimer, QPoint, QPropertyAnimation, QEasingCurve, pyqtSignal, QRectF, QPointF
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QBrush, QLinearGradient, QWheelEvent
from MiniMax import Minimax_Search
from Pruning import Alpha_Beta_Search
from Expectiminimax import Expectiminimax


class ZoomableGraphicsView(QGraphicsView):
    """Graphics view with zoom and pan capabilities"""
    def __init__(self):
        super().__init__()
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.zoom_factor = 1.15
        self.current_scale = 1.0
        
    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel for zooming"""
        if event.angleDelta().y() > 0:
            # Zoom in
            factor = self.zoom_factor
            self.current_scale *= factor
        else:
            # Zoom out
            factor = 1 / self.zoom_factor
            self.current_scale *= factor
        
        # Limit zoom range
        if 0.1 <= self.current_scale <= 10.0:
            self.scale(factor, factor)
        else:
            # Revert scale if out of bounds
            self.current_scale /= factor


class ExpandableNodeItem(QGraphicsEllipseItem):
    """A clickable circular node that can expand/collapse its children"""
    def __init__(self, node, x, y, radius, parent_widget):
        super().__init__(-radius, -radius, radius * 2, radius * 2)
        self.node = node
        self.parent_widget = parent_widget
        self.radius = radius
        
        # Set position
        self.setPos(x, y)
        
        # Make it clickable
        self.setFlag(QGraphicsEllipseItem.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.PointingHandCursor)
        
        # Determine color based on node type
        if hasattr(node, 'node_type'):
            if node.node_type == "expect":
                color = QColor("#FFA726")  # Orange
                self.icon = "△"
            elif node.node_type:  # Max node
                color = QColor("#66BB6A")  # Green
                self.icon = "▲"
            else:  # Min node
                color = QColor("#EF5350")  # Red
                self.icon = "▼"
        else:
            color = QColor("#42A5F5")  # Blue
            self.icon = "●"
        
        # Set appearance
        self.setBrush(QBrush(color))
        border_width = max(1, int(2 * (radius / 40)))
        self.setPen(QPen(QColor("#ffffff"), border_width))
        self.default_color = color
        
        # Add text label
        self.text_item = QGraphicsTextItem(self)
        self.updateText()
        
        # Center the text
        text_rect = self.text_item.boundingRect()
        self.text_item.setPos(-text_rect.width() / 2, -text_rect.height() / 2)
    
    def updateText(self):
        """Update the node text with expand/collapse indicator"""
        if hasattr(self.node, 'children') and self.node.children:
            is_expanded = self.node in self.parent_widget.expanded_nodes
            indicator = "-" if is_expanded else "+"
            text = f"{self.icon}\n{self.node.value}\n{indicator}"
        else:
            text = f"{self.icon}\n{self.node.value}"
        
        self.text_item.setPlainText(text)
        self.text_item.setDefaultTextColor(QColor("#ffffff"))
        font_size = max(6, int(10 * (self.radius / 40)))
        font = QFont("Arial", font_size, QFont.Bold)
        self.text_item.setFont(font)
        
        # Re-center the text
        text_rect = self.text_item.boundingRect()
        self.text_item.setPos(-text_rect.width() / 2, -text_rect.height() / 2)
    
    def mousePressEvent(self, event):
        """Handle click event - toggle expansion and show details"""
        if event.button() == Qt.LeftButton:
            # Show node details
            self.parent_widget.displayNodeDetails(self.node)
            
            # Toggle expansion if node has children
            if hasattr(self.node, 'children') and self.node.children:
                self.parent_widget.toggleNodeExpansion(self.node)
            
            # Visual feedback
            self.setBrush(QBrush(QColor("#FFD700")))
            
            # Update text to show new expansion state
            self.updateText()
        
        super().mousePressEvent(event)
    
    def hoverEnterEvent(self, event):
        """Handle hover enter"""
        border_width = max(2, int(3 * (self.radius / 40)))
        self.setPen(QPen(QColor("#FFD700"), border_width))
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Handle hover leave"""
        if not self.isSelected():
            border_width = max(1, int(2 * (self.radius / 40)))
            self.setPen(QPen(QColor("#ffffff"), border_width))
            self.setBrush(QBrush(self.default_color))
        super().hoverLeaveEvent(event)

class TreeWindow(QWidget):
    def __init__(self, root, algorithm_name=""):
        super().__init__()
        self.root = root
        self.algorithm_name = algorithm_name
        self.setWindowTitle(f"AI Search Tree - {algorithm_name}")
        self.setGeometry(100, 100, 1200, 800)
        
        # Apply dark theme styling
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f2027, stop:0.5 #203a43, stop:1 #2c5364);
            }
        """)
        
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side - Graphics view for tree with zoom
        self.graphics_view = ZoomableGraphicsView()
        self.graphics_view.setStyleSheet("""
            QGraphicsView {
                background: rgba(0, 0, 0, 0.3);
                border: 2px solid #667eea;
                border-radius: 8px;
            }
        """)
        
        self.scene = QGraphicsScene()
        self.graphics_view.setScene(self.scene)
        
        # Right side - Node details panel
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)
        
        details_label = QLabel("📋 Node Details")
        details_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 14px;
                font-weight: bold;
                padding: 5px;
            }
        """)
        right_layout.addWidget(details_label)
        
        self.details_widget = QTextEdit()
        self.details_widget.setReadOnly(True)
        self.details_widget.setStyleSheet("""
            QTextEdit {
                font-family: 'Courier New', monospace;
                font-size: 12px;
                background: rgba(0, 0, 0, 0.4);
                color: #ffffff;
                border: 2px solid #667eea;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        self.details_widget.setPlainText("Click on a node to view its details and expand/collapse its children...\n\nUse mouse wheel to zoom in/out\nDrag to pan")
        right_layout.addWidget(self.details_widget)
        
        # Add control buttons
        control_layout = QHBoxLayout()
        
        self.expand_all_btn = QPushButton("Expand All")
        self.expand_all_btn.clicked.connect(self.expandAllNodes)
        self.expand_all_btn.setStyleSheet("""
            QPushButton {
                background: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #45a049;
            }
        """)
        
        self.collapse_all_btn = QPushButton("Collapse All")
        self.collapse_all_btn.clicked.connect(self.collapseAllNodes)
        self.collapse_all_btn.setStyleSheet("""
            QPushButton {
                background: #f44336;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #da190b;
            }
        """)
        
        control_layout.addWidget(self.expand_all_btn)
        control_layout.addWidget(self.collapse_all_btn)
        right_layout.addLayout(control_layout)
        
        # Add widgets to splitter
        splitter.addWidget(self.graphics_view)
        splitter.addWidget(right_panel)
        splitter.setSizes([800, 400])
        
        self.main_layout.addWidget(splitter)
        
        # Tree state management
        self.expanded_nodes = set()  # Track which nodes are expanded
        self.node_items = {}  # Map nodes to their graphics items
        self.edge_items = {}  # Map node pairs to their edge items
        
        # Tree layout parameters
        self.node_radius = 20
        self.level_height = 80
        self.horizontal_spacing = 60
        
        # Draw the initial tree (only root)
        self.drawTree()
        
        # Fit tree in view
        QTimer.singleShot(100, self.fitTreeInView)
    
    def drawTree(self):
        """Draw the tree starting with only the root node"""
        self.scene.clear()
        self.node_items.clear()
        self.edge_items.clear()
        
        if self.root is None:
            return
        
        # Calculate positions and draw visible nodes
        positions = {}
        self.calculateLayout(self.root, 0, 400, positions, 1)  # Start at x=400 (center)
        
        self.drawNodesAndEdges(positions)
        
        # Set scene rect with padding
        self.scene.setSceneRect(self.scene.itemsBoundingRect().adjusted(-50, -50, 50, 50))
    
    def calculateLayout(self, node, depth, x, positions, direction):
        """Calculate positions for visible nodes only"""
        if node is None:
            return x
        
        # Store current node position
        y = depth * self.level_height + 50
        positions[node] = (x, y)
        
        # Process children only if node is expanded
        if (hasattr(node, 'children') and node.children and 
            node in self.expanded_nodes):
            
            num_children = len(node.children)
            total_width = self.horizontal_spacing * num_children
            
            # Start position for children
            start_x = x - total_width / 2 + self.horizontal_spacing / 2
            
            # Position each child
            for i, child in enumerate(node.children):
                child_x = start_x + i * self.horizontal_spacing
                self.calculateLayout(child, depth + 1, child_x, positions, direction)
        
        return x
    
    def drawNodesAndEdges(self, positions):
        """Draw nodes and edges for visible nodes only"""
        # Draw edges first (only for expanded nodes)
        for node, (x, y) in positions.items():
            if (hasattr(node, 'children') and node.children and 
                node in self.expanded_nodes):
                
                for child in node.children:
                    if child in positions:  # Only draw if child is visible
                        child_x, child_y = positions[child]
                        
                        # Create edge
                        edge = QGraphicsLineItem(x, y + self.node_radius, child_x, child_y - self.node_radius)
                        edge_pen = QPen(QColor("#667eea"), 2)
                        edge.setPen(edge_pen)
                        edge.setZValue(-1)
                        self.scene.addItem(edge)
                        
                        # Store edge reference
                        self.edge_items[(node, child)] = edge
                        
                        # Draw arrow head
                        self.drawArrowHead(edge, child_x, child_y - self.node_radius)
        
        # Draw all nodes that have positions
        for node, (x, y) in positions.items():
            # Create node with expand/collapse capability
            node_item = ExpandableNodeItem(node, x, y, self.node_radius, self)
            self.scene.addItem(node_item)
            self.node_items[node] = node_item
    
    def drawArrowHead(self, edge, end_x, end_y):
        """Draw an arrow head at the end of the edge"""
        arrow_size = 5
        
        # Get the line
        line = edge.line()
        
        # Calculate angle
        import math
        angle = math.atan2(line.dy(), line.dx())
        
        # Calculate arrow points
        p1 = QPointF(
            end_x - arrow_size * math.cos(angle - math.pi / 6),
            end_y - arrow_size * math.sin(angle - math.pi / 6)
        )
        p2 = QPointF(
            end_x - arrow_size * math.cos(angle + math.pi / 6),
            end_y - arrow_size * math.sin(angle + math.pi / 6)
        )
        
        # Draw arrow head lines
        arrow_pen = QPen(QColor("#667eea"), 2)
        line1 = QGraphicsLineItem(end_x, end_y, p1.x(), p1.y())
        line1.setPen(arrow_pen)
        line1.setZValue(-1)
        self.scene.addItem(line1)
        
        line2 = QGraphicsLineItem(end_x, end_y, p2.x(), p2.y())
        line2.setPen(arrow_pen)
        line2.setZValue(-1)
        self.scene.addItem(line2)
    
    def toggleNodeExpansion(self, node):
        """Toggle expansion state of a node - simply add/remove from expanded set"""
        if node in self.expanded_nodes:
            self.expanded_nodes.remove(node)
        else:
            self.expanded_nodes.add(node)
        
        # Redraw the tree
        self.drawTree()
        
        # Update the view
        self.graphics_view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
    
    def expandAllNodes(self):
        """Expand all nodes in the tree"""
        def addAllNodes(node):
            if node is None:
                return
            self.expanded_nodes.add(node)
            if hasattr(node, 'children'):
                for child in node.children:
                    addAllNodes(child)
        
        addAllNodes(self.root)
        self.drawTree()
        self.graphics_view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
    
    def collapseAllNodes(self):
        """Collapse all nodes except root"""
        self.expanded_nodes.clear()
        self.drawTree()
        self.graphics_view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
    
    def displayNodeDetails(self, node):
        """Display detailed information about the clicked node"""
        details = "═" * 40 + "\n"
        details += "           NODE INFORMATION\n"
        details += "═" * 40 + "\n\n"
        
        # Node type
        if hasattr(node, 'node_type'):
            if node.node_type == "expect":
                details += "Type:           △ EXPECT NODE\n"
            elif node.node_type:
                details += "Type:           ▲ MAX NODE\n"
            else:
                details += "Type:           ▼ MIN NODE\n"
        else:
            details += "Type:           ● STANDARD NODE\n"
        
        details += f"Value:          {node.value}\n"
        
        # Expansion state
        is_expanded = node in self.expanded_nodes
        details += f"Expanded:       {'Yes' if is_expanded else 'No'}\n"
        
        # Additional node attributes
        details += "\n" + "─" * 40 + "\n"
        details += "Additional Attributes:\n"
        details += "─" * 40 + "\n"
        
        for attr_name in dir(node):
            if not attr_name.startswith('_') and attr_name not in ['children', 'node_type', 'value']:
                try:
                    attr_value = getattr(node, attr_name)
                    if not callable(attr_value):
                        details += f"{attr_name:15} = {attr_value}\n"
                except:
                    pass
        
        # Children information
        if hasattr(node, 'children'):
            details += "\n" + "─" * 40 + "\n"
            details += f"Children:       {len(node.children)} child node(s)\n"
            details += "─" * 40 + "\n"
            for i, child in enumerate(node.children, 1):
                child_type = "?"
                if hasattr(child, 'node_type'):
                    if child.node_type == "expect":
                        child_type = "△"
                    elif child.node_type:
                        child_type = "▲"
                    else:
                        child_type = "▼"
                visible = "👁️" if child in self.expanded_nodes else "🙈"
                details += f"  [{i}] {child_type} Value: {child.value} {visible}\n"
        else:
            details += "\n" + "─" * 40 + "\n"
            details += "Children:       🍃 LEAF NODE (no children)\n"
            details += "─" * 40 + "\n"
        
        # Action instructions
        details += "\n" + "─" * 40 + "\n"
        details += "ACTIONS:\n"
        details += "─" * 40 + "\n"
        if hasattr(node, 'children') and node.children:
            if node in self.expanded_nodes:
                details += "• Click node again to HIDE children\n"
            else:
                details += "• Click node again to SHOW children\n"
        else:
            details += "• Leaf node - no children to show\n"
        
        self.details_widget.setPlainText(details)
    
    def fitTreeInView(self):
        """Fit the entire tree in the view"""
        self.graphics_view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        self.graphics_view.scale(0.9, 0.9)
        self.graphics_view.current_scale = 0.9

    def getTreeDepth(self, node):
        """Calculate the depth of the tree"""
        if node is None or not hasattr(node, 'children') or not node.children:
            return 1
        return 1 + max(self.getTreeDepth(child) for child in node.children)

# ... rest of the code remains the same (GameCell, Connect4GUI, etc.)

class GameCell(QFrame):
    """Custom widget for game board cells with animation"""
    clicked = pyqtSignal(int)
    
    def __init__(self, row, col):
        super().__init__()
        self.row = row
        self.col = col
        self.value = 0
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
            
            if self.value == 1:
                piece_gradient.setColorAt(0, QColor(255, 235, 59))
                piece_gradient.setColorAt(1, QColor(255, 193, 7))
                border_color = QColor(230, 180, 0)
            else:
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
        if self.value == 0:
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
        self.last_tree_root = None
        self.tree_window = None
        self.used_combinations = set()
        
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
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        left_panel = self.createLeftPanel()
        main_layout.addWidget(left_panel)
        
        right_panel = self.createGameBoard()
        main_layout.addWidget(right_panel)
        
    def createLeftPanel(self):
        panel = QWidget()
        panel.setFixedWidth(280)
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        
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
        
        settings_group = self.createSettingsGroup()
        layout.addWidget(settings_group)
        
        score_group = self.createScoreGroup()
        layout.addWidget(score_group)
        
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
        
        self.tree_btn = QPushButton('🌳 View Search Tree')
        self.tree_btn.clicked.connect(self.showSearchTree)
        self.tree_btn.setEnabled(False)
        self.styleButton(self.tree_btn, '#9C27B0', '#7B1FA2')
        button_layout.addWidget(self.tree_btn)
        
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
        self.last_tree_root = None
        self.used_combinations = set()
        self.scores['player'] = 0
        self.scores['ai'] = 0
        self.updateScore(self.scores['player'], self.scores['ai'])
        
        for row in self.cells:
            for cell in row:
                cell.setValue(0)
                cell.setLastMove(False)
                cell.setHighlighted(False)
        
        for btn in self.col_buttons:
            btn.setEnabled(True)
        
        self.reset_btn.setEnabled(True)
        self.tree_btn.setEnabled(False)
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
        self.last_tree_root = None
        self.used_combinations = set()
        self.scores['player'] = 0
        self.scores['ai'] = 0
        self.updateScore(self.scores['player'], self.scores['ai'])

        for row in self.cells:
            for cell in row:
                cell.setValue(0)
                cell.setLastMove(False)
                cell.setHighlighted(False)
        
        for btn in self.col_buttons:
            btn.setEnabled(False)
        
        self.reset_btn.setEnabled(False)
        self.tree_btn.setEnabled(False)
        self.algo_combo.setEnabled(True)
        self.depth_spin.setEnabled(True)
        
        self.status_label.setText('Press "Start New Game" to begin!')
        self.turn_label.setText('🎯 Waiting to start...')
    
    def makeMove(self, col):
        """Handle player move"""
        if not self.game_started or self.game_over:
            return
        
        row = self.findLowestEmptyRow(col)
        if row == -1:
            self.status_label.setText('⚠️ Column is full! Choose another column.')
            return
        
        self.board[row][col] = self.current_player
        self.cells[row][col].setValue(self.current_player)
        
        if self.last_move:
            self.cells[self.last_move[0]][self.last_move[1]].setLastMove(False)
        self.last_move = (row, col)
        self.cells[row][col].setLastMove(True)
        
        new_connections = self.checkNewConnections(row, col)
        if new_connections:
            self.updateScoreWithConnections(new_connections)
        
        if self.isBoardFull():
            self.handleGameEnd()
            return
        
        player_name = "Player" if self.current_player == 1 else "AI"
        self.status_label.setText(f'{player_name} placed at column {col + 1}')
        
        self.current_player = 2 if self.current_player == 1 else 1
        self.updateTurnLabel()
        
        if self.current_player == 2:
            QTimer.singleShot(500, self.makeAIMove)
    
    def checkNewConnections(self, row, col):
        """Check for new 4-in-a-row connections from the last move"""
        player = self.board[row][col]
        new_connections = []
        
        directions = [
            (0, 1),
            (1, 0),
            (1, 1),
            (1, -1)
        ]
        
        for dr, dc in directions:
            consecutive = []
            
            r, c = row, col
            while 0 <= r < self.ROWS and 0 <= c < self.COLS and self.board[r][c] == player:
                consecutive.append((r, c))
                r += dr
                c += dc
            
            r, c = row - dr, col - dc
            while 0 <= r < self.ROWS and 0 <= c < self.COLS and self.board[r][c] == player:
                consecutive.insert(0, (r, c))
                r -= dr
                c -= dc
            
            if len(consecutive) >= 4:
                for i in range(len(consecutive) - 3):
                    current_combo = consecutive[i:i+4]
                    combo_id = tuple(sorted(current_combo))
                    if combo_id not in self.used_combinations:
                        new_connections.append(current_combo)
                        self.used_combinations.add(combo_id)
        
        return new_connections
    
    def updateScoreWithConnections(self, connections):
        """Update score based on new connections"""
        for connection in connections:
            player = self.board[connection[0][0]][connection[0][1]]
            
            for row, col in connection:
                self.cells[row][col].setHighlighted(True)
            
            if player == 1:
                self.scores['player'] += 1
                self.status_label.setText(f'🎉 Player scored! +1 point (Total: {self.scores["player"]})')
            else:
                self.scores['ai'] += 1
                self.status_label.setText(f'🤖 AI scored! +1 point (Total: {self.scores["ai"]})')
            
            self.updateScore(self.scores['player'], self.scores['ai'])
            
            QTimer.singleShot(1500, self.removeHighlights)
    
    def removeHighlights(self):
        """Remove temporary highlights from cells"""
        for row in range(self.ROWS):
            for col in range(self.COLS):
                self.cells[row][col].setHighlighted(False)
    
    def makeAIMove(self):
        """AI move with tree generation"""
        if not self.game_started or self.game_over:
            return
        
        move, root = None, None
        algorithm = self.algo_combo.currentText()
        depth = self.depth_spin.value()
        
        try:
            if algorithm == "Minimax":
                move, root = Minimax_Search(self.board, depth)
            elif algorithm == "Alpha-Beta Pruning":
                move, root = Alpha_Beta_Search(self.board, depth)
            else:
                move, root = Expectiminimax(self.board, depth)
            
            self.last_tree_root = root
            self.tree_btn.setEnabled(True)
            
            if move is not None:
                self.makeMove(move)
        except Exception as e:
            self.status_label.setText(f'⚠️ AI Error: {str(e)}')
    
    def isBoardFull(self):
        """Check if the board is completely filled"""
        for row in range(self.ROWS):
            for col in range(self.COLS):
                if self.board[row][col] == 0:
                    return False
        return True
    
    def handleGameEnd(self):
        """Handle game end when board is full"""
        self.game_over = True
        
        for btn in self.col_buttons:
            btn.setEnabled(False)
        
        if self.scores['player'] > self.scores['ai']:
            message = f"🎉 Game Over! Player wins {self.scores['player']}-{self.scores['ai']}!"
        elif self.scores['ai'] > self.scores['player']:
            message = f"🤖 Game Over! AI wins {self.scores['ai']}-{self.scores['player']}!"
        else:
            message = f"🤝 Game Over! It's a tie {self.scores['player']}-{self.scores['ai']}!"
        
        self.showGameOver(message)
    
    def showSearchTree(self):
        """Display the search tree in a new window"""
        if self.last_tree_root is None:
            QMessageBox.warning(self, "No Tree", "No search tree available. AI must make a move first!")
            return
        
        if self.tree_window is not None:
            self.tree_window.close()
        
        algorithm = self.algo_combo.currentText()
        self.tree_window = TreeWindow(self.last_tree_root, algorithm)
        self.tree_window.show()
    
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
        """Get current game settings"""
        return {
            'algorithm': self.algo_combo.currentText(),
            'depth': self.depth_spin.value()
        }
    
    def updateScore(self, player_score, ai_score):
        """Update score display"""
        self.player_score.setText(str(player_score))
        self.ai_score.setText(str(ai_score))
    
    def showGameOver(self, message):
        """Show game over dialog"""
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
    app.setStyle('Fusion')
    
    window = Connect4GUI()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()