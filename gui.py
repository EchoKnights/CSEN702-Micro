import sys
import os
import numpy as _np
import tempfile

import context
import cycles
import fetch
import execute
import CDB
import cache

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QTabWidget, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QFileDialog, QSpinBox,
    QFormLayout, QMessageBox, QAbstractItemView, QCheckBox,
    QComboBox, QPlainTextEdit, QDialog, QDialogButtonBox
)

def reset_instruction_stats():
    context.instruction_stats = []
    for idx, inst in enumerate(context.instruction_memory):
        context.instruction_stats.append({
            "index": idx,
            "text": inst,
            "issue": None,
            "exec_start": None,
            "exec_cycles": 0,
            "exec_end": None,
            "writeback": None,
        })


def update_instruction_stat(inst_index, field, value):
    """Update a specific field for an instruction stat."""
    for inst in context.instruction_stats:
        if inst["index"] == inst_index:
            inst[field] = value
            break

def update_instruction_issue(inst_index, cycle):
    """Called when instruction is issued to a reservation station."""
    update_instruction_stat(inst_index, "issue", cycle)

def update_instruction_exec_start(inst_index, cycle):
    """Called when instruction starts executing."""
    update_instruction_stat(inst_index, "exec_start", cycle)

def update_instruction_exec_end(inst_index, cycle):
    """Called when instruction finishes executing."""
    update_instruction_stat(inst_index, "exec_end", cycle)

def update_instruction_writeback(inst_index, cycle):
    """Called when instruction writes back."""
    update_instruction_stat(inst_index, "writeback", cycle)


def simulation_done():
    no_more_insts = context.pc >= len(context.instruction_memory)

    all_adders_free = all(not st["busy"] for st in context.fp_adder_reservation_stations.values())
    all_mults_free = all(not st["busy"] for st in context.fp_mult_reservation_stations.values())
    all_fp_adders_free = all(not st["busy"] for st in context.adder_reservation_stations.values())
    all_fp_mults_free = all(not st["busy"] for st in context.mult_reservation_stations.values())
    all_loads_free = all(not st["busy"] for st in context.load_buffers.values())
    all_stores_free = all(not st["busy"] for st in context.store_buffers.values())

    queues_empty = (not cycles.TBE_Queue and not cycles.Execute_Queue and
                    not cycles.Ready_Queue and not cycles.Waiting_Queue and
                    not cycles.Result_Queue and not CDB.CDB_Queue)

    return (no_more_insts and all_adders_free and all_fp_adders_free and
            all_mults_free and all_fp_mults_free and all_loads_free and
            all_stores_free and queues_empty)

class InstructionBuilderDialog(QDialog):
    def __init__(self, parent=None, existing_instructions=None):
        super().__init__(parent)
        self.setWindowTitle("Custom Instruction Builder")
        self.resize(600, 400)

        self.custom_instructions = list(existing_instructions or [])

        layout = QVBoxLayout(self)

        # --- Builder controls ---
        form = QFormLayout()
        layout.addLayout(form)

        # Opcode
        self.cb_opcode = QComboBox()
        self.cb_opcode.addItems([
            "DADDI", "DSUBI",
            "ADD.D", "ADD.S", "SUB.D", "SUB.S",
            "MUL.D", "MUL.S", "DIV.D", "DIV.S",
            "LW", "LD", "L.S", "L.D",
            "SW", "SD", "S.S", "S.D",
            "BNE", "BEQ",
        ])
        self.cb_opcode.currentTextChanged.connect(self.on_opcode_changed)
        form.addRow("Opcode", self.cb_opcode)

        # Generic operand widgets
        self.cb_rd = QComboBox()
        self.cb_rs = QComboBox()
        self.cb_rt = QComboBox()
        self.cb_base = QComboBox()
        self.sp_imm = QSpinBox()
        self.sp_imm.setRange(-10_000, 10_000)
        self.le_branch_target = QLineEdit("0")

        def fill_int_regs(cb):
            cb.clear()
            for i in range(32):
                cb.addItem(f"R{i}")

        def fill_fp_regs(cb):
            cb.clear()
            for i in range(32):
                cb.addItem(f"F{i}")

        fill_fp_regs(self.cb_rd)
        fill_fp_regs(self.cb_rs)
        fill_fp_regs(self.cb_rt)
        fill_int_regs(self.cb_base)

        form.addRow("Dest (Fd/Rt)", self.cb_rd)
        form.addRow("Src1 (Fs/Rs)", self.cb_rs)
        form.addRow("Src2 (Ft/Rt)", self.cb_rt)
        form.addRow("Base (R)", self.cb_base)
        form.addRow("Offset / Imm", self.sp_imm)
        form.addRow("Branch target", self.le_branch_target)

        # Buttons (inside dialog)
        btn_row = QHBoxLayout()
        self.btn_add_instr = QPushButton("Add instruction")
        self.btn_clear_instr = QPushButton("Clear list")
        self.btn_add_instr.clicked.connect(self.on_add_custom_instruction)
        self.btn_clear_instr.clicked.connect(self.on_clear_custom_instructions)
        btn_row.addWidget(self.btn_add_instr)
        btn_row.addWidget(self.btn_clear_instr)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)

        # Text area showing list
        self.txt_custom_instr = QPlainTextEdit()
        self.txt_custom_instr.setReadOnly(True)
        layout.addWidget(QLabel("Current custom instruction list:"))
        layout.addWidget(self.txt_custom_instr, stretch=1)

        # Fill text area with existing list
        if self.custom_instructions:
            self.txt_custom_instr.setPlainText("\n".join(self.custom_instructions))

        # OK / Cancel
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.on_opcode_changed(self.cb_opcode.currentText())

    # ---------- dialog logic ----------

    def on_opcode_changed(self, opcode: str):
        for w in (self.cb_rd, self.cb_rs, self.cb_rt,
                  self.cb_base, self.sp_imm, self.le_branch_target):
            w.setEnabled(True)

        if opcode in {"ADD.D", "ADD.S", "SUB.D", "SUB.S",
                      "MUL.D", "MUL.S", "DIV.D", "DIV.S"}:
            self.cb_base.setEnabled(False)
            self.sp_imm.setEnabled(False)
            self.le_branch_target.setEnabled(False)

        elif opcode in {"DADDI", "DSUBI"}:
            self.cb_rt.setEnabled(False)
            self.cb_base.setEnabled(False)
            self.sp_imm.setEnabled(True)
            self.le_branch_target.setEnabled(False)

        elif opcode in {"LW", "LD", "L.S", "L.D", "SW", "SD", "S.S", "S.D"}:
            self.cb_rs.setEnabled(False)
            self.cb_rt.setEnabled(False)
            self.cb_base.setEnabled(True)
            self.sp_imm.setEnabled(True)
            self.le_branch_target.setEnabled(False)

        elif opcode in {"BNE", "BEQ"}:
            self.cb_rd.setEnabled(False)
            self.cb_base.setEnabled(False)
            self.sp_imm.setEnabled(False)
            self.le_branch_target.setEnabled(True)

    def on_add_custom_instruction(self):
        opcode = self.cb_opcode.currentText()
        imm = self.sp_imm.value()
        rd = self.cb_rd.currentText()
        rs = self.cb_rs.currentText()
        rt = self.cb_rt.currentText()
        base = self.cb_base.currentText()
        target = self.le_branch_target.text().strip()

        if opcode in {"ADD.D", "ADD.S", "SUB.D", "SUB.S",
                      "MUL.D", "MUL.S", "DIV.D", "DIV.S"}:
            line = f"{opcode} {rd}, {rs}, {rt}"
        elif opcode in {"DADDI", "DSUBI"}:
            line = f"{opcode} {rd}, {rs}, {imm}"
        elif opcode in {"LW", "LD", "L.S", "L.D",
                        "SW", "SD", "S.S", "S.D"}:
            line = f"{opcode} {rd}, {imm}({base})"
        elif opcode in {"BNE", "BEQ"}:
            line = f"{opcode} {rs}, {rt}, {target}"
        else:
            line = opcode

        self.custom_instructions.append(line)
        self.txt_custom_instr.appendPlainText(line)

    def on_clear_custom_instructions(self):
        self.custom_instructions.clear()
        self.txt_custom_instr.clear()

    def get_instructions(self):
        return self.custom_instructions

# ---------------------------
# Main Window
# ---------------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Tomasulo Simulator GUI")
        self.resize(1300, 800)

        self.sim_initialized = False

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        
        self.custom_instr_path = None
        self.custom_instructions = []

        # Top: configuration + control bar
        config_group = self.create_config_group()
        main_layout.addWidget(config_group)

        control_bar = self.create_control_bar()
        main_layout.addLayout(control_bar)

        # Middle: tabbed view
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs, stretch=1)

        # Tabs
        self.tab_instructions = self.create_instructions_tab()
        self.tab_registers = self.create_registers_tab()
        self.tab_stations = self.create_stations_tab()
        self.tab_cache = self.create_cache_tab()
        self.tab_queues = self.create_queues_tab()

        self.tabs.addTab(self.tab_instructions, "Instructions")
        self.tabs.addTab(self.tab_registers, "Registers")
        self.tabs.addTab(self.tab_stations, "Stations & Buffers")
        self.tabs.addTab(self.tab_cache, "Cache")
        self.tabs.addTab(self.tab_queues, "Queues")

        self.update_all()  # initial empty state

    # ------------- Config UI -------------

    def create_config_group(self):
        group = QGroupBox("Configuration (before Initialize)")
        layout = QGridLayout(group)

        # Left: Instruction file selection
        file_layout = QHBoxLayout()
        self.instr_path_edit = QLineEdit("instructions.txt")
        btn_browse = QPushButton("Browse…")
        btn_browse.clicked.connect(self.on_browse_file)
        file_layout.addWidget(QLabel("Instruction file:"))
        file_layout.addWidget(self.instr_path_edit, stretch=1)
        file_layout.addWidget(btn_browse)
        layout.addLayout(file_layout, 0, 0, 1, 2)

        custom_row = QHBoxLayout()
        self.chk_use_custom = QCheckBox("Use custom instruction list (if defined)")
        btn_edit_custom = QPushButton("Edit custom instructions…")
        btn_edit_custom.clicked.connect(self.on_edit_custom_instructions)
        custom_row.addWidget(self.chk_use_custom)
        custom_row.addWidget(btn_edit_custom)
        custom_row.addStretch(1)
        layout.addLayout(custom_row, 1, 0, 1, 2)
        

        # Middle: latencies
        lat_group = QGroupBox("Latencies (cycles)")
        lat_form = QFormLayout(lat_group)

        self.sp_fp_add = QSpinBox()
        self.sp_fp_add.setRange(1, 1000)
        self.sp_fp_add.setValue(context.fp_add_latency)

        self.sp_fp_mul = QSpinBox()
        self.sp_fp_mul.setRange(1, 1000)
        self.sp_fp_mul.setValue(context.fp_mult_latency)

        self.sp_fp_div = QSpinBox()
        self.sp_fp_div.setRange(1, 1000)
        self.sp_fp_div.setValue(context.fp_div_latency)

        self.sp_load_lat = QSpinBox()
        self.sp_load_lat.setRange(1, 1000)
        self.sp_load_lat.setValue(context.load_latency)

        self.sp_store_lat = QSpinBox()
        self.sp_store_lat.setRange(1, 1000)
        self.sp_store_lat.setValue(context.store_latency)

        self.sp_add_lat = QSpinBox()
        self.sp_add_lat.setRange(1, 1000)
        self.sp_add_lat.setValue(context.add_latency)

        lat_form.addRow("FP ADD latency", self.sp_fp_add)
        lat_form.addRow("FP MUL latency", self.sp_fp_mul)
        lat_form.addRow("FP DIV latency", self.sp_fp_div)
        lat_form.addRow("LOAD latency", self.sp_load_lat)
        lat_form.addRow("STORE latency", self.sp_store_lat)
        lat_form.addRow("INT ADD (DADDI/DSUBI)", self.sp_add_lat)

        layout.addWidget(lat_group, 2, 0)

        # Right: cache / memory
        cache_group = QGroupBox("Stations / Cache / Memory")
        cache_form = QFormLayout(cache_group)

        self.sp_data_mem_size = QSpinBox()
        self.sp_data_mem_size.setRange(64, 1_000_000)
        self.sp_data_mem_size.setValue(context.data_memory_size)

        self.sp_cache_size = QSpinBox()
        self.sp_cache_size.setRange(8, 65536)
        self.sp_cache_size.setValue(context.cache_size)

        self.sp_block_size = QSpinBox()
        self.sp_block_size.setRange(1, 1024)
        self.sp_block_size.setValue(context.block_size)

        self.sp_cache_hit = QSpinBox()
        self.sp_cache_hit.setRange(1, 1000)
        self.sp_cache_hit.setValue(context.cache_hit_latency)

        self.sp_cache_miss = QSpinBox()
        self.sp_cache_miss.setRange(1, 1000)
        self.sp_cache_miss.setValue(context.cache_miss_penalty)
        
        self.sp_general_registers = QSpinBox()
        self.sp_general_registers.setRange(1, 100)
        self.sp_general_registers.setValue(context.g)
        
        self.sp_floating_point_registers = QSpinBox()
        self.sp_floating_point_registers.setRange(1, 100)
        self.sp_floating_point_registers.setValue(context.f)
        
        self.sp_load_buffers = QSpinBox()
        self.sp_load_buffers.setRange(1, 100)
        self.sp_load_buffers.setValue(context.l)
        
        self.sp_store_buffers = QSpinBox()
        self.sp_store_buffers.setRange(1, 100)
        self.sp_store_buffers.setValue(context.s)
        
        self.sp_adder_stations = QSpinBox()
        self.sp_adder_stations.setRange(1, 100)
        self.sp_adder_stations.setValue(context.a)
        
        self.sp_mult_stations = QSpinBox()
        self.sp_mult_stations.setRange(1, 100)
        self.sp_mult_stations.setValue(context.m)
        
        self.sp_fp_adder_stations = QSpinBox()
        self.sp_fp_adder_stations.setRange(1, 100)
        self.sp_fp_adder_stations.setValue(context.fa)
        
        self.sp_fp_mult_stations = QSpinBox()
        self.sp_fp_mult_stations.setRange(1, 100)
        self.sp_fp_mult_stations.setValue(context.fm)
        
        cache_form.addRow("Load buffers", self.sp_load_buffers)
        cache_form.addRow("Store buffers", self.sp_store_buffers)
        cache_form.addRow("Adder stations", self.sp_adder_stations)
        cache_form.addRow("Multiplier stations", self.sp_mult_stations)
        cache_form.addRow("FP Adder stations", self.sp_fp_adder_stations)
        cache_form.addRow("FP Multiplier stations", self.sp_fp_mult_stations)

        cache_form.addRow("Data memory size (bytes)", self.sp_data_mem_size)
        cache_form.addRow("Cache size (bytes)", self.sp_cache_size)
        cache_form.addRow("Block size (bytes)", self.sp_block_size)
        cache_form.addRow("Cache hit latency", self.sp_cache_hit)
        cache_form.addRow("Cache miss penalty", self.sp_cache_miss)

        layout.addWidget(cache_group, 2, 1)

        # Bottom: initialize button
        self.btn_init = QPushButton("Initialize Simulator")
        self.btn_init.clicked.connect(self.on_initialize_clicked)
        layout.addWidget(self.btn_init, 3, 0, 1, 2)

        return group

    def on_edit_custom_instructions(self):
        dlg = InstructionBuilderDialog(self, self.custom_instructions)
        if dlg.exec() == QDialog.Accepted:
            self.custom_instructions = dlg.get_instructions()

    def on_browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select instruction file", os.getcwd(), "Text files (*.txt);;All files (*)"
        )
        if path:
            self.instr_path_edit.setText(path)
            
    def get_instruction_file_path(self) -> str:
        # Custom list mode
        if self.chk_use_custom.isChecked() and self.custom_instructions:
            # Create / overwrite temp file
            tmp_dir = tempfile.gettempdir()
            self.custom_instr_path = os.path.join(
                tmp_dir, "tomasulo_custom_instructions.txt"
            )
            with open(self.custom_instr_path, "w", encoding="utf-8") as f:
                f.write("\n".join(self.custom_instructions) + "\n")
            return self.custom_instr_path

        # Normal file mode
        return self.instr_path_edit.text().strip()



    # ------------- Control bar -------------

    def create_control_bar(self):
        layout = QHBoxLayout()

        self.lbl_cycle = QLabel("Cycle: 0")
        self.lbl_pc = QLabel("PC: 0")
        self.lbl_stall = QLabel("STALL: False")

        layout.addWidget(self.lbl_cycle)
        layout.addSpacing(20)
        layout.addWidget(self.lbl_pc)
        layout.addSpacing(20)
        layout.addWidget(self.lbl_stall)
        layout.addStretch()

        self.btn_next = QPushButton("Next Cycle")
        self.btn_next.clicked.connect(self.on_next_cycle)
        self.btn_next.setEnabled(False)
        layout.addWidget(self.btn_next)

        self.btn_reset = QPushButton("Reset")
        self.btn_reset.clicked.connect(self.on_reset_clicked)
        self.btn_reset.setEnabled(False)
        layout.addWidget(self.btn_reset)

        return layout

    # ------------- Tabs -------------

    # Instructions tab

    def create_instructions_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Instruction table
        self.tbl_instructions = QTableWidget()
        self.tbl_instructions.setColumnCount(7)
        self.tbl_instructions.setHorizontalHeaderLabels([
            "#", "Instruction",
            "Issue",
            "Exec Start",
            "Exec Cycles",
            "Exec End",
            "Writeback",
        ])
        self.tbl_instructions.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_instructions.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.tbl_instructions)

        return widget

    # Registers tab

    def create_registers_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        tabs = QTabWidget()
        layout.addWidget(tabs)

        # General registers
        self.tbl_gpr = QTableWidget()
        self.tbl_gpr.setColumnCount(3)
        self.tbl_gpr.setHorizontalHeaderLabels(["Reg", "Value", "Qi"])
        self.tbl_gpr.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.SelectedClicked)
        self.tbl_gpr.horizontalHeader().setStretchLastSection(True)
        self.tbl_gpr.itemChanged.connect(lambda item: self.on_register_value_changed(item, "general"))

        self.tbl_fpr = QTableWidget()
        self.tbl_fpr.setColumnCount(3)
        self.tbl_fpr.setHorizontalHeaderLabels(["Reg", "Value", "Qi"])
        self.tbl_fpr.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.SelectedClicked)
        self.tbl_fpr.horizontalHeader().setStretchLastSection(True)
        self.tbl_fpr.itemChanged.connect(lambda item: self.on_register_value_changed(item, "fp"))

        tabs.addTab(self.tbl_gpr, "General Registers (R)")
        tabs.addTab(self.tbl_fpr, "FP Registers (F)")

        return widget

    # Stations & buffers tab

    def create_stations_tab(self):
        widget = QWidget()
        layout = QGridLayout(widget)

        # Integer adder RS
        self.tbl_rs_int_add = self._create_rs_table(
            ["Name", "Busy", "Op", "Vj", "Vk", "Qj", "Qk", "A", "Time"]
        )
        grp_int_add = QGroupBox("Integer Adder Reservation Stations (A1...)")
        g_layout = QVBoxLayout(grp_int_add)
        g_layout.addWidget(self.tbl_rs_int_add)
        layout.addWidget(grp_int_add, 0, 0)

        # Integer mult RS
        self.tbl_rs_int_mul = self._create_rs_table(
            ["Name", "Busy", "Op", "Vj", "Vk", "Qj", "Qk", "A", "Time"]
        )
        grp_int_mul = QGroupBox("Integer Mult Reservation Stations (M1...)")
        gm_layout = QVBoxLayout(grp_int_mul)
        gm_layout.addWidget(self.tbl_rs_int_mul)
        layout.addWidget(grp_int_mul, 0, 1)

        # FP add RS
        self.tbl_rs_fp_add = self._create_rs_table(
            ["Name", "Busy", "Op", "Vj", "Vk", "Qj", "Qk", "A", "Time"]
        )
        grp_fp_add = QGroupBox("FP Adder Reservation Stations (FA1...)")
        fa_layout = QVBoxLayout(grp_fp_add)
        fa_layout.addWidget(self.tbl_rs_fp_add)
        layout.addWidget(grp_fp_add, 1, 0)

        # FP mult RS
        self.tbl_rs_fp_mul = self._create_rs_table(
            ["Name", "Busy", "Op", "Vj", "Vk", "Qj", "Qk", "A", "Time"]
        )
        grp_fp_mul = QGroupBox("FP Mult Reservation Stations (FM1...)")
        fm_layout = QVBoxLayout(grp_fp_mul)
        fm_layout.addWidget(self.tbl_rs_fp_mul)
        layout.addWidget(grp_fp_mul, 1, 1)

        # Load buffers
        self.tbl_load_buf = self._create_rs_table(
            ["Name", "Busy", "Op", "Vj", "Vk", "Qj", "Qk", "A", "Time"]
        )
        grp_load = QGroupBox("Load Buffers (L1...)")
        l_layout = QVBoxLayout(grp_load)
        l_layout.addWidget(self.tbl_load_buf)
        layout.addWidget(grp_load, 2, 0)

        # Store buffers
        self.tbl_store_buf = self._create_rs_table(
            ["Name", "Busy", "Op", "Vj", "Vk", "Qj", "Qk", "A", "Time"]
        )
        grp_store = QGroupBox("Store Buffers (S1...)")
        s_layout = QVBoxLayout(grp_store)
        s_layout.addWidget(self.tbl_store_buf)
        layout.addWidget(grp_store, 2, 1)

        return widget

    def _create_rs_table(self, headers):
        tbl = QTableWidget()
        tbl.setColumnCount(len(headers))
        tbl.setHorizontalHeaderLabels(headers)
        tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tbl.horizontalHeader().setStretchLastSection(True)
        return tbl

    # Cache tab

    def create_cache_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.tbl_cache = QTableWidget()
        self.tbl_cache.setColumnCount(4)
        self.tbl_cache.setHorizontalHeaderLabels(["Set", "Valid", "Tag", "Data (block)"])
        self.tbl_cache.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_cache.horizontalHeader().setStretchLastSection(True)

        layout.addWidget(self.tbl_cache)

        return widget

    # Queues tab

    def create_queues_tab(self):
        widget = QWidget()
        layout = QGridLayout(widget)

        self.tbl_tbe = self._create_queue_table()
        self.tbl_exec = self._create_queue_table()
        self.tbl_ready = self._create_queue_table()
        self.tbl_waiting = self._create_queue_table()
        self.tbl_result = self._create_queue_table()
        self.tbl_clear = self._create_queue_table()

        layout.addWidget(self._wrap_queue_group("To-Be-Executed Queue", self.tbl_tbe), 0, 0)
        layout.addWidget(self._wrap_queue_group("Execute Queue", self.tbl_exec), 0, 1)
        layout.addWidget(self._wrap_queue_group("Ready Queue", self.tbl_ready), 1, 0)
        layout.addWidget(self._wrap_queue_group("Waiting Queue", self.tbl_waiting), 1, 1)
        layout.addWidget(self._wrap_queue_group("Result Queue", self.tbl_result), 2, 0)
        layout.addWidget(self._wrap_queue_group("Clear Queue", self.tbl_clear), 2, 1)

        # CDB info
        self.lbl_cdb = QLabel("CDB: -")
        layout.addWidget(
            self.lbl_cdb,
            3, 0, 1, 2,
            alignment=Qt.AlignmentFlag.AlignLeft
        )

        return widget

    def _create_queue_table(self):
        tbl = QTableWidget()
        tbl.setColumnCount(2)
        tbl.setHorizontalHeaderLabels(["Name", "Station Snapshot"])
        tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tbl.horizontalHeader().setStretchLastSection(True)
        return tbl

    def _wrap_queue_group(self, title, table):
        grp = QGroupBox(title)
        l = QVBoxLayout(grp)
        l.addWidget(table)
        return grp

    # ------------- Button handlers -------------

    def on_initialize_clicked(self):
        path = self.instr_path_edit.text().strip()
        if not path:
            QMessageBox.warning(self, "No file", "Please provide an instruction file path.")
            return
        if not os.path.exists(path):
            QMessageBox.warning(self, "File not found", f"File not found:\n{path}")
            return

        # Apply config to context BEFORE initializing
        context.fp_add_latency = self.sp_fp_add.value()
        context.fp_mult_latency = self.sp_fp_mul.value()
        context.fp_div_latency = self.sp_fp_div.value()
        context.load_latency = self.sp_load_lat.value()
        context.store_latency = self.sp_store_lat.value()
        context.add_latency = self.sp_add_lat.value()

        context.data_memory_size = self.sp_data_mem_size.value()
        context.cache_size = self.sp_cache_size.value()
        context.block_size = self.sp_block_size.value()
        context.cache_hit_latency = self.sp_cache_hit.value()
        context.cache_miss_penalty = self.sp_cache_miss.value()

        context.cache_lines = context.cache_size // context.block_size
        context.address_size = _np.log2(context.data_memory_size).astype(int)
        context.index = _np.log2(context.cache_lines).astype(int)
        context.block_offset = _np.log2(context.block_size).astype(int)
        context.tag = context.address_size - (context.index + context.block_offset)


        path = self.get_instruction_file_path()
        instructions = context.open_instruction_file(path)
        context.load_instruction_memory(instructions)
        context.initialize_data_memory(
            data_memory_size=context.data_memory_size,
            cache_size=context.cache_size,
            block_size=context.block_size,
        )
        context.initialize_clock_cycle()
        context.initialize_program_counter()
        context.initialize_reservation_stations(
            g = self.sp_general_registers.value(),
            f = self.sp_floating_point_registers.value(),
            a = self.sp_adder_stations.value(),
            fa = self.sp_fp_adder_stations.value(),
            m = self.sp_mult_stations.value(),
            fm = self.sp_fp_mult_stations.value(),
            l = self.sp_load_buffers.value(),
            s = self.sp_store_buffers.value(),
        )

        # Clear queues & CDB
        cycles.TBE_Queue.clear()
        cycles.Execute_Queue.clear()
        cycles.Ready_Queue.clear()
        cycles.Waiting_Queue.clear()
        cycles.Result_Queue.clear()
        cycles.Clear_Queue.clear()
        CDB.CDB_Queue.clear()
        CDB.CDB = {}

        reset_instruction_stats()
        
        cache.preload_cache_values()
        fetch.preload_register_values()

        self.sim_initialized = True
        self.btn_next.setEnabled(True)
        self.btn_reset.setEnabled(True)

        self.update_all()

    def on_next_cycle(self):
        if not self.sim_initialized:
            QMessageBox.warning(self, "Not initialized", "Initialize the simulator first.")
            return

        # One full cycle: increment cycle, then WB, EX, Fetch (same order as simulator.py). 
        cycles.increment_cycle()
        cycles.cycle_writeback()
        cycles.cycle_execute()
        cycles.cycle_fetch()

        # (Optional) here is a good place to later update instruction_stats
        # if you add hooks into cycles/writeback.

        self.update_all()

        if simulation_done():
            self.btn_next.setEnabled(False)
            QMessageBox.information(self, "Done", "Simulation completed (pipelines empty, no more instructions).")

    def on_reset_clicked(self):
        # Clear custom list + checkbox
        self.custom_instructions.clear()
        print("Cleared custom instructions.")
        if hasattr(self, "chk_use_custom"):
            self.chk_use_custom.setChecked(False)
            print("Unchecked custom instructions checkbox.")

        # Remove temp file if it exists
        if self.custom_instr_path and os.path.exists(self.custom_instr_path):
            try:
                os.remove(self.custom_instr_path)
                print(f"Removed temporary custom instruction file: {self.custom_instr_path}")
            except OSError:
                pass
            self.custom_instr_path = None

        # Re-initialize with same config
        self.on_initialize_clicked()

    # ------------- Update UI -------------

    def update_all(self):
        self.update_top_labels()
        self.update_instruction_table()
        self.update_register_tables()
        self.update_rs_tables()
        self.update_cache_table()
        self.update_queue_tables()
        self.update_cdb_label()

    def update_top_labels(self):
        self.lbl_cycle.setText(f"Cycle: {context.clock_cycle}")
        self.lbl_pc.setText(f"PC: {context.pc}")
        self.lbl_stall.setText(f"STALL: {context.STALL}")

    def update_instruction_table(self):
        self.tbl_instructions.setRowCount(len(context.instruction_stats))
        for row, info in enumerate(context.instruction_stats):
            vals = [
                info["index"],
                info["text"],
                info["issue"],
                info["exec_start"],
                info["exec_cycles"],
                info["exec_end"],
                info["writeback"],
            ]
            for col, val in enumerate(vals):
                text = "-" if val is None else str(val)
                self.tbl_instructions.setItem(row, col, QTableWidgetItem(text))
        self.tbl_instructions.resizeColumnsToContents()

    def update_register_tables(self):
        # Temporarily disconnect signals to avoid triggering itemChanged during update
        try:
            self.tbl_gpr.itemChanged.disconnect()
            self.tbl_fpr.itemChanged.disconnect()
        except:
            pass
        
        # General registers
        gregs = context.general_registers
        self.tbl_gpr.setRowCount(len(gregs))
        for row, (name, reg) in enumerate(sorted(gregs.items())):
            # Column 0: Reg name (read-only)
            item_name = QTableWidgetItem(name)
            item_name.setFlags(item_name.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tbl_gpr.setItem(row, 0, item_name)
            
            # Column 1: Value (editable)
            item_value = QTableWidgetItem(str(reg["Value"]))
            self.tbl_gpr.setItem(row, 1, item_value)
            
            # Column 2: Qi (read-only)
            item_qi = QTableWidgetItem(str(reg["Qi"]))
            item_qi.setFlags(item_qi.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tbl_gpr.setItem(row, 2, item_qi)
        self.tbl_gpr.resizeColumnsToContents()

        # FP registers
        fregs = context.floating_point_registers
        self.tbl_fpr.setRowCount(len(fregs))
        for row, (name, reg) in enumerate(sorted(fregs.items())):
            # Column 0: Reg name (read-only)
            item_name = QTableWidgetItem(name)
            item_name.setFlags(item_name.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tbl_fpr.setItem(row, 0, item_name)
            
            # Column 1: Value (editable)
            item_value = QTableWidgetItem(str(reg["Value"]))
            self.tbl_fpr.setItem(row, 1, item_value)
            
            # Column 2: Qi (read-only)
            item_qi = QTableWidgetItem(str(reg["Qi"]))
            item_qi.setFlags(item_qi.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tbl_fpr.setItem(row, 2, item_qi)
        self.tbl_fpr.resizeColumnsToContents()
        
        # Reconnect signals
        self.tbl_gpr.itemChanged.connect(lambda item: self.on_register_value_changed(item, "general"))
        self.tbl_fpr.itemChanged.connect(lambda item: self.on_register_value_changed(item, "fp"))

    def on_register_value_changed(self, item, reg_type):
        """Handle when user edits a register value."""
        if item.column() != 1:  # Only column 1 (Value) should be editable
            return
        
        row = item.row()
        new_value_str = item.text()
        
        try:
            # Try to convert to appropriate numeric type
            if '.' in new_value_str:
                new_value = float(new_value_str)
            else:
                new_value = int(new_value_str)
            
            # Get register name from column 0
            if reg_type == "general":
                reg_name = self.tbl_gpr.item(row, 0).text()
                context.general_registers[reg_name]["Value"] = new_value
            else:  # fp
                reg_name = self.tbl_fpr.item(row, 0).text()
                context.floating_point_registers[reg_name]["Value"] = new_value
                
        except ValueError:
            QMessageBox.warning(self, "Invalid Value", f"'{new_value_str}' is not a valid numeric value.")
            # Restore original value
            self.update_register_tables()

    def update_rs_tables(self):
        # Helper to fill from dict[name -> station]
        def fill_rs_table(table, stations_dict):
            items = sorted(stations_dict.items())
            table.setRowCount(len(items))
            for row, (name, st) in enumerate(items):
                vals = [
                    name,
                    "1" if st["busy"] else "0",
                    str(st["op"]),
                    str(st["Vj"]),
                    str(st["Vk"]),
                    str(st["Qj"]),
                    str(st["Qk"]),
                    str(st["A"]),
                    str(st["time"]),
                ]
                for col, v in enumerate(vals):
                    table.setItem(row, col, QTableWidgetItem(v))
            table.resizeColumnsToContents()

        fill_rs_table(self.tbl_rs_int_add, context.adder_reservation_stations)
        fill_rs_table(self.tbl_rs_int_mul, context.mult_reservation_stations)
        fill_rs_table(self.tbl_rs_fp_add, context.fp_adder_reservation_stations)
        fill_rs_table(self.tbl_rs_fp_mul, context.fp_mult_reservation_stations)
        fill_rs_table(self.tbl_load_buf, context.load_buffers)
        fill_rs_table(self.tbl_store_buf, context.store_buffers)

    def update_cache_table(self):
        # context.cache is a dict[index -> {Set, valid, tag, data}] 
        cache_dict = context.cache
        items = sorted(cache_dict.items())
        self.tbl_cache.setRowCount(len(items))
        for row, (idx, line) in enumerate(items):
            set_id = line.get("Set", idx)
            valid = line.get("valid")
            tag = line.get("tag")
            data = line.get("data")

            # data is now a list of byte strings (8-bit binary strings)
            if isinstance(data, list):
                if len(data) > 0:
                    # Show first few bytes, or all if small
                    if len(data) <= 8:
                        data_str = ", ".join(data)
                    else:
                        data_str = ", ".join(data[:8]) + f" ... ({len(data)} bytes total)"
                else:
                    data_str = "(empty)"
            elif data:
                data_str = str(data)
            else:
                data_str = "(empty)"

            vals = [set_id, valid, tag if tag else "-", data_str]
            for col, v in enumerate(vals):
                self.tbl_cache.setItem(row, col, QTableWidgetItem(str(v)))
        self.tbl_cache.resizeColumnsToContents()

    def update_queue_tables(self):
        def fill_queue_table(table, queue):
            table.setRowCount(len(queue))
            for row, (name, st) in enumerate(queue):
                table.setItem(row, 0, QTableWidgetItem(name))
                # Provide a compact snapshot of the station/buffer
                snap = f"busy={st['busy']} op={st['op']} time={st['time']} Vj={st['Vj']} Vk={st['Vk']} Qj={st['Qj']} Qk={st['Qk']} A={st['A']}"
                table.setItem(row, 1, QTableWidgetItem(snap))
            table.resizeColumnsToContents()

        fill_queue_table(self.tbl_tbe, cycles.TBE_Queue)
        fill_queue_table(self.tbl_exec, cycles.Execute_Queue)
        fill_queue_table(self.tbl_ready, cycles.Ready_Queue)
        fill_queue_table(self.tbl_waiting, cycles.Waiting_Queue)
        fill_queue_table(self.tbl_result, cycles.Result_Queue)
        fill_queue_table(self.tbl_clear, cycles.Clear_Queue)

    def update_cdb_label(self):
        if not CDB.CDB:
            self.lbl_cdb.setText("CDB: -")
        else:
            tag = CDB.CDB.get("tag")
            val = CDB.CDB.get("value")
            self.lbl_cdb.setText(f"CDB: tag={tag}, value={val}")


# ---------------------------
# Entry point
# ---------------------------

def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
