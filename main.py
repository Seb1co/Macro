from PyQt6.QtWidgets import QApplication
import sys
from UI import Macro_UI

def main():
    app = QApplication(sys.argv)
    ui = Macro_UI()
    ui.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()


#
#
#
#
#
#
#
#
#
#