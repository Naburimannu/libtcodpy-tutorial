# libtcodpy-tutorial

An extension of Jotaf's Python roguelike tutorial for libtcod.

The code flows incredibly naturally from the tutorial, much like literate programming, but results in a single large file.
In practice that feels to me like the "Big Ball of Mud" architecture; I want to be able to base development off of something cleaner.
This refactoring starts with the same code and divides it up into 12 smaller files, all levelized:

1. roguelike: main menu, mainloop, load and save, player actions
2. cartographer: map generation
3. spells and targeting functions
4. interface
5. ai
6. actions: movement and combat (implementations shared between player and monsters)
7. renderer
8. components: Object, Fighter, Item, Equipment, AI
9. map
10. algebra: Rect, Location, Direction
11. log
12. config

Most of the global variables have been eliminated; modules export renderer.overay and log.game_msgs, while renderer also uses a few "globals" internally.
At the git tag 'basic-refactoring', the only other significant change should be:
* Get rid of the Tile class for a 2x reduction in filesize and 2x speedup in load/save.

Subsequently implemented externally-visible features include:
* Persistent maps, and up-stairs allowing backtracking.
* Support for maps smaller or larger than the screen.
* ^p opens old log, which can be scrolled through with numpad, vi keys, or mousewheel. 
* Move with vi keys (hjkl,yubn) as well as numpad.
* Running with shift-move until reaching an object, a change in architecture, or spotting a monster.
* Targeting with keyboard as well as mouse.
* Help screen on ? or F1.
* ~2.5x speedup drawing large maps (from 6-7 fps to 15-17 fps for 200x200).
* Stackable objects

