from src.photobook_as_code.themes import load_theme
try:
    load_theme("clean")
except Exception as e:
    import traceback
    traceback.print_exc()
