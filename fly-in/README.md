*This activity has been created as part of the 42 curriculum by lcoant--*

# Flyin

## Description

The goal of fly is to take a map and make a batch of drone go from their start zone to the end zone by going trought zones and connections.

To do so the first step was to parse a map file with certain constraints, then to plan a path for all the drone with an algorithm (Dijkstra with some modifications) and finaly to creat a visualizer that display all the drones actions's per turn.

## Instructions

You just need to use the provided Makefile.

To setup the activity do :

```
make install
```

To run the project without the visualizer do :

```
make run
```

To run the pproject with the visualizer do :

```
make visual
```

If you want to use a certain map or to change the delay for the visualisation just modify their variable with :

```
make visual MAP='your-map' DELAY='choosen-delay'
```

To use the other command of the Makefile just do :

```
make clean
make lint
make lint-strict
```

## Resources

Wikipedia :
- https://fr.wikipedia.org/wiki/Algorithme_d%27Edmonds-Karp
- https://fr.wikipedia.org/wiki/Th%C3%A9or%C3%A8me_flot-max/coupe-min
- https://fr.wikipedia.org/wiki/Coupe_(th%C3%A9orie_des_graphes)
- https://fr.wikipedia.org/wiki/P_(complexit%C3%A9)
- https://fr.wikipedia.org/wiki/Graphe_orient%C3%A9
- https://fr.wikipedia.org/wiki/Th%C3%A9orie_des_graphes#Flots_dans_les_r%C3%A9seaux
- https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm

Videos :
- Ivan monka videos of Dijkstra algorithm
- 'How dijkstra's algorithm' works by spanning tree
- 'The hidden beauty of the A* algorithm' by polylog
- other minor videos of graph theori and parsing

Book :
- Grokking algorithm

IA usage:
I use IA to give me insight on the differant step of the project and on the differant algorithm that I could use. I also used it to check my code and to make it more profesional (with code style concept). And to help me with algorithm implementatin.

## Addiional sections

### Algorithm

I look onto a lot of differants algorithm, simple BFS, max-flow / min-cut, Edmon-Karp, A* and so on and so on.
I didn't use Edmon-Karp and max-min(ford ferguson) because its improvement did not seem usefull to me, it's use to find the botleneck and to then act according to it (BASICLY, it's more complicated but it's just to say that in this case it's not usefull), and it's not realy the goal here, finding a way to dispatch the drone really efficency is not worth the complexity of this algorithm.
I use BFS as a structure (and also to check if the graph is feasable), Dijkstra is the algorithm that I choose because it's perfect for weighted graph and it's made to not go backward, A* wasn't worth using in my ooppinion because it's an heuristic (an heuristic of Dijkstra).
First the goal of the project is not to have the fastest algorithm.
Second since it's an heuristic the risk is that it could not found a "longer"but faster route.
Third it's a much more complicated algorithm were each vertex must have a computed heuristic value and im not doing allat.

### Visual representation

The visual representation is a simple terminal display, it use the color store in the metadata and hold a bar that check the drones delivered.
Even thourght it's not a neck plus ultra visual representation, I think that it does it's job quiet well and the use still can modify the delay.

### Exempe input output ?

For the easy map number 03 all the drone will go in a line to the end zone ?
