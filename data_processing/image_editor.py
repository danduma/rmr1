import re
import sys
import pandas as pd
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QCheckBox, 
                            QPushButton, QMessageBox, QSpinBox, QScrollArea)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QImage, QKeySequence, QShortcut, QNativeGestureEvent
import os
from dotenv import load_dotenv
from mouse_data import get_db, get_full_mice_data_from_db

load_dotenv()

LOCAL_BASE_PATH = os.getenv('LOCAL_BASE_PATH')

def tag_has_error(row):
    # Check ear tag condition
    tag_error = False
    if pd.isna(row['ear_tag']):
        tag_error = True
    else:
        try:
            tag_str = str(int(row['ear_tag']))  # Convert to int to remove decimals
            # Check if it's a 4-digit number starting with 5 or 6
            if not (len(tag_str) == 4 and tag_str[0] in ['5', '6']):
                tag_error = True
        except:
            tag_error = True
    return tag_error

def date_has_error(row):
     # Check date condition
    date_error = False
    if pd.isna(row['date']) or row['date'] == '':
        date_error = True
    else:
        try:
            # Try to extract year from the date string
            date_str = str(row['date'])
            if '2023' not in date_str and '2024' not in date_str:
                date_error = True
        except:
            date_error = True
            
    return date_error

def group_sex_dont_match(row, mouse_data):
    """
    Check if group or sex in the row differs from database values.
    Returns True if there's a mismatch, False otherwise.
    """
    try:
        # Find matching mouse by ear tag using dictionary lookup
        if pd.isna(row['ear_tag']):
            return False
            
        mouse = mouse_data.get(row['ear_tag'])
        if not mouse:
            return False
            
        # Check group mismatch - use direct attribute access instead of .get()
        if 'group' in row.index and not pd.isna(row['group']) and mouse.Group_Number is not None:
            if int(row['group']) != mouse.Group_Number:
                return True
                
        # Check sex mismatch - use direct attribute access instead of .get()
        if 'sex' in row.index and not pd.isna(row['sex']) and mouse.Sex:
            if row['sex'][0].upper() != mouse.Sex[0].upper():
                return True
                
        return False
        
    except Exception as e:
        print(f"Error checking group/sex match: {e}")
        return False

def needs_review(row, mice_data):
    tag_error = tag_has_error(row)
    date_error = date_has_error(row)
    mismatch_error = group_sex_dont_match(row, mice_data)
    
    return (tag_error or date_error or mismatch_error) and not row['corrupt']

def update_full_text(df, idx):
    """
    Updates the full_text field for a given row to ensure it starts with the correct ear tag.
    
    Args:
        df: DataFrame containing the data
        idx: Index of the row to update
        row: The row data
    """
    
    row = df.iloc[idx]
    if pd.isna(row['full_text']):
        match = None
    else:
        match = re.match(r"<\/s>\s*?([56]\d{3})\b.*", row['full_text'])
    
    if not tag_has_error(row) and (not match or not str(match.group(1)) == str(row['ear_tag'])):
        df.at[idx, 'full_text'] = f"</s>{row['ear_tag']}\n" + row['full_text'].replace(f"</s>", "")
        # print(row['ear_tag'], df.at[idx, 'full_text'])

    return df.at[idx, 'full_text']

def fix_full_text(df):
    # Iterate through the dataframe and modify full_text where needed
    for idx, row in df.iterrows():
        update_full_text(df, idx)
    return df

class ImageEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Editor")

        db = next(get_db())
        
        # Get mice data and create an indexed dictionary
        self.mice_data = get_full_mice_data_from_db(db=db)
        self.mice_by_tag = {m.EarTag: m for m in self.mice_data}
        
        # Get screen size
        screen = QApplication.primaryScreen().geometry()
        
        # Set window size to 80% of screen size
        width = min(int(screen.width() * 0.8), 1200)
        height = min(int(screen.height() * 0.8), 800)
        
        # Center the window
        x = (screen.width() - width) // 2
        y = (screen.height() - height) // 2
        
        self.setGeometry(x, y, width, height)
        
        # Set minimum sizes
        self.setMinimumSize(800, 600)
        
        # Load the CSV data
        self.csv_path = 'data/image_results.csv'  # Store path as instance variable
        self.df = pd.read_csv(self.csv_path, dtype={'ear_tag': 'Int64'})
        
        self.df = fix_full_text(self.df)
        
        # Filter rows based on conditions

        # Apply the filter
        self.rows_to_review = [
            idx for idx in range(len(self.df)) 
            if needs_review(self.df.iloc[idx], self.mice_by_tag)
        ]
        
        print(f"Found {len(self.rows_to_review)} rows needing review out of {len(self.df)} total rows")
        
        self.current_index = 0
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        layout.setSpacing(0)  # Remove spacing between panels
        layout.setContentsMargins(0, 0, 0, 0)  # Remove ALL margins
        
        # Left panel for image
        image_panel = QWidget()
        image_panel.setContentsMargins(0, 0, 0, 0)
        image_layout = QVBoxLayout(image_panel)
        image_layout.setContentsMargins(0, 0, 0, 0)
        image_layout.setSpacing(0)
        
        # Create scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        self.image_label = QLabel()
        self.image_label.setMinimumSize(800, 600)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("QLabel { padding: 0px; margin: 0px; }")
        
        self.scroll_area.setWidget(self.image_label)
        image_layout.addWidget(self.scroll_area)
        layout.addWidget(image_panel, stretch=4)
        
        # Add zoom tracking
        self.zoom_factor = 1.0
        self.original_pixmap = None
        
        # Right panel for controls
        form_widget = QWidget()
        form_widget.setMinimumWidth(400)
        form_widget.setMaximumWidth(500)
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(20, 20, 20, 20)
        
        # Set fixed width for labels to ensure alignment
        LABEL_WIDTH = 80
        
        # Create horizontal layout for ear tag
        ear_tag_layout = QHBoxLayout()
        ear_tag_label = QLabel("Ear Tag:")
        ear_tag_label.setFixedWidth(LABEL_WIDTH)
        ear_tag_layout.addWidget(ear_tag_label)
        self.ear_tag_input = QSpinBox()
        self.ear_tag_input.setRange(4000, 6999)
        self.ear_tag_input.setSpecialValueText("")
        ear_tag_layout.addWidget(self.ear_tag_input)
        ear_tag_layout.addStretch()  # Add stretch to push content to the left
        form_layout.addLayout(ear_tag_layout)
        
        # Create horizontal layout for date
        date_layout = QHBoxLayout()
        date_label = QLabel("Date:")
        date_label.setFixedWidth(LABEL_WIDTH)
        date_layout.addWidget(date_label)
        self.date_input = QLineEdit()
        date_layout.addWidget(self.date_input)
        date_layout.addStretch()  # Add stretch to push content to the left
        form_layout.addLayout(date_layout)
        
        # Create horizontal layout for group
        group_layout = QHBoxLayout()
        group_label = QLabel("Group:")
        group_label.setFixedWidth(LABEL_WIDTH)
        group_layout.addWidget(group_label)
        self.group_input = QSpinBox()
        self.group_input.setRange(0, 99)
        self.group_input.setSpecialValueText("")
        group_layout.addWidget(self.group_input)
        group_layout.addStretch()  # Add stretch to push content to the left
        form_layout.addLayout(group_layout)
        
        # Create horizontal layout for sex
        sex_layout = QHBoxLayout()
        sex_label = QLabel("Sex:")
        sex_label.setFixedWidth(LABEL_WIDTH)
        sex_layout.addWidget(sex_label)
        self.sex_input = QLineEdit()
        sex_layout.addWidget(self.sex_input)
        sex_layout.addStretch()  # Add stretch to push content to the left
        form_layout.addLayout(sex_layout)
        
        # Add database info label
        self.db_info_label = QLabel()
        self.db_info_label.setWordWrap(True)
        self.db_info_label.setStyleSheet("QLabel { color: #666666; }")
        form_layout.addWidget(self.db_info_label)
        
        # Add corrupt checkbox
        self.corrupt_checkbox = QCheckBox("Corrupt")
        form_layout.addWidget(self.corrupt_checkbox)
        
        layout.addWidget(form_widget, stretch=1)
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        self.prev_button = QPushButton("Previous (⌘←)")
        self.prev_button.setShortcut("Ctrl+Left")
        self.next_button = QPushButton("Next (⌘→)")
        self.next_button.setShortcut("Ctrl+Right")
        self.save_button = QPushButton("Save")
        
        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.next_button)
        nav_layout.addWidget(self.save_button)
        form_layout.addLayout(nav_layout)
        
        # Create status label with word wrap
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.status_label.setMinimumWidth(380)
        form_layout.addWidget(self.status_label)
        
        # Create notification label
        self.notification_label = QLabel()
        self.notification_label.setWordWrap(True)
        self.notification_label.setMinimumWidth(380)
        self.notification_label.setStyleSheet("QLabel { color: #2e8b57; }") # Dark sea green color
        form_layout.addWidget(self.notification_label)
        
        # Connect signals
        self.prev_button.clicked.connect(self.show_previous)
        self.next_button.clicked.connect(self.show_next)
        self.save_button.clicked.connect(self.save_changes)
        self.ear_tag_input.valueChanged.connect(self.update_db_info)
        self.ear_tag_input.textChanged.connect(self.update_current_row)
        self.date_input.textChanged.connect(self.update_current_row)
        self.corrupt_checkbox.stateChanged.connect(self.update_current_row)
        self.group_input.textChanged.connect(self.update_current_row)
        self.sex_input.textChanged.connect(self.update_current_row)
        
        # Set focus policy for the window and widgets
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.scroll_area.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.image_label.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Show first image
        self.show_current_row()
        
        # Store the normal status text
        self.current_status = ""

    def event(self, event):
        if isinstance(event, QNativeGestureEvent) and event.gestureType() == Qt.NativeGestureType.ZoomNativeGesture:
            if self.original_pixmap:
                # Get mouse position relative to the image label
                mouse_pos = self.image_label.mapFromGlobal(event.globalPosition().toPoint())
                
                # Calculate relative position in the image (0 to 1)
                rel_x = mouse_pos.x() / self.image_label.width()
                rel_y = mouse_pos.y() / self.image_label.height()
                
                # Calculate zoom
                zoom_change = event.value()
                self.zoom_factor *= (1 + zoom_change)
                self.zoom_factor = max(0.1, min(5.0, self.zoom_factor))
                
                # Calculate new size maintaining aspect ratio
                new_width = int(self.original_pixmap.width() * self.zoom_factor)
                new_height = int(self.original_pixmap.height() * self.zoom_factor)
                
                # Scale the pixmap
                scaled_pixmap = self.original_pixmap.scaled(
                    new_width,
                    new_height,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                
                # Update label size and pixmap
                self.image_label.setFixedSize(new_width, new_height)
                self.image_label.setPixmap(scaled_pixmap)
                
                # Calculate new scroll position to keep mouse point fixed
                viewport_width = self.scroll_area.viewport().width()
                viewport_height = self.scroll_area.viewport().height()
                
                new_x = int(rel_x * new_width - viewport_width/2)
                new_y = int(rel_y * new_height - viewport_height/2)
                
                # Update scroll position
                QTimer.singleShot(0, lambda: self._update_scroll_position(new_x, new_y))
                
                return True
        return super().event(event)

    def _update_scroll_position(self, x, y):
        # Ensure scroll positions are within bounds
        x = max(0, min(x, self.scroll_area.horizontalScrollBar().maximum()))
        y = max(0, min(y, self.scroll_area.verticalScrollBar().maximum()))
        
        self.scroll_area.horizontalScrollBar().setValue(x)
        self.scroll_area.verticalScrollBar().setValue(y)

    def show_current_row(self):
        if not self.rows_to_review:
            QMessageBox.information(self, "Complete", "No images to review!")
            self.close()
            return
            
        idx = self.rows_to_review[self.current_index]
        row = self.df.iloc[idx]
        
        # Update form fields
        self.ear_tag_input.setValue(int(row['ear_tag']) if pd.notna(row['ear_tag']) else 0)
        self.date_input.setText(str(row['date']) if pd.notna(row['date']) else '')
        self.corrupt_checkbox.setChecked(row.get('corrupt', False) if pd.notna(row.get('corrupt')) else False)
        self.group_input.setValue(int(row['group']) if pd.notna(row.get('group')) else 0)
        self.sex_input.setText(str(row['sex']) if pd.notna(row.get('sex')) else '')
        
        # Load and display image
        image_path = row['file_path']
        full_path = os.path.join(LOCAL_BASE_PATH, image_path)
        
        if os.path.exists(full_path):
            pixmap = QPixmap(full_path)
            if not pixmap.isNull():
                self.original_pixmap = pixmap  # Store original for zooming
                
                # Get the width of the scroll area
                available_width = self.scroll_area.width()
                
                # Calculate initial scale to fit width
                scale_factor = available_width / pixmap.width()
                self.zoom_factor = scale_factor
                
                # Scale the image
                new_width = int(pixmap.width() * scale_factor)
                new_height = int(pixmap.height() * scale_factor)
                
                scaled_pixmap = pixmap.scaled(
                    new_width,
                    new_height,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                
                # Set the label size and pixmap
                self.image_label.setFixedSize(new_width, new_height)
                self.image_label.setPixmap(scaled_pixmap)
        
        # Update status with absolute row number
        self.status_label.setText(
            f"Image {self.current_index + 1} of {len(self.rows_to_review)}\n"
            f"Row {idx + 1} of {len(self.df)}\n"
            f"File: {image_path}"
        )
        self.notification_label.clear()  # Clear any existing notification

        # Update database info
        ear_tag = row['ear_tag'] if pd.notna(row['ear_tag']) else None
        if ear_tag and ear_tag in self.mice_by_tag:
            mouse = self.mice_by_tag[ear_tag]
            self.db_info_label.setText(f"Database values:\nGroup: {mouse.Group_Number}\nSex: {mouse.Sex}")
        else:
            self.db_info_label.setText("No database record found")

    def show_previous(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.show_current_row()

    def show_next(self):
        if self.current_index < len(self.rows_to_review) - 1:
            self.current_index += 1
            self.show_current_row()

    def update_current_row(self):
        if self.rows_to_review:
            idx = self.rows_to_review[self.current_index]
            self.df.at[idx, 'ear_tag'] = self.ear_tag_input.value() or None  # Convert 0 to None
            self.df.at[idx, 'date'] = self.date_input.text()
            self.df.at[idx, 'corrupt'] = self.corrupt_checkbox.isChecked()
            self.df.at[idx, 'group'] = self.group_input.value() or None  # Convert 0 to None
            self.df.at[idx, 'sex'] = self.sex_input.text()
            update_full_text(self.df, idx)

    def save_changes(self):
        self.update_current_row()
        self.df.to_csv(self.csv_path, index=False)  # Use stored path
        
        # Show temporary success message in notification label
        self.notification_label.setText("✓ Changes saved!")
        
        # Clear notification after 2 seconds
        QTimer.singleShot(2000, self.notification_label.clear)

    def keyPressEvent(self, event):
        # Check for Command (Meta) + Arrow keys
        if event.modifiers() == Qt.KeyboardModifier.MetaModifier:
            if event.key() == Qt.Key.Key_Right:
                self.show_next()
                event.accept()
                return
            elif event.key() == Qt.Key.Key_Left:
                self.show_previous()
                event.accept()
                return
        super().keyPressEvent(event)

    def update_db_info(self):
        """Update the database info label based on the current ear tag value."""
        ear_tag = self.ear_tag_input.value() or None
        if ear_tag and ear_tag in self.mice_by_tag:
            mouse = self.mice_by_tag[ear_tag]
            self.db_info_label.setText(f"Database values:\nGroup: {mouse.Group_Number}\nSex: {mouse.Sex}")
        else:
            self.db_info_label.setText("No database record found")

def main():

    app = QApplication(sys.argv)
    window = ImageEditor()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 