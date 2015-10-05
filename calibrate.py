#!/usr/bin/env python

##########################################################################
# Copyright 2015 Sensel, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
##########################################################################

#
#  Read Contacts
#  by Aaron Zarraga - Sensel, Inc
#
#  This opens a Sensel sensor, reads contact data, and prints the data to the console.
#
#  Note: We have to use \r\n explicitly for print endings because the keyboard reading code
#        needs to set the terminal to "raw" mode.
##

from pylab import *
from keyboard_reader import *
import sensel
import math
import copy
import pickle

with open("dict.txt") as word_file:
    english_words = set(word.strip().lower() for word in word_file)

keys_pressed = {
    'a': 0,
    'b': 0,
    'c': 0,
    'd': 0,
    'e': 0,
    'f': 0,
    'g': 0,
    'h': 0,
    'i': 0,
    'j': 0,
    'k': 0,
    'l': 0,
    'm': 0,
    'n': 0,
    'o': 0,
    'p': 0,
    'q': 0,
    'r': 0,
    's': 0,
    't': 0,
    'u': 0,
    'v': 0,
    'w': 0,
    'x': 0,
    'y': 0,
    'z': 0,
    ' ': 0,
    'shift': 0,
    'backspace': 0,
    ',': 0,
    '.': 0,
}

load_grid = False
save_grid = False
plot_x = []
plot_y = []
grid = [[copy.deepcopy(keys_pressed) for y in range(120)] for x in range(230)]
starting_x = 0
starting_y = 0
offset_x = 0
offset_y = 0
num_dogs = 2
prompt_str = ''
for i in range(num_dogs):
    prompt_str += 'the quick brown fox jumps over the lazy dog '

prompt_str1 = ('the quick brown fox jumps over the lazy dog '
              'pack my box with five dozen liquor jugs '
              'jackdaws love my big sphinx of quartz '
              'a quick movement of the enemy will jeopardize six gunboats '
              'wafting zephyrs quickly vexed jumbo ')

prompt_str2 = ('nerd nerd nerd nerd nerd nerd nerd nerd nerd nerd')

def openSensorReadContacts():
    sensel_device = sensel.SenselDevice()

    if not sensel_device.openConnection():
        print "Unable to open Sensel sensor!"
        exit()

    #Enable contact sending
    sensel_device.setFrameContentControl(sensel.SENSEL_FRAME_CONTACTS_FLAG)

    #Enable scanning
    sensel_device.startScanning()
    global starting_x
    global starting_y
    global grid
    print 'Please put 8 fingers in a \'starting position\'.'
    position_set = False
    while not position_set:
        contacts = sensel_device.readContacts()
        if len(contacts) == 8:
            for c in contacts:
                starting_x += int(c.x_pos_mm)
                starting_y += int(c.y_pos_mm)
            starting_x /= 8
            starting_y /= 8
            position_set = True
            #print 'starting_x: ', starting_x
            #print 'starting_y: ', starting_y
    if load_grid:
        grid = pickle.load(open('saved', 'rb'))
    else:
        print 'Please type:', prompt_str
        typed_chars = 0;
        done_calibrating = False

        while not done_calibrating:
            contacts = sensel_device.readContacts()

            if len(contacts) == 0:
                continue

            for c in contacts:
                if c.type == sensel.SENSEL_EVENT_CONTACT_INVALID:
                    pass
                elif c.type == sensel.SENSEL_EVENT_CONTACT_START:
                    sensel_device.setLEDBrightness(c.id, 100) #Turn on LED
                    print prompt_str[typed_chars]
                    radius = int((c.major_axis_mm + c.minor_axis_mm) / 4)
                    calibrate_key(prompt_str[typed_chars], int(c.x_pos_mm),
                                  int(c.y_pos_mm), radius)
                    typed_chars += 1
                elif c.type == sensel.SENSEL_EVENT_CONTACT_MOVE:
                    pass
                elif c.type == sensel.SENSEL_EVENT_CONTACT_END:
                    sensel_device.setLEDBrightness(c.id, 0) #Turn off LED
                else:
                    pass
            done_calibrating = typed_chars == len(prompt_str)

    if save_grid:
        pickle.dump(grid, open('saved', 'wb'))
    #show_plot()
    receive_input(sensel_device)

def calibrate_key(key, x_pos, y_pos, radius):
    n = 3
    keys_pressed[key] += 1
    for x in range(x_pos - radius * n, x_pos + radius * n + 1):
        for y in range(y_pos - radius * n, y_pos + radius * n + 1):
            if math.sqrt((x_pos - x)**2 + (y_pos - y)**2) <= radius * n:
                if (x >= 0 and x < 230 and y >= 0 and y < 120):
                    grid[x][y][key] += 1
                    plot_x.append(x)
                    plot_y.append(y)
                    #fix later

def receive_input(sensel_device):

    global offset_x
    global offset_y

    for key in keys_pressed:
        for x in range(len(grid)):
            for y in range(len(grid[x])):
                if keys_pressed[key] > 0:
                    grid[x][y][key] /= (keys_pressed[key] + 0.0)

    print 'Start typing! :)'
    typed_chars = 0
    #still_typing = True
    output_str = ''
    possible_letters = []
    possible_words = []
    delete_cooldown = 0
    cooldown_mult = 1

    while True:
        if delete_cooldown != 0:
            delete_cooldown += cooldown_mult
        if delete_cooldown > 100:
            delete_cooldown = 0

        contacts = sensel_device.readContacts()
        if len(contacts) == 0:
            continue

        if len(contacts) == 8 and len([c for c in contacts if c.type == sensel.SENSEL_EVENT_CONTACT_START]):
            new_starting_x = 0
            new_starting_y = 0
            for c in contacts:
                new_starting_x += int(c.x_pos_mm)
                new_starting_y += int(c.y_pos_mm)
            new_starting_x /= 8
            new_starting_y /= 8
            offset_x = starting_x - new_starting_x
            offset_y = starting_y - new_starting_y
            #print 'offset_x: ', offset_x
            #print 'offset_y: ', offset_y
            output_str = ''

        if (len(contacts) == 3 and
            len([c for c in contacts if c.total_force > 7000]) == 3 and
            delete_cooldown == 0 and len(output_str)):
            average_forces = 0
            for c in contacts:
                average_forces += c.total_force
            average_forces /= 3
            cooldown_mult = ((average_forces - 6000) / 1000) ** 2
            delete_cooldown += cooldown_mult
            #length_last_word = len(output_str.rsplit(None, 1)[-1])
            #output_str = output_str[:len(output_str) - length_last_word - 1]
            output_str = output_str[:len(output_str) - 1]
            print output_str

        for c in contacts:
            if c.type == sensel.SENSEL_EVENT_CONTACT_START:
                typed_chars += 1
                x = int(c.x_pos_mm) + offset_x
                y = int(c.y_pos_mm) + offset_y
                if x >= 229:
                    x = 229
                if x < 0:
                    x = 0
                if y >= 119:
                    y = 119
                if y < 0:
                    y = 0
                total = 0
                for letter in grid[x][y]:
                    total += grid[x][y][letter]
                key = max(grid[x][y], key=grid[x][y].get)
                smaller_dict = copy.deepcopy(grid[x][y])
                del smaller_dict[key]
                key2 = max(smaller_dict, key=smaller_dict.get)
                if total > 0:
                    #print 'most likely: ', key, ' prob: ', grid[x][y][key], ' %: ', grid[x][y][key] / total
                    #print '2nd likely: ', key2, ' prob: ', grid[x][y][key2], ' %: ', grid[x][y][key2] / total
                    #print '\n'
                    output_str += key
                possible_letters.append((key, key2))
                if key == ' ':
                    possible_letters.pop()
                    possible_words = find_possible_words([], possible_letters)
                    real_words = []
                    for word in possible_words:
                        if word in english_words:
                            output_str = output_str[:len(output_str) - len(word) - 1] + word + ' '
                            break
                    possible_letters = []
                print output_str

        #still_typing = typed_chars < 320

    sensel_device.stopScanning();
    sensel_device.closeConnection();

def find_possible_words(list_of_words, list_of_tuples):
    if len(list_of_tuples) > 12:
        return []
    if not len(list_of_tuples):
        return list_of_words
    if not len(list_of_words):
        for letter in list_of_tuples[0]:
            list_of_words.append(letter)
        return find_possible_words(list_of_words, list_of_tuples[1:])
    new_words = []
    for word in list_of_words:
        for letter in list_of_tuples[0]:
            new_words.append(word + letter)
    return find_possible_words(new_words, list_of_tuples[1:])

def show_plot():
    hist2d(plot_x,plot_y, range=[[0, 230], [0, 120]], bins=[230,120])
    plt.gca().invert_yaxis()
    show()


if __name__ == "__main__":
    openSensorReadContacts()
