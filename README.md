# DOSCtl

A command-line tool to manage and play DOS games.

## Getting Started

1.  **List Games:** Find a game you want to play. The tool will automatically download the game list on the first run.
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

*   `dosctl run <game-id> [executable] [args...]`
    *   Runs a game. Downloads and installs it if necessary.
    *   Prompts for an executable on the first run.
    *   You can override the saved executable by providing one.
    *   `-c, --configure`: Force the interactive executable selection menu to appear.

*   `dosctl inspect <game-id>`
    *   Shows the list of installed files for a game.

*   `dosctl delete <game-id>`
    *   Deletes an installed game and its files.

*   `dosctl refresh --force`
    *   Forces a re-download of the master game list from the Internet Archive.

## Configuration

`dosctl` stores its data in standard user directories. On macOS, this will be:
*   **Configuration:** `~/.config/dosctl/run_config.json`
*   **Data & Cache:** `~/.local/share/dosctl/`

## Collection Backend

The default collection is the [**Total DOS Collection Release 14**](https://archive.org/details/Total_DOS_Collection_Release_14) from the Internet Archive.
