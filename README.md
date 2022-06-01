# Pong-PySDL2
This is a pretty simple Pong game made in Python and utilising the PySDL2 library. 

## Table of Contents
* [General Information](#general-information)
* [Technologies Used](#technologies-used)
* [Features](#features)
* [Usage](#usage)

## General Information
The purpose of this project was to learn the basics of the PySDL2 library as I was curious about rendering.  This was also the first time i've ever created a game and so I happened to learn about game physics (creating a simple velocity/force mechanic), AI, and also player Input.  I specifically chose the SDL2 library over PyGame, because the documentation seemed scarcer so it would encourage more understanding than copy-pasting a tutorial.

## Screenshot

![Pong GIF](https://github.com/DannyGeorgeWheeler/Pong-PySDL2/blob/main/screenshots/pong-pysdl2.gif?raw=true)

## Technologies Used
* Python v 3.10.4
* [PySDL2 v 0.9.11](https://pypi.org/project/PySDL2/)

## Features
### Implemented
* Rendering of sprites using the ext.spritefactory
* Rendering of the score using a numpy 3D array of the window surface pixels and a font stored in hexadecimal format.
* Momentum system that gives some weight to the feeling of the paddles using a velocity/force calculation.
* AI opponent that calculates the trajectory of the ball.
    * In order to make it possible to beat the AI, I added some random margin of error to the wall rebound trajectory calculation and also added a slight delay to the AI's response time, giving a more human like opponent.  The AI is still tough to beat, but it's behaviour feels realistic to me.
* I changed the pitch size to a taller rectangle because I found that creates a more exciting and fast-paced type of gameplay.
### Development Ideas
* Create a win condition.
* Create a pause/serve feature after a point is scored.
* Implement the dash feature (I have had a go at this with some success for the player, but found the AI implementation challenging so far!)

## Usage
To run this program run the python file from your terminal with the following command:
> python pysdl2-pong.py

## Controls
The game will detect a controller if connected and will disable keyboard controls.  If a controller is not detected then keyboard controls will be available.

Use the arrow keys or the D-Pad to move up & down on the keyboard or controller respectively.

