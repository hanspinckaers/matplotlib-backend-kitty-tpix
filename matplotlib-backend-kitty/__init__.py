# SPDX-License-Identifier: CC0-1.0

import os
import sys
import hashlib
from io import BytesIO
from subprocess import run

from matplotlib import interactive, is_interactive
from matplotlib._pylab_helpers import Gcf
from matplotlib.backend_bases import (_Backend, FigureManagerBase)
from matplotlib.backends.backend_agg import FigureCanvasAgg

# XXX heuristic for interactive repl
if sys.flags.interactive:
    interactive(True)

def get_file_checksum(file_path):
    """Calculate SHA256 checksum of a file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

class FigureManagerICat(FigureManagerBase):
    @classmethod
    def _run(cls, *cmd):
        def f(*args, output=True, **kwargs):
            if output:
                kwargs['capture_output'] = True
                kwargs['text'] = True
            r = run(cmd + args, **kwargs)
            if output:
                return r.stdout.rstrip()
        return f

    def show(self):
        # Save to temporary file first
        temp_path = '/tmp/img_temp.png'
        self.canvas.figure.savefig(temp_path, format='png', facecolor='#ffffff')
        
        # Calculate checksum
        checksum = get_file_checksum(temp_path)
        
        # Create final filename with checksum
        final_filename = f'img_{checksum[:8]}.png'
        final_path = os.path.join('/tmp', final_filename)
        
        # Move file to final location
        os.rename(temp_path, final_path)
        
        # Print image reference
        print(f'[!img kubernetes://{final_path}]')
        
        # Display using tpix if needed
        tpix = __class__._run('tpix')
        tpix(final_path, output=False)

class FigureCanvasICat(FigureCanvasAgg):
    manager_class = FigureManagerICat

@_Backend.export
class _BackendICatAgg(_Backend):
    FigureCanvas = FigureCanvasICat
    FigureManager = FigureManagerICat

    mainloop = lambda: None

    @classmethod
    def draw_if_interactive(cls):
        manager = Gcf.get_active()
        if is_interactive() and manager.canvas.figure.get_axes():
            cls.show()

    @classmethod
    def show(cls, *args, **kwargs):
        _Backend.show(*args, **kwargs)
        Gcf.destroy_all()
