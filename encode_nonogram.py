from ortools.sat.python import cp_model


class BlockEncoder:
    def __init__(self, width, height):
        self.model = cp_model.CpModel()
        self.width = width
        self.height = height

    def encode(self, rows, cols):
        row_cells = {}
        col_cells = {}
        for i, line in enumerate(rows):
            coverage = self.add_line_to_model(line, i, "row", self.width)
            for cell, line_vars in coverage.items():
                if cell not in row_cells:
                    row_cells[cell] = []
                row_cells[cell].extend(line_vars)
        for i, line in enumerate(cols):
            coverage = self.add_line_to_model(line, i, "col", self.width)
            for cell, line_vars in coverage.items():
                if cell not in col_cells:
                    col_cells[cell] = []
                col_cells[cell].extend(line_vars)
        self.add_cell_consistency(row_cells, col_cells)

    @staticmethod
    def get_possible_starts(line, n):
        left = 0
        right = n - sum(line) - len(line)
        locs = {}
        for i, count in enumerate(line):
            right += count + 1
            print(left, right)
            starts = []
            for j in range(left, right):
                starts.append(j)
            locs[i] = starts
            left += count + 1
        return locs

    @staticmethod
    def get_block_name(kind: str, index: int, block_num: int, block_start: int) -> str:
        return f"{kind}_{index}_block_{block_num}_{block_start}"

    def add_line_to_model(
        self, line: list[int], line_num: int, line_kind: str, n: int
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
                for i in range(size):
                    cell = i + start
                    if cell not in cell_coverage:
                        cell_coverage[cell] = []
                    cell_coverage[cell].append(block_terms[-1])
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
        # FIXME: so this is the point where i realized i'm not properly handling the 2d indexing



if __name__ == "__main__":
    rows = [[1, 1], [0], [1, 1], [3]]
    cols = [[1], [1, 1], [1], [1, 1], [1]]

    encoder = BlockEncoder(5, 4)

    print(encoder.get_possible_starts([2, 1], 3))
