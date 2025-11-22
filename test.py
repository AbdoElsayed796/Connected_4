from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTextEdit, QGraphicsView, QGraphicsScene, 
                             QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsTextItem,
                             QSplitter)
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPen, QBrush, QColor, QFont, QPainter

class ClickableNodeItem(QGraphicsEllipseItem):
    """A clickable circular node in the tree"""
    def __init__(self, node, x, y, radius, parent_widget):
        super().__init__(-radius, -radius, radius * 2, radius * 2)
        self.node = node
        self.parent_widget = parent_widget
        self.radius = radius
        
        # Set position
        self.setPos(x, y)
        
        # Make it clickable
        self.setFlag(QGraphicsEllipseItem.ItemIsSelectable)
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
        self.setPen(QPen(QColor("#ffffff"), 3))
        self.default_color = color
        
        # Add text label
        self.text_item = QGraphicsTextItem(self)
        self.text_item.setPlainText(f"{self.icon}\n{node.value}")
        self.text_item.setDefaultTextColor(QColor("#ffffff"))
        font = QFont("Arial", 12, QFont.Bold)
        self.text_item.setFont(font)
        
        # Center the text
        text_rect = self.text_item.boundingRect()
        self.text_item.setPos(-text_rect.width() / 2, -text_rect.height() / 2)
    
    def mousePressEvent(self, event):
        """Handle click event"""
        if event.button() == Qt.LeftButton:
            self.parent_widget.displayNodeDetails(self.node)
            # Highlight selected node
            self.setBrush(QBrush(QColor("#FFD700")))  # Gold color
        super().mousePressEvent(event)
    
    def hoverEnterEvent(self, event):
        """Handle hover enter"""
        self.setPen(QPen(QColor("#FFD700"), 5))
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Handle hover leave"""
        if not self.isSelected():
            self.setPen(QPen(QColor("#ffffff"), 3))
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
        
        # Add title label
        title = QLabel(f'🌳 {algorithm_name} Search Tree')
        title.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #ffffff;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 8px;
                padding: 12px;
                margin: 10px;
            }
        """)
        title.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(title)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side - Graphics view for tree
        self.graphics_view = QGraphicsView()
        self.graphics_view.setRenderHint(QPainter.Antialiasing)
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
        self.details_widget.setPlainText("Click on a node to view its details...")
        right_layout.addWidget(self.details_widget)
        
        # Add widgets to splitter
        splitter.addWidget(self.graphics_view)
        splitter.addWidget(right_panel)
        splitter.setSizes([800, 400])  # Initial sizes
        
        self.main_layout.addWidget(splitter)
        
        # Calculate tree dimensions and draw it
        self.node_radius = 40
        self.level_height = 120
        self.drawTree()
    
    def drawTree(self):
        """Draw the entire tree with nodes and edges"""
        if self.root is None:
            return
        
        # Calculate tree dimensions
        tree_depth = self.getTreeDepth(self.root)
        tree_width = self.getTreeWidth(self.root)
        
        # Calculate starting position (center top)
        start_x = tree_width * 100 / 2
        start_y = 50
        
        # Draw tree recursively
        self.drawNode(self.root, start_x, start_y, tree_width * 100 / 2)
        
        # Set scene rect
        self.scene.setSceneRect(self.scene.itemsBoundingRect().adjusted(-50, -50, 50, 50))
    
    def drawNode(self, node, x, y, horizontal_spacing):
        """Recursively draw node and its children with connecting edges"""
        if node is None:
            return
        
        # Create the node circle
        node_item = ClickableNodeItem(node, x, y, self.node_radius, self)
        self.scene.addItem(node_item)
        
        # Draw children
        if hasattr(node, 'children') and node.children:
            num_children = len(node.children)
            
            # Calculate spacing between children
            if num_children == 1:
                child_spacing = 0
            else:
                child_spacing = horizontal_spacing / (num_children - 1) if num_children > 1 else 0
            
            # Starting x position for children
            start_x = x - horizontal_spacing / 2
            
            for i, child in enumerate(node.children):
                # Calculate child position
                child_x = start_x + i * child_spacing if num_children > 1 else x
                child_y = y + self.level_height
                
                # Draw edge from parent to child
                edge = QGraphicsLineItem(x, y + self.node_radius, child_x, child_y - self.node_radius)
                edge_pen = QPen(QColor("#667eea"), 3)
                edge.setPen(edge_pen)
                edge.setZValue(-1)  # Draw edges behind nodes
                self.scene.addItem(edge)
                
                # Draw arrow head
                self.drawArrowHead(edge, child_x, child_y - self.node_radius)
                
                # Recursively draw child
                self.drawNode(child, child_x, child_y, horizontal_spacing / 2)
    
    def drawArrowHead(self, edge, end_x, end_y):
        """Draw an arrow head at the end of the edge"""
        arrow_size = 10
        
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
        arrow_pen = QPen(QColor("#667eea"), 3)
        line1 = QGraphicsLineItem(end_x, end_y, p1.x(), p1.y())
        line1.setPen(arrow_pen)
        line1.setZValue(-1)
        self.scene.addItem(line1)
        
        line2 = QGraphicsLineItem(end_x, end_y, p2.x(), p2.y())
        line2.setPen(arrow_pen)
        line2.setZValue(-1)
        self.scene.addItem(line2)
    
    def getTreeDepth(self, node):
        """Calculate the depth of the tree"""
        if node is None or not hasattr(node, 'children') or not node.children:
            return 1
        return 1 + max(self.getTreeDepth(child) for child in node.children)
    
    def getTreeWidth(self, node):
        """Calculate the width of the tree (number of leaf nodes)"""
        if node is None:
            return 0
        if not hasattr(node, 'children') or not node.children:
            return 1
        return sum(self.getTreeWidth(child) for child in node.children)
    
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
                details += f"  [{i}] {child_type} Value: {child.value}\n"
        else:
            details += "\n" + "─" * 40 + "\n"
            details += "Children:       🍃 LEAF NODE (no children)\n"
            details += "─" * 40 + "\n"
        
        self.details_widget.setPlainText(details)


# Example usage:
class Node:
    def __init__(self, value, node_type=None):
        self.value = value
        self.node_type = node_type  # "expect", True (max), False (min), or None
        self.children = []
    
    def add_child(self, child):
        self.children.append(child)
        return child


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    # Create sample tree matching your image
    root = Node(5, "expect")
    
    b = root.add_child(Node(3, True))
    c = root.add_child(Node(7, True))
    
    a = b.add_child(Node(2, False))
    d = b.add_child(Node(4, False))
    
    e = a.add_child(Node(1, None))
    f = d.add_child(Node(5, None))
    
    h = c.add_child(Node(6, False))
    i = c.add_child(Node(8, False))
    
    j = h.add_child(Node(7, None))
    
    app = QApplication(sys.argv)
    window = TreeWindow(root, "Expectimax")
    window.show()
    sys.exit(app.exec_())