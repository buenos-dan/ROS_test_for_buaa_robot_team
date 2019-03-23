#!/usr/bin/env python
'''
date   : 2018.6.30
version: 1.0.0v
'''
import time
import random
import numpy as np
import threading
import pygame
import rospy
from first_player.msg import *
from pygame.locals import *
from std_msgs.msg import UInt8
from settings import *

#init the pygame and set the window
pygame.init()
screen = pygame.display.set_mode(SCREEN_SIZE,0,32)
pygame.display.set_caption(SCREEN_CAPTION)
font = pygame.font.SysFont("arial",40)
map_img = pygame.image.load(IMG_PATH).convert()

'''
    this class creates a robot that can 
    receive velocity, move and send location.
'''
class ROBOT(object):
    def __init__(self,pos):
	self.pos = pos
	self.velocity = [0,0]
	self.pos_pub = rospy.Publisher("pos_msg",Pos,queue_size = 10)

    def move(self):
	self.pos = tuple(np.array(self.pos)+np.array(self.velocity))
	self.velocity = [0,0]
	self.pub_pos()

    def pub_pos(self):
	pos = Pos()
	pos.x = self.pos[0]
	pos.y = self.pos[1]
	self.pos_pub.publish(pos)
	

'''
    this class creates a game. graphical by pygame.
    control all the robot run the game legally
'''
class GAME(object):
    def __init__(self):
	self.end_pos = END_POS
	self.robot = ROBOT(START_POS)
	self.treasure_list = []
	self.treasured_list = []
	self.score = 0
	self.time = time.time()
	rospy.init_node("game",anonymous=True)
	rospy.Subscriber("velocity_msg",Vel,self.control_robot)
	self.treasure_pub = rospy.Publisher("treasure_msg",treasurePos,queue_size = 10)

    def pub_treasure(self):
	lastTime = time.time()-TREASURE_PUB_TIME+0.5
	while True:
	    if time.time()-lastTime>TREASURE_PUB_TIME:
		tp = treasurePos()
		tp.x = random.randrange(RECT_START[0],RECT_END[0])
		tp.y = random.randrange(RECT_START[1],RECT_END[1])
		tp.w = random.randint(3,6)
		self.treasure_pub.publish(tp)
		self.treasure_list.append(tp)
		lastTime = time.time()

    '''
	a thread to pub treasure location
    '''
    def send_pos(self):
	timer = threading.Thread(target=self.pub_treasure)
	timer.setDaemon(True) 
	timer.start()
	

    def drawAllElements(self):
	#draw the map
	screen.blit(map_img,RECT_START)
	#draw robot
	screen.blit(font.render('o',True,ROBOT_COLOR),self.robot.pos)
	#draw treasure
	for treasure in self.treasure_list:
	    screen.blit(font.render(str(treasure.w),True,TREASURE_COLOR),(treasure.x,treasure.y))
	#draw the score
	screen.blit(font.render(str(self.score),True,EXIT_COLOR),SCORE_POS1)
	screen.blit(font.render('>'+str(SET_SCORE),True,SCORE_COLOR),SCORE_POS3)
	screen.blit(font.render('score:',True,EXIT_COLOR),SCORE_POS2)
	#draw time
	screen.blit(font.render("time:",True,TIME_COLOR),TIME_POS1)
	screen.blit(font.render(str(int(time.time()-self.time)).rjust(5),True,TIME_COLOR),TIME_POS2)
	
	
    def control_robot(self,vel):
	if vel.vx**2+vel.vy**2 < MAX_SQUARE_VELOCITY:
	    self.robot.velocity = [vel.vx,vel.vy]
	else:
	    self.robot.velocity = [0,0]
	    print "it's an illegal velocity"
	
    def xwindow(self):
	while True:
	    screen.fill(BACKGROUND_COLOR)
	    self.drawAllElements()
	    pygame.display.update()
	    time.sleep(0.05)

    '''
	a thread to update the window 
    '''
    def display(self):
	timer = threading.Thread(target=self.xwindow)
	timer.setDaemon(True) 
	timer.start()

    '''
	judge is any robot win the game,then exit the game
    '''
    def is_over(self):
	if self.robot.pos == self.end_pos:
	    print "you win!"
	    return False
	else:
	    return True

    def is_getPoint(self):
	for treasure in self.treasure_list:
	    if treasure not in self.treasured_list:
		if treasure.x == self.robot.pos[0] and treasure.y == self.robot.pos[1]:
		    self.treasured_list.append(treasure)
		    self.score += treasure.w
		    break

    '''
	main loop to run the game
    '''
    def runGame(self):
	while self.is_over():
	    self.is_getPoint()
	    self.robot.move()
	    #frequency is 100hz.more than 100hz is useless
	    time.sleep(0.01)


if __name__=="__main__":
    game = GAME()
    game.display()
    game.send_pos()
    game.runGame()


