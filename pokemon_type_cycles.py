import tkinter as tk
from tkinter import ttk, messagebox
import itertools
import threading
import queue

# Define types and assign each type a unique integer ID for faster processing
TYPES = [
    'Normal', 'Fire', 'Water', 'Electric', 'Grass', 'Ice',
    'Fighting', 'Poison', 'Ground', 'Flying', 'Psychic', 'Bug',
    'Rock', 'Ghost', 'Dragon', 'Dark', 'Steel', 'Fairy'
]
TYPE_TO_ID = {type_name: idx for idx, type_name in enumerate(TYPES)}
ID_TO_TYPE = {idx: type_name for idx, type_name in enumerate(TYPES)}
NUM_TYPES = len(TYPES)

# Effectiveness multipliers as a 2D list for quick access
# Initialize all to 1.0 (neutral)
TYPE_CHART = [[1.0 for _ in range(NUM_TYPES)] for _ in range(NUM_TYPES)]

# Populate TYPE_CHART with specific effectiveness values
custom_effectiveness = {
    'Normal':    {'Rock': 0.5, 'Ghost': 0, 'Steel': 0.5},
    'Fire':      {'Fire': 0.5, 'Water': 0.5, 'Grass': 2, 'Ice': 2, 'Bug': 2,
                  'Rock': 0.5, 'Dragon': 0.5, 'Steel': 2},
    'Water':     {'Fire': 2, 'Water': 0.5, 'Grass': 0.5, 'Ground': 2, 'Rock': 2, 'Dragon': 0.5},
    'Electric':  {'Water': 2, 'Electric': 0.5, 'Grass': 0.5, 'Ground': 0,
                  'Flying': 2, 'Dragon': 0.5},
    'Grass':     {'Fire': 0.5, 'Water': 2, 'Grass': 0.5, 'Poison': 0.5,
                  'Ground': 2, 'Flying': 0.5, 'Bug': 0.5, 'Rock': 2, 'Dragon': 0.5, 'Steel': 0.5},
    'Ice':       {'Fire': 0.5, 'Water': 0.5, 'Grass': 2, 'Ice': 0.5, 'Ground': 2,
                  'Flying': 2, 'Dragon': 2, 'Steel': 0.5},
    'Fighting':  {'Normal': 2, 'Ice': 2, 'Poison': 0.5, 'Flying': 0.5, 'Psychic': 0.5,
                  'Bug': 0.5, 'Rock': 2, 'Ghost': 0, 'Dark': 2, 'Steel': 2, 'Fairy': 0.5},
    'Poison':    {'Grass': 2, 'Poison': 0.5, 'Ground': 0.5, 'Rock': 0.5, 'Ghost': 0.5,
                  'Steel': 0, 'Fairy': 2},
    'Ground':    {'Fire': 2, 'Electric': 2, 'Grass': 0.5, 'Poison': 2, 'Flying': 0,
                  'Bug': 0.5, 'Rock': 2, 'Steel': 2},
    'Flying':    {'Electric': 0.5, 'Grass': 2, 'Fighting': 2, 'Bug': 2, 'Rock': 0.5,
                  'Steel': 0.5},
    'Psychic':   {'Fighting': 2, 'Poison': 2, 'Psychic': 0.5, 'Dark': 0, 'Steel': 0.5},
    'Bug':       {'Fire': 0.5, 'Grass': 2, 'Fighting': 0.5, 'Poison': 0.5, 'Flying': 0.5,
                  'Psychic': 2, 'Ghost': 0.5, 'Dark': 2, 'Steel': 0.5, 'Fairy': 0.5},
    'Rock':      {'Fire': 2, 'Ice': 2, 'Fighting': 0.5, 'Ground': 0.5, 'Flying': 2,
                  'Bug': 2, 'Steel': 0.5},
    'Ghost':     {'Normal': 0, 'Psychic': 2, 'Ghost': 2, 'Dark': 0.5},
    'Dragon':    {'Dragon': 2, 'Steel': 0.5, 'Fairy': 0},
    'Dark':      {'Fighting': 0.5, 'Psychic': 2, 'Ghost': 2, 'Dark': 0.5, 'Fairy': 0.5},
    'Steel':     {'Fire': 0.5, 'Water': 0.5, 'Electric': 0.5, 'Ice': 2, 'Rock': 2,
                  'Steel': 0.5, 'Fairy': 2},
    'Fairy':     {'Fire': 0.5, 'Fighting': 2, 'Poison': 0.5, 'Dragon': 2, 'Dark': 2,
                  'Steel': 0.5},
}

for attacker, interactions in custom_effectiveness.items():
    attacker_id = TYPE_TO_ID[attacker]
    for defender, multiplier in interactions.items():
        defender_id = TYPE_TO_ID[defender]
        TYPE_CHART[attacker_id][defender_id] = multiplier

# Precompute dual type effectiveness as a 2D list for quick access
DUAL_EFFECTIVENESS = [[1.0 for _ in range(NUM_TYPES * (NUM_TYPES + 1) // 2)] for _ in range(NUM_TYPES)]

def get_double_type_id(defender1_id, defender2_id):
    """Returns a unique ID for a pair of defender types."""
    if defender1_id > defender2_id:
        defender1_id, defender2_id = defender2_id, defender1_id
    return defender1_id * NUM_TYPES - (defender1_id * (defender1_id + 1)) // 2 + defender2_id - defender1_id

# Precompute dual effectiveness without using caching decorators
def precompute_dual_effectiveness():
    for attacker in range(NUM_TYPES):
        for defender1 in range(NUM_TYPES):
            for defender2 in range(defender1, NUM_TYPES):
                eff1 = TYPE_CHART[attacker][defender1]
                eff2 = TYPE_CHART[attacker][defender2]
                dual_eff = eff1 * eff2
                dual_id = get_double_type_id(defender1, defender2)
                DUAL_EFFECTIVENESS[attacker][dual_id] = dual_eff

precompute_dual_effectiveness()

# Precompute all possible double type combinations
DOUBLE_TYPES = []
DOUBLE_TYPE_IDS = {}
current_id = 0
for i in range(NUM_TYPES):
    for j in range(i, NUM_TYPES):
        DOUBLE_TYPES.append((i, j))
        DOUBLE_TYPE_IDS[(i, j)] = current_id
        current_id += 1
TOTAL_DOUBLE_TYPES = len(DOUBLE_TYPES)

# Type colors using integer IDs
TYPE_COLORS = {
    0: '#A8A77A',  # Normal
    1: '#EE8130',  # Fire
    2: '#6390F0',  # Water
    3: '#F7D02C',  # Electric
    4: '#7AC74C',  # Grass
    5: '#96D9D6',  # Ice
    6: '#C22E28',  # Fighting
    7: '#A33EA1',  # Poison
    8: '#E2BF65',  # Ground
    9: '#A98FF3',  # Flying
    10: '#F95587', # Psychic
    11: '#A6B91A', # Bug
    12: '#B6A136', # Rock
    13: '#735797', # Ghost
    14: '#6F35FC', # Dragon
    15: '#705746', # Dark
    16: '#B7B7CE', # Steel
    17: '#D685AD', # Fairy
}

def get_effectiveness_double_int(attacking_id, defender1_id, defender2_id):
    """Retrieve precomputed effectiveness multiplier for dual-type defending using integer IDs."""
    dual_id = get_double_type_id(defender1_id, defender2_id)
    return DUAL_EFFECTIVENESS[attacking_id][dual_id]

def build_graph(selected_type_ids, is_double, allow_repetition):
    """Builds a graph where nodes are types and edges represent effectiveness."""
    graph = {type_id: set() for type_id in selected_type_ids}
    
    for attacker in selected_type_ids:
        for defender in selected_type_ids:
            if is_double:
                # Handle double types
                if not allow_repetition:
                    if attacker == defender:
                        continue
                # Each defender is a double type represented by unique ID
                attacker_id = attacker if isinstance(attacker, int) else DOUBLE_TYPE_IDS[attacker]
                defender_id = defender if isinstance(defender, int) else DOUBLE_TYPE_IDS[defender]
                attacker_effectiveness = DUAL_EFFECTIVENESS[attacker][defender_id]
                if attacker_effectiveness > 1.0:
                    graph[attacker].add(defender)
            else:
                # Single type
                effectiveness = TYPE_CHART[attacker][defender]
                if effectiveness > 1.0:
                    graph[attacker].add(defender)
    return graph

def find_cycles_optimized(graph, cycle_length, is_double, prevent_adjacent_same):
    """Finds all unique cycles of a given length in the graph using iterative DFS."""
    cycles = set()
    nodes = list(graph.keys())
    
    for start in nodes:
        if is_double:
            stack = [(start, [start])]
        else:
            stack = [(start, [start], set([start]))]
        while stack:
            if is_double:
                current, path = stack.pop()
                if len(path) == cycle_length:
                    if start in graph[current]:
                        cycle = tuple(path)
                        # Canonical form to avoid duplicates
                        min_node = min(cycle)
                        min_index = cycle.index(min_node)
                        normalized_cycle = cycle[min_index:] + cycle[:min_index]
                        # Optionally prevent adjacent same types
                        if prevent_adjacent_same:
                            if any(cycle[i] == cycle[(i + 1) % cycle_length] for i in range(cycle_length)):
                                continue
                        cycles.add(normalized_cycle)
                    continue
                for neighbor in graph[current]:
                    # Allow repetition for double types
                    stack.append((neighbor, path + [neighbor]))
            else:
                current, path, visited = stack.pop()
                if len(path) == cycle_length:
                    if start in graph[current]:
                        cycle = tuple(path)
                        # Canonical form to avoid duplicates
                        min_node = min(cycle)
                        min_index = cycle.index(min_node)
                        normalized_cycle = cycle[min_index:] + cycle[:min_index]
                        cycles.add(normalized_cycle)
                    continue
                for neighbor in graph[current]:
                    if neighbor not in visited:
                        stack.append((neighbor, path + [neighbor], visited | {neighbor}))
                    
    return list(cycles)

def generate_cycles_fast(cycle_length, selected_types, type_option, weakness, resist, allow_repetition, prevent_adjacent_same):
    """Generates all possible cycles based on the selected parameters."""
    # Validate inputs
    if type_option == "Single Types":
        is_double = False
    else:
        is_double = True
        
    # Map selected types to their IDs
    if is_double:
        # Handle double types
        selected_type_ids = []
        for combo in selected_types:
            # Ensure combo is a tuple
            if isinstance(combo, tuple):
                # Convert type names to their integer IDs and sort them
                type1, type2 = combo
                type1_id = TYPE_TO_ID[type1]
                type2_id = TYPE_TO_ID[type2]
                if type1_id > type2_id:
                    type1_id, type2_id = type2_id, type1_id
                double_id = DOUBLE_TYPE_IDS.get((type1_id, type2_id))
                if double_id is not None:
                    selected_type_ids.append(double_id)
    else:
        # Handle single types
        selected_type_ids = [TYPE_TO_ID[t] for t in selected_types]
    
    # Build the graph
    graph = build_graph(selected_type_ids, is_double, allow_repetition)
    
    # Find cycles
    cycles = find_cycles_optimized(graph, cycle_length, is_double, prevent_adjacent_same)
    
    return cycles

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Pokémon Type Cycle Generator")
        self.root.geometry("1000x800")
        self.root.configure(bg="#FFFFFF")
        
        # Queue for thread-safe UI updates
        self.queue = queue.Queue()
        
        # Main Frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Options Frame
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        options_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nw")
        
        # Cycle Length
        ttk.Label(options_frame, text="Cycle Length:").grid(row=0, column=0, sticky="w")
        self.cycle_length_var = tk.IntVar(value=3)
        self.cycle_length_spin = ttk.Spinbox(options_frame, from_=2, to=10, textvariable=self.cycle_length_var, width=5)
        self.cycle_length_spin.grid(row=0, column=1, sticky="w")
        
        # Type Option
        ttk.Label(options_frame, text="Type Option:").grid(row=1, column=0, sticky="w")
        self.type_option_var = tk.StringVar(value="Single Types")
        self.type_option_combo = ttk.Combobox(options_frame, textvariable=self.type_option_var, state="readonly",
                                             values=["Single Types", "Double Types"])
        self.type_option_combo.grid(row=1, column=1, sticky="w")
        self.type_option_combo.bind("<<ComboboxSelected>>", self.on_type_option_change)
        
        # Weakness and Resist Checkboxes
        self.weakness_var = tk.BooleanVar(value=True)
        self.resist_var = tk.BooleanVar(value=True)
        self.weakness_check = ttk.Checkbutton(options_frame, text="Weakness", variable=self.weakness_var)
        self.resist_check = ttk.Checkbutton(options_frame, text="Resist", variable=self.resist_var)
        self.weakness_check.grid(row=2, column=0, sticky="w")
        self.resist_check.grid(row=2, column=1, sticky="w")
        
        # Prevent Same Types Adjacent Checkbox
        self.prevent_adjacent_var = tk.BooleanVar(value=False)
        self.prevent_adjacent_check = ttk.Checkbutton(options_frame, text="Prevent Same Types Adjacent", 
                                                     variable=self.prevent_adjacent_var)
        self.prevent_adjacent_check.grid(row=3, column=0, columnspan=2, sticky="w", pady=5)
        
        # Allow Repetition Checkbox
        self.allow_repetition_var = tk.BooleanVar(value=True)
        self.allow_repetition_check = ttk.Checkbutton(options_frame, text="Allow Type Repetition in Cycle", 
                                                     variable=self.allow_repetition_var)
        self.allow_repetition_check.grid(row=4, column=0, columnspan=2, sticky="w", pady=5)
        
        # Submit Button
        self.submit_button = ttk.Button(options_frame, text="Generate Cycles", command=self.generate_cycles_all)
        self.submit_button.grid(row=5, column=0, columnspan=2, pady=10)
        
        # Progress Bar
        self.progress = ttk.Progressbar(options_frame, mode='indeterminate')
        self.progress.grid(row=6, column=0, columnspan=2, pady=5, sticky="ew")
        
        # Result Frame
        result_frame = ttk.LabelFrame(main_frame, text="Cycles", padding="10")
        result_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # Scrollbar for Results
        scrollbar = ttk.Scrollbar(result_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Results Text Widget
        self.result_text = tk.Text(result_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set, bg="#F0F0F0")
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.result_text.yview)
        
        # Initialize Tags for Coloring
        for type_id in range(NUM_TYPES):
            type_name = ID_TO_TYPE[type_id]
            color = TYPE_COLORS.get(type_id, 'black')
            self.result_text.tag_config(type_name, foreground=color, font=('Helvetica', 10, 'bold'))
        self.result_text.tag_config('arrow', foreground='black', font=('Helvetica', 10, 'bold'))
        self.result_text.tag_config('bracket', foreground='black', font=('Helvetica', 10, 'bold'))
        self.result_text.tag_config('slash', foreground='black', font=('Helvetica', 10, 'bold'))
        
        # Start processing queue
        self.process_queue()
    
    def on_type_option_change(self, event):
        """Handles changes in the Type Option combobox."""
        type_option = self.type_option_var.get()
        if type_option == "Single Types":
            self.allow_repetition_check.state(['disabled'])
            self.prevent_adjacent_check.state(['disabled'])
        else:
            self.allow_repetition_check.state(['!disabled'])
            self.prevent_adjacent_check.state(['!disabled'])
    
    def get_selected_types(self):
        """Retrieves selected types from the user."""
        type_option = self.type_option_var.get()
        if type_option == "Single Types":
            return TYPES
        else:
            return list(itertools.combinations_with_replacement(TYPES, 2))
    
    def generate_cycles_all(self):
        """Initiates cycle generation based on user inputs."""
        cycle_length = self.cycle_length_var.get()
        type_option = self.type_option_var.get()
        weakness = self.weakness_var.get()
        resist = self.resist_var.get()
        allow_repetition = self.allow_repetition_var.get()
        prevent_adjacent_same = self.prevent_adjacent_var.get()
        
        # Input Validations
        if not (weakness or resist):
            messagebox.showerror("Error", "Please select at least one of Weakness or Resist.")
            return
        if not (2 <= cycle_length <= 10):
            messagebox.showerror("Error", "Cycle length must be between 2 and 10.")
            return
        
        selected_types = self.get_selected_types()
        if type_option == "Double Types":
            if not allow_repetition:
                # Remove combinations where both types are the same
                selected_types = [combo for combo in selected_types if combo[0] != combo[1]]
                if not selected_types:
                    messagebox.showerror("Error", "No valid double types selected after removing duplicates.")
                    return
        
        self.result_text.delete(1.0, tk.END)
        self.progress.start()
        
        # Start cycle generation in a separate thread
        threading.Thread(target=self.run_generate_cycles, args=(cycle_length, selected_types, type_option,
                                                                weakness, resist, allow_repetition, prevent_adjacent_same), daemon=True).start()
    
    def run_generate_cycles(self, cycle_length, selected_types, type_option, weakness, resist, allow_repetition, prevent_adjacent_same):
        """Runs cycle generation and puts the result in the queue."""
        cycles = generate_cycles_fast(cycle_length, selected_types, type_option, weakness, resist, allow_repetition, prevent_adjacent_same)
        self.queue.put((cycles, type_option))
    
    def display_cycles(self, cycles, type_option):
        """Batch insert cycles to minimize UI updates."""
        output = []
        for cycle in cycles:
            if type_option == "Single Types":
                cycle_types = [ID_TO_TYPE[type_id] for type_id in cycle]
                cycle_str = ' -> '.join([f"[{t}]" for t in cycle_types]) + f" -> [{ID_TO_TYPE[cycle_types[0]]}]"
            else:
                cycle_types = [DOUBLE_TYPES[type_id] for type_id in cycle]
                formatted_types = [f"[{ID_TO_TYPE[t1]}/{ID_TO_TYPE[t2]}]" for t1, t2 in cycle_types]
                cycle_str = ' -> '.join(formatted_types) + f" -> [{ID_TO_TYPE[cycle_types[0][0]]}/{ID_TO_TYPE[cycle_types[0][1]]}]"
            output.append(cycle_str)
        formatted_output = '\n'.join(output)
        self.result_text.insert(tk.END, formatted_output)
        self.progress.stop()
    
    def process_queue(self):
        """Processes the queue to update the UI with generated cycles."""
        try:
            while True:
                cycles, type_option = self.queue.get_nowait()
                if cycles:
                    self.display_cycles(cycles, type_option)
                else:
                    self.result_text.insert(tk.END, "No cycles found.")
        except queue.Empty:
            pass
        self.root.after(100, self.process_queue)

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
