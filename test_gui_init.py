import traceback
import sys
sys.path.append(r'C:\Users\Junior T.I\scratch\data_analysis')

try:
    import main_gui
    app = main_gui.TMMApp()
    app.update()
    print('LOADED PERFECTLY')
except Exception as e:
    print('CRASHED WITH:')
    traceback.print_exc()
