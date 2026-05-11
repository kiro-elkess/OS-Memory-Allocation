# OS Memory Allocation Simulator

A Python-based Operating Systems project that simulates dynamic memory allocation techniques and memory segmentation strategies using an interactive GUI.

## Features

- Dynamic memory allocation simulation
- Supports:
  - First Fit
  - Best Fit
- Memory segmentation visualization
- Process allocation and deallocation
- Real-time memory status updates
- User-friendly graphical interface
- Executable `.exe` support using PyInstaller

## Technologies Used

- Python 3
- Tkinter (GUI)
- PyInstaller

## Project Structure

```text
OS_Memory_Allocation_V2/
│
├── memory_segmentation_v2.py
├── README.md
├── dist/
├── build/
└── screenshots/
```

## How to Run

### Run Using Python

```bash
python memory_segmentation_v2.py
```

### Build Executable File

```bash
python -m PyInstaller --onefile --windowed --clean memory_segmentation_v2.py
```

The generated executable will be located in:

```text
dist/memory_segmentation_v2.exe
```

## Memory Allocation Algorithms

### First Fit
Allocates the first available memory block that is large enough for the process.

### Best Fit
Allocates the smallest available memory block that can fit the process, minimizing wasted space.

## Screenshots

Add your screenshots inside a `screenshots` folder and reference them here.

Example:

```markdown
![Main Interface](screenshots/interface.png)
```

## Educational Objectives

This project demonstrates:

- Dynamic memory management
- Internal and external fragmentation
- Allocation strategies
- Operating system memory concepts
- GUI development with Python

## Contributors

- Kirollos Elkess Antonious Louiz

## License

This project is for educational purposes.
