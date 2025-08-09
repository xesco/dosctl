# DOSCtl

A command-line tool to manage and play DOS games.

## Getting Started

1.  **List Games:** Find a game you want to play. The tool will automatically download the game list from the [Total DOS Collection Release 14](https://archive.org/details/Total_DOS_Collection_Release_14) on the first run.
    ```bash
    dosctl list
    ```
2.  **Search for a Game:** Narrow down the list with a search.
    ```bash
    dosctl search "Dune" --sort-by year
    ```
3.  **Run a Game:** Run the game using its ID. The first time you run a game, `dosctl` will download and install it, then ask you to choose the correct executable.
    ```bash
    dosctl run <game-id>
    ```

## Core Concepts

### Game IDs
Every game in the collection is assigned a unique 8-character ID (a hash of its path). You use this ID for all operations like running, inspecting, or deleting games.

### First-Time Run
The first time you run a game, `dosctl` will prompt you to select the main executable file from a list of possibilities (`.exe`, `.com`, `.bat`). Your choice is remembered, so subsequent runs will launch the game immediately. You can force this selection again by using the `--configure` flag.

### Command Parts
You can specify exactly what DOS command to run by providing **command parts** after the game ID. This gives you fine-grained control over game execution:

- **Without command parts:** `dosctl run <game-id>` uses the saved default executable
- **With command parts:** `dosctl run <game-id> setup.exe -silent` runs the exact command you specify

Command parts are joined with spaces to form the final DOS command. This is useful for:
- Running different executables (setup, configuration tools, etc.)
- Passing command-line arguments to games
- Running batch files with parameters
- Bypassing the saved default when needed

**Examples:**
```bash
dosctl run 62ef2769 setup.exe          # Run setup instead of main game
dosctl run 62ef2769 game.exe -debug     # Run with debug flag
dosctl run 62ef2769 install.bat /q      # Run batch file quietly
dosctl run 62ef2769 editor.exe level1   # Run level editor with specific level
```

## Usage Examples

### List only your installed games
```bash
$ dosctl list -i
Available Games:
  [53ad2f67] (1991) Lemmings (1991)(Psygnosis Limited) [Strategy, Action]
  [fdcc9602] (1990) Secret of Monkey Island, The (VGA) (1990)(Lucasfilm Games LLC) [Adventure]
```

### Search for a game
```bash
$ dosctl search "metal mutant"
Found 5 game(s):
  [dd228682] (1991) Metal Mutant (1991)(Silmarils) [Action, Adventure]
  [55123659] (1991) Metal Mutant (1991)(Silmarils) [Codes]
  [9a5aa0b6] (1991) Metal Mutant (Es) (1991)(Silmarils) [Action, Adventure]
```

### Run a game for the first time
```bash
$ dosctl run dd228682
Downloading 'Metal Mutant (1991)(Silmarils) [Action, Adventure].zip'...
✅ Successfully installed 'Metal Mutant (1991)(Silmarils) [Action, Adventure]'
No default executable set for game 'dd228682'. Searching...
Found a single executable: 'METAL.EXE'. Setting as default.
Starting 'METAL.EXE' with DOSBox...
```

### Run a specific executable directly
```bash
$ dosctl run dd228682 setup.exe
Starting 'SETUP.EXE' with DOSBox...
```

### Run with command-line arguments
```bash
$ dosctl run dd228682 game.exe -difficulty hard -level 3
Starting 'GAME.EXE -DIFFICULTY HARD -LEVEL 3' with DOSBox...
```

### Run main executable with required parameters
```bash
$ dosctl run dd228682 metal.exe soundblaster
Starting 'METAL.EXE SOUNDBLASTER' with DOSBox...
```

### Force reconfiguration of saved executable
```bash
$ dosctl run dd228682 --configure
Please choose one of the following to run:
  1: METAL.EXE
  2: SETUP.EXE
  3: README.BAT
Select a file to execute: 2
Starting 'SETUP.EXE' with DOSBox...
```

### Inspect game files
```bash
$ dosctl inspect dd228682
Inspecting files for 'Metal Mutant (1991)(Silmarils) [Action, Adventure]' (ID: dd228682)
Location: ~/.local/share/dosctl/installed/dd228682
----------------------------------------
  METAL.EXE
  SETUP.EXE
  README.TXT
  DATA/LEVELS.DAT
  DATA/SOUNDS.DAT
```

### Show only executable files
```bash
$ dosctl inspect dd228682 --executables
Inspecting files for 'Metal Mutant (1991)(Silmarils) [Action, Adventure]' (ID: dd228682)
Location: ~/.local/share/dosctl/installed/dd228682
----------------------------------------
Executable files:
  METAL.EXE
  SETUP.EXE
```

## Commands

*   `dosctl list`
    *   Lists all available games.
    *   `-s, --sort-by [name|year]`: Sort the list by name or year.
    *   `-i, --installed`: Only show games that are currently installed.

*   `dosctl search <query>`
    *   Searches for games. The query is optional if `--year` is used.
    *   `-y, --year <year>`: Filter by a specific year.
    *   `-c, --case-sensitive`: Make the search case-sensitive.
    *   `-s, --sort-by [name|year]`: Sort the results by name or year.

*   `dosctl run <game-id> [command-parts...]`
    *   Runs a game. Downloads and installs it if necessary.
    *   Prompts for an executable on the first run.
    *   **Command Parts:** You can specify the exact DOS command to run instead of using the saved default.
    *   `-c, --configure`: Force the interactive executable selection menu to appear.

    **Examples:**
    ```bash
    dosctl run 62ef2769                    # Use saved/default executable
    dosctl run 62ef2769 --configure        # Choose executable interactively
    dosctl run 62ef2769 setup.exe          # Run specific executable
    dosctl run 62ef2769 game.exe -level 5  # Run with command-line arguments
    dosctl run 62ef2769 install.bat quiet  # Run batch file with parameters
    ```

*   `dosctl inspect <game-id>`
    *   Shows the list of installed files for a game.
    *   `-e, --executables`: Show only executable files (.exe, .com, .bat).

*   `dosctl delete <game-id>`
    *   Deletes an installed game and its files.

*   `dosctl refresh --force`
    *   Forces a re-download of the master game list from the Internet Archive.

## Configuration

`dosctl` stores its data in standard user directories. On macOS, this will be:
*   **Configuration:** `~/.config/dosctl/run_config.json`
*   **Data & Cache:** `~/.local/share/dosctl/`

## Collection Backend

By default, `dosctl` uses the [**Total DOS Collection Release 14**](https://archive.org/details/Total_DOS_Collection_Release_14) from the Internet Archive as its game collection source. This comprehensive collection contains thousands of DOS games from the 1980s and 1990s, all ready to download and play.

The collection includes:
- Classic DOS games from various genres (adventure, action, strategy, RPG, etc.)
- Games from major publishers like LucasArts, Sierra, id Software, and many others
- Both well-known titles and obscure gems
- Games in their original format, preserved for historical accuracy

When you first run `dosctl list` or `dosctl search`, the tool will automatically download the complete game catalog from this collection. The games themselves are downloaded individually only when you choose to run them.
