class TreeNode:
    def __init__(self, col=None, depth=0, node_type="max"):
        self.col = col         
        self.depth = depth        
        self.node_type = node_type 
        self.value = None        
        self.children = []        

    def add_child(self, child):
        self.children.append(child)

    def set_value(self, v):
        self.value = v

    def print_tree(self, indent=0):
        symbol = {
            "max":  "MAX",
            "min":  "MIN",
            "expect": "EXPECT"
        }[self.node_type]

        print(" " * indent + f"{symbol} Node | col={self.col} | value={self.value}")

        for child in self.children:
            child.print_tree(indent + 4)
