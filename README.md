# Cels2x

_A great way to finish 2024._

## Introduction

So my public presence in the homebrew dev scene has been low to inexistent in the past one or two years. 
That is because I kept struggling with my GBA/NDS engine idea and tried to find a way to write clean, intuitive and optimized code that
handles hardware manipulation and game logic. My latest successful attempt was a heavily object oriented scene-based engine library from 2022 with automatic VRAM initialization based on some specified requirements. Games created with this engine visibly suffered from performance issues, probably caused by intensive use of heap allocation and bloating the game loop with whatever data management features (under the belief that _my handmade_ stdlib alternatives _have_ to be "faster" 🤡). Since then, I tried migrating to a class-less and functional implementation that reduces engine overhead to bare minimum using the constant compiler features as much as possible. Hope there will be soon a working materialization of this idea. 

In the meantime, while studying [tonc's text engine](https://www.coranac.com/tonc/text/tte.htm) in search for some inspiration I remembered the pain I had with designing and debugging the spaghetti code in [Bugtris](https://github.com/NotImplementedLife/Bugtris) when handling cutscenes and other action that interrupt the normal flow of the game. To give a simpler example, let's image a simple fixed grid 2D RPG scroller where you (the player) want to move to the right. Let's say the player step count is 32px and takes 0.53 second (~32 frames).  In order for this to happen, you have to display the sprites for the current character orientation and keyframe animation (left/right leg moving), increment the x-position of the sprite, and do that on each one of the 32 frames. This can be done with no effort in pure C++ code once you set up the game loop, but what if you want to also handle object interaction, score tracking or environment quirks like animated tiles? Assuming no sophisticated weapons, this can again be easily done with a bunch of `if-else`s in the game loop. Now, imagine the following scenario: you interact with an NCP, it plays some dialog, _then_ it moves 2 steps right and one step up, _then_ talks again, gives you some yes/no choice and _then_ disappears beyond the screen's edge. And imagine doing that stuff for _every_ complex action in the game. Now what? This kind of serial actions trigger can be sanity killing unless you have set up some sort of scripting language, even as simple as a byte code event handling queue. This is a perfectly valid solution in my view, but it requires emulation or some sort of interpreter which may noy be the most efficient. And I was stuck in this point for such a long time because I thought I can do better than that. What if I had a high level way to say "show dialog, then move right, then up etc." AND it somehow automatically compiled to C++ code, while keeping part of the compiler optimization advantage?

## Celesta: multiframe programming language

I combined this concept with an older idea I tried of a programming language called Celesta (abbreviated Cels), which I created primarily as a scripting language for the Astralbrew GBA engine but it was in a proof of concept state and never reached an usable form, despite my attempts like [this one](https://github.com/EsotericDevZone/EsotericDevZone.Celesta) or [this one](https://github.com/Astralbrew/Celesta) and other non-public scrapped version. At that point I had no idea what direction I wanted to go with that project, and maye this is why I failed to finish it properly. But in the last couple of weeks, despite my lack of hope, I worked hard and tried again and actually created something useful. There were some key principles I based my language on:

- **Linearity of code that executes over the span of multiple frames**

This can be done using the concept of `multiframe` functions I included in the language. Basically, a multiframe function overrides the game loop to execute the logic specific to that function (e.g. player move animation), and then it gives the control back to the old loop, continuing the execution from where it left. Therefore, a serial sequence of events like the following one is possible:

```
/* Cels code */
multiframe function show_dialog(message:string):void;
multiframe function move_player(player:Player*, dx:int, dy:int, fps:int):void;

multiframe function talk_and_walk(player:Player*):void;
begin
    show_dialog("Hi!");
    move_player(player, 32, 0, 32); /* move player left 32px for 32 frames */
    move_player(player, 0, -32, 32); /* move player up 32px for 32 frames */
    show_dialog("Bye!");
    /* total function execution frames: 32 + 32 + <user interaction time> */
end;
```

- **Suspendability**

This works similarly to the yielding concept in threads. Except, it is for multiframe functions and you have to manually specify when it happens via the `suspend` keyword. When a multiframe function is suspended, the control is given to the C++ game loop for the rest of the frame. In this time, the game can call other routines that handle other aspects of the game or ambients (sounds, update graphics).

```
extern function print(x:int);

var i=0;
while i<3 do begin
    print(i);
    i = i+1; 
    suspend;       
end;
```

This Cels code will run across 3 frames, and on each frame will print a number (0 on the first frame, 1 on the second, and 2 on the last).


- **Easy C++ interoperability**

Remember, this is not exercise on designing a powerful good for all programming language. It just needs to fulfill its purpose. 

First, given that Cels compiles directly to C++ code, if you want to use for example the function `min`, then you just need declare it as extern. It will also compile to an extern C++ forward declaration, and you don't even need to include the correct headers since the linker will find it automatically assuming a symbol with the same name exists and has the same signature.

```
/* Corresponds to a C++ min function */
extern function min(x:int, y:int):int; 
```

Second, you can declare C++ structs and use them as pointers even without knowing the actual definitions. As long as you have a C++ binding funtion which uses that pointer, it's enough.

```
/* In C++, a Player struct can hold lots of player data.
   In Cels, you can only refer it by its name
 */
extern struct Player; 

/* And access the hidden data through getters/setters */
extern function Player_get_score(player: Player*): int;
extern function Player_set_score(player: Player*, new_score: int): void;
```

In essence, I designed with the following way to do things in mind: **C++ handles data, Celesta handles multiframe flow.**. There is no need for the language to know more about the environment than necessary. Of course, C++ can see all Celesta's exported symbols, and potentially use them when needing (e.g. calling the entry point of a multiframe function).

## Repository contents

In this repo, the `source/` directory contains the Python implementation of the language. The code is still (very) messy and unorganized, but potentially readable. The `examples/` directory contains application of the Celesta language. 

The `gba_celstris` project is a very simple GBA Tetris clone which features Celesta script for handling user inputs. The C++ extern functions only update the Tetris board (add pieces, test overlap, clear).


## To do list

The language is usable for its intended purpose (multiframe game loop control). However, there are some quality of life updates that can be done. For example, because there is no support for unary operators, you can't represent a negative constant in Cels so you'd have to write -1 as 0-1. The language is mainly procedural, and I do not intend to include OOP support as it would be too much of a work. However, a small addition to have an alternative syntax for calling `f(a,b)` as `a.f(b)` would do the trick. And only simple inheritance for extern structs may help in case we need for example to call from Cels a virtual C++ `Sprite::move` method on an object `Human` that inherits `Sprite`. Last but not least, I should include a language specification (until I won't forget all the features I designed :) ).


