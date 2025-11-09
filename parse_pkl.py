"""
 Function: Parse .pkl file, output .json file.
 Usage: python parse_pkl.py
"""
import sys
import os
import pickle
import json
import struct
import numpy as np
from typing import Any, Dict, List, Union
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QTreeWidget, QTreeWidgetItem, QPushButton, QLabel,
                            QFileDialog, QMessageBox, QHeaderView, QProgressBar,
                            QTextEdit, QTabWidget, QSplitter)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

class DataLoaderThread(QThread):
    """Thread for loading PKL files in background"""
    finished = pyqtSignal(object, str, str)  # data, filename, file_info
    error = pyqtSignal(str)

    def __init__(self, filename):
        super().__init__()
        self.filename = filename

    def run(self):
        try:
            file_info = self.analyze_file()

            # Try standard pickle loading first
            data, method = self.try_standard_pickle()
            if data is not None:
                self.finished.emit(data, os.path.basename(self.filename),
                                  f"File info: {file_info}\nLoaded with: {method}")
                return

            # If standard pickle fails, try alternative methods
            data, method = self.try_alternative_methods()
            if data is not None:
                self.finished.emit(data, os.path.basename(self.filename),
                                  f"File info: {file_info}\nLoaded with: {method}")
                return

            # If all attempts fail
            raise Exception(f"All loading attempts failed.\nFile analysis: {file_info}")

        except Exception as e:
            self.error.emit(str(e))

    def analyze_file(self):
        """Analyze the file to get basic information"""
        file_size = os.path.getsize(self.filename)
        file_info = f"Size: {file_size} bytes"

        # Read first few bytes to check file signature
        with open(self.filename, 'rb') as f:
            first_bytes = f.read(16)
            hex_repr = ' '.join(f'{b:02x}' for b in first_bytes)
            file_info += f"\nFirst 16 bytes (hex): {hex_repr}"

            # Check for common file signatures
            if first_bytes.startswith(b'\x80'):
                file_info += "\nDetected: Standard pickle file"
            elif first_bytes.startswith(b'\x50\x4b\x03\x04'):  # ZIP file
                file_info += "\nDetected: ZIP file (possibly joblib or compressed pickle)"
            elif first_bytes.startswith(b'\x89PNG\r\n\x1a\n'):  # PNG
                file_info += "\nDetected: PNG image file"
            elif first_bytes.startswith(b'\xff\xd8\xff'):  # JPEG
                file_info += "\nDetected: JPEG image file"
            elif first_bytes.startswith(b'PK\x03\x04'):  # ZIP (alternative)
                file_info += "\nDetected: ZIP archive"
            else:
                file_info += "\nFile type: Unknown (not a standard pickle file)"

        return file_info

    def try_standard_pickle(self):
        """Try standard pickle loading methods"""
        methods = [
            ("Default", {}),
            ("Latin1 encoding", {"encoding": "latin1"}),
            ("Bytes encoding", {"encoding": "bytes"}),
            ("Ignore errors", {"errors": "ignore"}),
        ]

        for method_name, kwargs in methods:
            try:
                with open(self.filename, 'rb') as f:
                    data = pickle.load(f, **kwargs)
                    return data, method_name
            except Exception:
                continue

        return None, None

    def try_alternative_methods(self):
        """Try alternative loading methods for non-standard files"""
        # Try loading as raw bytes and manual parsing
        try:
            with open(self.filename, 'rb') as f:
                content = f.read()

            # Try to detect and handle common issues
            if content.startswith(b'\x0b'):
                # Try skipping the problematic byte
                data = pickle.loads(content[1:])
                return data, "Skipped first byte (0x0b)"
        except:
            pass

        # Try joblib if available
        try:
            import joblib
            data = joblib.load(self.filename)
            return data, "joblib"
        except ImportError:
            pass
        except:
            pass

        # Try PyTorch if available
        try:
            import torch
            data = torch.load(self.filename)
            return data, "PyTorch"
        except ImportError:
            pass
        except:
            pass

        # Try to parse as JSON (in case it's actually a JSON file)
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data, "JSON"
        except:
            pass

        # Try to parse as text
        try:
            with open(self.filename, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(1000)  # Read first 1000 chars
                if any(keyword in content for keyword in ['{', '[', 'xml', 'html']):
                    return content[:500] + "...", "Text/Unknown format"
        except:
            pass

        return None, None

class PKLVisualizer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.data = None
        self.filename = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('PKL File Visualizer')
        self.setGeometry(100, 100, 1400, 900)

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # File selection section
        file_layout = QHBoxLayout()

        self.select_btn = QPushButton('Open')
        self.select_btn.clicked.connect(self.select_pkl_file)

        self.save_btn = QPushButton('Save As')
        self.save_btn.clicked.connect(self.save_as_json)
        self.save_btn.setEnabled(False)

        self.clear_btn = QPushButton('Clear')
        self.clear_btn.clicked.connect(self.clear_display)

        self.file_label = QLabel('No file selected')
        self.file_label.setStyleSheet('color: gray;')

        file_layout.addWidget(self.select_btn)
        file_layout.addWidget(self.save_btn)
        file_layout.addWidget(self.clear_btn)
        # file_layout.addWidget(self.hex_view_btn)
        file_layout.addStretch()
        file_layout.addWidget(self.file_label)

        # Progress bar for loading
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)

        # Create tab widget for different views
        self.tab_widget = QTabWidget()

        # Tree view tab
        self.tree_widget = QTreeWidget()
        # Remove the 'Value' column - only show Key, Type, Shape/Size
        self.tree_widget.setHeaderLabels(['Key', 'Type', 'Shape/Size'])
        self.tree_widget.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tree_widget.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tree_widget.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)

        # Value display on the right (initially empty)
        self.value_view = QTextEdit()
        self.value_view.setReadOnly(True)
        mono = QFont("Courier New")
        mono.setPointSize(10)
        self.value_view.setFont(mono)

        # Use a splitter to place tree (left) and value view (right)
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.tree_widget)
        splitter.addWidget(self.value_view)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 4)

        # Add splitter to tab
        self.tab_widget.addTab(splitter, "Data View")

        # Add widgets to main layout
        main_layout.addLayout(file_layout)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.tab_widget)

        # Connect double-click event for expanding nested structures
        self.tree_widget.itemDoubleClicked.connect(self.on_item_double_click)
        # Also connect single expand event so clicking the expand indicator (>)
        # will load children on the first click (fixes bug where first click did nothing)
        self.tree_widget.itemExpanded.connect(self.on_item_expanded)
        # Connect selection change to update the right-side value view
        self.tree_widget.itemSelectionChanged.connect(self.on_selection_changed)

    def on_selection_changed(self):
        """When a tree item is selected, show its full value in the right panel"""
        items = self.tree_widget.selectedItems()
        if not items or self.data is None:
            self.value_view.clear()
            return

        item = items[0]
        path = self.get_data_path(item)
        value = self.get_data_by_path(path)

        # Format value for display
        display_text = self.format_value_for_display(value)
        self.value_view.setPlainText(display_text)

    def format_value_for_display(self, value, max_chars=20000):
        """Format various Python objects into a readable string for the value panel.

        Tries to convert to JSON-friendly structure first; if that fails, falls back to
        repr() with truncation. For numpy arrays, shows shape, dtype and a small slice.
        """
        try:
            # Small helper to limit nested depth and items
            serializable = self.convert_to_json_serializable(value, max_depth=6)
            try:
                text = json.dumps(serializable, indent=2, ensure_ascii=False)
            except Exception:
                text = str(serializable)

            if len(text) > max_chars:
                return text[:max_chars] + "\n... (truncated)"
            return text
        except Exception:
            pass

        # Fallbacks
        try:
            # Numpy arrays: show shape, dtype and first few elements
            import numpy as _np
            if isinstance(value, _np.ndarray):
                preview = value
                try:
                    preview = value.flatten()[:100]
                    return f"ndarray shape={value.shape} dtype={value.dtype}\n{preview!r}"
                except Exception:
                    return f"ndarray shape={value.shape} dtype={value.dtype}"
        except Exception:
            pass

        try:
            text = repr(value)
            if len(text) > max_chars:
                return text[:max_chars] + "\n... (truncated)"
            return text
        except Exception:
            return f"<{type(value).__name__} (unrepresentable)>"

    def select_pkl_file(self):
        """Open file dialog to select PKL file"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            'Select File',
            '',
            'All Files (*);;PKL Files (*.pkl);;JSON Files (*.json);;Joblib Files (*.joblib)'
        )

        if filename:
            self.load_pkl_file(filename)

    def load_pkl_file(self, filename):
        """Load file using background thread"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.select_btn.setEnabled(False)

        self.loader_thread = DataLoaderThread(filename)
        self.loader_thread.finished.connect(self.on_file_loaded)
        self.loader_thread.error.connect(self.on_file_error)
        self.loader_thread.start()

    def on_file_loaded(self, data, filename, file_info):
        """Handle successful file loading"""
        self.data = data
        self.filename = filename
        self.file_label.setText(filename)
        self.save_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.select_btn.setEnabled(True)

        self.display_data()

        # Show success message
        data_type = type(data).__name__
        if hasattr(data, '__len__'):
            try:
                length = len(data)
                data_info = f"{data_type} with {length} elements"
            except:
                data_info = data_type
        else:
            data_info = data_type

    def on_file_error(self, error_msg):
        """Handle file loading errors"""
        self.progress_bar.setVisible(False)
        self.select_btn.setEnabled(True)

        # Provide detailed error information and suggestions
        detailed_error = f"Failed to load file:\n{error_msg}\n\n"

        # Add troubleshooting suggestions based on error type
        if "0x0b" in error_msg:
            detailed_error += "Troubleshooting suggestions for 0x0b error:\n"
            detailed_error += "1. The file might be corrupted or truncated\n"
            detailed_error += "2. It might be a pickle file from a different Python version\n"
            detailed_error += "3. Try opening it with the same Python version that created it\n"
            detailed_error += "4. The file might be in a custom format, not standard pickle\n"

        QMessageBox.critical(self, 'Error', detailed_error)

    def get_value_info(self, value, max_length=50):
        """Get value information for display"""
        value_type = type(value).__name__
        shape_info = ""
        display_value = ""

        if value is None:
            display_value = "None"
        elif isinstance(value, (str, int, float, bool)):
            display_value = str(value)
            if len(display_value) > max_length:
                display_value = display_value[:max_length] + "..."
        elif hasattr(value, 'shape'):  # numpy arrays
            shape_info = f"{value.shape}"
            display_value = f"{value.dtype}"
        elif hasattr(value, '__len__'):
            try:
                length = len(value)
                shape_info = f"{length}"
                if isinstance(value, (list, tuple, set)):
                    display_value = f"{value_type}"
                else:
                    display_value = f"{value_type}"
            except:
                display_value = f"{value_type}"
        else:
            display_value = f"{value_type}"

        return display_value, value_type, shape_info

    def is_expandable(self, value):
        """Determine whether a value should be considered expandable in the tree.

        Rules:
        - dict is always expandable
        - sequences (list/tuple/set) are expandable only if they contain at least
          one non-primitive element (dict, nested sequence, numpy array-like, etc.)
        - simple lists of scalars (e.g. [1,2,3,4]) are NOT expandable
        """
        # dicts are expandable
        if isinstance(value, dict):
            return True

        # sequences: check their elements
        if isinstance(value, (list, tuple, set)):
            try:
                # empty sequences: nothing to expand
                if len(value) == 0:
                    return False

                for x in value:
                    # nested container -> expandable
                    if isinstance(x, (dict, list, tuple, set)):
                        return True

                    # numpy arrays or array-like with shape -> expandable
                    if hasattr(x, 'shape'):
                        return True

                    # non-primitive object: treat as expandable
                    if not isinstance(x, (str, int, float, bool)):
                        return True

                # all elements are primitive scalars -> not expandable
                return False
            except Exception:
                return False

        return False

    def display_data(self, max_items=10, max_depth=3):
        """Display the loaded data in tree widget"""
        self.tree_widget.clear()

        if self.data is None:
            return

        # Create root item (value column removed)
        _, root_type, root_shape = self.get_value_info(self.data)
        root_item = QTreeWidgetItem(self.tree_widget, ['Root', root_type, root_shape])

        # Add data based on type
        if isinstance(self.data, dict):
            self.add_dict_items(self.data, root_item, max_items, max_depth, 1)
        elif isinstance(self.data, (list, tuple, set)):
            self.add_sequence_items(self.data, root_item, max_items, max_depth, 1)
        else:
            # Single value - value visualization disabled (hide actual value)
            _, value_type, shape_info = self.get_value_info(self.data)
            QTreeWidgetItem(root_item, ['Value', value_type, shape_info])

        root_item.setExpanded(True)
        self.tree_widget.addTopLevelItem(root_item)

    def add_dict_items(self, data_dict, parent_item, max_items, max_depth, current_depth):
        """Add dictionary items to tree"""
        items = list(data_dict.items())[:max_items]
        total_items = len(data_dict)

        for key, value in items:
            key_str = str(key)
            display_value, value_type, shape_info = self.get_value_info(value)

            # Hide value visualization for dictionary entries (keep type/shape)
            child_item = QTreeWidgetItem(parent_item,
                                        [key_str, value_type, shape_info])

            # Add placeholder for nested structures
            # Add placeholder for nested structures (skip simple lists of scalars)
            if self.is_expandable(value) and current_depth < max_depth:
                QTreeWidgetItem(child_item, ['Loading...', '', ''])

        # Show message if there are more items
        if total_items > max_items:
            QTreeWidgetItem(parent_item,
                           [f'... and {total_items - max_items} more', '', ''])

    def add_sequence_items(self, sequence, parent_item, max_items, max_depth, current_depth):
        """Add sequence items to tree"""
        if not hasattr(sequence, '__getitem__'):
            return

        items = list(sequence)[:max_items]
        total_items = len(sequence)

        for i, value in enumerate(items):
            display_value, value_type, shape_info = self.get_value_info(value)

            # Hide value visualization for sequence entries (keep type/shape)
            child_item = QTreeWidgetItem(parent_item,
                                        [f'[{i}]', value_type, shape_info])

            # Add placeholder for nested structures
            # Add placeholder for nested structures (skip simple lists of scalars)
            if self.is_expandable(value) and current_depth < max_depth:
                QTreeWidgetItem(child_item, ['Loading...', '', ''])

        # Show message if there are more items
        if total_items > max_items:
            QTreeWidgetItem(parent_item,
                           [f'... and {total_items - max_items} more', '', ''])

    def on_item_double_click(self, item, column):
        """Handle double-click to expand nested structures"""
        # Check if this item has a "Loading..." placeholder
        if item.childCount() == 1:
            first_child = item.child(0)
            if first_child.text(0) == 'Loading...':
                # Remove placeholder and load actual data
                item.removeChild(first_child)
                self.expand_item(item)

    def on_item_expanded(self, item):
        """Handle single expand (when user clicks the expand indicator)

        This ensures that clicking the '>' arrow will trigger loading of the
        placeholder child (if present) on the first click instead of requiring
        a double-click.
        """
        # Same logic as double-click: if a single placeholder child exists,
        # remove it and populate with the actual children.
        if item.childCount() == 1:
            first_child = item.child(0)
            if first_child.text(0) == 'Loading...':
                item.removeChild(first_child)
                self.expand_item(item)

    def expand_item(self, parent_item):
        """Expand a tree item to show its contents"""
        # Get the data path for this item
        data_path = self.get_data_path(parent_item)
        data = self.get_data_by_path(data_path)

        if data is None:
            return

        current_depth = self.get_item_depth(parent_item)
        max_depth = 3

        if isinstance(data, dict):
            self.add_dict_items(data, parent_item, 10, max_depth, current_depth + 1)
        elif isinstance(data, (list, tuple, set)):
            self.add_sequence_items(data, parent_item, 10, max_depth, current_depth + 1)

    def get_data_path(self, item):
        """Get the path to the data represented by this tree item"""
        path = []
        current_item = item

        while current_item:
            text = current_item.text(0)
            if text != 'Root' and not text.startswith('...'):
                # Handle index notation [0], [1], etc.
                if text.startswith('[') and text.endswith(']'):
                    try:
                        index = int(text[1:-1])
                        path.insert(0, index)
                    except ValueError:
                        path.insert(0, text)
                else:
                    path.insert(0, text)
            current_item = current_item.parent()

        return path[1:] if path and path[0] == 'Root' else path

    def get_data_by_path(self, path):
        """Get data by path list"""
        data = self.data
        for key in path:
            if isinstance(data, (list, tuple)) and isinstance(key, int):
                if 0 <= key < len(data):
                    data = data[key]
                else:
                    return None
            elif isinstance(data, dict) and key in data:
                data = data[key]
            else:
                # Try to convert string key for dictionary access
                try:
                    if key in data:
                        data = data[key]
                    else:
                        return None
                except:
                    return None
        return data

    def get_item_depth(self, item):
        """Calculate depth of tree item"""
        depth = 0
        current_item = item
        while current_item:
            depth += 1
            current_item = current_item.parent()
        return depth

    def save_as_json(self):
        """Save the data structure as JSON file"""
        if self.data is None:
            QMessageBox.warning(self, 'Warning', 'No data to save!')
            return

        filename, _ = QFileDialog.getSaveFileName(
            self,
            'Save as JSON',
            f'{os.path.splitext(self.filename)[0]}.json',
            'JSON Files (*.json);;All Files (*)'
        )

        if filename:
            try:
                json_data = self.convert_to_json_serializable(self.data)

                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, indent=2, ensure_ascii=False)

                QMessageBox.information(self, 'Success', f'Data saved to:\n{filename}')
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Failed to save file:\n{str(e)}')

    def convert_to_json_serializable(self, data, max_depth=10, current_depth=0):
        """Convert data to JSON serializable format"""
        if current_depth >= max_depth:
            return f"{type(data).__name__} (max depth reached)"

        if data is None or isinstance(data, (str, int, float, bool)):
            return data
        elif isinstance(data, dict):
            return {str(k): self.convert_to_json_serializable(v, max_depth, current_depth + 1)
                   for k, v in list(data.items())[:20]}  # Limit to first 20 items
        elif isinstance(data, (list, tuple, set)):
            return [self.convert_to_json_serializable(x, max_depth, current_depth + 1)
                   for x in list(data)[:20]]  # Limit to first 20 items
        elif hasattr(data, 'tolist'):  # numpy arrays
            try:
                return data.tolist()[:20] if hasattr(data.tolist(), '__getitem__') else str(data)
            except:
                return str(data)
        else:
            return str(type(data).__name__)

    def clear_display(self):
        """Clear the current display"""
        self.tree_widget.clear()
        self.data = None
        self.filename = None
        self.file_label.setText('No file selected')
        self.save_btn.setEnabled(False)

# Add missing import
from PyQt5.QtWidgets import QDialog

def main():
    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName('PKL File Visualizer')
    app.setApplicationVersion('0.1')

    # Create and show main window
    window = PKLVisualizer()
    window.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
