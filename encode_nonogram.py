from enum import Enum

from ortools.sat.python import cp_model


class LineKind(Enum):
    ROW = "row"
    COL = "col"


class BlockEncoder:
    def __init__(self, width, height):
        self.model = cp_model.CpModel()
        self.width = width
        self.height = height
        self.vars = []

    def encode(self, rows, cols):
        # encoding system from Arslani's thesis https://ai.dmi.unibas.ch/papers/theses/arslani-bachelor-25.pdf
        row_cells = {}
        col_cells = {}
        for i, line in enumerate(rows):
            coverage = self.add_line_to_model(line, i, LineKind.ROW, self.width)
            for cell, line_vars in coverage.items():
                if cell not in row_cells:
                    row_cells[cell] = []
                row_cells[cell].extend(line_vars)
        for i, line in enumerate(cols):
            coverage = self.add_line_to_model(line, i, LineKind.COL, self.height)
            for cell, line_vars in coverage.items():
                if cell not in col_cells:
                    col_cells[cell] = []
                col_cells[cell].extend(line_vars)
        self.row_cells = row_cells
        self.add_cell_consistency(row_cells, col_cells)

    def solve(self):
        solver = cp_model.CpSolver()
        status = solver.solve(self.model)
        print(f"Status: {solver.status_name(status)}")
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            for r in range(self.height):
                row = ""
                for c in range(self.width):
                    cell_vars = self.row_cells.get((r, c), [])
                    filled = any(solver.boolean_value(v) for v in cell_vars)
                    row += "#" if filled else "."
                print(row)

    @staticmethod
    def get_possible_starts(line, n):
        left = 0
        right = n - sum(line) - len(line)
        locs = {}
        for i, count in enumerate(line):
            right += count + 1
            starts = []
            for j in range(left, right - count + 1):
                starts.append(j)
            locs[i] = starts
            left += count + 1
        return locs

    @staticmethod
    def get_block_name(
        kind: LineKind, index: int, block_num: int, block_start: int
    ) -> str:
        return f"{kind.value}_{index}_block_{block_num}_{block_start}"

    def add_line_to_model(
        self, line: list[int], line_num: int, line_kind: LineKind, n: int
    ) -> dict:
        starts = self.get_possible_starts(line, n)
        cell_coverage = {}
        prev_starts = {}
        for block_num, block_starts in starts.items():
            size = line[block_num]
            block_terms = []
            block_terms_by_start = {}
            for start in block_starts:
                var_name = self.get_block_name(line_kind, line_num, block_num, start)
                block_terms.append(self.model.new_bool_var(var_name))
                block_terms_by_start[start] = block_terms[-1]
                self.vars.append(block_terms[-1])
                for i in range(size):
                    cell = i + start
                    global_coords = (
                        (line_num, cell)
                        if line_kind is LineKind.ROW
                        else (cell, line_num)
                    )
                    if global_coords not in cell_coverage:
                        cell_coverage[global_coords] = []
                    cell_coverage[global_coords].append(block_terms[-1])
            self.model.add_exactly_one(block_terms)
            # whitespace separation
            if prev_starts:
                for left_idx, left_var in prev_starts.items():
                    right_idx = left_idx + 1
                    right_var = block_terms_by_start.get(right_idx)
                    if right_var is not None:
                        self.model.add_bool_or(~left_var, ~right_var)
            prev_starts = block_terms_by_start
        return cell_coverage

    def add_cell_consistency(self, row_cells: dict[list], col_cells: dict[list]):
        for cell, row_vars in row_cells.items():
            col_vars = col_cells.get(cell)
            if col_vars is None:
                continue
            for rv in row_vars:
                self.model.add_bool_or(~rv, *col_vars)
            for cv in col_vars:
                self.model.add_bool_or(~cv, *row_vars)


if __name__ == "__main__":
    rows = [[1, 1], [0], [1, 1], [3]]
    cols = [[1], [1, 1], [1], [1, 1], [1]]
    rows = [
        [4],
        [1, 1, 2],
        [1, 4, 1],
        [1, 1, 1, 1],
        [1, 1, 2, 3],
        [1, 1, 1, 1],
        [1, 2, 3],
        [2, 3, 1],
        [3, 2],
        [1],
    ]
    cols = [
        [4],
        [2, 1],
        [1, 3, 1],
        [1, 2, 1, 1],
        [1, 1, 1, 2],
        [3, 2, 1],
        [1, 1, 2],
        [1, 2, 1, 2],
        [1, 1, 3],
        [4],
    ]

    # rows = [[1], [2], [1]]
    # cols = [[2], [1], [1]]

    encoder = BlockEncoder(len(cols), len(rows))
    encoder.encode(rows, cols)
    encoder.solve()
