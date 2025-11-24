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
from TreePrinter import TreePrinter



class ZoomableGraphicsView(QGraphicsView):
    """Graphics view with zoom and pan capabilities"""
    def __init__(self):
        super().__init__()
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.zoom_factor = 1.2
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
            elif node.node_type == "max" or node.node_type == True:
                color = QColor("#66BB6A")  # Green
            else:
                color = QColor("#EF5350")  # Red
        else:
            color = QColor("#42A5F5")  # Blue
        
        # Set appearance
        self.setBrush(QBrush(color))
        border_width = max(2, int(3 * (radius / 35)))
        self.setPen(QPen(QColor("#ffffff"), border_width))
        self.default_color = color
        
        # Tooltip with full information
        tooltip = f"Value: {node.value}"
        if hasattr(node, 'node_type'):
            tooltip += f"\nType: {node.node_type}"
        if hasattr(node, 'col') and node.col is not None:
            tooltip += f"\nColumn: {node.col}"
        if hasattr(node, 'depth'):
            tooltip += f"\nDepth: {node.depth}"
        self.setToolTip(tooltip)
        
        # CRITICAL: Add text label with guaranteed visibility
        self.text_item = QGraphicsTextItem(self)
        
        # Get value as string
        if node.value is None:
            display_text = "?"
        elif node.value == "PRUNED":
            display_text = "X"
        else:
            value_str = str(node.value)
            # Shorten if needed
            if len(value_str) > 6:
                try:
                    num_val = float(node.value)
                    if abs(num_val) >= 10000:
                        display_text = f"{int(num_val/1000)}K"
                    elif abs(num_val) >= 1000:
                        display_text = str(int(num_val))
                    else:
                        display_text = value_str[:6]
                except:
                    display_text = value_str[:6]
            else:
                display_text = value_str
        
        # Set the text
        self.text_item.setPlainText(display_text)
        
        # FORCE white color
        self.text_item.setDefaultTextColor(QColor(255, 255, 255))
        
        # FORCE visible font size based on radius
        if radius >= 25:
            font_size = 11
        elif radius >= 20:
            font_size = 10
        else:
            font_size = 9

        font = QFont("Arial", font_size, QFont.Bold)
        self.text_item.setFont(font)
        
        # FORCE text to be visible and on top
        self.text_item.setZValue(10)
        self.text_item.setVisible(True)
        
        # Center the text
        text_rect = self.text_item.boundingRect()
        x_pos = -text_rect.width() / 2
        y_pos = -text_rect.height() / 2
        self.text_item.setPos(x_pos, y_pos)
    
    def updateText(self):
        """Update the node text"""
        try:
            if self.scene() is None:
                return
            
            # Get value text
            if self.node.value is None:
                display_text = "?"
            elif self.node.value == "PRUNED":
                display_text = "X"
            else:
                value_str = str(self.node.value)
                if len(value_str) > 6:
                    try:
                        num_val = float(self.node.value)
                        if abs(num_val) >= 10000:
                            display_text = f"{int(num_val/1000)}K"
                        elif abs(num_val) >= 1000:
                            display_text = str(int(num_val))
                        else:
                            display_text = value_str[:6]
                    except:
                        display_text = value_str[:6]
                else:
                    display_text = value_str
            
            # Add expand/collapse indicator
            if hasattr(self.node, 'children') and self.node.children:
                is_expanded = self.node in self.parent_widget.expanded_nodes
                indicator = "-" if is_expanded else "+"
                display_text = f"{display_text}\n{indicator}"
            
            self.text_item.setPlainText(display_text)
            self.text_item.setDefaultTextColor(QColor(255, 255, 255))
            
            # Set font size
            if self.radius >= 30:
                font_size = 12
            elif self.radius >= 25:
                font_size = 10
            elif self.radius >= 20:
                font_size = 9
            else:
                font_size = 8
            
            font = QFont("Arial", font_size, QFont.Bold)
            self.text_item.setFont(font)
            
            # Ensure visibility
            self.text_item.setZValue(10)
            self.text_item.setVisible(True)
            
            # Re-center
            text_rect = self.text_item.boundingRect()
            self.text_item.setPos(-text_rect.width() / 2, -text_rect.height() / 2)
            
        except RuntimeError:
            pass
        except Exception as e:
            print(f"Error in updateText: {e}")
    
    def mousePressEvent(self, event):
        """Handle click event"""
        if event.button() == Qt.LeftButton:
            if self.scene() is None:
                return
            
            try:
                # Show node details
                self.parent_widget.displayNodeDetails(self.node)
                
                # Toggle expansion if node has children
                if hasattr(self.node, 'children') and self.node.children:
                    self.parent_widget.toggleNodeExpansion(self.node)
                
                # Visual feedback
                self.setBrush(QBrush(QColor("#FFD700")))
                
                # Update text
                self.updateText()
            except RuntimeError:
                return
            except Exception as e:
                print(f"Error in mousePressEvent: {e}")
        
        try:
            super().mousePressEvent(event)
        except RuntimeError:
            pass
    
    def hoverEnterEvent(self, event):
        """Handle hover enter"""
        try:
            if self.scene() is not None:
                border_width = max(3, int(4 * (self.radius / 35)))
                self.setPen(QPen(QColor("#FFD700"), border_width))
            super().hoverEnterEvent(event)
        except RuntimeError:
            pass
    
    def hoverLeaveEvent(self, event):
        """Handle hover leave"""
        try:
            if self.scene() is not None and not self.isSelected():
                border_width = max(2, int(3 * (self.radius / 35)))
                self.setPen(QPen(QColor("#ffffff"), border_width))
                self.setBrush(QBrush(self.default_color))
            super().hoverLeaveEvent(event)
        except RuntimeError:
            pass


class TreeWindow(QWidget):
    def __init__(self, root, algorithm_name=""):
        super().__init__()
        self.root = root
        self.algorithm_name = algorithm_name
        self.setWindowTitle(f"AI Search Tree - {algorithm_name}")
        self.setGeometry(100, 100, 1800, 1000)
        
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
        self.node_radius = 25
        self.level_height = 100
        self.horizontal_spacing = 60
        self.min_horizontal_spacing = 70
        
        # Draw the initial tree (only root)
        self.drawTree()
        
        # Fit tree in view
        QTimer.singleShot(100, self.fitTreeInView)
    
    def drawTree(self):
        for item in self.scene.items():
            self.scene.removeItem(item)
        
        self.node_items.clear()
        self.edge_items.clear()
        
        if self.root is None:
            return
        
        positions = {}
        self.calculateLayout(self.root, 0, 2000, positions, 1)
        
        self.drawNodesAndEdges(positions)
        
        rect = self.scene.itemsBoundingRect()
        self.scene.setSceneRect(rect.adjusted(-300, -100, 300, 100))

    def buildTreeText(self, node, prefix="", is_last=True, is_root=True):
        """Build a text representation of the tree"""
        if node is None:
            return ""
        
        result = ""
        
        # Determine node symbol based on type
        if is_root:
            node_symbol = "🌳"
        elif hasattr(node, 'node_type'):
            if node.node_type == "expect":
                node_symbol = "△"
            elif node.node_type == "max" or node.node_type == True:
                node_symbol = "▲"
            else:
                node_symbol = "▼"
        else:
            node_symbol = "●"
        
        # Format node value
        if node.value is None:
            value_str = "?"
        elif node.value == "PRUNED":
            value_str = "✂ PRUNED"
        else:
            try:
                value_str = f"{float(node.value):.2f}"
            except:
                value_str = str(node.value)
        
        # Build node information
        node_info = f"{node_symbol} Value: {value_str}"
        
        # Add additional attributes
        if hasattr(node, 'col') and node.col is not None:
            node_info += f" | Col: {node.col}"
        if hasattr(node, 'depth'):
            node_info += f" | Depth: {node.depth}"
        if hasattr(node, 'node_type') and node.node_type:
            node_info += f" | Type: {node.node_type}"
        
        # Determine the connector
        if is_root:
            connector = ""
            current_line = node_info + "\n"
        else:
            connector = "└── " if is_last else "├── "
            current_line = prefix + connector + node_info + "\n"
        
        result += current_line
        
        # Process children
        if hasattr(node, 'children') and node.children:
            # Update prefix for children
            if is_root:
                new_prefix = ""
            else:
                extension = "    " if is_last else "│   "
                new_prefix = prefix + extension
            
            # Add all children
            for i, child in enumerate(node.children):
                is_last_child = (i == len(node.children) - 1)
                result += self.buildTreeText(child, new_prefix, is_last_child, False)
        
        return result
    
    def calculateTreeStats(self, root):
        """Calculate tree statistics"""
        stats = {
            'total_nodes': 0,
            'max_depth': 0,
            'leaf_nodes': 0,
            'branch_nodes': 0,
            'pruned_nodes': 0,
            'total_children': 0,
            'branch_count': 0
        }
        
        def traverse(node, depth):
            if node is None:
                return
            
            stats['total_nodes'] += 1
            stats['max_depth'] = max(stats['max_depth'], depth)
            
            # Check if pruned
            if node.value == "PRUNED":
                stats['pruned_nodes'] += 1
            
            # Check if leaf or branch
            if hasattr(node, 'children') and node.children:
                stats['branch_nodes'] += 1
                stats['total_children'] += len(node.children)
                stats['branch_count'] += 1
                
                for child in node.children:
                    traverse(child, depth + 1)
            else:
                stats['leaf_nodes'] += 1
        
        traverse(root, 0)
        
        # Calculate average branching factor
        if stats['branch_count'] > 0:
            stats['avg_branching'] = stats['total_children'] / stats['branch_count']
        else:
            stats['avg_branching'] = 0
        
        return stats
    
    def calculateLayout(self, node, depth, x, positions, direction):
        if node is None:
            return x
        
        y = depth * self.level_height + 50
        positions[node] = (x, y)
        
        if (hasattr(node, 'children') and node.children and 
            node in self.expanded_nodes):
            
            num_children = len(node.children)
            spacing = max(self.min_horizontal_spacing / (1 + depth * 0.3), 50)
            total_width = spacing * (num_children - 1)
            start_x = x - total_width / 2
            
            for i, child in enumerate(node.children):
                child_x = start_x + i * spacing
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
        """Expand all nodes in the tree and show in Node Details panel"""
        def addAllNodes(node):
            if node is None:
                return
            self.expanded_nodes.add(node)
            if hasattr(node, 'children'):
                for child in node.children:
                    addAllNodes(child)
        
        # Expand all nodes
        addAllNodes(self.root)
        self.drawTree()
        self.graphics_view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        
        # Build and display full tree text in Node Details panel
        tree_text = "="*60 + "\n"
        tree_text += "           FULL TREE STRUCTURE\n"
        tree_text += "="*60 + "\n\n"
        tree_text += self.buildTreeText(self.root)
        tree_text += "\n" + "="*60 + "\n"
        
        # Calculate statistics
        stats = self.calculateTreeStats(self.root)
        tree_text += "             TREE STATISTICS\n"
        tree_text += "="*60 + "\n"
        tree_text += f"Total Nodes:        {stats['total_nodes']}\n"
        tree_text += f"Max Depth:          {stats['max_depth']}\n"
        tree_text += f"Leaf Nodes:         {stats['leaf_nodes']}\n"
        tree_text += f"Branch Nodes:       {stats['branch_nodes']}\n"
        tree_text += f"Pruned Nodes:       {stats['pruned_nodes']}\n"
        tree_text += f"Average Branching:  {stats['avg_branching']:.2f}\n"
        tree_text += "="*60 + "\n"
        
        self.details_widget.setPlainText(tree_text)
    
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
        if self.scene.items():
            rect = self.scene.sceneRect()
            self.graphics_view.setSceneRect(rect)
            self.graphics_view.fitInView(rect, Qt.KeepAspectRatio)
            self.graphics_view.resetTransform()
            self.graphics_view.fitInView(rect, Qt.KeepAspectRatio)
            self.graphics_view.current_scale = 1.0

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
        self.setFixedSize(120, 120)
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
            radius = 50
            
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
            radius = 50
            
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
        self.setFixedSize(120, 60)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3a7bc8, stop:1 #2962b3);
                border: 2px solid #1e4d8b;
                border-radius: 8px;
                color: white;
                font-size: 28px;
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
        self.setFixedSize(1500, 1300)
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
                font-size: 24px;
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

        self.stats_label = QLabel('📊 AI Statistics\n\nNodes: -\nTime: -')
        self.stats_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: white;
                background: rgba(102, 126, 234, 0.2);
                border: 2px solid #667eea;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        self.stats_label.setAlignment(Qt.AlignLeft)
        layout.addWidget(self.stats_label)
        
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
                font-size: 20px;
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
        algo_label.setStyleSheet('color: white; font-size: 18px;')
        self.algo_combo = QComboBox()
        self.algo_combo.addItems(['Minimax', 'Alpha-Beta Pruning', 'Expected Minimax'])
        self.algo_combo.setCurrentIndex(1)
        self.styleComboBox(self.algo_combo)
        algo_layout.addWidget(algo_label)
        algo_layout.addWidget(self.algo_combo)
        layout.addLayout(algo_layout)
        
        depth_layout = QVBoxLayout()
        depth_label = QLabel('Search Depth (K):')
        depth_label.setStyleSheet('color: white; font-size: 18px;')
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
                font-size: 20px;
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
        player_icon.setStyleSheet('font-size: 36px;')
        player_text = QLabel('Player:')
        player_text.setStyleSheet('color: white; font-size: 20px;')
        self.player_score = QLabel('0')
        self.player_score.setStyleSheet("""
            QLabel {
                color: #FFC107;
                font-size: 36px;
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
        ai_icon.setStyleSheet('font-size: 36px;')
        ai_text = QLabel('AI:')
        ai_text.setStyleSheet('color: white; font-size: 20px;')
        self.ai_score = QLabel('0')
        self.ai_score.setStyleSheet("""
            QLabel {
                color: #F44336;
                font-size: 36px;
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
                font-size: 24px;
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
        btn.setFixedHeight(60)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {color};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 20px;
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
                padding: 12px;
                font-size: 18px;
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
    
    def format_number(self, num):
        """Format large numbers with K, M abbreviations"""
        if num >= 1_000_000:
            return f"{num/1_000_000:.2f}M"
        elif num >= 1_000:
            return f"{num/1_000:.2f}K"
        else:
            return f"{num:,}"

    def updateAIStats(self, nodes_expanded, elapsed_time):
        """Update AI statistics display"""
        stats_text = f"📊 AI Statistics\n\n"
        stats_text += f"Nodes: {self.format_number(nodes_expanded)}\n"
        stats_text += f"Time: {elapsed_time:.4f}s"
        self.stats_label.setText(stats_text)
    
    def styleSpinBox(self, spin):
        spin.setStyleSheet("""
            QSpinBox {
                background: rgba(255, 255, 255, 0.1);
                color: white;
                border: 2px solid #667eea;
                border-radius: 5px;
                padding: 12px;
                font-size: 18px;
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
        self.stats_label.setText('📊 AI Statistics\n\nNodes: -\nTime: -')
        
        for row in self.cells:
            for cell in row:
                cell.setValue(0)
                cell.setLastMove(False)
                cell.setHighlighted(False)
        
        for btn in self.col_buttons:
            btn.setEnabled(True)
        
        self.reset_btn.setEnabled(True)
        self.tree_btn.setEnabled(False)
        
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
        self.stats_label.setText('📊 AI Statistics\n\nNodes: -\nTime: -')

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
        
        move, root, nodes_expanded, elapsed_time = None, None, 0, 0.0
        algorithm = self.algo_combo.currentText()
        depth = self.depth_spin.value()
        
        try:
            if algorithm == "Minimax":
                move, root, nodes_expanded, elapsed_time = Minimax_Search(self.board, depth)
            elif algorithm == "Alpha-Beta Pruning":
                move, root, nodes_expanded, elapsed_time = Alpha_Beta_Search(self.board, depth)
            else:
                move, root, nodes_expanded, elapsed_time = Expectiminimax(self.board, depth)
            
            self.last_tree_root = root
            self.tree_btn.setEnabled(True)
            
            # Update statistics display (NO TREE PRINTING HERE)
            self.updateAIStats(nodes_expanded, elapsed_time)
            
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
        
        # Print tree to terminal and file ONLY when button is clicked
        algorithm = self.algo_combo.currentText()
        print("\n" + "="*80)
        print(f"🌳 VIEWING SEARCH TREE - {algorithm}")
        print("="*80)
        
        tree_printer = TreePrinter(algorithm)
        tree_printer.print_tree(self.last_tree_root)
        
        # Also print compact version
        print("\n📋 COMPACT VIEW (First 4 Levels):")
        tree_printer.print_compact_tree(self.last_tree_root, max_depth=4)
        
        # Now show the GUI window
        if self.tree_window is not None:
            self.tree_window.close()
        
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
                    font-size: 24px;
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
                    font-size: 24px;
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