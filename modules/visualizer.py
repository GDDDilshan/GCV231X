import matplotlib
matplotlib.use('Agg') # Non-interactive backend for server/script rendering
import matplotlib.pyplot as plt
import os
from modules.config import OUTPUTS_DIR

class AttendanceVisualizer:
    def __init__(self, student_info, attendance_history):
        self.student_info = student_info
        self.attendance_history = attendance_history

    def generate_dashboard(self, save_path=None):
        """
        Generate complete graphical attendance report for student.
        Returns saved image path.
        """
        if not self.attendance_history:
            print(f"[Warning] No attendance history found for student {self.student_info['student_index']}")
            return None

        student_name = self.student_info.get('name', 'Unknown')
        student_idx = self.student_info.get('student_index', 'N/A')

        # Compute Metrics
        total_sessions = len(self.attendance_history)
        present_count = sum(1 for item in self.attendance_history if item['status'] == 'PRESENT')
        absent_count = total_sessions - present_count
        attendance_rate = (present_count / total_sessions * 100) if total_sessions > 0 else 0

        # Set Up Figure with Dark/Modern Professional Theme
        fig = plt.figure(figsize=(12, 7), facecolor='#1e1e2e')
        fig.suptitle(f"Student Attendance Analytics Report\n{student_name} ({student_idx})", 
                     fontsize=16, fontweight='bold', color='#ffffff', y=0.96)

        # Plot 1: Attendance Ratio Donut Chart (Left)
        ax1 = fig.add_subplot(1, 2, 1)
        ax1.set_facecolor('#1e1e2e')
        labels = ['Present', 'Absent']
        sizes = [present_count, absent_count]
        colors = ['#2ecc71', '#e74c3c']

        # Avoid zero division error in wedge creation
        if sum(sizes) == 0:
            sizes = [1, 0]

        wedges, texts, autotexts = ax1.pie(
            sizes, labels=labels, colors=colors, autopct='%1.1f%%',
            startangle=140, pctdistance=0.75,
            textprops=dict(color='#ffffff', fontweight='bold', fontsize=11),
            wedgeprops=dict(width=0.4, edgecolor='#1e1e2e', linewidth=3)
        )
        ax1.set_title(f"Overall Rate: {attendance_rate:.1f}%\n({present_count}/{total_sessions} Attended)", 
                      color='#ffffff', fontsize=13, pad=15)

        # Plot 2: Session-by-Session Timeline Bar Chart (Right)
        ax2 = fig.add_subplot(1, 2, 2)
        ax2.set_facecolor('#181825')

        dates = [item['date'] for item in self.attendance_history]
        statuses = [item['status'] for item in self.attendance_history]
        bar_colors = ['#2ecc71' if s == 'PRESENT' else '#e74c3c' for s in statuses]
        y_values = [1 if s == 'PRESENT' else 0.2 for s in statuses]

        bars = ax2.bar(range(len(dates)), y_values, color=bar_colors, width=0.45, edgecolor='#ffffff', linewidth=1)
        ax2.set_xticks(range(len(dates)))
        ax2.set_xticklabels(dates, rotation=30, ha='right', color='#ffffff', fontsize=10)
        ax2.set_yticks([0.0, 1.0])
        ax2.set_yticklabels(['ABSENT', 'PRESENT'], color='#ffffff', fontsize=11, fontweight='bold')
        ax2.set_ylim(0, 1.25)
        ax2.set_title("Session Attendance Timeline", color='#ffffff', fontsize=13, pad=15)
        ax2.grid(axis='y', linestyle='--', alpha=0.25, color='#888888')

        # Add bar value annotations
        for bar, status in zip(bars, statuses):
            h = bar.get_height()
            color = '#2ecc71' if status == 'PRESENT' else '#e74c3c'
            ax2.text(bar.get_x() + bar.get_width()/2., h + 0.04, status,
                     ha='center', va='bottom', color=color, fontsize=9, fontweight='bold')


        plt.tight_layout(rect=[0, 0.03, 1, 0.90])

        if save_path is None:
            save_path = os.path.join(OUTPUTS_DIR, f"attendance_viz_{student_idx}.png")

        fig.savefig(save_path, facecolor=fig.get_facecolor(), dpi=150)
        plt.close(fig)
        return save_path
