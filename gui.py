import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QTabWidget, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QFileDialog, QSpinBox,
    QFormLayout, QMessageBox, QAbstractItemView   # <-- add this
)

from PySide6.QtCore import Qt

import context
import cycles
import fetch
import execute
import CDB
import cache

# ---------------------------
# Simple per-instruction stats
# ---------------------------

# One entry per instruction:
# {
#   "index": int,
#   "text": str,
#   "issue": int | None,
#   "exec_start": int | None,
#   "exec_cycles": int,
#   "exec_end": int | None,
#   "writeback": int | None,
# }
instruction_stats = []


def reset_instruction_stats():
    """Create empty stats for each instruction currently in instruction_memory."""
    global instruction_stats
    instruction_stats = []
    for idx, inst in enumerate(context.instruction_memory):
        instruction_stats.append({
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
    global instruction_stats
    if 0 <= inst_index < len(instruction_stats):
        instruction_stats[inst_index][field] = value

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


# ---------------------------
# Done-condition (copied from simulator.py)
# ---------------------------

def simulation_done():
    """
    Same logic as simulator.done(), but kept local so we don't import simulator
    (it has a while True loop). :contentReference[oaicite:8]{index=8}
    """
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

        layout.addWidget(lat_group, 1, 0)

        # Right: cache / memory
        cache_group = QGroupBox("Cache / Memory")
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

        cache_form.addRow("Data memory size (bytes)", self.sp_data_mem_size)
        cache_form.addRow("Cache size (bytes)", self.sp_cache_size)
        cache_form.addRow("Block size (bytes)", self.sp_block_size)
        cache_form.addRow("Cache hit latency", self.sp_cache_hit)
        cache_form.addRow("Cache miss penalty", self.sp_cache_miss)

        layout.addWidget(cache_group, 1, 1)

        # Bottom: initialize button
        self.btn_init = QPushButton("Initialize Simulator")
        self.btn_init.clicked.connect(self.on_initialize_clicked)
        layout.addWidget(self.btn_init, 2, 0, 1, 2)

        return group

    def on_browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select instruction file", os.getcwd(), "Text files (*.txt);;All files (*)"
        )
        if path:
            self.instr_path_edit.setText(path)

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
        self.tbl_gpr.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_gpr.horizontalHeader().setStretchLastSection(True)

        self.tbl_fpr = QTableWidget()
        self.tbl_fpr.setColumnCount(3)
        self.tbl_fpr.setHorizontalHeaderLabels(["Reg", "Value", "Qi"])
        self.tbl_fpr.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_fpr.horizontalHeader().setStretchLastSection(True)


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

        # Recompute address_size, cache_lines, etc. :contentReference[oaicite:9]{index=9}
        import numpy as _np
        context.cache_lines = context.cache_size // context.block_size
        context.address_size = _np.log2(context.data_memory_size).astype(int)
        context.index = _np.log2(context.cache_lines).astype(int)
        context.block_offset = _np.log2(context.block_size).astype(int)
        context.tag = context.address_size - (context.index + context.block_offset)

        # Manually do what initialize_simulator() does, but with our parameters. :contentReference[oaicite:10]{index=10}
        instructions = context.open_instruction_file(path)
        context.load_instruction_memory(instructions)
        context.initialize_data_memory(
            data_memory_size=context.data_memory_size,
            cache_size=context.cache_size,
            block_size=context.block_size,
        )
        context.initialize_clock_cycle()
        context.initialize_program_counter()
        context.initialize_reservation_stations()

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
        cycles.writeback_cycle()
        cycles.execute_cycle()
        cycles.fetch_cycle()

        # (Optional) here is a good place to later update instruction_stats
        # if you add hooks into cycles/writeback.

        self.update_all()

        if simulation_done():
            self.btn_next.setEnabled(False)
            QMessageBox.information(self, "Done", "Simulation completed (pipelines empty, no more instructions).")

    def on_reset_clicked(self):
        # Reset is basically "re-initialize with same config & file"
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
        global instruction_stats
        self.tbl_instructions.setRowCount(len(instruction_stats))
        for row, info in enumerate(instruction_stats):
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
        # General registers
        gregs = context.general_registers
        self.tbl_gpr.setRowCount(len(gregs))
        for row, (name, reg) in enumerate(sorted(gregs.items())):
            self.tbl_gpr.setItem(row, 0, QTableWidgetItem(name))
            self.tbl_gpr.setItem(row, 1, QTableWidgetItem(str(reg["Value"])))
            self.tbl_gpr.setItem(row, 2, QTableWidgetItem(str(reg["Qi"])))
        self.tbl_gpr.resizeColumnsToContents()

        # FP registers
        fregs = context.floating_point_registers
        self.tbl_fpr.setRowCount(len(fregs))
        for row, (name, reg) in enumerate(sorted(fregs.items())):
            self.tbl_fpr.setItem(row, 0, QTableWidgetItem(name))
            self.tbl_fpr.setItem(row, 1, QTableWidgetItem(str(reg["Value"])))
            self.tbl_fpr.setItem(row, 2, QTableWidgetItem(str(reg["Qi"])))
        self.tbl_fpr.resizeColumnsToContents()

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
