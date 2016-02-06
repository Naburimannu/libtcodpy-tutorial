# libtcodpy-tutorial

An extension of Jotaf's Python roguelike tutorial for libtcod.

The code flows incredibly naturally from the tutorial, much like literate programming, but results in a single large file.
In practice that feels to me like the "Big Ball of Mud" architecture; I want to be able to base development off of something cleaner.
This refactoring starts with the same code and divides it up into 11 smaller files, all levelized:

1. roguelike: main menu, mainloop, load and save, player actions
2. cartographer: map generation
3. spells and targeting functions
4. ai
5. actions: movement and combat (implementations shared between player and monsters)
6. renderer
7. ui
8. components: Object, Fighter, Item, Equipment, AI
9. map
10. log
11. config

Most of the global variables have been eliminated; modules export ui.key, ui.mouse, and log.game_msgs, while renderer uses a few internally.
At the git tag 'basic-refactoring', the only other significant change should be:
* Get rid of the Tile class for a 2x reduction in filesize and 2x speedup in load/save.

Subsequent major changes include:
* 
