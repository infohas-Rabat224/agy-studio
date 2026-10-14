"""
Clipboard Manager for Agy Studio.
Provides native Windows desktop clipboard acquisition and web paste ingestion.
Prioritizes: 1. Image/Screenshot -> 2. Files -> 3. Text -> 4. Unsupported.
Never silently fails.
"""

import os
import sys
import time
import ctypes
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

class ClipboardManager:
    """
    Manages desktop clipboard acquisition on Windows and web bridge ingestion.
    """

    @classmethod
    def read_native_clipboard(cls) -> Tuple[str, Any, Optional[str]]:
        """
        Reads native Windows clipboard with strict priority:
        1. Image (bitmap / screenshot) -> ("image", PIL.Image.Image, None)
        2. Files (CF_HDROP) -> ("files", List[str], None)
        3. Text (CF_UNICODETEXT) -> ("text", str, None)
        4. Empty / Unsupported -> ("none", None, "Le presse-papiers est vide ou contient un format non pris en charge.")
        """
        # 1. Try PIL.ImageGrab first (handles both DIB image and CF_HDROP file lists natively on Windows)
        try:
            from PIL import ImageGrab, Image
            grabbed = ImageGrab.grabclipboard()
            if grabbed is not None:
                # If grabbed is a PIL Image
                if isinstance(grabbed, Image.Image):
                    return "image", grabbed, None
                # If grabbed is a list of file paths (CF_HDROP)
                if isinstance(grabbed, list) and all(isinstance(p, str) for p in grabbed):
                    valid_files = [p for p in grabbed if os.path.exists(p)]
                    if valid_files:
                        return "files", valid_files, None
        except Exception:
            pass

        # 2. Native Win32 ctypes acquisition for Text and Explorer Files (with 64-bit safety)
        if sys.platform == "win32":
            try:
                user32 = ctypes.windll.user32
                kernel32 = ctypes.windll.kernel32
                shell32 = ctypes.windll.shell32

                user32.OpenClipboard.argtypes = [ctypes.c_void_p]
                user32.OpenClipboard.restype = ctypes.c_bool
                user32.CloseClipboard.argtypes = []
                user32.CloseClipboard.restype = ctypes.c_bool
                user32.IsClipboardFormatAvailable.argtypes = [ctypes.c_uint]
                user32.IsClipboardFormatAvailable.restype = ctypes.c_bool
                user32.GetClipboardData.argtypes = [ctypes.c_uint]
                user32.GetClipboardData.restype = ctypes.c_void_p

                kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
                kernel32.GlobalLock.restype = ctypes.c_void_p
                kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
                kernel32.GlobalUnlock.restype = ctypes.c_bool

                shell32.DragQueryFileW.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_wchar_p, ctypes.c_uint]
                shell32.DragQueryFileW.restype = ctypes.c_uint

                CF_UNICODETEXT = 13
                CF_HDROP = 15

                if user32.OpenClipboard(None):
                    try:
                        # Check files (CF_HDROP)
                        if user32.IsClipboardFormatAvailable(CF_HDROP):
                            h_drop = user32.GetClipboardData(CF_HDROP)
                            if h_drop:
                                count = shell32.DragQueryFileW(h_drop, 0xFFFFFFFF, None, 0)
                                file_paths = []
                                buf = ctypes.create_unicode_buffer(1024)
                                for i in range(count):
                                    shell32.DragQueryFileW(h_drop, i, buf, 1024)
                                    file_paths.append(buf.value)
                                if file_paths:
                                    return "files", file_paths, None

                        # Check text (CF_UNICODETEXT)
                        if user32.IsClipboardFormatAvailable(CF_UNICODETEXT):
                            h_data = user32.GetClipboardData(CF_UNICODETEXT)
                            if h_data:
                                p_data = kernel32.GlobalLock(h_data)
                                if p_data:
                                    try:
                                        text = ctypes.c_wchar_p(p_data).value
                                        if text and text.strip():
                                            return "text", text, None
                                    finally:
                                        kernel32.GlobalUnlock(h_data)
                    finally:
                        user32.CloseClipboard()
            except Exception:
                pass

        return "none", None, "Le presse-papiers est vide ou ne contient aucune donnée compatible (image, fichier, texte)."
