# Student Attendance Management & Signature Fraud Detection System (SAMS)

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green.svg)](https://opencv.org/)
[![SQLite](https://img.shields.io/badge/SQLite-3-blue.svg)](https://www.sqlite.org/)

An automated, end-to-end Computer Vision and Image Processing system built in Python for automated student attendance extraction from physical signing sheets and dynamic signature verification / fraud detection.

---

## 👥 Project Team Members

| Student ID | Student Name | GitHub Username |
| :---: | :--- | :--- |
| **28990** | G D D Dilshan | [@GDDDilshan](https://github.com/GDDDilshan) |
| **29271** | G.K.J.P. Weerathunga | [@GKJPW](https://github.com/GKJPW) |
| **29135** | J.S.H. Hansaka | [@JSHhansaka](https://github.com/JSHhansaka) |
| **29341** | H.K.L Rupasinghe | [@KasunLakma](https://github.com/KasunLakma) |
| **21816** | R.M.P. Raviranga | [@Pramuditha200](https://github.com/Pramuditha200) |
| **29657** | K.K.G.A.Devinda | [@kgadevinda](https://github.com/kgadevinda) |
| **30341** | P.A.G Manawadu | [@PabinduAmodya](https://github.com/PabinduAmodya) |
| **29876** | M K Jayashan | [@mkjayashan](https://github.com/mkjayashan) |
| **28768** | R P C S D Rajaguru | [@ChamikaRajaguru](https://github.com/ChamikaRajaguru) |
| **29199** | A.T.S Samadhi | [@atssamadhi](https://github.com/atssamadhi) |

---

## 🚀 Quick Start Guide (Run on Your Computer)

Follow these simple steps to install and run this project on your local machine.

---

### Step 1: Clone or Download the Repository

Open your terminal and clone the repository, or download and extract the ZIP file:

```bash
git clone https://github.com/GDDDilshan/CGV.git
cd CGV
```

---

### Step 2: Install Python & Dependencies

Ensure you have **Python 3.8+** installed on your computer.

Install the required Python packages using `pip`:

```bash
pip install opencv-python numpy matplotlib
```

*(Note: `sqlite3` and `xml.etree.ElementTree` come pre-installed with standard Python distributions).*

---

### Step 3: SQLite Database Setup

The project uses an **SQLite database** (`database/attendance.db`). **No manual SQL installation or table creation is required.**

To initialize the database schema and populate student records from `info.xml`, run:

```bash
python3 sams.py sample_images/ info.xml
```

#### What this step automatically does on your computer:
1. Creates the database file `database/attendance.db`.
2. Creates the database tables (`students`, `sessions`, `attendance`, `signature_templates`).
3. Syncs student roster information from `info.xml` into SQLite.
4. Processes all signing sheet photos in `sample_images/` and populates attendance records.

#### Verify SQLite Records (Optional):
You can inspect the database records in your terminal by running:

```bash
sqlite3 database/attendance.db ".header on" ".mode column" "SELECT attendance_id, session_id, student_index, status, round(ink_density, 4) as ink_density FROM attendance LIMIT 12;"
```

---

### Step 4: Run the Application

You can run the project using **Web Dashboard** mode or **CLI Terminal** mode.

#### Option A: Run the Web Dashboard (Recommended)

Launch the web application by running:

```bash
python3 app.py
```

- This starts the local server and **automatically opens your web browser** to `http://localhost:5001`.
- **Tab 1 (Sheet Processing)**: Select or upload signing sheet photos to visualize the 5-step OpenCV image processing pipeline.
- **Tab 2 (Attendance Analytics)**: View interactive attendance charts, KPI summary cards, and download CSV reports (`attendance_report.csv`).
- **Tab 3 (Signature Verification)**: Run dynamic signature fraud detection and view SSIM & SIFT verification reports.

#### Option B: Run CLI Batch Processing

To process all signing sheets in batch mode via terminal:

```bash
python3 sams.py sample_images/ info.xml
```

#### Option C: Run Signature Fraud Verification (CLI)

To verify signatures for a specific student via terminal:

```bash
python3 investigate.py 10000409
```

---

## 🌟 System Features & Architecture Overview

1. **XML Roster Parsing (`info.xml`)**: Automatically extracts student metadata into SQLite.
2. **5-Step OpenCV Image Processing Pipeline**:
   - **Step 1: Original Image Loading** – Reads input signing sheet photos.
   - **Step 2: Grayscale Filtering** – Removes chromatic noise.
   - **Step 3: Adaptive Otsu Binarization** – Segments pen ink strokes from paper background.
   - **Step 4: Morphological Table & Grid ROI Detection** – Detects table lines and crops signature cells.
   - **Step 5: Ink Area Density Analysis** – Calculates ink percentage density to classify attendance as `PRESENT` or `ABSENT`.
3. **Computer Vision Signature Verification**:
   - Dynamic mathematical feature extraction using **Structural Similarity Index (SSIM)**, **SIFT Keypoint Matching**, and **2D Spatial Cross-Correlation**.
   - Classifies signatures into **`AUTHENTIC MATCH`** or 🚨 **`SUSPECTED MISMATCH / FRAUD`**.
4. **Administrative CSV Export**: Generate and download formatted `attendance_report.csv` files with one click.

---

## 📁 Project Directory Structure

```text
CGV/
├── app.py                      # Main dual launcher (Web server + browser auto-launch)
├── sams.py                     # CLI batch processing script
├── investigate.py              # CLI signature verification & fraud analysis tool
├── web_server.py               # REST API HTTP web server backend
├── info.xml                    # Student roster XML configuration file
├── modules/
│   ├── config.py               # Path definitions & system thresholds
│   ├── db_manager.py           # SQLite database ORM & sync functions
│   ├── image_processor.py      # 5-Step OpenCV image processing pipeline
│   ├── signature_verifier.py   # SSIM, SIFT keypoint, & fraud detection engine
│   └── visualizer.py           # Image overlay & progress visualizer
├── database/
│   └── attendance.db           # SQLite database file
├── sample_images/              # Input physical signing sheet photos
├── outputs/                    # Step-by-step OpenCV visual progress images
├── baseline_signatures/        # Cropped student signature ROI images
├── web/
│   └── index.html              # Multi-tab responsive web dashboard frontend
└── README.md                   # System setup & execution guide
```

---

## 📄 License
This software is provided open-source under the MIT License.
