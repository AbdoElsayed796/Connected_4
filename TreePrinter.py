import os
from datetime import datetime

class TreePrinter:
    """Class to print tree structures to terminal and file"""
    
    def __init__(self, algorithm_name=""):
        self.algorithm_name = algorithm_name
        self.output_lines = []
    
    def print_tree(self, root, output_file=None):
        """
        Print the tree structure to both terminal and file
        
        Args:
            root: The root node of the tree
            output_file: Optional filename for output (default: auto-generated)
        """
        if root is None:
            print("No tree to print!")
            return
        
        # Clear previous output
        self.output_lines = []
        
        # Add header
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header = f"""
{'='*80}
                        AI SEARCH TREE STRUCTURE
{'='*80}
Algorithm: {self.algorithm_name}
Timestamp: {timestamp}
{'='*80}
"""
        self.output_lines.append(header)
        
        # Build the tree structure
        self._build_tree_structure(root, "", True, True)
        
        # Add footer with statistics
        stats = self._calculate_statistics(root)
        footer = f"""
{'='*80}
                            TREE STATISTICS
{'='*80}
Total Nodes:        {stats['total_nodes']}
Max Depth:          {stats['max_depth']}
Leaf Nodes:         {stats['leaf_nodes']}
Branch Nodes:       {stats['branch_nodes']}
Pruned Nodes:       {stats['pruned_nodes']}
Average Branching:  {stats['avg_branching']:.2f}
{'='*80}
"""
        self.output_lines.append(footer)
        
        # Combine all lines
        full_output = "\n".join(self.output_lines)
        
        # Print to terminal
        print(full_output)
        
        # Save to file
        if output_file is None:
            # Auto-generate filename
            timestamp_file = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"tree_{self.algorithm_name.replace(' ', '_')}_{timestamp_file}.txt"
        
        # Create output directory if it doesn't exist
        output_dir = "tree_outputs"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        filepath = os.path.join(output_dir, output_file)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(full_output)
            print(f"\n✅ Tree saved to: {filepath}\n")
        except Exception as e:
            print(f"\n❌ Error saving tree to file: {e}\n")
    
    def _build_tree_structure(self, node, prefix, is_last, is_root):
        """
        Recursively build the tree structure using ASCII art
        
        Args:
            node: Current node
            prefix: String prefix for indentation
            is_last: Whether this is the last child
            is_root: Whether this is the root node
        """
        if node is None:
            return
        
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
            current_line = node_info
        else:
            connector = "└── " if is_last else "├── "
            current_line = prefix + connector + node_info
        
        # Add to output
        self.output_lines.append(current_line)
        
        # Process children
        if hasattr(node, 'children') and node.children:
            # Update prefix for children
            if is_root:
                new_prefix = ""
            else:
                extension = "    " if is_last else "│   "
                new_prefix = prefix + extension
            
            # Print all children
            for i, child in enumerate(node.children):
                is_last_child = (i == len(node.children) - 1)
                self._build_tree_structure(child, new_prefix, is_last_child, False)
    
    def _calculate_statistics(self, root):
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
    
    def print_compact_tree(self, root, max_depth=3):
        """
        Print a compact version of the tree (limited depth)
        
        Args:
            root: The root node
            max_depth: Maximum depth to print
        """
        if root is None:
            print("No tree to print!")
            return
        
        self.output_lines = []
        
        header = f"""
{'='*60}
            COMPACT TREE VIEW (Depth ≤ {max_depth})
{'='*60}
"""
        self.output_lines.append(header)
        
        self._build_compact_structure(root, "", True, True, 0, max_depth)
        
        footer = "\n" + "="*60 + "\n"
        self.output_lines.append(footer)
        
        full_output = "\n".join(self.output_lines)
        print(full_output)
    
    def _build_compact_structure(self, node, prefix, is_last, is_root, current_depth, max_depth):
        """Build compact tree structure with depth limit"""
        if node is None or current_depth > max_depth:
            return
        
        # Node symbol
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
        
        # Format value
        if node.value == "PRUNED":
            value_str = "✂"
        elif node.value is None:
            value_str = "?"
        else:
            try:
                value_str = f"{float(node.value):.1f}"
            except:
                value_str = str(node.value)[:6]
        
        # Build line
        if is_root:
            connector = ""
            current_line = f"{node_symbol} {value_str}"
        else:
            connector = "└─ " if is_last else "├─ "
            current_line = prefix + connector + f"{node_symbol} {value_str}"
        
        self.output_lines.append(current_line)
        
        # Process children if within depth limit
        if current_depth < max_depth and hasattr(node, 'children') and node.children:
            if is_root:
                new_prefix = ""
            else:
                extension = "   " if is_last else "│  "
                new_prefix = prefix + extension
            
            for i, child in enumerate(node.children):
                is_last_child = (i == len(node.children) - 1)
                self._build_compact_structure(child, new_prefix, is_last_child, False, 
                                             current_depth + 1, max_depth)
        elif current_depth == max_depth and hasattr(node, 'children') and node.children:
            # Indicate there are more children
            extension = "   " if is_last else "│  "
            new_prefix = prefix + extension
            self.output_lines.append(new_prefix + f"... ({len(node.children)} children)")


# Example usage function
def print_search_tree(root, algorithm_name, compact=False):
    """
    Convenience function to print a search tree
    
    Args:
        root: Root node of the tree
        algorithm_name: Name of the algorithm used
        compact: If True, print compact view; otherwise full tree
    """
    printer = TreePrinter(algorithm_name)
    
    if compact:
        printer.print_compact_tree(root, max_depth=4)
    else:
        printer.print_tree(root)