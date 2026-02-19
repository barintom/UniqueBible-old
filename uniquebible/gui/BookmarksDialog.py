import os
from uniquebible import config
from uniquebible.util.BibleVerseParser import BibleVerseParser

if config.qtLibrary == "pyside6":
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QRadioButton, QButtonGroup, QScrollArea, QWidget, QLabel
else:
    from qtpy.QtCore import Qt
    from qtpy.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QRadioButton, QButtonGroup, QScrollArea, QWidget, QLabel

class BookmarksDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle(config.thisTranslation.get("menu_bookmarks", "Bookmarks"))
        self.setMinimumSize(400, 300)
        self.setModal(True)
        self.bookmarks_file = os.path.join(config.ubaUserDir, "bookmarks.txt")
        
        # Load bookmarks once and keep a local copy
        self.bookmarks = self.load_bookmarks()
        
        # Get active verse reference
        self.current_verse = self.parent.bcvToVerseReference(config.mainB, config.mainC, config.mainV)
        
        self.setupUI()

    def load_bookmarks(self):
        if os.path.exists(self.bookmarks_file):
            try:
                with open(self.bookmarks_file, "r", encoding="utf-8") as f:
                    return [line.strip() for line in f if line.strip()]
            except Exception as e:
                print(f"Error loading bookmarks: {e}")
        return []

    def save_bookmarks(self):
        try:
            with open(self.bookmarks_file, "w", encoding="utf-8") as f:
                for b in self.bookmarks:
                    f.write(b + "\n")
        except Exception as e:
            print(f"Error saving bookmarks: {e}")

    def setupUI(self):
        self.mainLayout = QVBoxLayout()

        # Top buttons
        topLayout = QHBoxLayout()
        add_text = f"{config.thisTranslation.get('add', 'Add')} {self.current_verse}"
        self.addButton = QPushButton(add_text)
        self.addButton.clicked.connect(self.add_active_verse)
        topLayout.addWidget(self.addButton)

        self.removeButton = QPushButton(config.thisTranslation.get("remove_item", "Remove item"))
        self.removeButton.clicked.connect(self.remove_selected)
        topLayout.addWidget(self.removeButton)
        self.mainLayout.addLayout(topLayout)

        # Bookmarks list
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scrollContent = QWidget()
        self.scrollLayout = QVBoxLayout(self.scrollContent)
        self.scrollLayout.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.scrollContent)
        self.mainLayout.addWidget(self.scroll)

        self.buttonGroup = QButtonGroup(self)
        
        self.refresh_list()

        # Bottom buttons
        bottomLayout = QHBoxLayout()
        self.selectSaveButton = QPushButton(config.thisTranslation.get("select_save", "Select / Save"))
        self.selectSaveButton.clicked.connect(self.select_and_close)
        bottomLayout.addWidget(self.selectSaveButton)

        self.cancelButton = QPushButton(config.thisTranslation.get("message_cancel", "Cancel"))
        self.cancelButton.clicked.connect(self.reject)
        bottomLayout.addWidget(self.cancelButton)
        self.mainLayout.addLayout(bottomLayout)

        self.setLayout(self.mainLayout)

    def refresh_list(self):
        # Clear existing
        for i in reversed(range(self.scrollLayout.count())): 
            widget = self.scrollLayout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        # Completely recreate the button group to reset IDs
        if hasattr(self, "buttonGroup"):
            self.buttonGroup.deleteLater()
        self.buttonGroup = QButtonGroup(self)
        
        # Add bookmarks
        for index, bookmark in enumerate(self.bookmarks):
            rb = QRadioButton(bookmark)
            self.scrollLayout.addWidget(rb)
            self.buttonGroup.addButton(rb, index)
        
        if self.bookmarks and self.buttonGroup.button(0):
            self.buttonGroup.button(0).setChecked(True)

    def add_active_verse(self):
        if self.current_verse not in self.bookmarks:
            self.bookmarks.append(self.current_verse)
            self.refresh_list()
            # Select the newly added item
            self.buttonGroup.button(len(self.bookmarks)-1).setChecked(True)

    def remove_selected(self):
        checked_id = self.buttonGroup.checkedId()
        if checked_id != -1:
            self.bookmarks.pop(checked_id)
            self.refresh_list()

    def select_and_close(self):
        # Save to disk only upon confirmation
        self.save_bookmarks()
        
        checked_id = self.buttonGroup.checkedId()
        if checked_id != -1:
            selected_bookmark = self.bookmarks[checked_id]
            
            # Trigger the same action as clicking a verse number in the bible window
            # Command format: _vnsc:::{text}.{b}.{c}.{v}.{verseReference}
            try:
                # Use a parser to get B, C, V
                parser = BibleVerseParser(config.parserStandarisation)
                b, c, v, *rest = parser.verseReferenceToBCV(selected_bookmark)
            except Exception as e:
                print(f"Error parsing bookmark reference: {e}")
                # Fallback to current if parsing fails for some reason
                b, c, v = config.mainB, config.mainC, config.mainV

            vnsc_command = f"_vnsc:::{config.mainText}.{b}.{c}.{v}.{selected_bookmark}"
            
            self.parent.runTextCommand(vnsc_command, source="main")
            self.accept()
        else:
            self.accept()
