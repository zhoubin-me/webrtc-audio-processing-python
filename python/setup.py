import os
import subprocess
import sys
from pathlib import Path
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext as _build_ext

# Try to import pybind11
try:
    from pybind11 import get_cmake_dir
    import pybind11
    PYBIND11_AVAILABLE = True
except ImportError:
    PYBIND11_AVAILABLE = False
    print("Warning: pybind11 not found. Installing it first...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pybind11[global]>=2.6.0"])
    try:
        from pybind11 import get_cmake_dir
        import pybind11
        PYBIND11_AVAILABLE = True
    except ImportError:
        print("Error: Failed to install pybind11")
        sys.exit(1)

# Define the extension module
ext_modules = [
    Extension(
        "webrtc_audio_processing",
        [
            "webrtc_audio_processing.cpp",
        ],
        include_dirs=[
            # pybind11 includes
            pybind11.get_include(),
            # Path to webrtc headers
            "../install/include",  # Installed headers
            "../install/include/webrtc-audio-processing-2",
        ],
        libraries=["webrtc-audio-processing-2"],  # Link against the installed library
        library_dirs=[
            "/usr/local/lib",  # Common install location
            "../install/lib",  # Local install directory from meson build
        ],
        language='c++',
        define_macros=[
            ("VERSION_INFO", '"dev"'),
        ],
    ),
]


class BuildExt(_build_ext):
    """A custom build extension for adding compiler-specific options."""
    
    def build_extensions(self):
        # Check if we have the webrtc-audio-processing library available
        if not self.check_webrtc_library():
            print("WebRTC Audio Processing library not found.")
            print("Please build and install the C++ library first:")
            print("  meson . build -Dprefix=$PWD/install")
            print("  ninja -C build")
            print("  ninja -C build install")
            sys.exit(1)
        
        # Add C++ standard flag
        ct = self.compiler.compiler_type
        opts = []
        link_opts = []
        
        if ct == 'unix':
            opts.append('-std=c++17')
            if sys.platform == 'darwin':
                opts.append('-stdlib=libc++')
                link_opts.append('-stdlib=libc++')
        elif ct == 'msvc':
            opts.append('/std:c++17')
        
        for ext in self.extensions:
            ext.extra_compile_args = opts
            ext.extra_link_args = link_opts
        
        super().build_extensions()
    
    def check_webrtc_library(self):
        """Check if the webrtc-audio-processing library is available."""
        # Try to find the library in common locations
        search_paths = [
            "/usr/local/lib",
            "/usr/lib", 
            os.path.abspath("../install/lib"),
            "../install/lib",
            "install/lib",
        ]
        
        library_names = [
            "libwebrtc-audio-processing-2.so",
            "libwebrtc-audio-processing-2.a", 
            "libwebrtc-audio-processing-2.dylib",  # macOS
            "libwebrtc-audio-processing-2.1.dylib",  # macOS specific version
        ]
        
        for path in search_paths:
            for lib_name in library_names:
                lib_path = Path(path) / lib_name
                if lib_path.exists():
                    print(f"Found WebRTC library: {lib_path}")
                    return True
        
        # Also check if pkg-config can find it
        try:
            subprocess.check_call(
                ["pkg-config", "--exists", "webrtc-audio-processing-2"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            print("Found WebRTC library via pkg-config")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        return False


if __name__ == "__main__":
    setup(
        ext_modules=ext_modules,
        cmdclass={"build_ext": BuildExt},
        zip_safe=False,
        python_requires=">=3.8",
    )